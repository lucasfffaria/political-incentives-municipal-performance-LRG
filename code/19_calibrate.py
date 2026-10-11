"""
19_calibrate.py -- Bayesian calibration of the behavioural parameters by sampling-importance-resampling.

Prior draws of all 47 parameters (uniform priors, lrg2_sim.PRIORS) are weighted by how well the model, with the
same equations as the simulation (Appendix A), reproduces estimated responses to real incentives:
  M1  Ceara's results-based ICMS rule alone (Lautharte et al., 2021; Ponne, 2023): learning, years 1-3
  M2  the same rule with technical assistance (PAIC): learning, years 5-9
  M3  close 2020 races in which the incumbent ran (17_incentive_estimates.py): a lame duck (same mayor and party) against
      a new first-term mayor of another party, changes over 2021-24 in daycare, IDEB, formal jobs, sewage, value added.
      v4: RD = P + C - E, with E the electoral incentive (the model's effort of a mayor who can run again), C the
      continuity of the ruling party (the model's disruption, avoided) and P the continuity of the person, a nuisance
      between 0 and the largest party-continuity effect the data do not reject (Pmax, 17_incentive_estimates.py)
  M3o (v4) open seats of 2020: the outgoing mayor's party barely kept or lost the office, a new eligible mayor on both
      sides; RD = C. Separates party continuity from the electoral incentive (Section 7.1)
  M4  electoral return to measured performance, 2020 and 2024
  M5  unconditional money: daycare and formal jobs at the FPM population brackets (18_fpm_rd.py)
v4: the targets of a block share one source, so they enter a joint normal likelihood with the bootstrap correlations of
the estimates (M3, M3o, M5) and an assumed 0.5 between the two Ceara horizons (M1, M2); every standard error is widened
by an external-validity term. Variants (Section 7.5): main; v3 (the v3 likelihood: reproduces the v3 posterior exactly);
wide (wider priors for weakly identified parameters); noCE, noRD, noEL, noFPM (leave one group of targets out);
trans50 (Ceara's responses are twice the national ones); indep (no correlation between targets).
v5: cap2, cap8, lin (saturation of effort: the cap of a* = delta I / (1 + I / cap) is 2, 8 or infinite instead of 4).
usage: python 19_calibrate.py J [VARIANT]
Writes output/posterior_draws.npz and output/calibration.json (main), or *_VARIANT.* (other variants).
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json
import numpy as np
import pandas as pd
from scipy.stats import norm
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

OUT = _ROOT + '/output'
J = int(sys.argv[1]) if len(sys.argv) > 1 else 60000
VAR = sys.argv[2] if len(sys.argv) > 2 else 'main'
NPOST = 400
WIDE = {'delta_K1': (0.0, 0.06), 'delta_K2': (0.0, 0.06), 'delta_K3': (0.02, 4.0), 'delta_K4': (0.0, 0.6),
        'delta_K6': (0.0, 0.2), 'delta_K7': (0.0, 0.12), 'S2': (1.0, 4.0), 'S3': (1.0, 10.0), 'kappa_money': (0.05, 2.0),
        'kappa_party': (0.0, 1.0), 'cap_slope': (0.1, 1.0), 'chi_comm': (0.05, 0.7), 'beta_TA': (0.0, 0.8),
        'ta_quality': (0.1, 1.0), 'w_lrg': (0.05, 0.45), 'tau_turn': (0.0, 1.0), 'rho_dis': (0.3, 0.98),
        'kappa_el': (0.0, 2.0), 'beta_perf': (0.0, 0.5), 'rec_party': (0.0, 0.6), 'det_entry': (0.0, 0.4)}
PRI = dict(S.PRIORS)
if VAR == 'wide':
    PRI.update(WIDE)
rng = np.random.default_rng(20261009)
P = {k: rng.uniform(lo, hi, J) for k, (lo, hi) in PRI.items()}     # = S.draw_params(J, rng) when PRI == S.PRIORS
c = S.load()
CAPS = {'cap2': 2.0, 'cap8': 8.0, 'lin': np.inf}         # v5: saturation of effort, a* = delta I / (1 + I / cap)
FCAP = CAPS.get(VAR, 4.0)
f = lambda p: p / (1 + p / FCAP)
IE = json.load(open(OUT + '/incentive_estimates.json'))
FR = json.load(open(OUT + '/fpm_rd.json'))
rd = {r['var']: r for r in (IE['rd'] if VAR == 'v3' else [x for x in IE['rd_open'] if x['design'] == 'incumbent ran, pre-trend adjusted'])}
rdo = {r['var']: r for r in IE['rd_open'] if r['design'] == 'open seat, party, pre-trend adjusted'}
dec = {r['var']: r for r in IE['decomposition'] if r['version'] == 'adjusted'}

# ------------------------------------------------------------------ nuisance quantities of the analogues
T_CE = rng.uniform(0.045, 0.070, J)    # Ceara: 18% of the ICMS quota ~ 1.8% of current revenue = 5.6% of FPM-equivalent
CONV = rng.uniform(1.5, 3.0, J)        # municipal-SD per pupil-SD (pupil SD ~37 SAEB points; within-state municipal SD 14.9)
S_EL = 0.60                            # share of mayors who can run again (simulated status quo)
P_TURN = rng.uniform(0.75, 0.95, J)    # v3: where the incumbent loses, the ruling party changes
U_PC = np.random.default_rng(20261010).uniform(0.0, 1.0, J)   # v4: continuity of the person, as a share of Pmax (own stream)
if VAR != 'v3':
    P_TURN = np.ones(J)                # v4: the party label always changes where the incumbent loses (one candidate per party)
TR = 0.5 if VAR == 'trans50' else 1.0  # Ceara's responses relative to the national ones (transportability)
cap_e = lambda m: float(np.mean(S.norm.cdf(c['cap_index'][m] / np.sqrt(1.25))))
capCE = cap_e(c['uf'] == 'CE')
capNAT = cap_e(np.ones(c['N'], bool))
col = lambda k: P[k]

# ------------------------------------------------------------------ M1, M2: Ceara
pel = col('kappa_el') * col('beta_perf') / S.BETA_REF
pce = col('kappa_money') * (T_CE / 0.10) * 6.0                       # whole stake on learning (6 x the mean weight)
de = col('delta_K3') / TR * (S_EL * (f(pel + pce) - f(pel)) + (1 - S_EL) * f(pce))
capm_ce = 1 - col('cap_slope') * (1 - capCE)
rho = col('rhoA')
m1 = de * capm_ce * ((1 - rho) + (1 - rho ** 3)) / 2 / CONV
gap = 1 - capCE
capm_ta = 1 - col('cap_slope') * (1 - (capCE + gap * col('chi_comm')))
ata7 = col('beta_TA') / TR * gap * (1 - 0.95 ** 7) / 0.05
m2 = (de * capm_ta * (1 - rho ** 7) + ata7) / CONV

# ------------------------------------------------------------------ M3, M3o: career incentives and continuity (RD 2020)
capm_n = 1 - col('cap_slope') * (1 - capNAT)
W_DIS = {'day_21': ('K4', 4, 0.5), 'ideb_21': ('K3', 3, 1.0), 'jobs_21': ('K1', 4, 0.0), 'sew_21': ('K6', 2, 0.0), 'va_21': ('K2', 1, 0.0)}


def e_elect(k, t):                     # effort of a mayor who can run again, accumulated over t years
    return col('delta_' + k) * f(pel) * capm_n * (1 - rho ** t)


def cont_party(t, w_dis):              # disruption avoided when the ruling party stays
    return col('tau_turn') * w_dis * col('rho_dis') ** t


m3, m3o = {}, {}
for v, (k, t, w) in W_DIS.items():
    e_el = col('delta_' + k) * f(pel) * capm_n
    m3[v] = -e_el * (1 - rho ** t) + P_TURN * col('tau_turn') * w * col('rho_dis') ** t        # the v3 expression
    if VAR != 'v3':
        m3[v] = m3[v] + U_PC * dec[v]['pmax']
    m3o[v] = cont_party(t, w)

# ------------------------------------------------------------------ targets, by block
EXT = 0.02
er = pd.DataFrame(IE['electoral_returns'])
comp = er[er['var'].str.startswith('composite')]
b_hat = float((comp.logit_per_sd / (comp.se_pp / comp.coef_pp * comp.logit_per_sd) ** 2).sum() /
              (1 / (comp.se_pp / comp.coef_pp * comp.logit_per_sd) ** 2).sum())
b_se = float(np.sqrt(1 / (1 / (comp.se_pp / comp.coef_pp * comp.logit_per_sd) ** 2).sum()))
FRr = {r['var']: r for r in FR['rd'] if r['kind'] == 'reduced form'}
X100 = 100.0
m5_day = 0.25 * (1 - col('w_gen')) * X100 / col('cost_slot') / 0.075 * 100 / 12.2
m5_jobs = np.log1p(X100 * 100 / col('cost_job') / 10.0) / 0.89
M3V = IE['corr_vars']
BLOCKS = {   # name: (list of (label, model, target, se)), correlation matrix
    'CE': ([('M1 Ceara, rule alone (pupil SD)', m1, 0.06, np.hypot(0.035, 0.02)),
            ('M2 Ceara, rule + PAIC (pupil SD)', m2, 0.42, np.hypot(0.06, 0.15))], np.array([[1, 0.5], [0.5, 1]])),
    'RD': ([(f'M3 lame minus first-term: {v}', m3[v], rd[v]['coef'], np.hypot(rd[v]['se'], EXT)) for v in M3V],
           np.array(IE['corr_rd_inc'])),
    'RDo': ([(f'M3o party kept minus lost, open seats: {v}', m3o[v], rdo[v]['coef'], np.hypot(rdo[v]['se'], EXT)) for v in M3V],
            np.array(IE['corr_rd_open'])),
    'EL': ([('M4 electoral return (logit per SD)', col('beta_perf'), b_hat, np.hypot(b_se, 0.02))], np.eye(1)),
    'FPM': ([('M5 FPM brackets: daycare level per R$100', m5_day, FRr['day_lv']['per100rs'], np.hypot(FRr['day_lv']['per100rs_se'], 0.02)),
             ('M5 FPM brackets: formal jobs per R$100', m5_jobs, FRr['jobs']['per100rs'], np.hypot(FRr['jobs']['per100rs_se'], 0.02))],
            np.array([[1, FR.get('corr_m5', 0.0)], [FR.get('corr_m5', 0.0), 1]])),
}
USE = {'main': ['CE', 'RD', 'RDo', 'EL', 'FPM'], 'v3': ['CE', 'RD', 'EL', 'FPM'], 'wide': ['CE', 'RD', 'RDo', 'EL', 'FPM'],
       'noCE': ['RD', 'RDo', 'EL', 'FPM'], 'noRD': ['CE', 'EL', 'FPM'], 'noEL': ['CE', 'RD', 'RDo', 'FPM'],
       'noFPM': ['CE', 'RD', 'RDo', 'EL'], 'trans50': ['CE', 'RD', 'RDo', 'EL', 'FPM'], 'indep': ['CE', 'RD', 'RDo', 'EL', 'FPM'],
       'cap2': ['CE', 'RD', 'RDo', 'EL', 'FPM'], 'cap8': ['CE', 'RD', 'RDo', 'EL', 'FPM'], 'lin': ['CE', 'RD', 'RDo', 'EL', 'FPM']}[VAR]
lw = np.zeros(J)
for b in USE:
    items, C = BLOCKS[b]
    if VAR in ('v3', 'indep'):
        C = np.eye(len(items))
    if np.allclose(C, np.eye(len(items))):              # independent targets (the v3 likelihood, term by term)
        for name, mv, tgt, se in items:
            lw += norm.logpdf(mv, tgt, se)
    else:
        sd = np.array([it[3] for it in items])
        Sig = np.diag(sd) @ C @ np.diag(sd)
        Lc = np.linalg.cholesky(Sig)
        resid = np.stack([it[1] - it[2] for it in items])          # (n, J)
        z = np.linalg.solve(Lc, resid)
        lw += -0.5 * (z ** 2).sum(0) - np.log(np.diag(Lc)).sum()
log_evidence = float(lw.max() + np.log(np.mean(np.exp(lw - lw.max()))))   # v5: log mean likelihood over the prior
w = np.exp(lw - lw.max()); w /= w.sum()
ess = float(1 / (w ** 2).sum())
# systematic resampling
u = (rng.random() + np.arange(NPOST)) / NPOST
idx = np.minimum(np.searchsorted(np.cumsum(w), u), J - 1)
post = {k: v[idx] for k, v in P.items()}
SUF = '' if VAR == 'main' else '_' + VAR
np.savez_compressed(OUT + f'/posterior_draws{SUF}.npz', **post)


# ------------------------------------------------------------------ summaries, fit, validation
def wq(x, q):
    o = np.argsort(x); cw = np.cumsum(w[o])
    return float(x[o][min(np.searchsorted(cw, q), len(x) - 1)])


summ = {}
for k, (lo, hi) in PRI.items():
    x = P[k]
    summ[k] = dict(prior=[lo, hi], post_p5=wq(x, 0.05), post_med=wq(x, 0.5), post_p95=wq(x, 0.95),
                   shrink=1 - (wq(x, 0.95) - wq(x, 0.05)) / (0.9 * (hi - lo)))
fit = []
for b, (items, C) in BLOCKS.items():
    for name, mv, tgt, se in items:
        fit.append(dict(block=b, used=b in USE, moment=name, target=float(tgt), se=float(se),
                        prior_p5=float(np.percentile(mv, 5)), prior_p95=float(np.percentile(mv, 95)),
                        post_med=wq(mv, 0.5), post_p5=wq(mv, 0.05), post_p95=wq(mv, 0.95),
                        z=float((wq(mv, 0.5) - tgt) / se)))
# checks not used for weighting: panel estimates of career incentives, the literacy discontinuities, Ceara's time path
pan = {r['ind']: r for r in IE['panel']}
checks = []
for k, ind, t, wd in [('K4', 'day', 4, 0.5), ('K3', 'ideb', 4, 1.0), ('K1', 'jobs', 4, 0.0)]:
    e_el = col('delta_' + k) * f(pel) * capm_n
    # all mandates: lame ducks against first-term mayors, of whom about 60% replaced a mayor of another party
    mv = -e_el * (1 - rho ** t) + 0.6 * col('tau_turn') * wd * col('rho_dis') ** min(t, 3)
    checks.append(dict(check=f'panel lame-duck coefficient, {ind}', estimate=pan[ind]['fe_coef'], se=pan[ind]['fe_se'],
                       post_med=wq(mv, 0.5), post_p5=wq(mv, 0.05), post_p95=wq(mv, 0.95)))
lit_inc = [x for x in IE['rd_open'] if x['design'] == 'incumbent ran, pre-trend adjusted' and x['var'] == 'lit_24'][0]
lit_open = [x for x in IE['rd_open'] if x['design'] == 'open seat, party, pre-trend adjusted' and x['var'] == 'lit_24'][0]
mv = -e_elect('K3', 4) + P_TURN * cont_party(4, 1.0) + (0.0 if VAR == 'v3' else U_PC * dec['ideb_21']['pmax'])
checks.append(dict(check='RD literacy 2024, incumbent ran', estimate=lit_inc['coef'], se=lit_inc['se'],
                   post_med=wq(mv, 0.5), post_p5=wq(mv, 0.05), post_p95=wq(mv, 0.95)))
mv = cont_party(4, 1.0)
checks.append(dict(check='RD literacy 2024, open seats', estimate=lit_open['coef'], se=lit_open['se'],
                   post_med=wq(mv, 0.5), post_p5=wq(mv, 0.05), post_p95=wq(mv, 0.95)))
# time profile of Ceara's gains (Ponne, 2023, Figure 7: synthetic-control gaps in 5th-grade Portuguese, SAEB points; the rule
# from 2008, PAIC in grades 3-5 from 2011), not used for weighting: model path with the rule from year 1 and assistance from year 3
PONNE = {2009: 4.0, 2011: 10.5, 2013: 17.0, 2015: 23.0, 2017: 22.5, 2019: 19.5}
path = []
for yr_, gap_pts in PONNE.items():
    t = yr_ - 2008
    ta_t = max(t - 2, 0)
    a_ti = de * (capm_ce if ta_t == 0 else capm_ta) * (1 - rho ** t)
    a_ta = col('beta_TA') / TR * gap * (1 - 0.95 ** ta_t) / 0.05
    mv = (a_ti + a_ta) / CONV
    path.append(dict(year=yr_, observed_pupil_sd=gap_pts / 37.0, post_med=wq(mv, 0.5), post_p5=wq(mv, 0.05), post_p95=wq(mv, 0.95)))
# money at stake: Ceara's education share of the ICMS quota and the LRG tranche, as shares of current revenue (2024)
bb = pd.read_csv(_ROOT + '/data/derived/municipios_base.csv', usecols=['uf', 'rev_current_2024', 'rev_state_2024', 'fpm_gross_2024'])
ce = bb[(bb.uf == 'CE')].dropna()
nat = bb.dropna(subset=['rev_current_2024'])
stake = dict(ce_state_transfers_share=float((ce.rev_state_2024 / ce.rev_current_2024).median()),
             ce_fpm_share=float((ce.fpm_gross_2024 / ce.rev_current_2024).median()),
             ce_edu_stake_share_lo=float(0.18 * 0.80 * (ce.rev_state_2024 / ce.rev_current_2024).median()),
             ce_edu_stake_share_hi=float(0.18 * 0.95 * (ce.rev_state_2024 / ce.rev_current_2024).median()),
             lrg_tranche_share=float(0.10 * (nat.fpm_gross_2024 / nat.rev_current_2024).median()),
             t_ce_range=[0.045, 0.070], n_ce=int(len(ce)))
# the electoral incentive's effect on learning implied by the posterior (lame duck against eligible, 3 years), for Section 7.1
eff_learn = e_elect('K3', 3)
res = dict(variant=VAR, used=USE, J=J, ess=ess, log_evidence=log_evidence, eff_cap=float(FCAP) if np.isfinite(FCAP) else None, n_post=NPOST, unique_post=int(len(np.unique(idx))), beta_hat=b_hat, beta_se=b_se,
           capCE=capCE, capNAT=capNAT, params=summ, fit=fit, checks=checks, stake=stake, ceara_path=path,
           elect_effect_learning=dict(post_med=wq(eff_learn, 0.5), post_p5=wq(eff_learn, 0.05), post_p95=wq(eff_learn, 0.95),
                                      prior_p5=float(np.percentile(eff_learn, 5)), prior_p95=float(np.percentile(eff_learn, 95))),
           person_share=dict(post_med=wq(U_PC, 0.5), post_p5=wq(U_PC, 0.05), post_p95=wq(U_PC, 0.95)))
json.dump(res, open(OUT + f'/calibration{SUF}.json', 'w'), indent=1)
pd.set_option('display.width', 220)
print(f'{VAR}: J={J}  ESS={ess:.0f}  unique resampled={res["unique_post"]}  beta_hat={b_hat:.3f} ({b_se:.3f})  capCE={capCE:.2f} capNAT={capNAT:.2f}')
print(pd.DataFrame(fit).round(3).to_string())
print(pd.DataFrame(checks).round(3).to_string())
print(pd.DataFrame(path).round(3).to_string())
ps = pd.DataFrame(summ).T
print(ps[ps.shrink.astype(float) > 0.05].round(3).to_string())
print('electoral effect on learning (3 years):', {k: round(v, 3) for k, v in res['elect_effect_learning'].items()})
