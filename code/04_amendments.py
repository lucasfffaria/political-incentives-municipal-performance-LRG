"""
04_amendments.py -- how parliamentary amendments reach municipalities today (real data: the 13,177 action plans
of the 2025 "transferencias especiais", i.e. the most discretionary amendments, R$ 8.2 bn to municipalities).

(1) where the money goes by policy area (what it buys), (2) per capita by size and region, against need,
(3) political alignment: share of each author's money going to mayors of the author's own party, against the
share expected if the author spread the money over the municipalities of the state in proportion to population.
Outputs: output/amendments.json, tables/T_amendments_area.csv, tables/T_amendments_alignment.csv
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, re
import numpy as np
import pandas as pd

RAW = _ROOT + '/data/raw/elections/emendas_transferegov_tb'
DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'; TAB = _ROOT + '/tables'
NORM = {'PODE': 'PODEMOS', 'PC do B': 'PCDOB', 'UNIÃO': 'UNIAO', 'PSL': 'UNIAO', 'DEM': 'UNIAO', 'PRB': 'REPUBLICANOS',
        'PR': 'PL', 'PPS': 'CIDADANIA', 'PMDB': 'MDB', 'PATRIOTA': 'PRD', 'PTB': 'PRD', 'PROS': 'SOLIDARIEDADE',
        'PSC': 'PODEMOS', 'PHS': 'PODEMOS', 'PMN': 'MOBILIZA', 'PTC': 'AGIR', 'SD': 'SOLIDARIEDADE'}
b = pd.read_csv(DER + '/municipios_base.csv')
pl = pd.read_csv(RAW + '/transferencias_especiais_2025_plano_acao_enriquecido.csv')
pl = pl[pl.codigo_ibge_municipio.notna()].copy()
pl['cod_ibge'] = pl.codigo_ibge_municipio.astype(int)
pl = pl[pl.cod_ibge.isin(b.cod_ibge)]
res = {'n_plans': int(len(pl)), 'value_bn': float(pl.valor_plano.sum() / 1e9), 'paid_bn': float(pl.valor_pago.sum() / 1e9),
       'n_municipalities': int(pl.cod_ibge.nunique()), 'n_authors': int(pl.codigo_parlamentar_emenda_plano_acao.nunique())}
res['share_impeded'] = float(pl.loc[pl.situacao_plano_acao.str.contains('IMPEDIDO', na=False), 'valor_plano'].sum() / pl.valor_plano.sum())

# ---------------------------------------------------------------- (1) policy areas (first function listed; split equally if several)
def areas(s):
    if not isinstance(s, str) or not s.strip():
        return ['Not reported']
    out = []
    for part in s.split(','):
        m = re.match(r'\s*(\d+)-([^/]+)', part)
        if m:
            out.append(m.group(2).strip())
    return out or ['Not reported']
rows = []
for v, s in zip(pl.valor_plano, pl.codigo_descricao_areas_politicas_publicas_plano_acao):
    a = areas(s)
    for x in a:
        rows.append((x, v / len(a)))
ar = pd.DataFrame(rows, columns=['area', 'value']).groupby('area').value.sum().sort_values(ascending=False)
ar = (ar / ar.sum()).rename('share').reset_index()
ar.to_csv(TAB + '/T_amendments_area.csv', index=False)
res['area_shares'] = dict(zip(ar.area, ar.share.round(4)))
print(ar.head(15).to_string())

# ---------------------------------------------------------------- (2) per capita and need
b['pix_pc'] = b.pix_plan_2025 / b.pop2024
b['cls'] = pd.cut(b.pop2024, [0, 5e3, 1e4, 2e4, 5e4, 1e5, np.inf], labels=['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k'])
res['per_capita_by_size'] = b.groupby('cls', observed=True).apply(lambda g: g.pix_plan_2025.sum() / g.pop2024.sum()).round(1).to_dict()
res['per_capita_by_region'] = b.groupby('region').apply(lambda g: g.pix_plan_2025.sum() / g.pop2024.sum()).round(1).to_dict()
res['share_munis_zero'] = float((b.pix_plan_2025 == 0).mean())
lp = np.log1p(b.pix_pc)
for need, lab in [('bf_share_households', 'corr_with_bolsa_familia_share'), ('sh_sewer_census', 'corr_with_sewer_share'),
                  ('K3_literacy_2024', 'corr_with_literacy'), ('gdp_pc_2021', 'corr_with_log_gdp_pc')]:
    x = np.log(b[need]) if need == 'gdp_pc_2021' else b[need]
    ok = x.notna() & lp.notna()
    res[lab] = float(np.corrcoef(lp[ok], x[ok])[0, 1])
# partial: within size class
res['corr_with_bf_within_size'] = float(b.assign(lp=lp).groupby('cls', observed=True).apply(
    lambda g: np.corrcoef(g.lp, g.bf_share_households)[0, 1]).mean())

# ---------------------------------------------------------------- (3) alignment with the mayor's party
b['party24'] = b.party_2024.replace(NORM)
pl['party_author'] = pl.partido_eleicao.replace(NORM)
pl['party_mayor'] = pl.cod_ibge.map(b.set_index('cod_ibge').party24)
pl['uf'] = pl.uf_beneficiario_plano_acao
dep = pl[pl.cargo.str.contains('DEPUTADO', na=False) & pl.party_author.notna()].copy()
dep['same'] = (dep.party_author == dep.party_mayor)
obs = dep.groupby('codigo_parlamentar_emenda_plano_acao').apply(lambda g: (g.valor_plano * g.same).sum() / g.valor_plano.sum())
# expected: share of the author's state population (and of the state's municipalities) governed by the author's party
popsh = b.groupby(['uf', 'party24']).pop2024.sum() / b.groupby('uf').pop2024.sum()
cntsh = b.groupby(['uf', 'party24']).size() / b.groupby('uf').size()
auth = dep.groupby('codigo_parlamentar_emenda_plano_acao').agg(uf=('uf', lambda s: s.mode().iloc[0]), party=('party_author', 'first'),
                                                              value=('valor_plano', 'sum'))
auth['obs_same'] = obs
auth['exp_pop'] = [popsh.get((u, p), 0.0) for u, p in zip(auth.uf, auth.party)]
auth['exp_cnt'] = [cntsh.get((u, p), 0.0) for u, p in zip(auth.uf, auth.party)]
w = auth.value / auth.value.sum()
res['alignment'] = dict(value_weighted_obs=float((auth.obs_same * w).sum()), value_weighted_exp_pop=float((auth.exp_pop * w).sum()),
                        value_weighted_exp_cnt=float((auth.exp_cnt * w).sum()), n_deputies=int(len(auth)))
res['alignment']['ratio_obs_to_exp_cnt'] = res['alignment']['value_weighted_obs'] / res['alignment']['value_weighted_exp_cnt']
byp = auth.groupby('party').apply(lambda g: pd.Series({'n_deputies': len(g), 'value_mn': g.value.sum() / 1e6,
                                                         'obs_same': np.average(g.obs_same, weights=g.value),
                                                         'exp_same_cnt': np.average(g.exp_cnt, weights=g.value)}))
byp['ratio'] = byp.obs_same / byp.exp_same_cnt.replace(0, np.nan)
byp = byp.sort_values('value_mn', ascending=False)
byp.round(3).to_csv(TAB + '/T_amendments_alignment.csv')
print(byp.round(3).head(14).to_string())
# concentration: number of municipalities per author and share of the author's money in the top municipality
g = dep.groupby('codigo_parlamentar_emenda_plano_acao')
res['author_concentration'] = dict(median_munis=float(g.cod_ibge.nunique().median()),
                                   median_top1_share=float(g.apply(lambda x: x.groupby('cod_ibge').valor_plano.sum().max() / x.valor_plano.sum()).median()))
json.dump(res, open(OUT + '/amendments.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k != 'area_shares'}, indent=1, default=float))
