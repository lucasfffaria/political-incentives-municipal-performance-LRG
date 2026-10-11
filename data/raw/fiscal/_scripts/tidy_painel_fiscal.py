import sys, json, unicodedata, re
import pandas as pd
from pathlib import Path
src = Path(sys.argv[1]); out = Path(sys.argv[2])
d = json.load(open(src, encoding='utf-8'))
def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')
# 1. RGF 2024 Q3 personnel
cols = ['cod_ibge','nome','uf','populacao','publicou','pct_pessoal_rcl_ajustada','limite_prudencial_pct','despesa_pessoal','rcl_ajustada']
assert d['colunas'] == ['codigo','nome','uf','populacao','publicou','percentual','limitePrudencial','despesa','rclAjustada'], d['colunas']
rgf = pd.DataFrame(d['municipios'], columns=cols)
rgf.insert(1, 'exercicio', d['exercicio']); rgf.insert(2, 'quadrimestre', d['periodo'])
rgf.to_csv(out/'siconfi_rgf_anexo01_pessoal_2024q3.csv', index=False)
base = rgf[['cod_ibge','nome','uf','populacao']]
# 2. RGF series (percent only)
rows = []
for cod, lst in d['serie'].items():
    for ex, pe, pub, pct in lst:
        rows.append((int(cod), ex, pe, pub, pct))
ser = pd.DataFrame(rows, columns=['cod_ibge','exercicio','quadrimestre','publicou','pct_pessoal_rcl_ajustada'])
ser.to_csv(out/'siconfi_rgf_anexo01_pct_pessoal_serie_2020_2024.csv', index=False)
# 3. RREO Anexo 01 revenues
r = d['receita']; rot = [slug(x) for x in r['rotulos']]; rotd = [slug(x) for x in r['rotulosDetalhe']]
rows = []
for ex in r['exercicios']:
    for cod, (total, vals, det) in ex['porMunicipio'].items():
        row = {'cod_ibge': int(cod), 'exercicio': ex['exercicio'], 'bimestre': r['periodo'], 'receitas_correntes_total_declarado': total}
        for c in rot: row[c] = 0
        for c in rotd: row['det_' + c] = None
        for i, v in vals: row[rot[i]] = v
        for i, v in det: row['det_' + rotd[i]] = v
        rows.append(row)
rec = pd.DataFrame(rows)
rec = base.merge(rec, on='cod_ibge', how='right')
rec.to_csv(out/'siconfi_rreo_anexo01_receitas_correntes_2024.csv', index=False)
# 4. RREO Anexo 02 functions
f = d['funcoes']; frot = [slug(x) for x in f['rotulos']]
rows = []
for ex in f['exercicios']:
    for cod, (total, vals) in ex['porMunicipio'].items():
        row = {'cod_ibge': int(cod), 'exercicio': ex['exercicio'], 'bimestre': f['periodo'], 'despesa_liquidada_total_declarado': total}
        for c in frot: row[c] = 0
        for i, v in vals: row[frot[i]] = v
        rows.append(row)
fun = pd.DataFrame(rows)
fun.to_csv(out/'siconfi_rreo_anexo02_despesa_funcao_2019_2024.csv', index=False)
# 5. SIOPS
s = d['saude']; rows = []
for cod, vals in s['porMunicipio'].items():
    for ano, v in zip(s['anos'], vals):
        rows.append((int(cod), ano, v))
sio = pd.DataFrame(rows, columns=['cod_ibge','ano','pct_recursos_proprios_saude_ec29'])
sio.to_csv(out/'siops_pct_recursos_proprios_saude_2000_2025.csv', index=False)
# ---- verification
print('RGF 2024Q3:', rgf.shape, 'distinct', rgf.cod_ibge.nunique(), 'published', int(rgf.publicou.sum()))
print(rgf[rgf.publicou].sort_values('despesa_pessoal', ascending=False)[['nome','uf','despesa_pessoal','rcl_ajustada','pct_pessoal_rcl_ajustada']].head(4).to_string())
print('pct>54 among published:', int((rgf.pct_pessoal_rcl_ajustada>54).sum()), ' median pct', rgf.pct_pessoal_rcl_ajustada.median())
bins = [0,5000,10000,20000,50000,100000,1e9]
rgf['faixa'] = pd.cut(rgf.populacao, bins)
print(rgf.groupby('faixa', observed=True).publicou.agg(['size','sum','mean']).to_string())
print('RGF serie:', ser.shape, 'munis', ser.cod_ibge.nunique(), ser.groupby(['exercicio','quadrimestre']).publicou.sum().to_dict())
print('RREO rec:', rec.shape, 'distinct', rec.cod_ibge.nunique())
print(rec.sort_values('impostos_taxas_e_contribuicoes_de_melhoria', ascending=False)[['nome','uf','receitas_correntes_total_declarado','impostos_taxas_e_contribuicoes_de_melhoria','det_impostos','transferencias_correntes','det_transferencias_da_uniao_e_de_suas_entidades']].head(5).to_string())
chk = rec[rot].sum(axis=1) - rec.receitas_correntes_total_declarado
print('components minus declared total: max abs', chk.abs().max())
print('sum receitas correntes (R$ bn)', rec.receitas_correntes_total_declarado.sum()/1e9)
print('FUN:', fun.shape, fun.groupby('exercicio').cod_ibge.nunique().to_dict())
print('SIOPS:', sio.shape, 'munis', sio.cod_ibge.nunique(), 'nonnull', sio.pct_recursos_proprios_saude_ec29.notna().sum())
