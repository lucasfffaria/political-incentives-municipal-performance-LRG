import sys, os, json, glob
import pandas as pd
D = sys.argv[1]
rows, tots = [], []
for f in sorted(glob.glob(os.path.join(D, 'json', '*-c0006.json'))):
    j = json.load(open(f, encoding='utf-8'))
    uf = j['cdabr'].upper()
    assert j['carg'][0]['cd'] == '6'
    tots.append({'sg_uf': uf, 'vagas_uf': int(j['carg'][0]['nv']), 'votos_validos_total_uf': int(j['v']['vv']),
                 'votos_brancos': int(j['v']['vb']), 'votos_nulos': int(j['v']['tvn']), 'comparecimento': int(j['e']['c']),
                 'eleitores_aptos': int(j['e']['te']), 'data_totalizacao': j['dt']})
    for g in j['carg'][0]['agr']:
        for p in g['par']:
            n_el = sum(1 for c in p['cand'] if c['e'] == 's')
            rows.append({'sg_uf': uf, 'agremiacao': g['com'], 'agremiacao_vagas': int(g['vag']), 'sg_partido': p['sg'],
                         'votos_nominais_validos': int(p['tvan']), 'eleitos': n_el, 'n_candidatos_com_votos': len(p['cand'])})
df = pd.DataFrame(rows); tt = pd.DataFrame(tots)
tt['votos_nominais_validos_uf'] = tt.sg_uf.map(df.groupby('sg_uf').votos_nominais_validos.sum())
tt['votos_legenda_uf_implicito'] = tt.votos_validos_total_uf - tt.votos_nominais_validos_uf
tt['eleitos_uf'] = tt.sg_uf.map(df.groupby('sg_uf').eleitos.sum())
df.to_csv(os.path.join(D, 'camara_2022_partido_uf.csv'), index=False)
tt.to_csv(os.path.join(D, 'camara_2022_totais_uf.csv'), index=False)
nat = df.groupby('sg_partido').agg(votos_nominais_validos=('votos_nominais_validos','sum'), eleitos=('eleitos','sum')).sort_values('eleitos', ascending=False)
nat['share_votos_nominais'] = nat.votos_nominais_validos / nat.votos_nominais_validos.sum()
nat.to_csv(os.path.join(D, 'camara_2022_partido_nacional.csv'))
print(nat.to_string())
print('total seats', nat.eleitos.sum(), 'UF check', (tt.vagas_uf == tt.eleitos_uf).all())
print(tt[['sg_uf','vagas_uf','eleitos_uf','votos_validos_total_uf','votos_nominais_validos_uf','votos_legenda_uf_implicito','data_totalizacao']].to_string())
print('national valid votes', tt.votos_validos_total_uf.sum(), 'nominal', tt.votos_nominais_validos_uf.sum())
