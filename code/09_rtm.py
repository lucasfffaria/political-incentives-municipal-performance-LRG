"""
09_rtm.py -- regression to the mean in real data: how much would municipalities that a scorecard flags improve
"by themselves", with no law at all? For each indicator with consecutive readings, municipalities below the
national 20th percentile of their population group in year t (worse than the floor) are compared with the
others in year t+1 (t+2 for biennial IDEB). Also the share of flagged municipalities that would exit the flag.
Outputs: output/rtm.json
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import numpy as np
import pandas as pd

DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'
b = pd.read_csv(DER + '/municipios_base.csv').set_index('cod_ibge')
grp = pd.cut(b.pop2022, [0, 20000, 100000, np.inf], labels=['small', 'medium', 'large'])
res = {}
specs = [('Literacy (K3)', 'panel_K3_literacy.csv', 'value', [(2023, 2024)], 1),
         ('IDEB', 'panel_E_ideb.csv', 'value', [(2017, 2019), (2019, 2021), (2021, 2023), (2023, 2025)], 1),
         ('Homicides (K7)', 'panel_K7_homicides.csv', 'value', [(t, t + 1) for t in range(2010, 2016)], -1),
         ('Daycare (K4)', 'panel_K4_daycare.csv', 'value', [(t, t + 1) for t in range(2016, 2025)], 1),
         ('Formal jobs (K1)', 'panel_K1_formal_jobs.csv', 'value', [(t, t + 1) for t in range(2015, 2024)], 1)]
for name, f, col, pairs, orient in specs:
    d = pd.read_csv(DER + '/' + f)
    if 'K1' in f:
        d = d[d[col] > 0].copy(); d[col] = np.log(d[col])
    w = d.pivot_table(index='cod_ibge', columns='year', values=col)
    rows = []
    for t0, t1 in pairs:
        if t0 not in w.columns or t1 not in w.columns:
            continue
        x = w[[t0, t1]].dropna() * orient
        gg = grp.reindex(x.index)
        fl = x.groupby(gg, observed=True)[t0].transform(lambda s: s.quantile(0.2))
        below = x[t0] < fl
        dlt = x[t1] - x[t0]
        rel = dlt[below].mean() - dlt[~below].mean()
        exit_ = (x.loc[below, t1] >= fl[below]).mean()
        sd = x[t0].std()
        rows.append((t0, t1, rel, rel / sd, exit_, int(below.sum())))
    r = pd.DataFrame(rows, columns=['t0', 't1', 'rel_gain', 'rel_gain_sd', 'exit_share', 'n_flagged'])
    res[name] = dict(pairs=r.round(4).to_dict('records'), mean_rel_gain=float(r.rel_gain.mean()),
                     mean_rel_gain_sd=float(r.rel_gain_sd.mean()), mean_exit_share=float(r.exit_share.mean()),
                     unit='log points' if 'K1' in f else ('per 100,000 (sign reversed: fall)' if orient < 0 else 'natural units'))
    print(name, r.round(3).to_string(index=False))
json.dump(res, open(OUT + '/rtm.json', 'w'), indent=1)
