"""
08_chain.py -- from mayors to Brasilia: an illustrative chain from the simulated municipal outcomes to the vote
of the parties that depend most on municipal brokerage (the "centrao"). It is deliberately reduced-form.

A share b of all Chamber votes is assumed to be delivered by mayors ("brokerage vote"), in proportion to the
population each party's mayors govern; it scales with national clientelist capacity CC (vulnerability x
discretionary money). The rest of each party's vote is unaffected by mayors. Campaign money multiplies the vote
with elasticity e:

  V_p = [ (V_p0 - b * M_p0)  +  b * M_p * CC / CC0 ] * ((F_p + 1e-4) / (F_p0 + 1e-4)) ** e,   renormalised to 1,

where V_p0 is the party's 2022 Chamber vote share, M_p0 (M_p) the share of the population governed by its mayors in
2024 (2036), F_p0 (F_p) its FEFC share today (2036). Priors: b ~ U(0.05, 0.25), e ~ U(0.05, 0.30), paired with the
simulation draws; the status quo in 2036 is computed with the same formula, and the effect is the difference.
Outputs: output/chain.json
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json
import numpy as np
import pandas as pd
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

OUT = _ROOT + '/output'
c = S.load()
parties = c['parties']
M = np.load(OUT + '/designs_metrics.npz')
cam = pd.read_csv(_ROOT + '/data/raw/elections/camara_2022_kalebefukuda/camara_2022_partido_nacional.csv')
cam['party'] = cam.sg_partido.replace(S.NORM_PARTY)
V0 = cam.groupby('party').share_votos_nominais.sum()
V0 = np.array([V0.get(p, 0.0) for p in parties]); V0 = V0 / V0.sum()
CENTRAO = [parties.index(p) for p in ['PSD', 'MDB', 'PP', 'UNIAO', 'PL', 'REPUBLICANOS', 'PODEMOS', 'AVANTE',
                                      'SOLIDARIEDADE', 'PRD', 'AGIR', 'MOBILIZA', 'PMB', 'DC', 'PRTB'] if p in parties]
fp0, fe0 = S.sq_shares(parties)
pop0 = np.bincount(c['pidx0'], weights=c['pop'], minlength=len(parties)) / c['pop'].sum()
VUL0 = S.Calib().vul_mean
rng = np.random.default_rng(42)
res = {}
R_ALL = M['W0__mayors_pop_2036'].shape[0]
for key in ['F11111', 'ROB', 'F00100', 'F00001', 'F10000', 'F01000', 'F00010']:
    if f'{key}__mayors_pop_2036' not in M.files:
        if key == 'ROB':                              # v5: the v4 redesign is no longer simulated; its draws of b and e are
            rng.uniform(0.05, 0.25, R_ALL); rng.uniform(0.05, 0.30, R_ALL)   # skipped so the other designs keep theirs
        continue
    Md, M0 = M[f'{key}__mayors_pop_2036'], M['W0__mayors_pop_2036']
    Fd, F0 = M[f'{key}__fe_2036'], M['W0__fe_2036']
    Dd, D0 = M[f'{key}__disc_2036'], M['W0__disc_2036']
    vul = M[f'{key}__vul_2036']                       # design minus status quo (mean level difference)
    R = Md.shape[0]
    b = rng.uniform(0.05, 0.25, R); e = rng.uniform(0.05, 0.30, R)
    cc_ratio = (Dd / D0) * (VUL0 + vul) / VUL0

    def vote(Mx, Fx, ccr):
        base = np.maximum(V0[None] - b[:, None] * pop0[None], 0.1 * V0[None])
        v = (base + b[:, None] * Mx * ccr[:, None]) * ((Fx + 1e-4) / (fe0[None] + 1e-4)) ** e[:, None]
        return v / v.sum(1, keepdims=True)
    vd = vote(Md, Fd, cc_ratio); v0 = vote(M0, F0, np.ones(R))
    dc = (vd[:, CENTRAO].sum(1) - v0[:, CENTRAO].sum(1)) * 100
    # decomposition: municipal base and brokerage (no money channel) vs money channel only
    vd_nomoney = vote(Md, F0, cc_ratio)
    dc_base = (vd_nomoney[:, CENTRAO].sum(1) - v0[:, CENTRAO].sum(1)) * 100
    res[key] = dict(delta_centrao_pp=[float(np.percentile(dc, q)) for q in (5, 50, 95)],
                    delta_centrao_mayors_only_pp=[float(np.percentile(dc_base, q)) for q in (5, 50, 95)],
                    centrao_2022=float(V0[CENTRAO].sum() * 100),
                    centrao_base_2036=float(v0[:, CENTRAO].sum(1).mean() * 100),
                    disc_ratio=[float(np.percentile(Dd / D0, q)) for q in (5, 50, 95)],
                    cc_ratio=[float(np.percentile(cc_ratio, q)) for q in (5, 50, 95)],
                    vul_change=[float(np.percentile(vul, q)) for q in (5, 50, 95)],
                    share_draws_centrao_falls=float((dc < 0).mean()))
    print(key, json.dumps({k: (np.round(v, 3).tolist() if isinstance(v, list) else round(v, 3)) for k, v in res[key].items()}))
json.dump(res, open(OUT + '/chain.json', 'w'), indent=1)
