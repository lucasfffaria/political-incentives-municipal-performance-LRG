import sys, pandas as pd
bf_in, bf_out, pib_in, pib_out = sys.argv[1:5]
bf = pd.read_parquet(bf_in)
bf = bf.rename(columns={'quantidade_beneficiados': 'n_pagamentos_familias', 'valor_total': 'valor_total_reais'})
bf[['codigo_municipio_ibge','sigla_uf','codigo_municipio_siafi','nome_municipio','mes_referencia','n_pagamentos_familias','valor_total_reais']].to_csv(bf_out, index=False)
df = pd.read_excel(pib_in, sheet_name=0)
cols = list(df.columns)
keep = {cols[0]:'ano', cols[3]:'cod_uf', cols[4]:'sigla_uf', cols[6]:'cod_ibge', cols[7]:'nome_municipio',
        cols[29]:'amazonia_legal', cols[30]:'semiarido', cols[24]:'hierarquia_urbana',
        cols[32]:'vab_agropecuaria', cols[33]:'vab_industria', cols[34]:'vab_servicos_exc_adm_publica',
        cols[35]:'vab_adm_publica_defesa_educ_saude_seg_social', cols[36]:'vab_total', cols[37]:'impostos_liq_subsidios',
        cols[38]:'pib', cols[39]:'pib_per_capita_reais'}
out = df[list(keep)].rename(columns=keep)
out['populacao_implicita'] = (out.pib * 1000 / out.pib_per_capita_reais).round()
out.to_csv(pib_out, index=False)
print(bf.shape, out.shape)
print(out[out.ano==2021][['vab_total','pib']].sum()/1e6)
