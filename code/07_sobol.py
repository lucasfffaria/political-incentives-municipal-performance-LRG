"""
07_sobol.py -- variance-based (Sobol) sensitivity of the main results to the 47 uncertain parameters, grouped
into 17 families (Saltelli design, first-order and total-effect indices). Each parameter varies uniformly over its
calibrated range (5th-95th posterior percentiles, output/calibration.json). Designs: status quo, LRG as proposed and,
in v5, three counterfactuals of the LRG as proposed: without bans for results, without any performance sanction, and
with bans executed but not anticipated; outputs are paired differences against the status quo with common random numbers.
v4: the implementation complementarity of Section 3 (lambda, 0-0.75) enters as an uncertain parameter of its own group;
the runs can be split. v5: outputs nb_ratio (share of the effect kept without bans), ns_ratio (kept without any
performance sanction), threat_gain (effect of the deterrence of bans) and exec_effect (effect of executing bans that
nobody anticipates).
usage: python 07_sobol.py N_BASE [run PART NPARTS | merge NPARTS | analyse]   (default: everything in one process)
Outputs: output/sobol.csv, output/sobol_runs.npz
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, time, json
from dataclasses import replace
import numpy as np
import pandas as pd
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

OUT = _ROOT + '/output'
NB = int(sys.argv[1]) if len(sys.argv) > 1 else 64
GROUPS = {
    'Real response: education': ['delta_K3', 'delta_K4'],
    'Real response: other indicators': ['delta_K1', 'delta_K2', 'delta_K6', 'delta_K7'],
    'Manipulation shares': ['gam_K1', 'gam_K2', 'gam_K3', 'gam_K4', 'gam_K6', 'gam_K7'],
    'Weight of tutelage and ban': ['S2', 'S3'],
    'Money incentive': ['kappa_money'],
    'Party pressure and recruitment': ['kappa_party', 'rec_party', 'switch_pts', 'eta_funds'],
    'Persistence and competence': ['rhoA', 'phi_comp'],
    'Neglect of unscored tasks': ['xi_unscored'],
    'Capacity and commissioners': ['cap_slope', 'chi_comm', 'beta_TA', 'ta_other', 'ta_quality'],
    'Tutelage side effects': ['tut_cap', 'tut_drag'],
    'Productivity of money': ['w_sq', 'w_lrg', 'w_gen'],
    'Unit costs': ['cost_sewer', 'cost_slot', 'mu_lit', 'cost_job'],
    'Clientelism': ['kappa_cl', 'eta_emp'],
    'Electoral accountability and information': ['kappa_el', 'beta_perf', 'beta_info'],
    'Turnover and deterrence': ['det_entry', 'tau_turn', 'rho_dis'],
    'Selection by money and pay': ['zeta_curse', 'sel_pay', 'v_office'],
    'Implementation complementarity': ['impl_lambda'],
}
NAMES = S.PNAMES + ['impl_lambda']
gof = {p: g for g, ps in GROUPS.items() for p in ps}
problem = {'num_vars': len(NAMES), 'names': NAMES, 'bounds': [[0, 1]] * len(NAMES),
           'groups': [gof[p] for p in NAMES]}
X = sobol_sample.sample(problem, NB, calc_second_order=False, seed=11)
CAL = json.load(open(OUT + '/calibration.json'))['params']
LO = np.array([CAL[k]['post_p5'] for k in S.PNAMES] + [0.0]); HI = np.array([CAL[k]['post_p95'] for k in S.PNAMES] + [0.75])


def params_from_unit(U):
    return {k: LO[j] + U[:, j] * (HI[j] - LO[j]) for j, k in enumerate(NAMES)}
print('runs per design:', len(X), flush=True)
MODE = sys.argv[2] if len(sys.argv) > 2 else 'all'
ANALYSE_ONLY = MODE in ('analyse', 'merge')
PART, NPARTS = (int(sys.argv[3]), int(sys.argv[4])) if MODE == 'run' else (0, 1)
c = S.load()
AP = S.Design(name='as proposed', law=True, sanctions=True, fpm=True, amend=True, capacity=True, party=True)
AP_nb = replace(AP, name='as proposed without bans for results', bans_results=False)
AP_nS = replace(AP, name='as proposed without performance sanctions', sanctions=False)
AP_ex = replace(AP, name='as proposed, bans executed but not anticipated', ban_threat=False)
BIG6 = [c['parties'].index(p) for p in ['PSD', 'MDB', 'PP', 'UNIAO', 'PL', 'REPUBLICANOS']]
TERM2 = [i for i, y in enumerate(S.YEARS) if y >= 2029]
EVAL = [i for i, y in enumerate(S.YEARS) if 2027 <= y <= 2035]
Y2033 = list(S.YEARS).index(2033)
CH = 40
Y = {k: [] for k in ['eff_true', 'eff_pw', 'gap_meas', 'unscored', 'bans', 'wrongful', 'fp_big6', 'theta', 'nb_ratio',
                     'ns_ratio', 'threat_gain', 'exec_effect']}
t0 = time.time()
starts = list(range(0, len(X), CH))
mine = starts[PART::NPARTS]
for i in ([] if ANALYSE_ONLY else mine):
    P = params_from_unit(X[i:i + CH])
    seed = 9000                                    # one world for every parameter vector (common shocks)
    o0 = S.simulate(c, P, S.Design(), seed, common_shocks=True)
    o1 = S.simulate(c, P, AP, seed, common_shocks=True)
    eff_of = lambda des: (S.simulate(c, P, des, seed, common_shocks=True)['q'] - o0['q'])[TERM2].mean(0).mean(1)
    e1 = (o1['q'] - o0['q'])[TERM2].mean(0).mean(1)
    e_nb, e_ns, e_ex = eff_of(AP_nb), eff_of(AP_nS), eff_of(AP_ex)
    den = np.where(np.abs(e1) > 1e-6, e1, np.nan)
    Y['eff_true'].append(e1)
    Y['eff_pw'].append((o1['qpw'] - o0['qpw'])[TERM2].mean(0).mean(1))
    Y['gap_meas'].append((o1['y'] - o0['y'])[TERM2].mean(0).mean(1) - e1)
    Y['unscored'].append(o1['U'][-1] - o0['U'][-1])
    bans = o1['stage3'][TERM2].sum(0)
    Y['bans'].append(bans / 2 * 100)
    Y['wrongful'].append(np.where(bans > 0, o1['stage3_wrong'][TERM2].sum(0) / np.maximum(bans, 1e-12), 0))
    Y['fp_big6'].append(o1['fp'][-1][:, BIG6].sum(1))
    Y['theta'].append(o1['thetapw'][Y2033] - o0['thetapw'][Y2033])
    Y['nb_ratio'].append(e_nb / den)
    Y['ns_ratio'].append(e_ns / den)
    Y['threat_gain'].append(e1 - e_ex)
    Y['exec_effect'].append(e_ex - e_nb)
    print(f'{i + CH}/{len(X)} {time.time() - t0:.0f}s', flush=True)
if MODE == 'run':
    np.savez_compressed(OUT + f'/sobol_runs_part{PART}.npz', starts=np.array(mine), **{k: np.concatenate(v) for k, v in Y.items()})
    print('part saved %.0fs' % (time.time() - t0)); sys.exit(0)
if MODE == 'merge':                                # reassemble the parts in the order of the Saltelli sample
    npart = int(sys.argv[3])
    pieces = {}
    for pp in range(npart):
        Z = np.load(OUT + f'/sobol_runs_part{pp}.npz')
        for j, st_ in enumerate(Z['starts']):
            n_ = min(CH, len(X) - st_)
            pieces[int(st_)] = {k: Z[k][j * CH: j * CH + n_] for k in Y}
    Y = {k: np.concatenate([pieces[s_][k] for s_ in sorted(pieces)]) for k in Y}
    np.savez_compressed(OUT + '/sobol_runs.npz', X=X, **Y)
elif ANALYSE_ONLY:
    Z = np.load(OUT + '/sobol_runs.npz'); Y = {k: Z[k] for k in Y}
else:
    Y = {k: np.concatenate(v) for k, v in Y.items()}
    np.savez_compressed(OUT + '/sobol_runs.npz', X=X, **Y)
rows = []
for k, v in Y.items():
    vv = np.nan_to_num(v, nan=np.nanmedian(v))
    Si = sobol_analyze.analyze(problem, vv, calc_second_order=False, print_to_console=False, seed=3)
    gnames = list(dict.fromkeys(problem['groups']))
    for g, s1, st, stc in zip(gnames, Si['S1'], Si['ST'], Si['ST_conf']):
        rows.append(dict(output=k, group=g, S1=s1, ST=st, ST_conf=stc, mean=float(np.mean(vv)), var=float(np.var(vv))))
pd.DataFrame(rows).to_csv(OUT + '/sobol.csv', index=False)
print('done %.0fs' % (time.time() - t0))
