"""
17_incentive_estimates.py -- how much do Brazilian mayors' incentives move the LRG indicators? Real data.

(E1) Career incentives. A mayor re-elected for a second consecutive mandate cannot run again (lame duck); a
     first-term mayor can. Two designs:
     (a) regression discontinuity on the 2020 races in which the 2016 winner ran: where the incumbent barely won,
         a lame duck governs 2021-24; where the incumbent barely lost, a new first-term mayor does. Outcomes are
         changes over 2021-24; changes over 2017-20 (same mayor on both sides) are placebo tests.
     (b) panel of three mandates (2013-16, 2017-20, 2021-24) with municipality and state-by-mandate fixed
         effects: the change in an indicator under a lame duck against the change under a first-term mayor in
         the same municipality.
(E4) Electoral returns to performance. Among incumbents who ran (2020, 2024), how much does re-election
     respond to the change in the indicators during the mandate, measured as voters could see them?

(v4) Robustness of the discontinuity (bandwidths, local quadratic, CER bandwidth, donut, covariates); a second discontinuity
     in the open seats of 2020 (party continuity with a new, eligible mayor on both sides); bootstrap correlations of the
     estimates; bounds that separate the electoral incentive from administrative continuity.
Units: indicators in the standard-deviation units of the simulation (within-state SD of the true indicator,
Section 7.1): formal jobs 0.89 log points, value added 10.8 pp, literacy 9.6 pp, daycare 12.2 pp, sewage 23.5 pp;
IDEB in its own within-state SD. Writes output/incentive_estimates.json and tables/incentive_*.csv.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from rdrobust import rdrobust
from rddensity import rddensity
from linearmodels.iv.absorbing import AbsorbingLS

warnings.filterwarnings('ignore')
DER = _ROOT + '/data/derived'
OUT = _ROOT + '/output'
TAB = _ROOT + '/tables'
SDU = {'jobs': 0.89, 'va': 10.8, 'lit': 9.6, 'day': 12.2, 'sew': 23.5, 'hom': 10.9}

inc = pd.read_csv(DER + '/incumbency_2012_2024.csv')
base = pd.read_csv(DER + '/municipios_base.csv')
inc = inc.merge(base[['cod_ibge', 'pop2010', 'pop2016', 'pop2020', 'pop2024', 'region', 'gdp_pc_2021', 'higher_ed_share',
                      'bf_share_households', 'capital']], on='cod_ibge', how='left')


def panel(name, col='value'):
    d = pd.read_csv(f'{DER}/{name}.csv')
    return d.pivot_table(index='cod_ibge', columns='year', values=col)


J = np.log(panel('panel_K1_formal_jobs').clip(lower=0.2))
VA = panel('panel_K2_private_va_share')
LIT = panel('panel_K3_literacy')
DAY = panel('panel_K4_daycare')
HOM = panel('panel_K7_homicides')
ID = panel('panel_E_ideb')
sn = pd.read_csv(DER + '/panel_K6_sanitation_snis.csv')
SEW = sn.pivot_table(index='cod_ibge', columns='year', values='sewer_pop_share')
if SEW.stack().max() <= 1.5:
    SEW = 100 * SEW
PERS = panel('panel_F_personnel_rcl')
# within-state SD of IDEB (2019), the unit for IDEB effects
idb = ID[2019].rename('i').to_frame().join(base.set_index('cod_ibge').uf)
SDU['ideb'] = float(np.sqrt((idb.i - idb.groupby('uf').i.transform('mean')).pow(2).mean()))


def chg(P, a, b):
    return (P[b] - P[a]) if (a in P and b in P) else pd.Series(dtype=float)


inc = inc.set_index('cod_ibge')
X = pd.DataFrame(index=inc.index)
# changes over the 2021-24 mandate (outcomes) and over 2017-20 (placebo)
X['day_21'] = chg(DAY, 2020, 2024) / SDU['day']; X['day_17'] = chg(DAY, 2016, 2020) / SDU['day']
X['ideb_21'] = chg(ID, 2019, 2023) / SDU['ideb']; X['ideb_17'] = chg(ID, 2015, 2019) / SDU['ideb']
X['jobs_21'] = chg(J, 2020, 2024) / SDU['jobs']; X['jobs_17'] = chg(J, 2016, 2020) / SDU['jobs']; X['jobs_13'] = chg(J, 2012, 2016) / SDU['jobs']
X['sew_21'] = chg(SEW, 2020, 2022) / SDU['sew']; X['sew_17'] = chg(SEW, 2016, 2020) / SDU['sew']; X['sew_13'] = chg(SEW, 2012, 2016) / SDU['sew']
X['va_21'] = chg(VA, 2020, 2021) / SDU['va']; X['va_17'] = chg(VA, 2016, 2020) / SDU['va']; X['va_13'] = chg(VA, 2012, 2016) / SDU['va']
X['lit_24'] = LIT[2024] / SDU['lit']; X['lit_23'] = LIT[2023] / SDU['lit']
X['hom_13'] = (HOM[[2013, 2014, 2015, 2016]].mean(1) - HOM[[2009, 2010, 2011, 2012]].mean(1)) / SDU['hom']
X['pers_21'] = chg(PERS, 2020, 2024)
X['ideb19'] = ID[2019] / SDU['ideb']; X['day20'] = DAY[2020] / SDU['day']; X['jobs20'] = J[2020] / SDU['jobs']
X['lpop'] = np.log(inc.pop2020)
X['lgdp'] = np.log(inc.gdp_pc_2021)
D = inc.join(X)

LAB = {'day': 'Daycare and preschool coverage', 'ideb': 'IDEB (early grades, municipal schools)', 'jobs': 'Formal jobs (log)',
       'sew': 'Sewage coverage (self-reported)', 'va': 'Non-public value added', 'lit': 'Literacy, end of 2nd grade',
       'hom': 'Homicide rate (negative = fewer)', 'pers': 'Personnel spending, % of current net revenue'}
res = {'sd_units': SDU}

# ============================================================================ E1a: regression discontinuity, 2020
R = D[D.margin_2020.notna() & ~D.round2_2020.fillna(False).astype(bool)].copy()
R['x'] = R.margin_2020
res['rd_n'] = int(len(R)); res['rd_n_5pp'] = int((R.x.abs() < 5).sum())
dens = rddensity(X=R.x.values, c=0)
p_dens = float(np.asarray(dens.test['p_jk']).ravel()[0])
res['rd_density_p'] = p_dens


def rd(y, covs=None, h=None):
    m = R[y].notna() & np.isfinite(R[y])
    yy = R.loc[m, y].values; xx = R.loc[m, 'x'].values
    kw = dict(y=yy, x=xx, c=0)
    if covs is not None:
        kw['covs'] = R.loc[m, covs].fillna(R.loc[m, covs].mean()).values
    if h is not None:
        kw['h'] = h
    o = rdrobust(**kw)
    co = float(o.coef.iloc[0, 0]); se = float(o.se.iloc[0, 0])
    ci = [float(o.ci.iloc[2, 0]), float(o.ci.iloc[2, 1])]          # robust bias-corrected 95% CI
    return dict(coef=co, se=se, ci_rb=ci, p_rb=float(o.pv.iloc[2, 0]), h=float(o.bws.iloc[0, 0]),
                n_eff=int(o.N_h[0] + o.N_h[1]), n=int(m.sum()))


rows = []
spec = [('day_21', 'day', 'outcome', ['day20']), ('ideb_21', 'ideb', 'outcome', ['ideb19']), ('lit_24', 'lit', 'outcome', ['ideb19', 'day20']),
        ('jobs_21', 'jobs', 'outcome', ['jobs20']), ('sew_21', 'sew', 'outcome', None), ('va_21', 'va', 'outcome', None),
        ('pers_21', 'pers', 'outcome', None),
        ('day_17', 'day', 'placebo', None), ('ideb_17', 'ideb', 'placebo', None), ('jobs_17', 'jobs', 'placebo', None),
        ('sew_17', 'sew', 'placebo', None), ('va_17', 'va', 'placebo', None),
        ('lpop', 'lpop', 'balance', None), ('lgdp', 'lgdp', 'balance', None), ('ideb19', 'ideb', 'balance', None),
        ('day20', 'day', 'balance', None), ('jobs20', 'jobs', 'balance', None)]
for y, k, kind, cv in spec:
    r = rd(y)
    r.update(var=y, ind=k, kind=kind)
    if cv:
        rc = rd(y, covs=cv)
        r.update(coef_cov=rc['coef'], se_cov=rc['se'], ci_rb_cov=rc['ci_rb'])
    rows.append(r)
rdt = pd.DataFrame(rows)
res['rd'] = rdt.to_dict('records')
rdt.to_csv(TAB + '/incentive_rd_2020.csv', index=False)

# ============================================================================ E1b: panel of three mandates
pan = []
for t, ld, cols in [(2013, 'lame_2013', {'jobs': 'jobs_13', 'sew': 'sew_13', 'va': 'va_13', 'hom': 'hom_13'}),
                    (2017, 'lame_2017', {'jobs': 'jobs_17', 'sew': 'sew_17', 'va': 'va_17', 'day': 'day_17', 'ideb': 'ideb_17'}),
                    (2021, 'lame_2021', {'jobs': 'jobs_21', 'sew': 'sew_21', 'va': 'va_21', 'day': 'day_21', 'ideb': 'ideb_21'})]:
    for k, cname in cols.items():
        s = D[[ld, cname, 'uf']].rename(columns={ld: 'lame', cname: 'dy'}).dropna()
        s['term'] = t; s['ind'] = k; s['mun'] = s.index
        pan.append(s)
PAN = pd.concat(pan)
prow = []
for k, g in PAN.groupby('ind'):
    g = g.copy().reset_index(drop=True); g['st'] = g.uf + '_' + g.term.astype(str)
    multi = g.groupby('mun').term.nunique()
    g2 = g[g.mun.isin(multi[multi > 1].index)]
    fe = None
    if len(g2):
        ab = pd.DataFrame({'mun': pd.Categorical(g2.mun), 'st': pd.Categorical(g2.st)}, index=g2.index)
        fe = AbsorbingLS(g2.dy, g2[['lame']].astype(float), absorb=ab.reset_index(drop=True).set_index(g2.index)).fit(
            cov_type='clustered', clusters=pd.Series(pd.Categorical(g2.mun).codes, index=g2.index))
    xs = smf.ols('dy ~ lame + C(st)', data=g).fit(cov_type='cluster', cov_kwds={'groups': g.mun.astype(str)})
    prow.append(dict(ind=k, terms=sorted(g.term.unique().tolist()), n=int(len(g)),
                     xs_coef=float(xs.params['lame']), xs_se=float(xs.bse['lame']),
                     fe_coef=float(fe.params['lame']) if fe is not None else np.nan, fe_se=float(fe.std_errors['lame']) if fe is not None else np.nan,
                     fe_n=int(len(g2)), fe_switchers=int((g2.groupby('mun').lame.nunique() > 1).sum())))
pt = pd.DataFrame(prow)
res['panel'] = pt.to_dict('records')
pt.to_csv(TAB + '/incentive_panel.csv', index=False)

# ============================================================================ E4: electoral returns to performance
er = []
# 2020: incumbents (2016 winners) who ran; performance visible before November 2020
E20 = D[D.inc_ran_2020 == 1].copy()
E20['won'] = (E20.lame_2021 == 1).astype(float)
E20['z_ideb'] = chg(ID, 2015, 2019).reindex(E20.index) / SDU['ideb']
E20['z_day'] = chg(DAY, 2016, 2019).reindex(E20.index) / SDU['day']
E20['z_jobs'] = chg(J, 2016, 2019).reindex(E20.index) / SDU['jobs']
E20['z_sew'] = chg(SEW, 2016, 2018).reindex(E20.index) / SDU['sew']
E24 = D[D.inc20_ran_2024 == 1].copy()
E24['won'] = E24.inc_won_2024.astype(float)
E24['z_ideb'] = chg(ID, 2019, 2023).reindex(E24.index) / SDU['ideb']
E24['z_day'] = chg(DAY, 2020, 2023).reindex(E24.index) / SDU['day']
E24['z_jobs'] = chg(J, 2020, 2023).reindex(E24.index) / SDU['jobs']
E24['z_lit'] = LIT[2023].reindex(E24.index) / SDU['lit']
for yr, Ed, zs in [(2020, E20, ['z_ideb', 'z_day', 'z_jobs', 'z_sew']), (2024, E24, ['z_ideb', 'z_day', 'z_jobs', 'z_lit'])]:
    Ed = Ed.copy(); Ed['lpop'] = np.log(Ed.pop2020)
    for z in zs:
        s = Ed[['won', z, 'uf', 'lpop']].dropna()
        lp = smf.ols(f'won ~ {z} + lpop + C(uf)', data=s).fit(cov_type='HC1')
        er.append(dict(year=yr, var=z, n=int(len(s)), mean_win=float(s.won.mean()), coef_pp=100 * float(lp.params[z]),
                       se_pp=100 * float(lp.bse[z]), logit_per_sd=float(lp.params[z]) / max(s.won.mean() * (1 - s.won.mean()), 1e-9)))
    zc = [z for z in zs if z != 'z_sew']
    s = Ed[['won', 'uf', 'lpop'] + zc].dropna()
    s['comp'] = s[zc].mean(1) / s[zc].mean(1).std()
    lp = smf.ols('won ~ comp + lpop + C(uf)', data=s).fit(cov_type='HC1')
    er.append(dict(year=yr, var='composite (SD of composite)', n=int(len(s)), mean_win=float(s.won.mean()), coef_pp=100 * float(lp.params['comp']),
                   se_pp=100 * float(lp.bse['comp']), logit_per_sd=float(lp.params['comp']) / max(s.won.mean() * (1 - s.won.mean()), 1e-9)))
ert = pd.DataFrame(er)
res['electoral_returns'] = ert.to_dict('records')
ert.to_csv(TAB + '/incentive_electoral_returns.csv', index=False)


# ============================================================================ v4: robustness, open seats and decomposition
# (a) robustness of the 2020 discontinuity: bandwidth multiples, local quadratic, CER bandwidth, donut, covariates
MAIN = ['day_21', 'ideb_21', 'jobs_21', 'sew_21', 'va_21', 'lit_24']
COV = {'day_21': ['day20'], 'ideb_21': ['ideb19'], 'jobs_21': ['jobs20'], 'lit_24': ['ideb19', 'day20']}
h0 = {r['var']: r['h'] for r in rows}


def rd_on(S_, y, x='x', **kw):
    m = S_[y].notna() & np.isfinite(S_[y]) & S_[x].notna()
    a = dict(y=S_.loc[m, y].values, x=S_.loc[m, x].values, c=0)
    covs = kw.pop('covs', None)
    if covs:
        a['covs'] = S_.loc[m, covs].fillna(S_.loc[m, covs].mean()).values
    a.update(kw)
    o = rdrobust(**a)
    return dict(coef=float(o.coef.iloc[0, 0]), se=float(o.se.iloc[0, 0]), ci_rb=[float(o.ci.iloc[2, 0]), float(o.ci.iloc[2, 1])],
                p_rb=float(o.pv.iloc[2, 0]), h=float(o.bws.iloc[0, 0]), n_eff=int(o.N_h[0] + o.N_h[1]))


rob = []
for y in MAIN:
    specs = [('h x 0.5', dict(h=0.5 * h0[y])), ('h x 0.75', dict(h=0.75 * h0[y])), ('MSE-optimal h', {}),
             ('h x 1.5', dict(h=1.5 * h0[y])), ('h x 2', dict(h=2.0 * h0[y])), ('local quadratic', dict(p=2)),
             ('CER-optimal h', dict(bwselect='cerrd'))]
    if y in COV:
        specs.append(('with baseline covariates', dict(covs=COV[y])))
    for nm, kw in specs:
        r = rd_on(R, y, **kw); r.update(var=y, spec=nm, design='incumbent ran'); rob.append(r)
    Rd = R[R.x.abs() >= 0.5]
    r = rd_on(Rd, y); r.update(var=y, spec='donut (|margin| >= 0.5 pp)', design='incumbent ran'); rob.append(r)

# (b) open seats: the 2016 winner did not run; the outgoing mayor's 2016 party barely kept or lost the office. Both sides are
#     governed by a new first-term mayor who can run again, so the jump measures party continuity alone.
O = D[(D.inc_ran_2020 == 0) & ~D.round2_2020.fillna(False).astype(bool) & D.margin_party_2020.notna()].copy()
O['x'] = O.margin_party_2020
res['open_n'] = int(len(O)); res['open_n_10pp'] = int((O.x.abs() < 10).sum())
res['open_density_p'] = float(np.asarray(rddensity(X=O.x.values, c=0).test['p_jk']).ravel()[0])
OC = D[(D.inc_ran_2020 == 0) & ~D.round2_2020.fillna(False).astype(bool) & D.margin_coal_2020.notna()].copy()
OC['x'] = OC.margin_coal_2020
res['openc_n'] = int(len(OC))
orow = []
for y, kind in [('day_21', 'outcome'), ('ideb_21', 'outcome'), ('jobs_21', 'outcome'), ('sew_21', 'outcome'), ('va_21', 'outcome'),
                ('lit_24', 'outcome'), ('day_17', 'placebo'), ('ideb_17', 'placebo'), ('jobs_17', 'placebo'), ('sew_17', 'placebo'),
                ('va_17', 'placebo'), ('lpop', 'balance'), ('lgdp', 'balance'), ('ideb19', 'balance'), ('day20', 'balance'), ('jobs20', 'balance')]:
    r = rd_on(O, y); r.update(var=y, kind=kind, design='open seat, party'); orow.append(r)
    if kind == 'outcome':
        r = rd_on(OC, y); r.update(var=y, kind=kind, design='open seat, coalition'); orow.append(r)
        r = rd_on(O, y, h=2.0 * orow[-2]['h']); r.update(var=y, kind=kind, design='open seat, party, h x 2'); orow.append(r)
# with the previous mandate's change and the baseline level as covariates (the open-seat placebo on 2017-20 is imbalanced)
PRE = {'day_21': ['day_17', 'day20'], 'ideb_21': ['ideb_17', 'ideb19'], 'jobs_21': ['jobs_17', 'jobs20'], 'sew_21': ['sew_17'],
       'va_21': ['va_17'], 'lit_24': ['ideb_17', 'ideb19', 'day20']}
for y in PRE:
    r = rd_on(O, y, covs=PRE[y]); r.update(var=y, kind='outcome', design='open seat, party, pre-trend adjusted'); orow.append(r)
    r = rd_on(R, y, covs=PRE[y]); r.update(var=y, kind='outcome', design='incumbent ran, pre-trend adjusted'); orow.append(r)
res['rd_open'] = orow

# (c) covariance of the estimates within each design (bootstrap over municipalities, local linear fits at each outcome's
#     bandwidth, triangular kernel); used by the calibration (19_calibrate.py) for the joint likelihood
M3V = ['day_21', 'ideb_21', 'jobs_21', 'sew_21', 'va_21']


def ll_jump(yv, xv, h):
    w = np.clip(1 - np.abs(xv) / h, 0, None); m = (w > 0) & np.isfinite(yv)
    if m.sum() < 20:
        return np.nan
    xm = xv[m]; t = (xm >= 0).astype(float)
    Xd = np.column_stack([np.ones(m.sum()), t, xm, t * xm]); sw = np.sqrt(w[m])
    return float(np.linalg.lstsq(Xd * sw[:, None], yv[m] * sw, rcond=None)[0][1])


def boot_corr(S_, hs, B=500, seed=7):
    rg = np.random.default_rng(seed)
    Y = S_[M3V].values; xv = S_.x.values; n = len(S_)
    est = np.full((B, len(M3V)), np.nan)
    for b in range(B):
        ix = rg.integers(0, n, n)
        for j, v in enumerate(M3V):
            est[b, j] = ll_jump(Y[ix, j], xv[ix], hs[v])
    return pd.DataFrame(est, columns=M3V).corr().values


hs_open = {r['var']: r['h'] for r in orow if r['design'] == 'open seat, party' and r['kind'] == 'outcome'}
res['corr_rd_inc'] = boot_corr(R, h0).tolist()
res['corr_rd_open'] = boot_corr(O, hs_open).tolist()
res['corr_vars'] = M3V

# (d) decomposition. Incumbent-ran design: lame duck, same mayor and party, against a new first-term mayor of another party:
#     RD_inc = P (keeping the person) + C (keeping the party) - E (the electoral incentive of a mayor who can run again).
#     Open-seat design: RD_open = C. Hence E = P + RD_open - RD_inc. P is not identified; bounds take 0 <= P <= Pmax, with
#     Pmax the largest party-continuity effect the open-seat design does not reject (|estimate| + 1.96 SE).
dec = []
for ver, dn_inc, dn_open in [('adjusted', 'incumbent ran, pre-trend adjusted', 'open seat, party, pre-trend adjusted'),
                             ('unadjusted', None, 'open seat, party')]:
    opn = {r['var']: r for r in orow if r['design'] == dn_open}
    inc_ = {r['var']: r for r in orow if r['design'] == dn_inc} if dn_inc else {r['var']: r for r in rows}
    for v in M3V:
        a, b = inc_[v], opn[v]
        d0 = b['coef'] - a['coef']; sd = float(np.hypot(a['se'], b['se']))
        pmax = abs(b['coef']) + 1.96 * b['se']
        dec.append(dict(version=ver, var=v, rd_inc=a['coef'], rd_inc_se=a['se'], rd_open=b['coef'], rd_open_se=b['se'], pmax=pmax,
                        E_lo=d0, E_hi=d0 + pmax, E_lo_ci=d0 - 1.96 * sd, E_hi_ci=d0 + pmax + 1.96 * sd))
res['decomposition'] = dec
pd.DataFrame(rob).to_csv(TAB + '/incentive_rd_robustness.csv', index=False)
pd.DataFrame(orow).to_csv(TAB + '/incentive_rd_open_seats.csv', index=False)
pd.DataFrame(dec).to_csv(TAB + '/incentive_rd_decomposition.csv', index=False)
res['rd_robustness'] = rob


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, float) and not np.isfinite(o):
        return None
    if isinstance(o, (np.floating,)):
        return clean(float(o))
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


json.dump(clean(res), open(OUT + '/incentive_estimates.json', 'w'), indent=1, allow_nan=False)
pd.set_option('display.width', 220)
print('RD sample', res['rd_n'], ' within 5 pp', res['rd_n_5pp'], ' density test p =', round(p_dens, 3), ' IDEB SD', round(SDU['ideb'], 3))
print(rdt[['var', 'kind', 'coef', 'se', 'ci_rb', 'p_rb', 'h', 'n_eff'] + [c for c in ['coef_cov', 'se_cov'] if c in rdt]].round(3).to_string())
print(pt.round(4).to_string())
print(ert.round(3).to_string())
print('ROBUSTNESS'); print(pd.DataFrame(rob)[['var', 'spec', 'coef', 'se', 'ci_rb', 'h', 'n_eff']].round(3).to_string())
print('OPEN SEATS n', res['open_n'], 'within 10pp', res['open_n_10pp'], 'density p', round(res['open_density_p'], 3), 'coalition n', res['openc_n'])
print(pd.DataFrame(orow)[['var', 'kind', 'design', 'coef', 'se', 'ci_rb', 'p_rb', 'h', 'n_eff']].round(3).to_string())
print('DECOMPOSITION'); print(pd.DataFrame(dec).round(3).to_string())
print('corr inc', np.round(res['corr_rd_inc'], 2)); print('corr open', np.round(res['corr_rd_open'], 2))
