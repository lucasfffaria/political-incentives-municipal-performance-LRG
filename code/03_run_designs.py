"""
03_run_designs.py -- Monte Carlo over the calibrated parameters (400 posterior draws from 19_calibrate.py) for the
status quo, a placebo, a full 2^5 factorial of the LRG pillars (sanctions S, FPM tranche F, tied amendments A,
commissioners C, party funds P; the scorecard is published whenever the law is on), single-deviation variants of the
LRG as proposed, doses of the FPM tranche, the LRG without bans for results and, in v5, the tests of the ban on the LRG
as proposed: deterrence without execution (AP_th), execution without deterrence (AP_ex), the intensity of the threat
(AP_s05 ... AP_s8), the same tests with the sanctions alone (S_*), and a personal bonus for mayors on the LRG's own
scorecard (a theoretical benchmark, Appendix). Common random numbers: every design sees the same parameter draws and
the same shocks.

usage: python 03_run_designs.py R_TOTAL [CHUNK] [DESIGNS|all] [TAG] [SCENARIO] [POSTERIOR]
       (with TAG, results go to designs_metrics_TAG.npz; merge the parts with 03b_merge_runs.py)
       SCENARIO applies one setting to every design, the status quo included: base (default); v3 (the v3 specification
       of the ban threat); lameM (banned mayors still respond to money); implementation complementarity iB, iC, iD;
       voters' reward for performance eN (none), eH2, eH4 (x2, x4); manipulation m0 (none), m0s (none, effort redirected
       to real improvement), mL (x0.5), mH (x1.5), mA (audits remove 60%), mAs (audits and redirection); v5: saturation
       of effort cap2, cap8, lin (each with its own calibration, POSTERIOR); responsiveness of effort dm15, dm2, dm3
       (x1.5, x2, x3, no recalibration); weight of money km2, km3 (x2, x3, no recalibration).
       POSTERIOR: a posterior_draws file (default output/posterior_draws.npz).
Outputs: output/designs_metrics.npz (draw-level metrics per design), output/designs_summary.csv
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, time, itertools, json
from dataclasses import replace
import numpy as np
import pandas as pd
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

OUT = _ROOT + '/output'
R_TOTAL = int(sys.argv[1]) if len(sys.argv) > 1 else 200
CHUNK = int(sys.argv[2]) if len(sys.argv) > 2 else 40
ONLY = sys.argv[3].split(',') if (len(sys.argv) > 3 and sys.argv[3] != 'all') else None
TAG = sys.argv[4] if len(sys.argv) > 4 else ''           # run designs in parallel processes, then merge (see merge_runs)
SCEN = sys.argv[5] if len(sys.argv) > 5 else 'base'
POSTFILE = sys.argv[6] if len(sys.argv) > 6 else OUT + '/posterior_draws.npz'
SCENARIOS = {'base': {}, 'v3': dict(threat_v3=True), 'lameM': dict(lame_rule='money'), 'iDlameM': dict(impl_lambda=0.75, lame_rule='money'),
             'iB': dict(impl_lambda=0.25), 'iC': dict(impl_lambda=0.50), 'iD': dict(impl_lambda=0.75),
             'eN': dict(beta_mult=0.0), 'eH2': dict(beta_mult=2.0), 'eH4': dict(beta_mult=4.0),
             'm0': dict(manip_scale=0.0), 'm0s': dict(manip_scale=0.0, manip_subst=1.0), 'mL': dict(manip_scale=0.5),
             'mH': dict(manip_scale=1.5), 'mA': dict(manip_audit=0.6), 'mAs': dict(manip_audit=0.6, manip_subst=1.0),
             # v5: saturation of effort (run with the matching calibration), responsiveness and weight of money
             'cap2': dict(eff_cap=2.0), 'cap8': dict(eff_cap=8.0), 'lin': dict(eff_cap=float('inf')),
             'dm15': dict(delta_mult=1.5), 'dm2': dict(delta_mult=2.0), 'dm3': dict(delta_mult=3.0),
             'km2': dict(pmult=(('kappa_money', 2.0),)), 'km3': dict(pmult=(('kappa_money', 3.0),))}

AS_PROPOSED = S.Design(name='LRG as proposed', law=True, sanctions=True, fpm=True, amend=True, capacity=True, party=True)
DESIGNS = {'W0': S.Design(name='Status quo'),
           'WP': S.Design(name='Placebo (rules, no response)', law=True, sanctions=True, placebo=True)}
PILLARS = ['sanctions', 'fpm', 'amend', 'capacity', 'party']        # S, F, A, C, P
for bits in itertools.product([0, 1], repeat=5):
    key = 'F' + ''.join(str(x) for x in bits)
    DESIGNS[key] = replace(AS_PROPOSED, name='Factorial ' + key, **{p: bool(b) for p, b in zip(PILLARS, bits)})
DESIGNS['V_literal'] = replace(AS_PROPOSED, name='As proposed, no tolerance', tol_mult=0.0)
DESIGNS['V_far15'] = replace(AS_PROPOSED, name='As proposed, red at 1.5 SD below the floor', far_sd=1.5)
DESIGNS['V_noNI'] = replace(AS_PROPOSED, name='As proposed, without the no-improvement rule', no_improve_rule=False)
DESIGNS['V_ramp'] = replace(AS_PROPOSED, name='As proposed, feasible hiring (1,500 commissioners/yr)', comm_ramp=1500)
DESIGNS['V_poptranche'] = replace(AS_PROPOSED, name='As proposed, tranche by points x population', tranche_basis='pop')
DESIGNS['V_redirect'] = replace(AS_PROPOSED, name='As proposed, amendments redirected away', em_condition='redirect')
DESIGNS['V_bands'] = replace(AS_PROPOSED, name='As proposed, party funds by colour bands', party_rule='bands')
DESIGNS['V_missao'] = replace(AS_PROPOSED, name='As proposed, new party with 3% of votes and 3% of open seats',
                              missao_fp_sq=0.03, missao_open_seat=0.03)
DESIGNS['W0_missao'] = replace(DESIGNS['W0'], name='Status quo, new party with 3% of votes and 3% of open seats',
                               missao_fp_sq=0.03, missao_open_seat=0.03)
DESIGNS['V_leak50'] = replace(AS_PROPOSED, name='As proposed, half of the tied money leaks to discretionary channels', em_leak=0.5)
DESIGNS['V_termx5'] = replace(AS_PROPOSED, name='As proposed, mayor component with five times the estimated variance', term_mult=float(np.sqrt(5)))
# a personal bonus for the mayor on the LRG's own scorecard (published, nothing else): a theoretical benchmark (Appendix)
BON = S.Design(name='Personal bonus', law=True)
DESIGNS['B025'] = replace(BON, name='Personal bonus, 0.25 salary per SD', bonus=0.25)
DESIGNS['B05'] = replace(BON, name='Personal bonus, half a salary per SD', bonus=0.5)
DESIGNS['B10'] = replace(BON, name='Personal bonus, one salary per SD', bonus=1.0)
# doses of the FPM tranche alone
for tr in (0.025, 0.05, 0.20):
    DESIGNS[f'F_t{int(tr * 1000):03d}'] = replace(DESIGNS['F01000'], name=f'FPM tranche alone, {100 * tr:g}% of the FPM', tranche=tr)
# v4: isolating the removal of the ban (the other instruments held fixed)
DESIGNS['AP_nb'] = replace(AS_PROPOSED, name='As proposed without bans for results (alerts and tutelage kept)', bans_results=False)
# v5: deterrence against execution of the ban, and the intensity of the threat, on the LRG as proposed and on the sanctions alone
MULTS = {'s05': 0.5, 's2': 2.0, 's4': 4.0, 's8': 8.0}
DESIGNS['AP_th'] = replace(AS_PROPOSED, name='As proposed, bans threatened but never executed (deterrence only)', ban_execute=False)
DESIGNS['AP_ex'] = replace(AS_PROPOSED, name='As proposed, bans executed but not anticipated (no deterrence)', ban_threat=False)
for tg, m in MULTS.items():
    DESIGNS['AP_' + tg] = replace(AS_PROPOSED, name=f'As proposed, weight of a ban x{m:g}', s3_mult=m)
SAN = DESIGNS['F10000']
DESIGNS['S_nb'] = replace(SAN, name='Sanctions alone without bans for results (alerts and tutelage)', bans_results=False)
DESIGNS['S_th'] = replace(SAN, name='Sanctions alone, bans threatened but never executed', ban_execute=False)
DESIGNS['S_ex'] = replace(SAN, name='Sanctions alone, bans executed but not anticipated', ban_threat=False)
for tg, m in MULTS.items():
    DESIGNS['S_' + tg] = replace(SAN, name=f'Sanctions alone, weight of a ban x{m:g}', s3_mult=m)
# v5 check of the no-sanction counterfactual: the tutelage classification no longer routes tied amendments
DESIGNS['F01111_nd'] = replace(DESIGNS['F01111'], name='Without performance sanctions, amendments not routed by the classification',
                               amend_disq=False)
if ONLY:
    DESIGNS = {k: v for k, v in DESIGNS.items() if k in ONLY or k == 'W0'}
if SCENARIOS[SCEN]:
    DESIGNS = {k: replace(v, **SCENARIOS[SCEN]) for k, v in DESIGNS.items()}

c = S.load()
parties = c['parties']
BIG6 = [parties.index(p) for p in ['PSD', 'MDB', 'PP', 'UNIAO', 'PL', 'REPUBLICANOS']]
LEFT = [parties.index(p) for p in ['PT', 'PSB', 'PDT', 'PCDOB', 'PV', 'REDE', 'PSOL'] if p in parties]
IM = parties.index('MISSAO')
YI = {y: i for i, y in enumerate(S.YEARS)}
EVAL = [YI[y] for y in range(2027, 2036)]                # money flows decided on evaluations 2027-2035
EVALALL = [YI[y] for y in range(2027, 2037)]             # all evaluations (data years 2027-2036)
TERM2 = [YI[y] for y in range(2029, 2037)]


def metrics(o, o0):
    R = o['q'].shape[1]
    m = {}
    eff = o['q'] - o0['q']                                  # (T, R, K) SD units, unweighted municipal mean
    effp = o['qpw'] - o0['qpw']
    meas = o['y'] - o0['y']
    m['eff_K'] = eff[TERM2].mean(0)                         # (R, K) average 2029-2036
    m['eff_K_2036'] = eff[-1]
    m['effpw_K'] = effp[TERM2].mean(0)
    m['meas_K'] = meas[TERM2].mean(0)
    m['eff_comp'] = m['eff_K'].mean(1)
    m['effpw_comp'] = m['effpw_K'].mean(1)
    m['meas_comp'] = m['meas_K'].mean(1)
    m['U_2036'] = o['U'][-1] - o0['U'][-1]
    m['eff_reg'] = (o['q_reg'] - o0['q_reg'])[TERM2].mean(0)
    m['eff_cls'] = (o['q_cls'] - o0['q_cls'])[TERM2].mean(0)
    m['eff_capq'] = (o['q_capq'] - o0['q_capq'])[TERM2].mean(0)
    m['flag'] = o['flag'][EVALALL].mean(0)
    m['tutelage'] = o['stage2'][EVALALL].mean(0)
    m['flag_wrong'] = o['flag_wrong'][EVALALL].mean(0)
    m['red_wrong'] = o['red_wrong'][EVALALL].mean(0)
    m['red_true_hit'] = o['red_true_hit'][EVALALL].mean(0)
    bans = o['stage3'][TERM2].sum(0)                        # bans per mayor in the two full mandates 2029-2036
    m['bans_per100_term'] = bans / 2 * 100
    m['bans_ni_per100_term'] = o['stage3_ni'][TERM2].sum(0) / 2 * 100
    m['wrongful'] = np.where(bans > 0, o['stage3_wrong'][TERM2].sum(0) / np.maximum(bans, 1e-12), np.nan)
    m['place_driven'] = np.where(bans > 0, o['stage3_place'][TERM2].sum(0) / np.maximum(bans, 1e-12), np.nan)
    m['bans_reg_per100'] = o['inel_reg'] / np.bincount(c['reg_idx'], minlength=5)[None] / 2 * 100
    m['bans_cls_per100'] = o['inel_cls'] / np.bincount(c['cls'], minlength=6)[None] / 2 * 100
    m['wrong_cls'] = np.where(o['inel_cls'] > 0, o['inel_wrong_cls'] / np.maximum(o['inel_cls'], 1e-12), np.nan)
    m['tut_reg'] = o['stage2_reg'] / len(EVALALL)
    m['tut_cls'] = o['stage2_cls'] / len(EVALALL)
    m['money_reg'] = o['money_reg'][EVAL].mean(0)           # R$ bn per year
    m['money_gdpq'] = o['money_gdpq'][EVAL].mean(0)
    m['money_corr'] = np.nanmean(o['money_corr_gdp'][EVAL], 0)
    m['money_losers'] = o['money_losers'][EVAL].mean(0)
    m['em_lost'] = o['em_lost'][EVAL].mean(0)
    m['comm_final'] = o['comm'][-1]
    m['comm_cost_bn'] = o['comm'][-1] * S.Calib().cost_commissioner / 1e9   # annual cost once deployed (2036)
    m['cap_2036'] = o['cap'][-1]
    m['theta_2033'] = o['theta'][YI[2033]]
    m['thetapw_2033'] = o['thetapw'][YI[2033]]
    m['turnover'] = o['turnover'][[YI[2032], YI[2036]]].mean(0)
    m['incumb_win'] = o['incumb_win'][[YI[2032], YI[2036]]].mean(0)
    m['incumb_run'] = o['incumb_run'][[YI[2032], YI[2036]]].mean(0)
    m['reelect_elig'] = o['reelect_elig'][[YI[2032], YI[2036]]].mean(0)
    m['fp_2036'] = o['fp'][-1]                              # (R, NP)
    m['fe_2036'] = o['fe'][-1]
    m['fp_big6'] = o['fp'][-1][:, BIG6].sum(1)
    m['fp_left'] = o['fp'][-1][:, LEFT].sum(1)
    m['fp_hhi'] = (o['fp'][-1] ** 2).sum(1)
    m['fp_missao'] = o['fp'][:, :, IM]                      # (T, R)
    m['mayors_2036'] = o['mayors'][-1]
    m['mayors_pop_2036'] = o['mayors_pop'][-1]
    m['mayors_big6'] = o['mayors'][-1][:, BIG6].sum(1)
    m['mayors_missao'] = o['mayors'][:, :, IM]
    m['disc_2036'] = o['disc'][-1]
    m['vul_2036'] = o['vul'][-1] - o0['vul'][-1]
    m['pts_corr'] = np.nanmean(o['pts_corr'][EVAL], 0)
    m['ever_tut'] = (o['muni']['stage2_years'] > 0).mean(1)
    m['ban_theta_neg'] = np.where(o['ban_n'] > 0, o['ban_theta_neg'] / np.maximum(o['ban_n'], 1e-9), np.nan)
    m['ban_theta_mean'] = np.where(o['ban_n'] > 0, o['ban_theta_sum'] / np.maximum(o['ban_n'], 1e-9), np.nan)
    m['ever_ban'] = (o['muni']['inel'] > 0).mean(1)
    m['ban_k_share_grp'] = o['ban_k_grp'] / np.maximum(o['ban_red_grp'][:, :, None], 1e-9)   # (R, 3, K)
    # mechanisms: change in each component of true quality against the status quo, 2029-36 (SD units)
    for ch in ('eff', 'vol', 'alloc', 'ta', 'sel', 'dis', 'man'):
        m['ch_' + ch] = (o['ch_' + ch] - o0['ch_' + ch])[TERM2].mean(0)
        if ch != 'man':
            m['chpw_' + ch] = (o['ch_' + ch + '_pw'] - o0['ch_' + ch + '_pw'])[TERM2].mean(0)
    m['mei'] = o['mei']                                     # (R, 7, 6): marginal expected incentive by source and size class, 2030
    m['bonus_cost'] = o['bonus_cost'][EVAL].mean(0)          # R$ bn a year
    m['elig'] = o['elig'][TERM2].mean(0)
    for kk in ('iota_m', 'iota_ta', 'ratio_m', 'ratio_ta'):          # v4: implementation quality of programmes, 2029-36
        m[kk] = o[kk][TERM2].mean(0)
    m['eff_K_y'] = eff                                      # (T, R, K) yearly effects
    return m


if __name__ == '__main__':
    POST = np.load(POSTFILE)
    assert len(POST[S.PNAMES[0]]) >= R_TOTAL, 'run 19_calibrate.py first'
    master = np.random.default_rng(20261008)
    nchunks = (R_TOTAL + CHUNK - 1) // CHUNK
    seeds = master.integers(0, 2 ** 31, size=nchunks)
    store = {k: [] for k in DESIGNS}
    t0 = time.time()
    # checkpoints: each chunk is saved as it finishes, so an interrupted run resumes where it stopped (results identical)
    CKD = OUT + f'/ckpt_{TAG or "all"}_{SCEN}_{R_TOTAL}_{CHUNK}_{_os.path.basename(POSTFILE).replace(".npz", "")}'
    _os.makedirs(CKD, exist_ok=True)
    for ci, sd in enumerate(seeds):
        R = min(CHUNK, R_TOTAL - ci * CHUNK)
        ckf = f'{CKD}/chunk{ci:03d}.npz'
        if _os.path.exists(ckf):
            z = np.load(ckf)
            got = {key: {mk.split('__', 1)[1]: z[mk] for mk in z.files if mk.split('__', 1)[0] == key} for key in DESIGNS}
            if all(len(v) for v in got.values()):
                for key in DESIGNS:
                    store[key].append(got[key])
                print(f'chunk {ci + 1}/{nchunks} loaded from checkpoint', flush=True)
                continue
        P = {k: POST[k][ci * CHUNK: ci * CHUNK + R] for k in S.PNAMES}
        outs = {}
        o0 = S.simulate(c, P, DESIGNS['W0'], int(sd))
        for key, des in DESIGNS.items():
            o = o0 if key == 'W0' else S.simulate(c, P, des, int(sd))
            m = metrics(o, o0)
            m['params'] = np.stack([P[k] for k in S.PNAMES], 1)
            store[key].append(m)
            del o
        tmp = ckf + '.tmp'
        with open(tmp, 'wb') as fh:
            np.savez(fh, **{f'{key}__{mk}': v for key in DESIGNS for mk, v in store[key][-1].items()})
        _os.replace(tmp, ckf)
        print(f'chunk {ci + 1}/{nchunks} done, {time.time() - t0:.0f}s', flush=True)
    flat = {}
    for key, lst in store.items():
        for mk in lst[0]:
            flat[f'{key}__{mk}'] = np.concatenate([x[mk] for x in lst], axis=1 if lst[0][mk].ndim >= 2 and mk in ('fp_missao', 'mayors_missao', 'eff_K_y') else 0)
    KEEP_Y = {'F11111', 'F01111', 'AP_nb', 'AP_th', 'AP_ex', 'F01000', 'F00100', 'F00010', 'F10000', 'F00001', 'B05', 'F00000'} if SCEN == 'base' else set()
    flat = {k: (v.astype(np.float32) if v.dtype == np.float64 else v) for k, v in flat.items()
            if not (k.endswith('__eff_K_y') and k.split('__')[0] not in KEEP_Y)}
    np.savez_compressed(OUT + (f'/designs_metrics_{TAG}.npz' if TAG else ('/designs_metrics.npz' if not ONLY else '/designs_metrics_partial.npz')), **flat)
    rows = []
    for key, des in DESIGNS.items():
        g = lambda mk: flat[f'{key}__{mk}']
        r = dict(design=key, name=des.name)
        for mk in ['eff_comp', 'effpw_comp', 'meas_comp', 'U_2036', 'flag', 'tutelage', 'bans_per100_term', 'wrongful', 'place_driven',
                   'money_corr', 'money_losers', 'comm_cost_bn', 'theta_2033', 'thetapw_2033', 'turnover', 'incumb_win', 'fp_big6',
                   'fp_left', 'pts_corr', 'disc_2036', 'vul_2036']:
            v = g(mk)
            r[mk + '_med'] = np.nanmedian(v); r[mk + '_p5'] = np.nanpercentile(v, 5); r[mk + '_p95'] = np.nanpercentile(v, 95)
        for k, kn in enumerate(S.KN):
            v = g('eff_K')[:, k]; r[f'eff_{kn}_med'] = np.nanmedian(v)
            v = g('meas_K')[:, k]; r[f'meas_{kn}_med'] = np.nanmedian(v)
        rows.append(r)
    pd.DataFrame(rows).to_csv(OUT + (f'/designs_summary_{TAG}.csv' if TAG else ('/designs_summary.csv' if not ONLY else '/designs_summary_partial.csv')), index=False)
    import shutil
    shutil.rmtree(CKD, ignore_errors=True)
    print('saved; total %.0fs' % (time.time() - t0))
