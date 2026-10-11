"""
02_indicator_properties.py -- what each scorecard indicator measures, with real data.

For every indicator with a municipal panel we estimate, by method of moments on within-state-year residuals,
    Cov(y_it, y_is) = s_f^2 + s_a^2 rho^|t-s| + s_b^2 1[same mayoral term] + s_e^2(size) 1[t = s]
(persistent level, slowly moving drift, component that switches with the mayoral term, transitory noise whose
variance falls with population). Homicides are also decomposed into Poisson noise and real fluctuation.
Literacy has two editions in one term only (test-retest reliability).

Outputs: output/indicator_properties.json, tables/T_indicator_variance.csv, output/reliability_curves.csv,
         output/measurement_validity.json
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'; TAB = _ROOT + '/tables'
for d in (OUT, TAB):
    _os.makedirs(d, exist_ok=True)
base = pd.read_csv(DER + '/municipios_base.csv')
POP = base.set_index('cod_ibge').pop2022
UF = base.set_index('cod_ibge').uf
EDGES = [0, 5000, 10000, 20000, 50000, 100000, np.inf]
LABELS = ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']


def term_of(year):
    return (np.asarray(year) - 2001) // 4          # 2001-04 -> 0, 2005-08 -> 1, ..., 2021-24 -> 5, 2025-28 -> 6


def prep(df, value='value', years=None, log=False, winsor=0.005):
    d = df[['cod_ibge', 'year', value]].dropna().rename(columns={value: 'v'}).copy()
    if years is not None:
        d = d[d.year.isin(years)]
    d = d[d.cod_ibge.isin(POP.index)]
    if log:
        d = d[d.v > 0]; d['v'] = np.log(d.v)
    lo, hi = d.groupby('year').v.transform(lambda s: s.quantile(winsor)), d.groupby('year').v.transform(lambda s: s.quantile(1 - winsor))
    d['v'] = d.v.clip(lo, hi)
    d['uf'] = d.cod_ibge.map(UF)
    d['r'] = d.v - d.groupby(['uf', 'year']).v.transform('mean')
    d['cls'] = pd.cut(d.cod_ibge.map(POP), EDGES, labels=False, right=True)
    return d


def moments(d):
    W = d.pivot_table(index='cod_ibge', columns='year', values='r')
    cls = d.groupby('cod_ibge').cls.first().reindex(W.index)
    years = sorted(W.columns)
    rows = []
    for c in range(len(LABELS)):
        Wc = W[cls == c]
        for i, t in enumerate(years):
            for s in years[i:]:
                a, b = Wc[t], Wc[s]
                ok = a.notna() & b.notna()
                n = int(ok.sum())
                if n < 30:
                    continue
                aa, bb = a[ok] - a[ok].mean(), b[ok] - b[ok].mean()
                rows.append((c, t, s, float((aa * bb).mean()), n))
    return pd.DataFrame(rows, columns=['cls', 't', 's', 'cov', 'n']), years


def fit(M, use_term=True):
    """per size class c: Cov = sf2_c + sa2_c rho_c^lag + sb2_c 1[same term] + se2_c 1[t=s].
    returns array (n_classes, 5): sf2, sa2, rho, sb2, se2 (NaN for classes without enough moments)"""
    P = np.full((len(LABELS), 5), np.nan)
    for c in range(len(LABELS)):
        Mc = M[M.cls == c]
        if len(Mc) < 8:
            continue
        t, s = Mc.t.values, Mc.s.values
        same = (term_of(t) == term_of(s)).astype(float)
        eq = (t == s).astype(float); lag = np.abs(t - s); w = np.sqrt(Mc.n.values)

        def model(p):
            return p[0] + p[1] * p[2] ** lag + (p[3] * same if use_term else 0) + p[4] * eq

        def res(p):
            return w * (model(p) - Mc['cov'].values)
        v0 = Mc[Mc.t == Mc.s]['cov'].mean()
        p0 = np.r_[0.4 * v0, 0.3 * v0, 0.85, 0.02 * v0, 0.2 * v0]
        r = least_squares(res, p0, bounds=(np.r_[0, 0, 0, 0, 0], np.r_[np.inf, np.inf, 0.995, np.inf, np.inf]),
                          loss='soft_l1', f_scale=np.median(np.abs(res(p0))) + 1e-12)
        P[c] = r.x
    return P


def bootstrap_term_share(d, B=60, seed=1):
    """cluster bootstrap over municipalities: sampling distribution of the term share"""
    rng = np.random.default_rng(seed)
    ids = d.cod_ibge.unique()
    out = []
    for _ in range(B):
        pick = rng.choice(ids, size=len(ids), replace=True)
        cnt = pd.Series(pick).value_counts()
        dd = d[d.cod_ibge.isin(cnt.index)].copy()
        # replicate multiplicities by integer weights: approximate by repeating rows
        rep = dd.cod_ibge.map(cnt).values
        dd = dd.loc[dd.index.repeat(rep)].copy()
        dd['cod_ibge'] = dd.cod_ibge.astype(str) + '_' + dd.groupby(['cod_ibge', 'year']).cumcount().astype(str)
        M, _ = moments(dd)
        P = fit(M)
        tot = P[:, 0] + P[:, 1] + P[:, 3] + P[:, 4]
        nn = dd.groupby('cls').cod_ibge.nunique().reindex(range(len(LABELS))).fillna(0).values
        ok = np.isfinite(tot)
        out.append(np.average(P[ok, 3] / tot[ok], weights=nn[ok]))
    return np.array(out)


def summarize(name, d, P, unit, note, boot=None):
    sf2, sa2, rho, sb2, se2 = P.T
    cls_n = d.groupby('cls').cod_ibge.nunique().reindex(range(len(LABELS))).fillna(0).values
    ok = np.isfinite(sf2) & (cls_n > 30)
    tot = sf2 + sa2 + sb2 + se2
    wts = np.where(ok, cls_n, 0)
    sh = lambda x: float(np.average((x / tot)[ok], weights=wts[ok]))
    popmed = np.array([d[d.cls == c].cod_ibge.map(POP).median() for c in range(len(LABELS))])
    X = np.c_[np.ones(ok.sum()), 1 / popmed[ok]]
    ab = np.linalg.lstsq(X * np.sqrt(cls_n[ok])[:, None], se2[ok] * np.sqrt(cls_n[ok]), rcond=None)[0]
    signal = sf2 + sa2 + sb2
    rel_level = signal / (signal + se2)
    sig_change = 2 * sa2 * (1 - rho)                 # one-year change within a term
    rel_change = sig_change / (sig_change + 2 * se2)
    out = dict(indicator=name, unit=unit, note=note, years=[int(min(d.year)), int(max(d.year))],
               n_mun=int(d.cod_ibge.nunique()),
               sd_within_state=float(np.sqrt(np.average(tot[ok], weights=wts[ok]))),
               sd_by_class=np.sqrt(tot).tolist(), sf2_by_class=sf2.tolist(), sa2_by_class=sa2.tolist(),
               rho_by_class=rho.tolist(), sb2_by_class=sb2.tolist(), se2_by_class=se2.tolist(),
               share_persistent=sh(sf2 + sa2), share_term=sh(sb2), share_noise=sh(se2),
               share_term_by_class=(sb2 / tot).tolist(), share_noise_by_class=(se2 / tot).tolist(),
               rel_level_by_class=rel_level.tolist(), rel_change_by_class=rel_change.tolist(),
               noise_fn=dict(a=float(ab[0]), b=float(ab[1])), pop_median_by_class=popmed.tolist(),
               n_by_class=cls_n.tolist())
    if boot is not None:
        out['term_share_boot_p5_p95'] = [float(np.percentile(boot, 5)), float(np.percentile(boot, 95))]
    return out


results = {}
specs = [
    ('K1_formal_jobs_log', 'panel_K1_formal_jobs.csv', 'value', list(range(2006, 2025)), True,
     'log private formal jobs per 100 inhabitants (RAIS)', 'log points'),
    ('K2_private_va_share', 'panel_K2_private_va_share.csv', 'value', list(range(2010, 2022)), False,
     'share of value added not from public administration (IBGE)', 'percentage points'),
    ('K4_daycare_coverage', 'panel_K4_daycare.csv', 'value', list(range(2015, 2026)), False,
     'enrolments 0-5 per 100 children (School Census / estimated population)', 'percentage points'),
    ('K6_sewage_coverage', 'panel_K6_sanitation_snis.csv', 'sewer_pop_share', list(range(2010, 2023)), False,
     'population served by sewage collection, % (SNIS, self-reported)', 'percentage points'),
    ('K7_homicide_rate', 'panel_K7_homicides.csv', 'value', list(range(2004, 2017)), False,
     'homicides per 100,000 (Atlas da Violencia / SIM)', 'per 100,000'),
    ('E_ideb', 'panel_E_ideb.csv', 'value', [2015, 2017, 2019, 2021, 2023, 2025], False,
     'IDEB anos iniciais, municipal network (INEP)', 'IDEB points'),
]
for name, f, val, yrs, lg, note, unit in specs:
    df = pd.read_csv(DER + '/' + f)
    if name == 'K6_sewage_coverage':
        df = df[(df.sewer_pop_share > 0) & (df.sewer_pop_share <= 100)]
    if name == 'K4_daycare_coverage':
        df = df[(df.value > 0) & (df.value < 200)]
    d = prep(df, val, yrs, log=lg)
    M, years = moments(d)
    p = fit(M)
    boot = bootstrap_term_share(d, B=40) if name in ('K1_formal_jobs_log', 'K4_daycare_coverage', 'E_ideb',
                                                     'K6_sewage_coverage', 'K2_private_va_share',
                                                     'K7_homicide_rate') else None
    results[name] = summarize(name, d, p, unit, note, boot)
    r = results[name]
    print('%-22s n=%4d sd=%.3f persist=%.2f term=%.3f noise=%.2f | noise by class %s | rel level %s | rel change %s | term CI %s' % (
        name, r['n_mun'], r['sd_within_state'], r['share_persistent'], r['share_term'], r['share_noise'],
        np.round(r['share_noise_by_class'], 2), np.round(r['rel_level_by_class'], 2), np.round(r['rel_change_by_class'], 2),
        np.round(r.get('term_share_boot_p5_p95', [np.nan, np.nan]), 3)))

# ------------------------------------------------------------------ homicides: Poisson part of the noise
h = pd.read_csv(DER + '/panel_K7_homicides.csv')
h = h[(h.year >= 2004) & (h.year <= 2016)].dropna(subset=['value', 'pop'])
h['cls'] = pd.cut(h.cod_ibge.map(POP), EDGES, labels=False)
pois = h.assign(pv=h.value * 1e5 / h['pop']).groupby('cls').pv.mean()      # E[lambda*1e5/pop] = Poisson variance
se2 = np.array(results['K7_homicide_rate']['se2_by_class'])
results['K7_homicide_rate']['poisson_var_by_class'] = pois.reindex(range(len(LABELS))).tolist()
results['K7_homicide_rate']['poisson_share_of_noise_by_class'] = (pois.reindex(range(len(LABELS))).values / se2).tolist()
print('homicide noise: Poisson share of transitory variance by class:',
      np.round(pois.reindex(range(len(LABELS))).values / se2, 2))

# ------------------------------------------------------------------ literacy: test-retest (2023, 2024)
li = pd.read_csv(DER + '/panel_K3_literacy.csv')
li = li[li.cod_ibge.isin(POP.index)].copy()
w = li.pivot_table(index='cod_ibge', columns='year', values='value').dropna()
w['uf'] = w.index.map(UF); w['cls'] = pd.cut(w.index.map(POP), EDGES, labels=False)
for y in (2023, 2024):
    w[f'r{y}'] = w[y] - w.groupby('uf')[y].transform('mean')
rel_li, var_li, cov_li = [], [], []
for c in range(len(LABELS)):
    q = w[w.cls == c]
    cv = np.cov(q.r2023, q.r2024)
    cov_li.append(cv[0, 1]); var_li.append(0.5 * (cv[0, 0] + cv[1, 1])); rel_li.append(cv[0, 1] / (0.5 * (cv[0, 0] + cv[1, 1])))
popmed = np.array([w[w.cls == c].index.map(POP).to_series().median() for c in range(len(LABELS))])
se2_li = np.array(var_li) - np.array(cov_li)
nn = np.array([(w.cls == c).sum() for c in range(len(LABELS))])
X = np.c_[np.ones(len(LABELS)), 1 / popmed]
ab = np.linalg.lstsq(X * np.sqrt(nn)[:, None], se2_li * np.sqrt(nn), rcond=None)[0]
sig_li = np.average(cov_li, weights=nn)
results['K3_literacy'] = dict(indicator='K3_literacy', unit='percentage points',
                              note='% of 2nd graders literate, municipal network (INEP ICA), 2023-2024',
                              years=[2023, 2024], n_mun=int(len(w)), sd_within_state=float(np.sqrt(np.average(var_li, weights=nn))),
                              signal_var=float(sig_li), se2_by_class=se2_li.tolist(), rel_level_by_class=rel_li,
                              noise_fn=dict(a=float(ab[0]), b=float(ab[1])), pop_median_by_class=popmed.tolist(),
                              n_by_class=nn.tolist(), share_noise=float(np.average(se2_li, weights=nn) / np.average(var_li, weights=nn)))
print('K3 literacy test-retest reliability by class:', np.round(rel_li, 2), ' noise share %.2f' % results['K3_literacy']['share_noise'])

# ------------------------------------------------------------------ reliability curves (for figures)
pops = np.exp(np.linspace(np.log(800), np.log(1e6), 120))
rows = []
for k, r in results.items():
    a, b = r['noise_fn']['a'], r['noise_fn']['b']
    se2p = np.maximum(a + b / pops, 1e-9)
    if 'sf2_by_class' in r:
        nn = np.array(r['n_by_class']); okc = np.isfinite(np.array(r['sf2_by_class'], dtype=float))
        sig = np.average((np.array(r['sf2_by_class']) + np.array(r['sa2_by_class']) + np.array(r['sb2_by_class']))[okc], weights=nn[okc])
        sc = np.average((2 * np.array(r['sa2_by_class']) * (1 - np.array(r['rho_by_class'])))[okc], weights=nn[okc])
        relc = sc / (sc + 2 * se2p)
    else:
        sig = r['signal_var']; relc = np.full_like(pops, np.nan)
    rel = sig / (sig + se2p)
    for pp, x, y in zip(pops, rel, relc):
        rows.append((k, pp, x, y))
pd.DataFrame(rows, columns=['indicator', 'pop', 'rel_level', 'rel_change']).to_csv(OUT + '/reliability_curves.csv', index=False)

# ------------------------------------------------------------------ measurement validity
val = {}
b = base.copy()
ok = b.sewer_snis_2022.notna()
diff = b.loc[ok, 'sewer_snis_2022'] - 100 * b.loc[ok, 'sh_sewer_census']
val['sewer_snis_vs_census'] = dict(n=int(ok.sum()), mean_diff=float(diff.mean()), mad=float(diff.abs().median()),
                                   rmse=float(np.sqrt((diff ** 2).mean())), corr=float(np.corrcoef(b.loc[ok, 'sewer_snis_2022'], b.loc[ok, 'sh_sewer_census'])[0, 1]),
                                   share_abs_diff_gt10=float((diff.abs() > 10).mean()),
                                   by_class={LABELS[c]: float(diff[pd.cut(b.loc[ok, 'pop2022'], EDGES, labels=False) == c].abs().median()) for c in range(6)},
                                   no_snis_but_census_network_gt20=int(((~ok) & (b.sh_sewer_census > 0.2)).sum()))
pe = (b.pop2021 / b.pop2022 - 1) * 100
val['population_estimate_error_2021_vs_census'] = dict(mean=float(pe.mean()), median_abs=float(pe.abs().median()),
                                                       share_abs_gt5=float((pe.abs() > 5).mean()), share_abs_gt10=float((pe.abs() > 10).mean()),
                                                       by_class_median_abs={LABELS[c]: float(pe[pd.cut(b.pop2022, EDGES, labels=False) == c].abs().median()) for c in range(6)})
print(json.dumps(val, indent=1))

json.dump(results, open(OUT + '/indicator_properties.json', 'w'), indent=1)
json.dump(val, open(OUT + '/measurement_validity.json', 'w'), indent=1)
tab = []
for k, r in results.items():
    tab.append(dict(indicator=k, years='%d-%d' % tuple(r['years']), n=r['n_mun'], sd=r['sd_within_state'],
                    persistent=r.get('share_persistent'), term=r.get('share_term'),
                    noise=r.get('share_noise'), rel_level_lt5k=r['rel_level_by_class'][0],
                    rel_level_gt100k=r['rel_level_by_class'][-1],
                    rel_change_lt5k=r.get('rel_change_by_class', [np.nan])[0],
                    rel_change_gt100k=r.get('rel_change_by_class', [np.nan] * 6)[-1]))
pd.DataFrame(tab).to_csv(TAB + '/T_indicator_variance.csv', index=False)

# ------------------------------------------------------------------ change decomposition over mandates (upper bound on mayor share)
# For terms k (4-year blocks), D_k = mean(y in last year of term k) - mean(y in last year of term k-1).
# Persistent municipal trends make successive term changes covary: Cov(D_k, D_k+1) estimates the trend variance.
# Var(D) - trend - 2*noise bounds from above what a new administration could add (mayor + local shocks).
chg = {}
term_end_years = {'K1_formal_jobs_log': [2008, 2012, 2016, 2020, 2024], 'K2_private_va_share': [2012, 2016, 2020],
                  'K4_daycare_coverage': [2016, 2020, 2024], 'K6_sewage_coverage': [2012, 2016, 2020],
                  'K7_homicide_rate': [2004, 2008, 2012, 2016], 'E_ideb': [2015, 2019, 2023]}
for name, f, val, yrs, lg, note, unit in specs:
    df = pd.read_csv(DER + '/' + f)
    if name == 'K6_sewage_coverage':
        df = df[(df.sewer_pop_share > 0) & (df.sewer_pop_share <= 100)]
    if name == 'K4_daycare_coverage':
        df = df[(df.value > 0) & (df.value < 200)]
    d = prep(df, val, None, log=lg)
    W = d.pivot_table(index='cod_ibge', columns='year', values='r')
    ends = [y for y in term_end_years[name] if y in W.columns]
    D = pd.DataFrame({e: W[e] - W[s] for s, e in zip(ends[:-1], ends[1:])})
    cls = pd.cut(D.index.map(POP), EDGES, labels=False)
    rows = []
    se2 = np.array(results[name]['se2_by_class'])
    for c in range(len(LABELS)):
        Dc = D[cls == c]
        vs, cvs = [], []
        for a, b in zip(D.columns[:-1], D.columns[1:]):
            ok = Dc[a].notna() & Dc[b].notna()
            if ok.sum() > 30:
                cvs.append(np.cov(Dc.loc[ok, a], Dc.loc[ok, b])[0, 1])
        for a in D.columns:
            ok = Dc[a].notna()
            if ok.sum() > 30:
                vs.append(Dc.loc[ok, a].var())
        if not vs:
            rows.append([np.nan] * 4); continue
        vD = np.mean(vs); trend = max(np.mean(cvs) if cvs else 0.0, 0.0)
        noise = 2 * se2[c] if np.isfinite(se2[c]) else 0.0
        rows.append([vD, trend / vD, min(noise / vD, 1.0), max(1 - trend / vD - noise / vD, 0.0)])
    rows = np.array(rows, dtype=float)
    chg[name] = dict(var_change_by_class=rows[:, 0].tolist(), trend_share=rows[:, 1].tolist(),
                     noise_share=rows[:, 2].tolist(), max_mayor_share=rows[:, 3].tolist())
    print('%-22s 4-yr change: trend share %s | noise share %s | upper bound mayor+shocks %s' % (
        name, np.round(rows[:, 1], 2), np.round(rows[:, 2], 2), np.round(rows[:, 3], 2)))
for k in chg:
    results[k]['change_decomposition'] = chg[k]
json.dump(results, open(OUT + '/indicator_properties.json', 'w'), indent=1)
