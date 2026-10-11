"""
18_fpm_rd.py -- how much do municipal indicators improve when a municipality receives more unconditional federal
money? Regression discontinuity at the population brackets of the FPM (Brollo et al., 2013).

The FPM coefficient of an interior municipality rises in steps of 0.2 at 10,189, 13,585, 16,981, 23,773, 30,565,
37,357 and 44,149 inhabitants, so a municipality just above a bracket receives 11-33% more FPM than one just
below. Part A documents that the population counts that reset the coefficients (2000, 2010 and 2022 Censuses, 2007
Count) bunch just above the thresholds, while IBGE's intercensal estimates do not. Part B therefore uses the 2013
IBGE estimate as the running variable (the estimates set the 2014-19 coefficients and show no bunching) and
outcomes over 2013-2019, before the 2019 freeze of coefficients. Thresholds are pooled with the distance to the
threshold in percent, with threshold and state fixed effects (robust bias-corrected local-linear estimates).

Money is expressed in R$ per inhabitant a year at 2024 values of the FPM structure, multiplied by the real value
of the FPM in 2014-19 relative to 2024 (REAL_1419, an assumption with a range in the calibration).
Writes output/fpm_rd.json and tables/fpm_rd.csv.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, warnings
import numpy as np
import pandas as pd
from rdrobust import rdrobust
from rddensity import rddensity

warnings.filterwarnings('ignore')
DER = _ROOT + '/data/derived'
OUT = _ROOT + '/output'
TAB = _ROOT + '/tables'
SDU = {'jobs': 0.89, 'va': 10.8, 'lit': 9.6, 'day': 12.2, 'sew': 23.5, 'hom': 10.9}
REAL_1419 = 0.63                      # real FPM 2014-19 relative to 2024; the calibration draws it from U(0.55, 0.75)
T = np.array([10189, 13585, 16981, 23773, 30565, 37357, 44149])
BRK = [10188, 13584, 16980, 23772, 30564, 37356, 44148, 50940, 61128, 71316, 81504, 91692, 101880, 115464, 129048, 142632, 156216]
COEFS = np.arange(0.6, 4.01, 0.2)
coef_of = lambda p: COEFS[np.searchsorted(BRK, p, side='left')]

base = pd.read_csv(DER + '/municipios_base.csv')
pp = pd.read_csv(_ROOT + '/data/raw/social/populacao/ibge_pop_municipios_2000_2025.csv')
POP = pp.pivot_table(index='code_muni', columns='year', values='pop')     # IBGE counts and estimates (TCU basis)
b = base.set_index('cod_ibge')
b['per_coef'] = b.fpm_gross_2024 / b.fpm_coef                  # R$ per coefficient unit, 2024 (state-specific)
st_pc = b[b.capital == 0].groupby('uf').per_coef.median()


def panel(name, col='value'):
    d = pd.read_csv(f'{DER}/{name}.csv')
    return d.pivot_table(index='cod_ibge', columns='year', values=col)


J = np.log(panel('panel_K1_formal_jobs').clip(lower=0.2))
VA = panel('panel_K2_private_va_share')
DAY = panel('panel_K4_daycare')
HOM = panel('panel_K7_homicides')
ID = panel('panel_E_ideb')
LIT = panel('panel_K3_literacy')
sn = pd.read_csv(DER + '/panel_K6_sanitation_snis.csv')
SEW = sn.pivot_table(index='cod_ibge', columns='year', values='sewer_pop_share')
if SEW.stack().max() <= 1.5:
    SEW = 100 * SEW
idb = ID[2019].rename('i').to_frame().join(b.uf)
SDU['ideb'] = float(np.sqrt((idb.i - idb.groupby('uf').i.transform('mean')).pow(2).mean()))

# ------------------------------------------------------------------ A: bunching above the thresholds, by year
bun = []
for y in sorted(POP.columns):
    p = POP[y].dropna()
    p = p[~p.index.isin(b.index[b.capital == 1])]
    row = dict(year=int(y), kind='count' if y in (2000, 2007, 2010, 2022) else 'estimate')
    for w in (1, 2):
        lo = hi = 0
        for t in T:
            r = 100 * (p - t) / t
            lo += int(((r >= -w) & (r < 0)).sum()); hi += int(((r >= 0) & (r < w)).sum())
        row[f'below_{w}pct'] = lo; row[f'above_{w}pct'] = hi
    bun.append(row)
BUN = pd.DataFrame(bun)
BUN.to_csv(TAB + '/fpm_bunching.csv', index=False)

# ------------------------------------------------------------------ B: regression discontinuity on the 2013 estimate
RUN = 2013
d = pd.DataFrame(index=b.index)
d['uf'] = b.uf; d['capital'] = b.capital
d['p0'] = POP[RUN].reindex(d.index)
d = d[(d.capital == 0) & d.p0.between(6793, 50940)].copy()
d['j'] = np.abs(np.log(d.p0.values[:, None] / T[None, :])).argmin(1)
d['T'] = T[d.j]
d['r'] = 100 * (d.p0 - d['T']) / d['T']
d['above'] = (d.r >= 0).astype(float)
# theoretical FPM per capita (2024 structure x REAL_1419): the coefficient of year t+1 follows the estimate of year t
yrs = list(range(RUN, 2019))
lam = np.stack([coef_of(POP[y].reindex(d.index).fillna(d.p0).values) for y in yrs], 1)
d['lam'] = lam.mean(1)
d['fpm_pc'] = REAL_1419 * d.lam * d.uf.map(st_pc) / d.p0
d['lfpm'] = np.log(d.fpm_pc)
# outcomes over 2013-19 (in simulation SD units)
d['jobs'] = (J[2019] - J[2013]).reindex(d.index) / SDU['jobs']
d['sew'] = (SEW[2019] - SEW[2013]).reindex(d.index) / SDU['sew']
d['day'] = (DAY[2019] - DAY[2015]).reindex(d.index) / SDU['day']
d['day_lv'] = DAY[[2017, 2018, 2019]].mean(1).reindex(d.index) / SDU['day']
d['ideb'] = (ID[2019] - ID[2015]).reindex(d.index) / SDU['ideb']
d['ideb_lv'] = ID[[2017, 2019]].mean(1).reindex(d.index) / SDU['ideb']
d['hom'] = -(HOM[[2014, 2015, 2016]].mean(1) - HOM[[2010, 2011, 2012, 2013]].mean(1)).reindex(d.index) / SDU['hom']
d['va'] = (VA[2019] - VA[2013]).reindex(d.index) / SDU['va']
# predetermined (2013 and before) for balance
d['jobs13'] = J[2013].reindex(d.index) / SDU['jobs']
d['va13'] = VA[2013].reindex(d.index) / SDU['va']
d['hom1013'] = HOM[[2010, 2011, 2012, 2013]].mean(1).reindex(d.index) / SDU['hom']
d['sew13'] = SEW[2013].reindex(d.index) / SDU['sew']
d['lat'] = b.latitude.reindex(d.index); d['lon'] = b.longitude.reindex(d.index)
fe = pd.get_dummies(d.j.astype(str), prefix='t', drop_first=True).astype(float)
fe = fe.join(pd.get_dummies(d.uf, prefix='s', drop_first=True).astype(float))


def rd(y, extra=None, fuzzy=False):
    cols = list(fe.columns) + (extra or [])
    m = d[y].notna() & np.isfinite(d[y]) & d[extra or []].notna().all(1)
    covs = (fe.join(d[extra]) if extra else fe).loc[m, cols]
    covs = covs.loc[:, covs.std() > 0]
    kw = dict(y=d.loc[m, y].values, x=d.loc[m, 'r'].values, c=0, covs=covs.values)
    if fuzzy:
        kw['fuzzy'] = d.loc[m, 'lfpm'].values
    o = rdrobust(**kw)
    return dict(var=y, coef=float(o.coef.iloc[0, 0]), se=float(o.se.iloc[0, 0]), ci_rb=[float(o.ci.iloc[2, 0]), float(o.ci.iloc[2, 1])],
                p_rb=float(o.pv.iloc[2, 0]), h=float(o.bws.iloc[0, 0]), n_eff=int(o.N_h[0] + o.N_h[1]), n=int(m.sum()))


res = {'n': int(len(d)), 'running_year': RUN, 'real_1419': REAL_1419, 'sd_units': SDU, 'bunching': BUN.to_dict('records')}
dens = rddensity(X=d.r.values, c=0)
res['density_p'] = float(np.asarray(dens.test['p_jk']).ravel()[0])
fs = rd('lfpm')
res['first_stage_log'] = fs
jump_pct = 100 * (np.exp(fs['coef']) - 1)
# R$ per inhabitant at the threshold (2024 structure x REAL_1419)
near = d[d.r.abs() < 5]
res['jump_pct'] = jump_pct
res['jump_rs_pc'] = float((near.fpm_pc * (np.exp(fs['coef']) - 1) / np.exp(fs['coef'] * near.above)).mean())
res['fpm_pc_near'] = float(near.fpm_pc.mean())
rows = []
for y in ['day', 'day_lv', 'ideb', 'ideb_lv', 'jobs', 'sew', 'hom', 'va']:
    r1 = rd(y); r1['kind'] = 'reduced form'
    r2 = rd(y, fuzzy=True); r2['kind'] = 'per log point of FPM'
    r1['per10pct'] = r2['coef'] * np.log(1.1); r1['per10pct_se'] = r2['se'] * np.log(1.1)
    r1['per100rs'] = r1['coef'] / res['jump_rs_pc'] * 100; r1['per100rs_se'] = r1['se'] / res['jump_rs_pc'] * 100
    rows += [r1, r2]
for y in ['jobs13', 'va13', 'hom1013', 'sew13', 'lat', 'lon']:
    r1 = rd(y); r1['kind'] = 'balance'; rows.append(r1)
t = pd.DataFrame(rows)
res['rd'] = t.to_dict('records')
# v4: correlation of the two reduced-form estimates used by the calibration (daycare level, formal jobs), by bootstrap over
# municipalities (local linear fits at each outcome's bandwidth, triangular kernel, threshold and state effects partialled out)
hh = {r['var']: r['h'] for r in rows if r.get('kind') == 'reduced form'}
Zfe = fe.values


def jump_fe(yv, xv, h, Z):
    w = np.clip(1 - np.abs(xv) / h, 0, None); m = (w > 0) & np.isfinite(yv)
    xm = xv[m]; tt = (xm >= 0).astype(float)
    Xd = np.column_stack([np.ones(m.sum()), tt, xm, tt * xm, Z[m][:, Z[m].std(0) > 0]]); sw = np.sqrt(w[m])
    return float(np.linalg.lstsq(Xd * sw[:, None], yv[m] * sw, rcond=None)[0][1])


rgb = np.random.default_rng(11)
est = []
yv1, yv2, xv = d['day_lv'].values, d['jobs'].values, d['r'].values
for b_ in range(500):
    ix = rgb.integers(0, len(d), len(d))
    est.append([jump_fe(yv1[ix], xv[ix], hh['day_lv'], Zfe[ix]), jump_fe(yv2[ix], xv[ix], hh['jobs'], Zfe[ix])])
est = np.array(est)
res['corr_m5'] = float(pd.DataFrame(est).corr().iloc[0, 1])
t.to_csv(TAB + '/fpm_rd.csv', index=False)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


json.dump(clean(res), open(OUT + '/fpm_rd.json', 'w'), indent=1, allow_nan=False)
pd.set_option('display.width', 220)
print(BUN.to_string())
print('n', res['n'], 'density p', round(res['density_p'], 3), ' first stage (log FPM)', round(fs['coef'], 3), '(', round(fs['se'], 3), ')',
      ' jump %', round(jump_pct, 1), ' R$ pc', round(res['jump_rs_pc'], 0), ' FPM pc near', round(res['fpm_pc_near'], 0))
print(t[['var', 'kind', 'coef', 'se', 'ci_rb', 'p_rb', 'h', 'n_eff', 'per10pct', 'per100rs', 'per100rs_se']].round(4).to_string())
print('bootstrap correlation of the daycare and jobs estimates:', round(res['corr_m5'], 3))
