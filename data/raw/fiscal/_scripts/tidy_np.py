import sys, json, pandas as pd
d = json.load(open(sys.argv[1], encoding='utf-8'))
df = pd.DataFrame(d['municipios'], columns=d['colunas'])
meta = pd.DataFrame(d['indicadores'])
per = dict(zip(meta.codigo, meta.periodo))
ren = {c: (c.replace('-', '_') + '_' + str(per[c])) for c in df.columns if c in per}
df = df.rename(columns=ren).rename(columns={'codigo': 'cod_ibge'})
df.to_csv(sys.argv[2], index=False)
meta[['codigo','nome','unidade','agregado','variavel','periodo','origem','coletadoEm']].to_csv(sys.argv[3], index=False)
print(df.shape, 'distinct', df.cod_ibge.nunique())
for c in ['assalariados_empresas_2024','pessoal_ocupado_empresas_2024','empresas_atuantes_2024','salarios_empresas_2024','pib_municipal_2023','populacao_censo_2022_2022','populacao_estimada_2026']:
    print(c, 'sum=', df[c].sum(), 'nonnull=', df[c].notna().sum())
print(df.sort_values('assalariados_empresas_2024', ascending=False)[['cod_ibge','nome','uf','assalariados_empresas_2024','pessoal_ocupado_empresas_2024']].head(4).to_string())
