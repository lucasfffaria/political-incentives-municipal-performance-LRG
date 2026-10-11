import sys, gzip, json, struct
import numpy as np, pandas as pd
from pathlib import Path
raw = Path(sys.argv[1]); out = Path(sys.argv[2])
mun = json.loads(gzip.decompress((raw/'municipios.json.gz').read_bytes()))
meta = json.loads((raw/'meta.json').read_text(encoding='utf-8'))
codes = mun['mun']; names = mun['nome']; ufs = mun['uf']
print('dict munis', len(codes), codes[:3], names[:3], ufs[:3])
print('setor dims', meta['dims']['setor'])
TY = {'u8': np.uint8, 'u16': np.uint16, 'u32': np.uint32}
def decode(path):
    b = gzip.decompress(path.read_bytes())
    hl = struct.unpack('<I', b[:4])[0]
    hdr = json.loads(b[4:4+hl].decode().strip())
    n = hdr['n']; base = 4 + hl
    cols = {}
    for c in hdr['cols']:
        t = TY[c['t']]; size = np.dtype(t).itemsize
        start = base + c['o']; buf = np.frombuffer(b, dtype=np.uint8, count=n*size, offset=start)
        if c.get('p'):
            arr = buf.reshape(size, n).T.copy().view('<u4').reshape(n)
        else:
            arr = buf.view(t).copy()
        cols[c['k']] = arr
    return pd.DataFrame(cols)
frames = []
for y in range(2006, 2025):
    df = decode(raw/f'mun_{y}.bin.gz')
    df['ano'] = y
    frames.append(df)
d = pd.concat(frames, ignore_index=True)
print(d.shape, d.columns.tolist())
d['id_municipio'] = np.array(codes)[d['mi'].astype(int)]
d['rem_n'] = (d['ativos'].astype('int64') - d['rem_f'].astype('int64')).clip(lower=0)
d['rem_s_aprox'] = d['rem_m'].astype('int64') * d['rem_n']
g = d.groupby(['ano','id_municipio','setor'], as_index=False)[['ativos','adm','desl','rem_n','rem_s_aprox']].sum()
w = g.pivot_table(index=['ano','id_municipio'], columns='setor', values=['ativos','rem_s_aprox','rem_n'], aggfunc='sum', fill_value=0)
w.columns = [f'{a}_setor{s}' for a, s in w.columns]
w = w.reset_index()
tot = g.groupby(['ano','id_municipio'], as_index=False)[['ativos','adm','desl','rem_n','rem_s_aprox']].sum()
res = tot.merge(w, on=['ano','id_municipio'])
ren = {'ativos_setor1':'ativos_adm_publica','ativos_setor2':'ativos_empresas','ativos_setor3':'ativos_sem_fins_outros',
       'rem_s_aprox_setor1':'rem_dez_soma_adm_publica','rem_s_aprox_setor2':'rem_dez_soma_empresas','rem_s_aprox_setor3':'rem_dez_soma_sem_fins_outros',
       'rem_n_setor1':'rem_n_adm_publica','rem_n_setor2':'rem_n_empresas','rem_n_setor3':'rem_n_sem_fins_outros',
       'ativos':'ativos_total','adm':'admissoes','desl':'desligamentos','rem_s_aprox':'rem_dez_soma_total','rem_n':'rem_n_total'}
res = res.rename(columns=ren)
nm = dict(zip(codes, names)); uf = dict(zip(codes, ufs))
res.insert(2, 'nome', res.id_municipio.map(nm)); res.insert(3, 'cod_uf', res.id_municipio.map(uf))
res.to_csv(out, index=False)
print(res.shape)
s = res.groupby('ano').agg(n=('id_municipio','nunique'), ativos=('ativos_total','sum'), adm_pub=('ativos_adm_publica','sum'))
print(s.to_string())
r24 = res[res.ano==2024].sort_values('ativos_total', ascending=False).head(5)
print(r24[['id_municipio','nome','cod_uf','ativos_total','ativos_adm_publica']].to_string())
r = res[res.ano==2024]
print('2024 munis with zero active jobs:', (r.ativos_total==0).sum(), ' median public share:', (r.ativos_adm_publica/r.ativos_total).median())
