"""
23_v5_tests.py -- v5: the tests of the LRG as proposed reported in Section 9 and in the supplementary material.

 1 deterrence against execution of the ban for results: AP (threat and execution), AP_th (threat, never executed),
   AP_ex (executed, not anticipated), AP_nb (neither); the same with the sanctions alone (F10000, S_th, S_ex, S_nb);
   in the main run (400 draws) and in every scenario family (first 120 draws)
 2 intensity of the threat: the weight of a ban x0, x0.5, x1, x2, x4, x8 (AP_s*, S_s*), in alert units and in the
   salary equivalent the model's own conversion implies
 3 complementarity: the marginal effect of each instrument in each of the 16 configurations of the other four
   (the 2^5 factorial), under implementation scenarios A (main) and D (sc_iD, first 120 draws)
 4 heterogeneity by indicator: effects in natural units, Shapley decomposition by indicator, measured and cosmetic parts
 5 why the sanctions add less on top of the other instruments: the incentive the other instruments already create and
   the curvature of effort (marginal effort at that incentive relative to the sanctions alone)
 6 what would it take: the LRG's response with a more responsive effort (x1.5, x2, x3), a heavier weight of money
   (x2, x3) and a different saturation of effort (recalibrated), and what each value implies for the estimated
   responses the calibration matches (log-likelihood change, implied moments against their targets)
 7 checks: the no-sanction counterfactual (classification for tutelage and the routing of amendments), and which designs
   the v3 specification of the threat changes
Writes output/v5_tests.json.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json, math, itertools
import numpy as np
from scipy.stats import norm, chi2
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

OUT = _ROOT + '/output'
M = np.load(OUT + '/designs_metrics.npz')
c = S.load()
PILL = ['S', 'F', 'A', 'C', 'P']
KN = S.KN
SDU = np.array([float(x) for x in c['sd_unit']])
# natural units of each indicator: (label, unit, scale of one SD unit, sign convention)
NAT = {'K1': ('Formal jobs', '%', 100.0), 'K2': ('Non-public value added', 'pp of GDP', 1.0), 'K3': ('Literacy', 'pp', 1.0),
       'K4': ('Daycare and preschool', 'pp', 1.0), 'K6': ('Sewage', 'pp', 1.0), 'K7': ('Homicides (fewer)', 'per 100,000', 1.0)}


def q3(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    return dict(med=float(np.median(a)), p5=float(np.percentile(a, 5)), p95=float(np.percentile(a, 95)), mean=float(a.mean()),
                share_pos=float((a > 0).mean()))


class First:
    """An npz restricted to its first n draws (comparable with the scenario runs, which use the first 120 draws)."""
    def __init__(self, z, n):
        self.z, self.n, self.files = z, n, z.files
        self.R = z['W0__eff_comp'].shape[0]

    def __getitem__(self, k):
        a = self.z[k]
        if k.endswith(('fp_missao', 'mayors_missao', 'eff_K_y')):
            return a[:, :self.n]
        return a[:self.n] if (a.ndim >= 1 and a.shape[0] == self.R) else a


def getter(z):
    return lambda d, m: (z[f'{d}__{m}'] if f'{d}__{m}' in z.files else None)


def has(z, *ds):
    return all(f'{d}__eff_comp' in z.files for d in ds)


def shapley(fn, pill=PILL):
    n = len(pill); phi = {p: 0.0 for p in pill}
    for j, pj in enumerate(pill):
        others = [i for i in range(n) if i != j]
        for k in range(n):
            for T in itertools.combinations(others, k):
                w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                b0 = [1 if i in T else 0 for i in range(n)]; b1 = b0.copy(); b1[j] = 1
                phi[pj] = phi[pj] + w * (fn('F' + ''.join(map(str, b1))) - fn('F' + ''.join(map(str, b0))))
    return phi


OUTS = {'eff': lambda g, d: g(d, 'eff_comp'), 'effpw': lambda g, d: g(d, 'effpw_comp'),
        'meas': lambda g, d: g(d, 'meas_comp'), 'cosmetic': lambda g, d: g(d, 'meas_comp') - g(d, 'eff_comp'),
        'effort': lambda g, d: g(d, 'ch_eff'), 'sel': lambda g, d: g(d, 'ch_sel'), 'dis': lambda g, d: g(d, 'ch_dis'),
        'man': lambda g, d: g(d, 'ch_man'), 'bans': lambda g, d: g(d, 'bans_per100_term'),
        'turnover': lambda g, d: 100 * g(d, 'turnover'), 'incumb_win': lambda g, d: 100 * g(d, 'incumb_win'),
        'thetapw': lambda g, d: g(d, 'thetapw_2033'), 'lit_pp': lambda g, d: g(d, 'eff_K')[:, 2] * SDU[2]}
R = {}

# =========================================================================== 1 deterrence against execution
def threat_exec(z, full, threat, execu, none_, base=None):
    """Decomposition of the ban's contribution: deterrence (threat, no execution), execution (no deterrence), their
    interaction; levels of each design against the status quo (or against `base`)."""
    g = getter(z)
    if not has(z, full, threat, execu, none_):
        return None
    out = {'levels': {}, 'decomp': {}}
    for o, fn in OUTS.items():
        try:
            vals = {d: fn(g, d) for d in (full, threat, execu, none_)}
        except TypeError:
            continue
        if any(v is None for v in vals.values()):
            continue
        b = fn(g, base) if base else 0.0
        out['levels'][o] = {d: q3(v - b) for d, v in vals.items()}
        out['decomp'][o] = dict(
            ban_total=q3(vals[full] - vals[none_]),                   # what the ban adds, as proposed
            deterrence=q3(vals[threat] - vals[none_]),                # the threat alone (nobody is ever banned)
            execution=q3(vals[execu] - vals[none_]),                  # executing bans nobody anticipates
            interaction=q3(vals[full] - vals[threat] - vals[execu] + vals[none_]),
            deterrence_given_exec=q3(vals[full] - vals[execu]),
            execution_given_threat=q3(vals[full] - vals[threat]))
    e_full = g(full, 'eff_comp')
    out['ratio_to_full'] = {d: q3(g(d, 'eff_comp') / np.where(np.abs(e_full) > 1e-6, e_full, np.nan)) for d in (threat, execu, none_)}
    return out


R['threat_exec'] = {'main': threat_exec(M, 'F11111', 'AP_th', 'AP_ex', 'AP_nb'),
                    'sanctions_alone': threat_exec(M, 'F10000', 'S_th', 'S_ex', 'S_nb', base='F00000')}
# where the execution effect comes from: banned mayors stop responding (lame-duck mandate), selection of who replaces
# them, disruption from more changes of ruling party, and deterred entry of good candidates (through wrongful bans)
g = getter(M)
if has(M, 'F11111', 'AP_th'):
    R['threat_exec']['execution_mechanisms'] = dict(
        effort=q3(g('F11111', 'ch_eff') - g('AP_th', 'ch_eff')), selection=q3(g('F11111', 'ch_sel') - g('AP_th', 'ch_sel')),
        disruption=q3(g('F11111', 'ch_dis') - g('AP_th', 'ch_dis')), turnover_pp=q3(100 * (g('F11111', 'turnover') - g('AP_th', 'turnover'))),
        thetapw=q3(g('F11111', 'thetapw_2033') - g('AP_th', 'thetapw_2033')),
        elig_pp=q3(100 * (g('F11111', 'elig') - g('AP_th', 'elig'))),
        bans=q3(g('F11111', 'bans_per100_term')), ban_theta_neg=q3(g('F11111', 'ban_theta_neg')))
# the ladder of sanctions, paired: what the bans add to alerts and tutelage, and what alerts and tutelage add
if has(M, 'F11111', 'AP_nb', 'F01111'):
    R['threat_exec']['ladder'] = {o: dict(bans=q3(g('F11111', m) - g('AP_nb', m)), alerts_tutelage=q3(g('AP_nb', m) - g('F01111', m)),
                                          all_sanctions=q3(g('F11111', m) - g('F01111', m)))
                                  for o, m in (('eff', 'eff_comp'), ('effort', 'ch_eff'), ('effpw', 'effpw_comp'))}
fam = {}
for f in sorted(_os.listdir(OUT)):
    if f.startswith('designs_metrics_') and (f[16:].startswith('sc_') or f[16:].startswith('cv_')) and f.endswith('.npz'):
        tag = f[16:-4]
        z = np.load(OUT + '/' + f)
        if has(z, 'F11111', 'AP_th', 'AP_ex', 'AP_nb'):
            r_ = threat_exec(z, 'F11111', 'AP_th', 'AP_ex', 'AP_nb')
            fam[tag] = dict(eff=r_['decomp']['eff'], effort=r_['decomp']['effort'],
                            levels_eff=r_['levels']['eff'], ratio=r_['ratio_to_full'])
NS = 120
R['threat_exec']['mainS'] = threat_exec(First(M, NS), 'F11111', 'AP_th', 'AP_ex', 'AP_nb')
R['threat_exec']['families'] = fam

# =========================================================================== 2 intensity of the threat
POST = np.load(OUT + '/posterior_draws.npz')
S3 = POST['S3']; S2 = POST['S2']
# the model's conversion of alert units into a bonus: b salaries a year per SD of the score create an incentive of
# kappa_el * b / (v_office * BETA_REF * P_WIN_VAR) alert units (lrg2_sim.pressure); its inverse prices an alert unit
sal_per_unit = POST['v_office'] * S.BETA_REF * S.P_WIN_VAR / np.maximum(POST['kappa_el'], 1e-3)
pel0 = POST['kappa_el'] * POST['beta_perf'] / S.BETA_REF                      # electoral incentive of an eligible mayor
ints = {}
for lab, (dA, dS) in {'0': ('AP_ex', 'S_ex'), '0.5': ('AP_s05', 'S_s05'), '1': ('F11111', 'F10000'), '2': ('AP_s2', 'S_s2'),
                      '4': ('AP_s4', 'S_s4'), '8': ('AP_s8', 'S_s8')}.items():
    m_ = float(lab)
    row = dict(weight_alert=q3(m_ * S3), weight_vs_electoral=q3(m_ * S3 / np.maximum(pel0, 1e-3)),
               salary_equiv=q3(m_ * S3 * sal_per_unit))
    for nm_, d_, base_ in (('lrg', dA, None), ('alone', dS, 'F00000')):
        if f'{d_}__eff_comp' in M.files:
            b = (lambda o: g(base_, o)) if base_ else (lambda o: 0.0)
            row[nm_] = dict(eff=q3(g(d_, 'eff_comp') - b('eff_comp')), effort=q3(g(d_, 'ch_eff') - b('ch_eff')),
                            cosmetic=q3((g(d_, 'meas_comp') - g(d_, 'eff_comp')) - ((b('meas_comp') - b('eff_comp')) if base_ else 0.0)),
                            bans=q3(g(d_, 'bans_per100_term')), wrongful=q3(g(d_, 'wrongful')),
                            vs_x1=q3(g(d_, 'eff_comp') - g('F11111' if nm_ == 'lrg' else 'F10000', 'eff_comp')),
                            effort_vs_x1=q3(g(d_, 'ch_eff') - g('F11111' if nm_ == 'lrg' else 'F10000', 'ch_eff')))
    ints[lab] = row
R['intensity'] = ints
R['intensity_ref'] = dict(S3=q3(S3), S2=q3(S2), pel0=q3(pel0), sal_per_unit=q3(sal_per_unit))

# =========================================================================== 3 complementarity
def complementarity(z):
    g_ = getter(z)
    keys = ['F' + ''.join(map(str, b)) for b in itertools.product([0, 1], repeat=5)]
    if not all(f'{k}__eff_comp' in z.files for k in keys):
        return None
    out = {}
    for j, p in enumerate(PILL):
        ctx = {}
        for bits in itertools.product([0, 1], repeat=4):
            b0 = list(bits[:j]) + [0] + list(bits[j:]); b1 = b0.copy(); b1[j] = 1
            k0 = 'F' + ''.join(map(str, b0)); k1 = 'F' + ''.join(map(str, b1))
            lab = ''.join(q if bb else '-' for q, bb in zip([x for x in PILL if x != p], bits))
            ctx[lab] = dict(eff=q3(g_(k1, 'eff_comp') - g_(k0, 'eff_comp')), effort=q3(g_(k1, 'ch_eff') - g_(k0, 'ch_eff')),
                            cosmetic=q3((g_(k1, 'meas_comp') - g_(k1, 'eff_comp')) - (g_(k0, 'meas_comp') - g_(k0, 'eff_comp'))),
                            n_other=int(sum(bits)))
        # conditional averages: the instrument's marginal effect with each other instrument on and off
        cond = {}
        for q in [x for x in PILL if x != p]:
            qi = [x for x in PILL if x != p].index(q)
            on, off = [], []
            for bits in itertools.product([0, 1], repeat=4):
                b0 = list(bits[:j]) + [0] + list(bits[j:]); b1 = b0.copy(); b1[j] = 1
                d_ = g_('F' + ''.join(map(str, b1)), 'eff_comp') - g_('F' + ''.join(map(str, b0)), 'eff_comp')
                (on if bits[qi] else off).append(d_)
            on, off = np.mean(on, 0), np.mean(off, 0)
            cond[q] = dict(on=q3(on), off=q3(off), diff=q3(on - off))
        alone = [x for x in ctx if set(x) == {'-'}][0]
        allon = [x for x in ctx if '-' not in x][0]
        out[p] = dict(contexts=ctx, conditional=cond, alone=ctx[alone], last=ctx[allon])
    ph = shapley(lambda k: g_(k, 'eff_comp'))
    out['shapley'] = {p: q3(ph[p]) for p in PILL}
    out['total'] = q3(g_('F11111', 'eff_comp') - g_('W0', 'eff_comp'))
    tot = np.abs(np.stack([ph[p] for p in PILL])).sum(0)
    out['shapley_share'] = {p: float(np.nanmedian(np.abs(ph[p]) / np.where(tot > 0, tot, np.nan))) for p in PILL}
    out['scorecard'] = q3(g_('F00000', 'eff_comp') - g_('W0', 'eff_comp'))
    return out


R['complementarity'] = {'A': complementarity(M)}
if _os.path.exists(OUT + '/designs_metrics_sc_iD.npz'):
    R['complementarity']['D'] = complementarity(np.load(OUT + '/designs_metrics_sc_iD.npz'))
    R['complementarity']['A120'] = complementarity(First(M, NS))

# =========================================================================== 4 heterogeneity by indicator
het = {}
for i, kn in enumerate(KN):
    lab, unit, sc = NAT[kn]
    u = SDU[i] * sc
    e = g('F11111', 'eff_K')[:, i]; m_ = g('F11111', 'meas_K')[:, i]
    ph = shapley(lambda k, i=i: g(k, 'eff_K')[:, i])
    het[kn] = dict(label=lab, unit=unit, sd_unit=float(SDU[i]), eff_sd=q3(e), eff_nat=q3(e * u), meas_nat=q3(m_ * u),
                   cosmetic_nat=q3((m_ - e) * u), cosmetic_share=q3(1 - e / np.where(np.abs(m_) > 1e-6, m_, np.nan)),
                   shapley_sd={p: q3(ph[p]) for p in PILL}, scorecard_sd=q3(g('F00000', 'eff_K')[:, i] - g('W0', 'eff_K')[:, i]),
                   alone_sd={p: q3(g(k, 'eff_K')[:, i] - g('F00000', 'eff_K')[:, i]) for p, k in zip(PILL, ['F10000', 'F01000', 'F00100', 'F00010', 'F00001'])},
                   no_bans_nat=q3(g('AP_nb', 'eff_K')[:, i] * u), no_sanctions_nat=q3(g('F01111', 'eff_K')[:, i] * u))
R['by_indicator'] = het
IP = json.load(open(OUT + '/indicator_properties.json'))
R['attribution'] = {k: {kk: IP[k].get(kk) for kk in ('share_persistent', 'share_term', 'share_noise', 'sd_within_state')
                        if isinstance(IP[k], dict) and kk in IP[k]} for k in IP}

# =========================================================================== 5 why sanctions add less on top of the others
me = {d: g(d, 'mei') for d in ('F11111', 'F10000', 'F01111') if f'{d}__mei' in M.files}   # (R, 7, 6): sources x size classes
if me:
    w_cls = np.bincount(c['cls'], minlength=6) / c['N']
    inc = lambda d, js: (me[d][:, js, :].sum(1) * w_cls[None]).sum(1)           # municipal-average incentive, alert units
    I_el = inc('F11111', [0, 1])                        # elections and published score (same in every design with the law)
    I_S = inc('F11111', [2]); I_oth = inc('F11111', [3, 4, 5])
    f_ = lambda I, cap=4.0: I / (1 + I / cap)
    gain_alone = f_(I_el + I_S) - f_(I_el); gain_last = f_(I_el + I_oth + I_S) - f_(I_el + I_oth)
    R['saturation'] = dict(I_elect=q3(I_el), I_sanctions=q3(I_S), I_others=q3(I_oth),
                           effort_gain_alone=q3(gain_alone), effort_gain_last=q3(gain_last),
                           ratio_last_to_alone=q3(gain_last / np.where(gain_alone > 1e-9, gain_alone, np.nan)))
    if has(M, 'F10000', 'F00000', 'F01111'):
        alone = g('F10000', 'eff_comp') - g('F00000', 'eff_comp'); last = g('F11111', 'eff_comp') - g('F01111', 'eff_comp')
        ealone = g('F10000', 'ch_eff') - g('F00000', 'ch_eff'); elast = g('F11111', 'ch_eff') - g('F01111', 'ch_eff')
        R['saturation'].update(eff_alone=q3(alone), eff_last=q3(last), effort_alone=q3(ealone), effort_last=q3(elast),
                               ratio_eff=q3(last / np.where(np.abs(alone) > 1e-6, alone, np.nan)),
                               ratio_effort=q3(elast / np.where(np.abs(ealone) > 1e-6, ealone, np.nan)),
                               cosmetic_alone=q3((g('F10000', 'meas_comp') - g('F10000', 'eff_comp')) - (g('F00000', 'meas_comp') - g('F00000', 'eff_comp'))),
                               cosmetic_last=q3((g('F11111', 'meas_comp') - g('F11111', 'eff_comp')) - (g('F01111', 'meas_comp') - g('F01111', 'eff_comp'))),
                               shapley=q3(shapley(lambda k: g(k, 'eff_comp'))['S']))

# =========================================================================== 6 what would it take
CALJ = json.load(open(OUT + '/calibration.json'))
IE = json.load(open(OUT + '/incentive_estimates.json'))
FR = json.load(open(OUT + '/fpm_rd.json'))
rd = {r['var']: r for r in [x for x in IE['rd_open'] if x['design'] == 'incumbent ran, pre-trend adjusted']}
rdo = {r['var']: r for r in IE['rd_open'] if r['design'] == 'open seat, party, pre-trend adjusted'}
dec = {r['var']: r for r in IE['decomposition'] if r['version'] == 'adjusted'}
EXT = 0.02
cap_e = lambda m: float(np.mean(S.norm.cdf(c['cap_index'][m] / np.sqrt(1.25))))
capCE = cap_e(c['uf'] == 'CE'); capNAT = cap_e(np.ones(c['N'], bool))
W_DIS = {'day_21': ('K4', 4, 0.5), 'ideb_21': ('K3', 3, 1.0), 'jobs_21': ('K1', 4, 0.0), 'sew_21': ('K6', 2, 0.0), 'va_21': ('K2', 1, 0.0)}
M3V = IE['corr_vars']
FRr = {r['var']: r for r in FR['rd'] if r['kind'] == 'reduced form'}
er = [x for x in IE['electoral_returns'] if x['var'].startswith('composite')]
lw_ = np.array([1 / (x['se_pp'] / x['coef_pp'] * x['logit_per_sd']) ** 2 for x in er])
b_hat = float((np.array([x['logit_per_sd'] for x in er]) * lw_).sum() / lw_.sum()); b_se = float(np.sqrt(1 / lw_.sum()))


def posterior_nuisance(post, J):
    """The nuisance quantities of each posterior draw, recovered exactly: 19_calibrate.py draws the J prior vectors and
    the nuisance quantities from fixed seeds, and the posterior is a resample of those J vectors."""
    rng = np.random.default_rng(20261009)
    Pp = {k: rng.uniform(lo, hi, J) for k, (lo, hi) in S.PRIORS.items()}
    T_CE = rng.uniform(0.045, 0.070, J); CONV = rng.uniform(1.5, 3.0, J); _ = rng.uniform(0.75, 0.95, J)
    U_PC = np.random.default_rng(20261010).uniform(0.0, 1.0, J)
    pos = {v: i for i, v in enumerate(Pp['S2'])}
    idx = np.array([pos[v] for v in post['S2']])
    assert all(np.array_equal(Pp[k][idx], post[k]) for k in S.PNAMES), 'posterior draws not found among the prior draws'
    return dict(T_CE=T_CE[idx][:, None], CONV=CONV[idx][:, None], U_PC=U_PC[idx][:, None])


def moments(P, cap=4.0, nuis=None):
    """The calibration moments of 19_calibrate.py (main variant) for parameter draws P, with the nuisance quantities of
    each draw. Returns {block: (list of model arrays (n, 1), targets, ses, corr)}."""
    col = lambda k: np.asarray(P[k], float)[:, None]
    T_CE, CONV, U_PC = nuis['T_CE'], nuis['CONV'], nuis['U_PC']
    f = lambda p: p / (1 + p / cap)
    pel = col('kappa_el') * col('beta_perf') / S.BETA_REF
    pce = col('kappa_money') * (T_CE / 0.10) * 6.0
    S_EL = 0.60
    de = col('delta_K3') * (S_EL * (f(pel + pce) - f(pel)) + (1 - S_EL) * f(pce))
    rho = col('rhoA')
    m1 = de * (1 - col('cap_slope') * (1 - capCE)) * ((1 - rho) + (1 - rho ** 3)) / 2 / CONV
    gap = 1 - capCE
    capm_ta = 1 - col('cap_slope') * (1 - (capCE + gap * col('chi_comm')))
    m2 = (de * capm_ta * (1 - rho ** 7) + col('beta_TA') * gap * (1 - 0.95 ** 7) / 0.05) / CONV
    capm_n = 1 - col('cap_slope') * (1 - capNAT)
    m3, m3o = {}, {}
    for v, (k, t, w) in W_DIS.items():
        e_el = col('delta_' + k) * f(pel) * capm_n
        m3[v] = -e_el * (1 - rho ** t) + col('tau_turn') * w * col('rho_dis') ** t + U_PC * dec[v]['pmax']
        m3o[v] = col('tau_turn') * w * col('rho_dis') ** t
    m5_day = 0.25 * (1 - col('w_gen')) * 100 / col('cost_slot') / 0.075 * 100 / 12.2
    m5_jobs = np.log1p(100 * 100 / col('cost_job') / 10.0) / 0.89
    return {
        'CE': ([m1, m2], [0.06, 0.42], [np.hypot(0.035, 0.02), np.hypot(0.06, 0.15)], np.array([[1, 0.5], [0.5, 1]])),
        'RD': ([m3[v] for v in M3V], [rd[v]['coef'] for v in M3V], [np.hypot(rd[v]['se'], EXT) for v in M3V], np.array(IE['corr_rd_inc'])),
        'RDo': ([m3o[v] for v in M3V], [rdo[v]['coef'] for v in M3V], [np.hypot(rdo[v]['se'], EXT) for v in M3V], np.array(IE['corr_rd_open'])),
        'EL': ([col('beta_perf')], [b_hat], [np.hypot(b_se, 0.02)], np.eye(1)),
        'FPM': ([m5_day, m5_jobs], [FRr['day_lv']['per100rs'], FRr['jobs']['per100rs']],
                [np.hypot(FRr['day_lv']['per100rs_se'], 0.02), np.hypot(FRr['jobs']['per100rs_se'], 0.02)],
                np.array([[1, FR.get('corr_m5', 0.0)], [FR.get('corr_m5', 0.0), 1]])),
    }


def loglik(mom):
    """Joint normal log-likelihood of the moments (19_calibrate.py, main variant), averaged over the nuisance draws
    (log of the mean likelihood), per parameter draw; and the chi-square statistic of the median moments."""
    tot = 0.0; chis = 0.0; df = 0
    for b, (items, tg, se, C) in mom.items():
        sd = np.array(se); Sig = np.diag(sd) @ C @ np.diag(sd); Lc = np.linalg.cholesky(Sig)
        resid = np.stack([it - t for it, t in zip(items, tg)])           # (k, n, nk)
        zz = np.linalg.solve(Lc, resid.reshape(len(items), -1)).reshape(resid.shape)
        tot = tot + (-0.5 * (zz ** 2).sum(0) - np.log(np.diag(Lc)).sum())
    lmax = tot.max(1, keepdims=True)
    return (lmax[:, 0] + np.log(np.mean(np.exp(tot - lmax), 1)))


def chisq(mom):
    tot = 0.0; df = 0
    for b, (items, tg, se, C) in mom.items():
        sd = np.array(se); Sig = np.diag(sd) @ C @ np.diag(sd); Lc = np.linalg.cholesky(Sig)
        resid = np.stack([it[:, 0] - t for it, t in zip(items, tg)])
        tot = tot + (np.linalg.solve(Lc, resid) ** 2).sum(0); df += len(items)
    return tot, df


def implied(mom):
    out = {}
    for b, (items, tg, se, C) in mom.items():
        for j, (it, t, s_) in enumerate(zip(items, tg, se)):
            md = np.median(it, 1)
            out[f'{b}{j}'] = dict(med=float(np.median(md)), p5=float(np.percentile(md, 5)), p95=float(np.percentile(md, 95)),
                                  target=float(t), se=float(s_), z=float((np.median(md) - t) / s_))
    return out


lme = lambda a: float(a.max() + np.log(np.mean(np.exp(a - a.max()))))     # log of the mean of exp(a)
P0 = {k: POST[k] for k in S.PNAMES}
NUIS = posterior_nuisance(POST, CALJ['J'])
mom0 = moments(P0, nuis=NUIS)
ll0 = loglik(mom0)
# check the replication against the calibration's own summary (posterior medians of the fitted moments)
fitmed = [r['post_med'] for r in CALJ['fit']]
repl = implied(mom0)
R['wwt_check'] = dict(calib_post_med=fitmed, replicated_med=[v['med'] for v in repl.values()])
wwt = {}
for lab, mult in [('dm1', {}), ('dm15', {'delta': 1.5}), ('dm2', {'delta': 2.0}), ('dm3', {'delta': 3.0}),
                  ('km2', {'kappa_money': 2.0}), ('km3', {'kappa_money': 3.0})]:
    P_ = dict(P0)
    for k_, f_ in mult.items():
        if k_ == 'delta':
            for kk in [x for x in S.PNAMES if x.startswith('delta_')]:
                P_[kk] = P0[kk] * f_
        else:
            P_[k_] = P0[k_] * f_
    mo = moments(P_, nuis=NUIS)
    ll = loglik(mo)
    imp = implied(mo)
    ch, df = chisq(mo)
    row = dict(dloglik=q3(ll - ll0), mean_dloglik=float(np.mean(ll - ll0)),
               inside95=float((ch < chi2.ppf(0.95, df)).mean()), chisq_med=float(np.median(ch)), df=df,
               # likelihood ratio of the whole posterior: mean over draws of L_m / mean of L_1
               lr_posterior=float(np.exp(lme(ll) - lme(ll0))),        # mean likelihood over the posterior draws, relative to x1
               M1=imp['CE0'], M2=imp['CE1'], RD_ideb=imp['RD1'], RD_day=imp['RD0'], RD_jobs=imp['RD2'])
    sc = OUT + f'/designs_metrics_sc_{lab}.npz'
    if lab == 'dm1':
        z = First(M, NS)
    else:
        z = np.load(sc) if _os.path.exists(sc) else None
    if z is not None and has(z, 'F11111'):
        gz = getter(z)
        row['lrg'] = dict(eff=q3(gz('F11111', 'eff_comp')), effort=q3(gz('F11111', 'ch_eff')),
                          cosmetic=q3(gz('F11111', 'meas_comp') - gz('F11111', 'eff_comp')),
                          sanctions_last=q3(gz('F11111', 'eff_comp') - gz('F01111', 'eff_comp')) if has(z, 'F01111') else None,
                          ban_total=q3(gz('F11111', 'eff_comp') - gz('AP_nb', 'eff_comp')) if has(z, 'AP_nb') else None,
                          sanctions_alone=q3(gz('F10000', 'eff_comp')) if has(z, 'F10000') else None,
                          fpm_alone=q3(gz('F01000', 'eff_comp')) if has(z, 'F01000') else None,
                          effort_share=q3(gz('F11111', 'ch_eff') / np.where(np.abs(gz('F11111', 'eff_comp')) > 1e-6, gz('F11111', 'eff_comp'), np.nan)))
    wwt[lab] = row
R['what_would_it_take'] = wwt
# saturation of effort, each variant recalibrated: evidence and the LRG's response
sat = {}
for v, cap in [('main', 4.0), ('cap2', 2.0), ('cap8', 8.0), ('lin', None)]:
    cj = CALJ if v == 'main' else json.load(open(OUT + f'/calibration_{v}.json'))
    row = dict(cap=cap, ess=cj['ess'], log_evidence=cj.get('log_evidence'),
               delta_K3=cj['params']['delta_K3'], delta_K4=cj['params']['delta_K4'], kappa_money=cj['params']['kappa_money'])
    z = (First(M, NS) if v == 'main'
         else (np.load(OUT + f'/designs_metrics_cv_{v}.npz') if _os.path.exists(OUT + f'/designs_metrics_cv_{v}.npz') else None))
    if z is not None and has(z, 'F11111'):
        gz = getter(z)
        row['lrg'] = dict(eff=q3(gz('F11111', 'eff_comp')), effort=q3(gz('F11111', 'ch_eff')),
                          sanctions_last=q3(gz('F11111', 'eff_comp') - gz('F01111', 'eff_comp')) if has(z, 'F01111') else None,
                          sanctions_alone=q3(gz('F10000', 'eff_comp') - gz('F00000', 'eff_comp')) if has(z, 'F10000', 'F00000') else None,
                          ban_total=q3(gz('F11111', 'eff_comp') - gz('AP_nb', 'eff_comp')) if has(z, 'AP_nb') else None,
                          deterrence=q3(gz('AP_th', 'eff_comp') - gz('AP_nb', 'eff_comp')) if has(z, 'AP_th', 'AP_nb') else None,
                          execution=q3(gz('AP_ex', 'eff_comp') - gz('AP_nb', 'eff_comp')) if has(z, 'AP_ex', 'AP_nb') else None)
    sat[v] = row
if sat.get('main', {}).get('log_evidence') is None:
    # the main calibration predates v5: its log evidence is recomputed by the same code in a scratch root (identical draws)
    sp = _os.environ.get('LRG_MAIN_CALIB')
    if sp and _os.path.exists(sp):
        sat['main']['log_evidence'] = json.load(open(sp)).get('log_evidence')
R['saturation_variants'] = sat

# =========================================================================== 7 checks
chk = {}
if has(M, 'F01111', 'F01111_nd'):
    chk['no_sanction'] = dict(eff_diff=q3(g('F01111_nd', 'eff_comp') - g('F01111', 'eff_comp')),
                              classified_F01111=q3(100 * g('F01111', 'tutelage')), classified_F11111=q3(100 * g('F11111', 'tutelage')),
                              ever_classified_F01111=q3(100 * g('F01111', 'ever_tut')))
for tag in ('chk5base', 'chk5v3'):
    p_ = OUT + f'/designs_metrics_{tag}.npz'
    if _os.path.exists(p_):
        a = np.load(p_); V4 = np.load(OUT + '/designs_metrics_v4full.npz')
        res = {}
        for d in sorted({k.split('__')[0] for k in a.files}):
            n_, nd_ = 0, 0
            for k in [x for x in a.files if x.split('__')[0] == d]:
                if k not in V4.files:
                    continue
                b = V4[k][:, :40] if k.endswith(('fp_missao', 'mayors_missao', 'eff_K_y')) else V4[k][:40]
                n_ += 1; nd_ += int(not np.array_equal(np.nan_to_num(a[k], nan=-9), np.nan_to_num(b, nan=-9)))
            e_ = a[f'{d}__eff_comp']; e4 = V4[f'{d}__eff_comp'][:40] if f'{d}__eff_comp' in V4.files else None
            res[d] = dict(arrays=n_, differing=nd_, eff_med=float(np.median(e_)),
                          eff_med_v4=float(np.median(e4)) if e4 is not None else None,
                          max_abs_diff=float(np.max(np.abs(e_ - e4))) if e4 is not None else None)
        chk[tag] = res
R['checks'] = chk


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


json.dump(clean(R), open(OUT + '/v5_tests.json', 'w'), indent=1, allow_nan=False)
te = R['threat_exec']['main']
if te:
    d_ = te['decomp']['eff']
    print('ban total %+.4f  deterrence %+.4f  execution %+.4f  interaction %+.4f' % tuple(d_[k]['med'] for k in ('ban_total', 'deterrence', 'execution', 'interaction')))
print('saved v5_tests.json')
