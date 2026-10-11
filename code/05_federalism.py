"""
05_federalism.py -- the federative side of the reform, with real data:
 (1) fiscal "viability": own tax revenue / current revenue (SICONFI RREO 2024, 3,243 municipalities; imputed for
     the rest from size, income and region), the PEC 188/2019 criterion (< 5,000 inhabitants and own taxes < 10%);
 (2) a merger exercise: each PEC-188 municipality joins its most populous contiguous neighbour in the same state;
     effects on the number of mayors and councils, on councillor pay, and on the FPM (concave coefficients);
 (3) unpaid councillors below 65,000 inhabitants (CF art. 29 IV and VI caps);
 (4) the Comissariado: staffing and cost under the proposal and under a feasible ramp;
 (5) do fiscal viability and scorecard performance pick the same municipalities?
Outputs: output/federalism.json, tables/T_viability.csv
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import numpy as np
import pandas as pd
import geopandas as gpd

DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'; TAB = _ROOT + '/tables'
b = pd.read_csv(DER + '/municipios_base.csv')
res = {}
EDG = [0, 5e3, 1e4, 2e4, 5e4, 1e5, np.inf]
LAB = ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']
b['cls'] = pd.cut(b.pop2024, EDG, labels=LAB)

# ---------------------------------------------------------------- (1) own tax share, observed and imputed
obs = b.own_tax_share_2024.notna() & (b.own_tax_share_2024 > 0) & (b.own_tax_share_2024 < 0.9)
X = pd.DataFrame({'lpop': np.log(b.pop2024), 'lpop2': np.log(b.pop2024) ** 2, 'lgdp': np.log(b.gdp_pc_2021),
                  'agro': b.va_agro_share_2021, 'pubva': b.va_pub_share_2021, 'cap': b.capital,
                  'bf': b.bf_share_households, 'hied': b.higher_ed_share})
for r in ['NE', 'N', 'S', 'CO']:
    X['r_' + r] = (b.region == r).astype(float)
X = X.fillna(X.median())
Xo = np.c_[np.ones(obs.sum()), X[obs].values]
yo = np.log(b.loc[obs, 'own_tax_share_2024'] / (1 - b.loc[obs, 'own_tax_share_2024']))
beta, *_ = np.linalg.lstsq(Xo, yo.values, rcond=None)
resid_sd = np.std(yo.values - Xo @ beta)
pred = np.c_[np.ones(len(b)), X.values] @ beta
rng = np.random.default_rng(5)
draws = pred[:, None] + resid_sd * rng.standard_normal((len(b), 500))
share_draws = 1 / (1 + np.exp(-draws))
share_draws[obs.values] = b.loc[obs, 'own_tax_share_2024'].values[:, None]
r2 = 1 - np.var(yo.values - Xo @ beta) / np.var(yo.values)
b['own_tax_hat'] = np.where(obs, b.own_tax_share_2024, 1 / (1 + np.exp(-pred)))
small = (b.pop2022 < 5000).values
below10 = share_draws < 0.10
res['own_tax'] = dict(n_observed=int(obs.sum()), r2_logit_model=float(r2),
                      observed_share_below10=float((b.loc[obs, 'own_tax_share_2024'] < 0.10).mean()),
                      n_below10_all=[float(np.percentile(below10.sum(0), q)) for q in (5, 50, 95)],
                      n_pec188=[float(np.percentile((below10 & small[:, None]).sum(0), q)) for q in (5, 50, 95)],
                      n_small=int(small.sum()),
                      pop_pec188_mn=float(np.median(((below10 & small[:, None]) * b.pop2022.values[:, None]).sum(0)) / 1e6),
                      median_share_by_size={k: float(v) for k, v in b.groupby('cls', observed=True).own_tax_hat.median().items()},
                      note='RREO "impostos" includes IRRF retained by the municipality (art. 158 I); the PEC 188 test used IPTU, ISS and ITBI only, so these shares are upper bounds.')
for reg in ['N', 'NE', 'SE', 'S', 'CO']:
    m = (b.region == reg).values
    res['own_tax'].setdefault('n_below10_by_region', {})[reg] = float(np.median(below10[m].sum(0)))
tv = b.groupby('cls', observed=True).agg(n=('cod_ibge', 'size'), observed=('own_tax_share_2024', lambda s: s.notna().sum()),
                                         own_tax_median=('own_tax_hat', 'median'),
                                         fpm_pc=('fpm_gross_2024', lambda s: np.nan))
tv['fpm_pc'] = b[b.cod_ibge != 5300108].groupby('cls', observed=True).apply(lambda g: g.fpm_gross_2024.sum() / g.pop2024.sum())   # Brasilia receives no FPM
tv['share_below10'] = [float(np.median(below10[(b.cls == c_).values].mean(0))) for c_ in tv.index]
tv.to_csv(TAB + '/T_viability.csv')
print(tv.round(3))

# ---------------------------------------------------------------- (2) merger exercise (median own-tax draw)
pec = small & (b.own_tax_hat.values < 0.10)
g = gpd.read_file(_ROOT + '/data/raw/geo/geojs-100-mun.json')
g['cod_ibge'] = g.id.astype(int)
g = g.merge(b[['cod_ibge', 'pop2022', 'uf']], on='cod_ibge', how='inner').to_crs(5880)
g['geometry'] = g.buffer(50)
nb = gpd.sjoin(g[['cod_ibge', 'geometry']], g[['cod_ibge', 'geometry']], predicate='intersects')
nb = nb[nb.cod_ibge_left != nb.cod_ibge_right]
popd = b.set_index('cod_ibge').pop2022; ufd = b.set_index('cod_ibge').uf
nb = nb[[ufd.get(a) == ufd.get(c_) for a, c_ in zip(nb.cod_ibge_left, nb.cod_ibge_right)]]
pecset = set(b.loc[pec, 'cod_ibge'])
target = {}
for cod, grp in nb.groupby('cod_ibge_left'):
    if cod in pecset:
        cands = [x for x in grp.cod_ibge_right if x not in pecset] or list(grp.cod_ibge_right)
        target[cod] = max(cands, key=lambda x: popd.get(x, 0))
# resolve chains (pec -> pec) to a final host
host = {}
for cod in target:
    t = target[cod]; seen = {cod}
    while t in target and t not in seen:
        seen.add(t); t = target[t]
    host[cod] = t
b['host'] = b.cod_ibge.map(host).fillna(b.cod_ibge).astype(int)
newpop = b.groupby('host').pop2024.sum()
brk = [10188, 13584, 16980, 23772, 30564, 37356, 44148, 50940, 61128, 71316, 81504, 91692, 101880, 115464,
       129048, 142632, 156216]
coefs = np.arange(0.6, 4.01, 0.2)
coef_of = lambda p: coefs[np.searchsorted(brk, p, side='left')]
b['coef_now'] = coef_of(b.pop2024.values)
merged = b[b.capital == 0].copy()
coef_new = merged.groupby('host').pop2024.sum().map(coef_of)
st_now = merged.groupby('uf').coef_now.sum()
coef_new_df = pd.DataFrame({'host': coef_new.index, 'coef': coef_new.values})
coef_new_df['uf'] = coef_new_df.host.map(ufd)
st_new = coef_new_df.groupby('uf').coef.sum()
# FPM to merged areas before and after (within-state shares are fixed; the state pool is redistributed)
areas = merged.groupby('host').agg(coef_old=('coef_now', 'sum'), fpm_old=('fpm_gross_2024', 'sum'), n=('cod_ibge', 'size'),
                                   uf=('uf', 'first'))
areas['coef_new'] = coef_new
areas['fpm_new'] = areas.fpm_old / areas.coef_old * areas.coef_new * areas.uf.map(st_now / st_new)
mareas = areas[areas.n > 1]
n_merged = int(pec.sum())
pay_cap = {0: 0.20, 1: 0.30, 2: 0.40, 3: 0.50, 4: 0.60, 5: 0.75}
STATE_DEP = 33006.39                              # 75% of the federal deputy subsidy (R$ 44,008.52, 2025)


def councillors(p):
    caps = [(15e3, 9), (30e3, 11), (50e3, 13), (80e3, 15), (120e3, 17), (160e3, 19), (300e3, 21), (450e3, 23),
            (600e3, 25), (750e3, 27), (900e3, 29), (1.05e6, 31), (1.2e6, 33), (1.35e6, 35), (1.5e6, 37), (1.8e6, 39),
            (2.4e6, 41), (3e6, 43), (4e6, 45), (5e6, 47), (6e6, 49), (7e6, 51), (8e6, 53)]
    for lim, n in caps:
        if p <= lim:
            return n
    return 55


def pay_share(p):
    return 0.20 if p <= 1e4 else 0.30 if p <= 5e4 else 0.40 if p <= 1e5 else 0.50 if p <= 3e5 else 0.60 if p <= 5e5 else 0.75


b['councillors_max'] = b.pop2022.map(councillors)
b['councillor_pay_cap'] = b.pop2022.map(pay_share) * STATE_DEP
seats_lost = b.loc[pec, 'councillors_max'].sum()
pay_lost = (b.loc[pec, 'councillors_max'] * b.loc[pec, 'councillor_pay_cap'] * 13).sum()
res['mergers'] = dict(n_absorbed=n_merged, n_host_areas=int(len(mareas)),
                      pop_absorbed_mn=float(b.loc[pec, 'pop2024'].sum() / 1e6),
                      municipalities_after=int(len(b) - n_merged),
                      councillor_seats_removed=int(seats_lost), councillor_pay_saved_bn_cap=float(pay_lost / 1e9),
                      fpm_change_merged_areas_bn=float((mareas.fpm_new - mareas.fpm_old).sum() / 1e9),
                      fpm_change_merged_areas_pct=float((mareas.fpm_new.sum() / mareas.fpm_old.sum() - 1) * 100),
                      fpm_merged_areas_bn=float(mareas.fpm_old.sum() / 1e9),
                      share_absorbed_NE=float((b.loc[pec, 'region'] == 'NE').mean()),
                      by_region={r: int(((b.region == r) & pec).sum()) for r in ['N', 'NE', 'SE', 'S', 'CO']})
print(json.dumps(res['mergers'], indent=1))

# ---------------------------------------------------------------- (3) unpaid councillors below 65,000
sm = b.pop2022 <= 65000
tot_seats = b.councillors_max.sum()
res['councillors'] = dict(max_seats_total=int(tot_seats), seats_below65k=int(b.loc[sm, 'councillors_max'].sum()),
                          municipalities_below65k=int(sm.sum()),
                          pay_cap_bill_below65k_bn=float((b.loc[sm, 'councillors_max'] * b.loc[sm, 'councillor_pay_cap'] * 13).sum() / 1e9),
                          pay_cap_bill_all_bn=float((b.councillors_max * b.councillor_pay_cap * 13).sum() / 1e9),
                          state_deputy_subsidy=STATE_DEP,
                          note='Upper bounds: the caps are maxima; councils fix pay below them and may have fewer seats.')
print(json.dumps(res['councillors'], indent=1))

# ---------------------------------------------------------------- (4) Comissariado
cost = 0.35e6
res['comissariado'] = dict(one_per_municipality_cost_bn=float(len(b) * cost / 1e9),
                           teams_of_three_cost_bn=float(3 * len(b) * cost / 1e9),
                           eppgg_active_2023=930, cnu_2024_federal_vacancies_note='ATPS 500, EPPGG 150 in the 2024 national exam',
                           years_to_staff_at_1500=float(len(b) / 1500),
                           cost_share_of_fpm=float(len(b) * cost / b.fpm_gross_2024.sum()))

# ---------------------------------------------------------------- (5) viability vs performance
kp = {'K1_formal_jobs_2024': 1, 'K3_literacy_2024': 1, 'K4_daycare_2023': 1, 'sh_sewer_census': 1, 'hom_rate_2022': -1,
      'ideb_2025': 1}
z = pd.DataFrame({k: s * (b[k] - b[k].mean()) / b[k].std() for k, s in kp.items()})
b['perf_index'] = z.mean(1)
res['viability_vs_performance'] = dict(
    corr_owntax_perf=float(np.corrcoef(np.log(b.own_tax_hat), b.perf_index.fillna(b.perf_index.mean()))[0, 1]),
    perf_pec188_mean=float(b.loc[pec, 'perf_index'].mean()), perf_others_small_mean=float(b.loc[small & ~pec, 'perf_index'].mean()),
    perf_all_mean=float(b.perf_index.mean()),
    share_pec188_in_bottom_quintile_perf=float((b.loc[pec, 'perf_index'] < b.perf_index.quantile(0.2)).mean()))
print(json.dumps(res['viability_vs_performance'], indent=1))
b[['cod_ibge', 'own_tax_hat', 'host', 'perf_index', 'councillors_max', 'councillor_pay_cap']].to_csv(DER + '/federalism_muni.csv', index=False)
json.dump(res, open(OUT + '/federalism.json', 'w'), indent=1, default=float)
