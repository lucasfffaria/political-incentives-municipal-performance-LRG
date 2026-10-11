"""
20_pilot_power.py -- how large a randomised pilot would have to be to tell the LRG's instruments apart.

Design (Section 10.2): municipalities drawn by lot into a 2 x 2 factorial with the same expected money in every arm:
  A transfer without performance condition        B the same expected transfer paid by results (incentive)
  C A plus technical assistance (commissioners)   D B plus technical assistance
Main effects (incentive: B+D vs A+C; assistance: C+D vs A+B) and the interaction (D-C-B+A) are estimated by
ANCOVA on the change in each indicator over two years, with the baseline as a covariate and randomisation within
strata (state x size class). The residual standard deviation comes from real two-year changes; the effects the
pilot should detect come from the simulation (posterior draws, years 2029-2030 of the factorial designs).
Writes output/pilot_power.json.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DER = _ROOT + '/data/derived'
OUT = _ROOT + '/output'
SDU = {'jobs': 0.89, 'lit': 9.6, 'day': 12.2, 'sew': 23.5}
base = pd.read_csv(DER + '/municipios_base.csv').set_index('cod_ibge')
cls = pd.cut(base.pop2024, [0, 5000, 10000, 20000, 50000, 100000, np.inf], labels=False)


def panel(name, col='value'):
    d = pd.read_csv(f'{DER}/{name}.csv')
    return d.pivot_table(index='cod_ibge', columns='year', values=col)


J = np.log(panel('panel_K1_formal_jobs').clip(lower=0.2))
LIT = panel('panel_K3_literacy')
DAY = panel('panel_K4_daycare')
sn = pd.read_csv(DER + '/panel_K6_sanitation_snis.csv')
SEW = sn.pivot_table(index='cod_ibge', columns='year', values='sewer_pop_share')
if SEW.stack().max() <= 1.5:
    SEW = 100 * SEW
# two-year changes (literacy: one year, the only change observed), in simulation SD units
spec = {'lit': (LIT, 2023, 2024), 'day': (DAY, 2022, 2024), 'jobs': (J, 2022, 2024), 'sew': (SEW, 2020, 2022)}
res = {'sigma_res': {}, 'r2': {}}
Z = pd.DataFrame(index=base.index)
for k, (Pn, a, b) in spec.items():
    d = pd.DataFrame({'y1': Pn[b] / SDU[k], 'y0': Pn[a] / SDU[k]}).join(base.uf).join(cls.rename('cls')).dropna()
    m = smf.ols('y1 ~ y0 + C(uf):C(cls)', data=d).fit()
    res['sigma_res'][k] = float(np.sqrt(m.scale)); res['r2'][k] = float(m.rsquared)
    Z[k] = m.resid
zc = Z[['lit', 'day', 'jobs', 'sew']].dropna()
res['sigma_res']['composite'] = float(zc.mean(1).std())
res['n_composite'] = int(len(zc))
z = 1.96 + 0.8416                                                   # 5% two-sided, 80% power
NS = [200, 400, 800, 1200, 1600, 2400]
res['N'] = NS
res['mde_main'] = {k: [z * 2 * s / np.sqrt(n) for n in NS] for k, s in res['sigma_res'].items()}
res['mde_inter'] = {k: [z * 4 * s / np.sqrt(n) for n in NS] for k, s in res['sigma_res'].items()}
# effects the pilot should detect: simulated effects of each instrument alone, two years after the start (2029-30) and,
# for assistance, which builds up slowly, also after four (2031-32); posterior medians and 5th-95th percentiles.
# The pilot gives every arm the same expected money, so its incentive contrast is the effort part of the FPM tranche:
# the tranche's effect scaled by the effort channel's share of its real effect (channel accounting, 2029-36).
try:
    Mz = np.load(OUT + '/designs_metrics.npz')
    YRS = list(range(2025, 2037))
    KI = {'jobs': 0, 'lit': 2, 'day': 3, 'sew': 4}
    eff = {}
    chs = ['eff', 'vol', 'alloc', 'ta', 'sel', 'dis']
    def chan_share(key, ch):
        tot = sum(Mz[f'{key}__ch_{c}'] - Mz[f'F00000__ch_{c}'] for c in chs)
        return np.clip((Mz[f'{key}__ch_{ch}'] - Mz[f'F00000__ch_{ch}']) / np.where(np.abs(tot) > 1e-6, tot, np.nan), 0, 1)
    for key, lab, yrs, ch in [('F01000', 'incentive (effort part of the FPM tranche), two years', (2029, 2030), 'eff'),
                              ('F00010', 'technical assistance (commissioners), two years', (2029, 2030), None),
                              ('F00010', 'technical assistance (commissioners), four years', (2031, 2032), None)]:
        if f'{key}__eff_K_y' in Mz.files:
            idx = [YRS.index(y) for y in yrs]
            e = Mz[f'{key}__eff_K_y'][idx].mean(0) - Mz['F00000__eff_K_y'][idx].mean(0)      # (R, K)
            if ch:
                e = e * np.nan_to_num(chan_share(key, ch), nan=0.0)[:, None]
            eff[lab] = {k: [float(np.percentile(e[:, i], q)) for q in (5, 50, 95)] for k, i in KI.items()}
            comp = e[:, [0, 2, 3, 4]].mean(1)
            eff[lab]['composite'] = [float(np.percentile(comp, q)) for q in (5, 50, 95)]
    res['sim_effects_2yr'] = eff
except FileNotFoundError:
    res['sim_effects_2yr'] = {}
json.dump(res, open(OUT + '/pilot_power.json', 'w'), indent=1)
print(json.dumps({k: res[k] for k in ['sigma_res', 'r2', 'n_composite']}, indent=1))
for k in res['mde_main']:
    print(k, 'MDE main', [round(x, 3) for x in res['mde_main'][k]], ' interaction', [round(x, 3) for x in res['mde_inter'][k]])
print(json.dumps(res['sim_effects_2yr'], indent=1)[:1500])
