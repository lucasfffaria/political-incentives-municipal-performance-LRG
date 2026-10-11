import sys, json, pandas as pd
dados = json.load(open(sys.argv[1], encoding='utf-8'))
munis = pd.DataFrame(json.load(open(sys.argv[2], encoding='utf-8')))
rows = []
supp = {}
for cod, d in dados.items():
    r = {'cod_ibge': cod, 'ref': d.get('ref'), 'massa_total': d.get('massa_total'), 'massa_per_capita': d.get('massa_per_capita')}
    for linha, v in (d.get('linhas') or {}).items():
        if v is None: continue
        for k, x in v.items():
            if k == 'unidade': continue
            if k == 'esferas':
                for e, n in x.items(): r[f'{linha}_n_{e}'] = n
            elif isinstance(x, (dict, list)):
                r[f'{linha}_{k}'] = json.dumps(x, ensure_ascii=False)
            else:
                r[f'{linha}_{k}'] = x
    s = d.get('supressoes') or []
    if s: supp[cod] = s
    r['supressoes'] = json.dumps(s, ensure_ascii=False) if s else ''
    rows.append(r)
df = pd.DataFrame(rows)
munis = munis.rename(columns={'id':'cod_ibge'})
df = munis.merge(df, on='cod_ibge', how='outer')
print(df.shape, 'distinct', df.cod_ibge.nunique())
print(df.columns.tolist())
print('refs', df.ref.value_counts(dropna=False).to_dict())
for c in ['salario_privado_n','salario_publico_n','salario_publico_n_municipal','salario_publico_n_estadual','salario_publico_n_federal','bolsa_familia_n','bolsa_familia_massa','bolsa_familia_pessoas','previdencia_n','pop']:
    if c in df: print(c, 'sum=', df[c].sum(), 'nonnull=', df[c].notna().sum())
print('suppressions in', len(supp), 'munis; examples', list(supp.items())[:3])
print(df.sort_values('salario_privado_n', ascending=False)[['cod_ibge','nome','uf','salario_privado_n','salario_publico_n','bolsa_familia_n']].head(5).to_string())
bad = df[~df.cod_ibge.str.match(r'^\d{7}$', na=False)]
print('non-7-digit codes:', bad[['cod_ibge','nome','uf']].to_string() if len(bad) else 0)
df.to_csv(sys.argv[3], index=False)
