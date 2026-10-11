"""
13_numbers.py -- collects every number quoted in the article into output/numbers.json (the article's JS reads it).
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json, math, itertools
import numpy as np
import pandas as pd
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

OUT = _ROOT + '/output'
M = np.load(OUT + '/designs_metrics.npz')
c = S.load()
parties = c['parties']
keys = sorted({k.split('__')[0] for k in M.files})
g = lambda key, mk: M[f'{key}__{mk}']


def q3(a):
    a = np.asarray(a, float)
    return dict(med=float(np.nanmedian(a)), p5=float(np.nanpercentile(a, 5)), p95=float(np.nanpercentile(a, 95)),
                mean=float(np.nanmean(a)))


PILL = ['S', 'F', 'A', 'C', 'P']


def shapley(fn):
    n = 5; phi = {p: 0.0 for p in PILL}
    for j, pj in enumerate(PILL):
        others = [i for i in range(n) if i != j]
        for k in range(n):
            for T in itertools.combinations(others, k):
                w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                b0 = [1 if i in T else 0 for i in range(n)]; b1 = b0.copy(); b1[j] = 1
                phi[pj] = phi[pj] + w * (fn('F' + ''.join(map(str, b1))) - fn('F' + ''.join(map(str, b0))))
    return phi


N = {'designs': {}}
scal = ['eff_comp', 'effpw_comp', 'meas_comp', 'U_2036', 'flag', 'tutelage', 'flag_wrong', 'red_wrong', 'red_true_hit',
        'bans_per100_term', 'bans_ni_per100_term', 'wrongful', 'place_driven', 'money_corr', 'money_losers', 'em_lost',
        'comm_final', 'comm_cost_bn', 'cap_2036', 'theta_2033', 'thetapw_2033', 'turnover', 'incumb_win', 'incumb_run', 'reelect_elig', 'fp_big6',
        'fp_left', 'fp_hhi', 'mayors_big6', 'disc_2036', 'vul_2036', 'pts_corr', 'ever_tut', 'ever_ban', 'ban_theta_neg', 'ban_theta_mean']
for k in keys:
    dd = {}
    for mk in scal:
        if f'{k}__{mk}' in M.files:
            dd[mk] = q3(g(k, mk))
    for mk in ['eff_K', 'meas_K', 'effpw_K', 'eff_K_2036']:
        dd[mk] = {kn: q3(g(k, mk)[:, i]) for i, kn in enumerate(S.KN)}
    dd['cosmetic_share_K'] = {kn: q3(1 - g(k, 'eff_K')[:, i] / np.where(np.abs(g(k, 'meas_K')[:, i]) > 1e-6, g(k, 'meas_K')[:, i], np.nan)) for i, kn in enumerate(S.KN)}
    dd['cosmetic_gap'] = q3(g(k, 'meas_comp') - g(k, 'eff_comp'))   # median of the per-draw gap (as in Tables 10 and 13)
    for mk, labs in [('eff_reg', S.REGS), ('eff_cls', ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']),
                     ('eff_capq', ['q1', 'q2', 'q3', 'q4', 'q5']), ('bans_reg_per100', S.REGS),
                     ('bans_cls_per100', ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']),
                     ('wrong_cls', ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']),
                     ('tut_reg', S.REGS), ('tut_cls', ['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k']),
                     ('money_reg', S.REGS), ('money_gdpq', ['q1', 'q2', 'q3', 'q4', 'q5'])]:
        v = g(k, mk)
        dd[mk] = {l: q3(v[:, i]) for i, l in enumerate(labs)}
    if f'{k}__ban_k_share_grp' in M.files:
        bk = g(k, 'ban_k_share_grp')
        dd['ban_k_share_grp'] = {gname: {kn: q3(bk[:, gi, i]) for i, kn in enumerate(S.KN)} for gi, gname in enumerate(['small', 'medium', 'large'])}
    fp = g(k, 'fp_2036'); fe = g(k, 'fe_2036'); my = g(k, 'mayors_pop_2036')
    dd['fp_2036'] = {p: q3(100 * fp[:, i]) for i, p in enumerate(parties) if np.nanmedian(fp[:, i]) > 0.002 or p == 'MISSAO'}
    dd['mayors_pop_2036'] = {p: q3(100 * my[:, i]) for i, p in enumerate(parties) if np.nanmedian(my[:, i]) > 0.002}
    mi = g(k, 'fp_missao')
    dd['fp_missao_path'] = {int(y): q3(100 * mi[t]) for t, y in enumerate(S.YEARS)}
    dd['fp_missao_avg'] = q3(100 * mi[[t for t, y in enumerate(S.YEARS) if 2027 <= y <= 2036]].mean(0))
    mm = g(k, 'mayors_missao')
    dd['mayors_missao_path'] = {int(y): q3(100 * mm[t]) for t, y in enumerate(S.YEARS)}
    N['designs'][k] = dd
# v5: tutelage applied. The scorecard classifies municipalities for tutelage whenever the law is on; the consequences of
# tutelage (co-signature, supervision, extra support, slower execution) and the bans follow only where performance
# sanctions are switched on and mayors respond (not in the placebo)
SANC = lambda k: (k.startswith('F1') or k.startswith('AP_') or k.startswith('S_') or k.startswith('V_')) and k not in ('W0', 'WP')
for k in keys:
    if f'{k}__tutelage' in M.files:
        N['designs'][k]['sanctions_on'] = bool(SANC(k))
        N['designs'][k]['tutelage_applied'] = q3(g(k, 'tutelage') * (1.0 if SANC(k) else 0.0))
# differences against the status quo (paired)
for k in keys:
    dd = N['designs'][k]
    for mk in ['theta_2033', 'thetapw_2033', 'turnover', 'incumb_win', 'incumb_run', 'reelect_elig', 'fp_big6', 'fp_left', 'fp_hhi', 'mayors_big6', 'disc_2036', 'cap_2036']:
        if f'{k}__{mk}' in M.files:
            dd[mk + '_vs_W0'] = q3(g(k, mk) - g('W0', mk))
# Shapley decompositions
fns = {'eff_comp': lambda k: g(k, 'eff_comp'), 'effpw_comp': lambda k: g(k, 'effpw_comp'),
       'cosmetic': lambda k: g(k, 'meas_comp') - g(k, 'eff_comp'), 'unscored': lambda k: g(k, 'U_2036'),
       'bans': lambda k: g(k, 'bans_per100_term'), 'wrong_bans': lambda k: g(k, 'bans_per100_term') * np.nan_to_num(g(k, 'wrongful')),
       'tutelage': lambda k: g(k, 'tutelage'), 'fp_big6': lambda k: 100 * g(k, 'fp_big6'), 'incumb_win': lambda k: 100 * g(k, 'incumb_win'),
       'theta': lambda k: g(k, 'theta_2033'), 'thetapw': lambda k: g(k, 'thetapw_2033'), 'turnover': lambda k: 100 * g(k, 'turnover'), 'disc': lambda k: g(k, 'disc_2036')}
for i, kn in enumerate(S.KN):
    fns[f'eff_{kn}'] = (lambda ii: (lambda k: g(k, 'eff_K')[:, ii]))(i)
N['shapley'] = {}
for name, fn in fns.items():
    ph = shapley(fn)
    N['shapley'][name] = {p: q3(ph[p]) for p in PILL}
    N['shapley'][name]['I'] = q3(fn('F00000') - fn('W0'))
    N['shapley'][name]['total'] = q3(fn('F11111') - fn('W0'))
    tot = np.abs(np.stack([ph[p] for p in PILL])).sum(0)
    N['shapley'][name]['share_of_abs'] = {p: float(np.nanmedian(np.abs(ph[p]) / np.where(tot > 0, tot, np.nan))) for p in PILL}
# v5: the LRG as proposed against its own counterfactuals (paired ratios of the real effect, same draws and shocks)
N['counterfactuals'] = {}
for k_ in ['AP_nb', 'F01111', 'AP_th', 'AP_ex', 'F01111_nd']:
    if f'{k_}__eff_comp' in M.files:
        N['counterfactuals'][f'ratio_{k_}'] = q3(g(k_, 'eff_comp') / g('F11111', 'eff_comp'))
        N['counterfactuals'][f'ratio_pw_{k_}'] = q3(g(k_, 'effpw_comp') / g('F11111', 'effpw_comp'))
        N['counterfactuals'][f'diff_{k_}'] = q3(g('F11111', 'eff_comp') - g(k_, 'eff_comp'))
        N['counterfactuals'][f'share_draws_lower_{k_}'] = float((g(k_, 'eff_comp') < g('F11111', 'eff_comp')).mean())
if 'V_leak50__eff_comp' in M.files:
    N['leak50_ratio'] = q3(g('V_leak50', 'eff_comp') / g('F11111', 'eff_comp'))
# main effects (each instrument alone, scorecard published) and interaction
N['main_effects'] = {}
for nm_, key_ in zip(PILL, ['F10000', 'F01000', 'F00100', 'F00010', 'F00001']):
    N['main_effects'][nm_] = {o_: q3(g(key_, o_) - g('F00000', o_)) for o_ in ['eff_comp', 'effpw_comp']}
for o_ in ['eff_comp', 'effpw_comp']:
    tot_ = g('F11111', o_) - g('F00000', o_)
    sum_ = sum(g(k_, o_) - g('F00000', o_) for k_ in ['F10000', 'F01000', 'F00100', 'F00010', 'F00001'])
    N['main_effects']['sum_' + o_] = q3(sum_); N['main_effects']['joint_' + o_] = q3(tot_)
    N['main_effects']['interaction_' + o_] = q3(tot_ - sum_)
# placebo / information-only / regression to the mean
N['checks'] = dict(incumb_win_W0=q3(g('W0', 'incumb_win')), incumb_run_W0=q3(g('W0', 'incumb_run')),
                   turnover_W0=q3(g('W0', 'turnover')), reelect_elig_W0=q3(g('W0', 'reelect_elig')),
                   lit_effect_F01000=q3(g('F01000', 'eff_K')[:, 2]), lit_effect_F01010=q3(g('F01010', 'eff_K')[:, 2]),
                   lit_effect_F10000=q3(g('F10000', 'eff_K')[:, 2]), lit_effect_F11111=q3(g('F11111', 'eff_K')[:, 2]))
# real benchmarks for the checks (TSE winners 2016, 2020, 2024; see data/raw/elections)
pan = pd.read_csv(_ROOT + '/data/raw/elections/derived/prefeitos_painel_2016_2020_2024.csv')
nm = lambda s_: s_.replace(S.NORM_PARTY)
x_ = pan.dropna(subset=['partido_2020', 'partido_2024'])
el_ = pan[pan.eleito_2020_igual_eleito_2016_cpf == 0]
op_ = x_[x_.reeleito_2024_proxy == 0]; re_ = x_[x_.reeleito_2024_proxy == 1]
N['checks']['real'] = dict(
    reelect_elig_2024=float(el_.reeleito_2024_proxy.mean()),
    turnover_open_2024=float(((x_.reeleito_2024_proxy == 0) & (nm(x_.partido_2020) != nm(x_.partido_2024))).mean()),
    open_seat_same_party_2024=float((nm(op_.partido_2020) == nm(op_.partido_2024)).mean()),
    reelected_switched_2024=float((nm(re_.partido_2020) != nm(re_.partido_2024)).mean()),
    n_eligible_2024=int(len(el_)))
# ------------------------------------------------------------------ mechanisms (v3)
CH = ['eff', 'vol', 'alloc', 'ta', 'sel', 'dis', 'man']
for k in keys:
    dd = N['designs'][k]
    if f'{k}__ch_eff' in M.files:
        dd['channels'] = {ch: q3(g(k, 'ch_' + ch)) for ch in CH}
        dd['channels_pw'] = {ch: q3(g(k, 'chpw_' + ch)) for ch in CH if ch != 'man'}
        real = sum(g(k, 'ch_' + ch) for ch in CH if ch != 'man')
        dd['channels_real_sum'] = q3(real)
        dd['channel_share'] = {ch: q3(g(k, 'ch_' + ch) / np.where(np.abs(real) > 1e-6, real, np.nan)) for ch in CH if ch != 'man'}
    if f'{k}__mei' in M.files:
        me = g(k, 'mei')                                        # (R, 7, 6)
        dd['mei'] = {src: {cl: float(np.nanmedian(me[:, j, i])) for i, cl in enumerate(['<5k', '5-10k', '10-20k', '20-50k', '50-100k', '>100k'])}
                     for j, src in enumerate(['elections', 'information', 'S', 'F', 'A', 'P', 'B'])}
    if f'{k}__bonus_cost' in M.files:
        dd['bonus_cost'] = q3(g(k, 'bonus_cost'))
    if f'{k}__elig' in M.files:
        dd['elig'] = q3(g(k, 'elig'))
for ch in CH:
    fns_ch = lambda kk, ch=ch: g(kk, 'ch_' + ch)
    ph = shapley(fns_ch)
    N['shapley']['ch_' + ch] = {p: q3(ph[p]) for p in PILL}
    N['shapley']['ch_' + ch]['I'] = q3(fns_ch('F00000') - fns_ch('W0'))
    N['shapley']['ch_' + ch]['total'] = q3(fns_ch('F11111') - fns_ch('W0'))
# scenario B (personal bonus) and doses of the FPM tranche
N['bonus'] = {}
for k in ['B025', 'B05', 'B10']:
    if f'{k}__eff_comp' in M.files:
        e = g(k, 'eff_comp') - g('F00000', 'eff_comp'); cost = g(k, 'bonus_cost')
        N['bonus'][k] = dict(eff=q3(g(k, 'eff_comp')), effpw=q3(g(k, 'effpw_comp')), meas=q3(g(k, 'meas_comp')),
                             cosmetic_share=q3(1 - g(k, 'eff_comp') / np.where(np.abs(g(k, 'meas_comp')) > 1e-6, g(k, 'meas_comp'), np.nan)),
                             unscored=q3(g(k, 'U_2036')), cost_bn=q3(cost), eff_vs_scorecard=q3(e),
                             sd_per_bn=q3(e / np.where(cost > 1e-6, cost, np.nan)), lit=q3(g(k, 'eff_K')[:, 2]))
N['tranche_dose'] = {}
for tr, k in [(2.5, 'F_t025'), (5, 'F_t050'), (10, 'F01000'), (20, 'F_t200')]:
    if f'{k}__eff_comp' in M.files:
        N['tranche_dose'][str(tr)] = dict(eff=q3(g(k, 'eff_comp') - g('F00000', 'eff_comp')), effpw=q3(g(k, 'effpw_comp') - g('F00000', 'effpw_comp')),
                                          cosmetic=q3(g(k, 'meas_comp') - g(k, 'eff_comp')), losers=q3(g(k, 'money_losers')),
                                          lit=q3(g(k, 'eff_K')[:, 2] - g('F00000', 'eff_K')[:, 2]))
# cost-effectiveness of each instrument (alone, scorecard published): real effect per R$ bn of fiscal cost or of money moved
cal_ = S.Calib()
N['cost_eff'] = {}
for p_, key_, moved in [('S', 'F10000', 0.0), ('F', 'F01000', 0.10 * cal_.fpm_gross / 1e9), ('A', 'F00100', 0.7 * cal_.emendas_mun / 1e9),
                        ('C', 'F00010', None), ('P', 'F00001', 0.0), ('B', 'B05', None)]:
    base_ = 'F00000'
    e_ = g(key_, 'eff_comp') - g(base_, 'eff_comp')
    cost_ = g(key_, 'comm_cost_bn') if p_ == 'C' else (g(key_, 'bonus_cost') if p_ == 'B' else np.zeros_like(e_))
    N['cost_eff'][p_] = dict(eff=q3(e_), fiscal_cost_bn=q3(cost_), money_moved_bn=moved,
                             sd_per_bn_cost=q3(e_ / np.where(cost_ > 1e-6, cost_, np.nan)) if p_ in ('C', 'B') else None,
                             sd_per_10bn_moved=q3(10 * e_ / moved) if moved else None,
                             cosmetic=q3((g(key_, 'meas_comp') - g(key_, 'eff_comp')) - (g(base_, 'meas_comp') - g(base_, 'eff_comp'))))
# real-data files
for f in ['indicator_properties', 'measurement_validity', 'amendments', 'federalism', 'party_funds', 'chain', 'rtm',
          'incentive_estimates', 'fpm_rd', 'calibration', 'pilot_power']:
    p_ = OUT + f'/{f}.json'
    if _os.path.exists(p_):
        N[f] = json.load(open(p_))
if _os.path.exists(OUT + '/sobol.csv'):
    s = pd.read_csv(OUT + '/sobol.csv')
    N['sobol'] = {o: dict(zip(s[s.output == o].group, s[s.output == o].ST.round(6))) for o in s.output.unique()}
    N['sobol_stats'] = {o: dict(mean=float(s[s.output == o]['mean'].iloc[0]), sd=float(np.sqrt(s[s.output == o]['var'].iloc[0]))) for o in s.output.unique()}
# v4: scenario analyses (22_scenarios.py), calibration variants (19_calibrate.py) and the v3 reference
if _os.path.exists(OUT + '/scenarios.json'):
    N['scenarios'] = json.load(open(OUT + '/scenarios.json'))
N['calib_variants'] = {}
for v in ['v3', 'wide', 'noCE', 'noRD', 'noEL', 'noFPM', 'trans50', 'indep', 'cap2', 'cap8', 'lin']:
    p_ = OUT + f'/calibration_{v}.json'
    if _os.path.exists(p_):
        cv = json.load(open(p_))
        N['calib_variants'][v] = dict(ess=cv['ess'], params=cv['params'], elect_effect_learning=cv['elect_effect_learning'],
                                      fit=cv['fit'], used=cv['used'], log_evidence=cv.get('log_evidence'))
# v5: the tests of Sections 9.10-9.11 and the checks of the supplementary material (23_v5_tests.py)
if _os.path.exists(OUT + '/v5_tests.json'):
    N['v5'] = json.load(open(OUT + '/v5_tests.json'))
N['n_draws'] = int(g('W0', 'eff_comp').shape[0])
N['n_designs'] = len(keys)
N['priors'] = {k: [float(lo), float(hi)] for k, (lo, hi) in S.PRIORS.items()}
N['sd_unit'] = dict(zip(S.KN, [float(x) for x in c['sd_unit']]))
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


json.dump(clean(N), open(OUT + '/numbers.json', 'w'), indent=1, allow_nan=False)
print('saved numbers.json; draws:', N['n_draws'], '; designs:', len(keys))
