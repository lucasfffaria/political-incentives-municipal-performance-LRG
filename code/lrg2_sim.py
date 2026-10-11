"""
lrg2_sim.py -- national microsimulation of the Lei de Responsabilidade Gerencial (LRG) as a system:
measurement (scorecard, colour bands), sanctions (tutelage, ineligibility), money (performance tranche of the
FPM, conditional amendments), capacity (federal commissioners), party funds (Fundo Partidario / FEFC by mayors'
points), selection (elections, party switching, candidate pools) and clientelism (incumbent advantage fuelled
by discretionary money and household vulnerability).

Units: 5,570 real municipalities; data years 2025-2036 (terms 2025-28, 2029-32, 2033-36; municipal elections
in October 2028, 2032, 2036). The law is approved in 2027; data year t is evaluated early in t+1.
Order within a year t: true quality q_t -> measurement y_t -> elections (October, using evaluations of data
up to t-1) -> evaluation of data year t -> money, capacity and behaviour that shape t+1.
Paired worlds share common random numbers: draws come from generators seeded by (chunk seed, year, stream)
and are taken in the same order whatever the design.

Indicators (the measurable core of the ten announced KPIs), goodness orientation via ORIENT:
  K1 log private formal jobs per 100 inhabitants (RAIS)                         publication lag 1
  K2 % of value added outside public administration (IBGE)                      lag 2
  K3 % of 2nd graders literate (INEP, Indicador Crianca Alfabetizada)            lag 1
  K4 enrolments aged 0-5 per 100 children (School Census)                        lag 1
  K6 % population with sewage collection (truth: Census 2022; measured: self-report) lag 1
  K7 homicides per 100,000 (SIM), Poisson counts                                 lag 1
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import norm, poisson

DER = _ROOT + '/data/derived'
OUT = _ROOT + '/output'
KN = ['K1', 'K2', 'K3', 'K4', 'K6', 'K7']
K = len(KN)
ORIENT = np.array([1, 1, 1, 1, 1, -1.0])
LAG = np.array([1, 2, 1, 1, 1, 1])
W_POINTS = np.array([0.25, 0.15, 0.15, 0.15, 0.15, 0.15])
EDU = np.array([0, 0, 1, 1, 0, 0.0])
SERV = np.array([0, 0, 1, 1, 1, 0.0])
YEARS = np.arange(2025, 2037)
ELECTIONS = (2028, 2032, 2036)
EDGES = [0, 5000, 10000, 20000, 50000, 100000, np.inf]
REGS = ['N', 'NE', 'SE', 'S', 'CO']
NORM_PARTY = {'PODE': 'PODEMOS', 'PC do B': 'PCDOB', 'UNIÃO': 'UNIAO', 'PSL': 'UNIAO', 'DEM': 'UNIAO',
              'PRB': 'REPUBLICANOS', 'PR': 'PL', 'PPS': 'CIDADANIA', 'PMDB': 'MDB', 'PATRIOTA': 'PRD', 'PTB': 'PRD',
              'PROS': 'SOLIDARIEDADE', 'PSC': 'PODEMOS', 'PHS': 'PODEMOS', 'PMN': 'MOBILIZA', 'PTC': 'AGIR',
              'PEN': 'PRD', 'PTN': 'PODEMOS', 'PSDC': 'DC', 'PRP': 'PRD', 'PPL': 'PCDOB', 'SD': 'SOLIDARIEDADE'}


@dataclass
class Calib:
    trend: tuple = (0.02, 0.15, 1.2, 1.0, 1.0, -0.4)     # per year; K3 slows to 0.5 after 2030
    fpm_gross: float = 216e9
    emendas_mun: float = 32e9
    fp_total: float = 1.229e9
    fefc_total: float = 4.96e9
    cost_commissioner: float = 0.35e6
    p_run: float = 0.82
    p_win: float = 0.81                                 # 0.82 x 0.81 = 0.666 re-elected among eligible (2024)
    switch_hazard: float = 0.15
    stay_party_open: float = 0.236
    sewer_bias_sd: float = 9.0
    vul_mean: float = 0.134
    em_share_of_discretion: float = 0.5                 # amendments in mayors' discretionary (clientelist) money


def load():
    b = pd.read_csv(DER + '/municipios_base.csv')
    props = json.load(open(OUT + '/indicator_properties.json'))
    N = len(b)
    c = {'N': N, 'cod': b.cod_ibge.values}
    c['pop'] = b.pop2024.fillna(b.pop2022).values.astype(float)
    c['uf'] = b.uf.values
    c['region'] = b.region.values
    c['reg_idx'] = np.array([REGS.index(r) for r in c['region']])
    c['capital'] = b.capital.values
    c['cls'] = np.clip(np.searchsorted(EDGES, c['pop'], side='left') - 1, 0, 5)
    c['grp'] = np.where(c['pop'] <= 20000, 0, np.where(c['pop'] <= 100000, 1, 2))
    c['gdp_pc'] = b.gdp_pc_2021.values
    c['gdp_q'] = pd.qcut(np.log(c['gdp_pc']), 5, labels=False).astype(int)
    c['higher_ed'] = b.higher_ed_share.fillna(b.higher_ed_share.median()).values
    c['bf_share'] = b.bf_share_households.clip(0, 1.2).fillna(0.3).values
    c['fpm_pc'] = (b.fpm_gross_2024.fillna(0) / c['pop']).values
    pix = b.pix_plan_2025.fillna(0).values
    em_w = pix + 0.25 * np.median(pix[pix > 0] / c['pop'][pix > 0]) * c['pop']
    c['em_share'] = em_w / em_w.sum()
    party = b.party_2024.replace(NORM_PARTY).fillna('OUTROS').values
    c['term_limited0'] = (b.reelected_2024.fillna(0).values == 1)
    c['own_tax_share'] = b.own_tax_share_2024.values
    # current revenue per inhabitant (SICONFI 2024; missing values imputed by state x size class medians)
    rpc = b.rev_current_2024 / b.pop2024
    key = b.uf.astype(str) + '_' + pd.Series(c['cls']).astype(str)
    rpc = rpc.fillna(rpc.groupby(key).transform('median')).fillna(rpc.groupby(pd.Series(c['cls'])).transform('median'))
    c['rev_pc'] = rpc.values.astype(float)
    # mayors' annual pay (subsidio x 13.33): an assumption by size class, used only for the bonus scenario
    c['salary'] = np.select([c['pop'] <= 10000, c['pop'] <= 50000, c['pop'] <= 200000], [15e3, 18e3, 22e3], 28e3) * 13.33
    # ------------------------------------------------------------------ baselines (measured)
    y = np.zeros((N, K))
    jobs = 100 * b.jobs_private_2024 / b.pop2024
    y[:, 0] = np.log(jobs.clip(0.2, 150).fillna(jobs.median()))
    y[:, 1] = b.K2_private_va_2021.values
    lit = b.K3_literacy_2024.copy()
    lit = lit.fillna(lit.groupby([b.uf, c['grp']]).transform('mean')).fillna(lit.mean())
    y[:, 2] = lit.values
    y[:, 3] = b.K4_daycare_2023.clip(5, 150).values
    y[:, 4] = 100 * b.sh_sewer_census.clip(0, 1).values
    y[:, 5] = b.hom_rate_2022.clip(0, 300).values
    c['y_obs0'] = y
    # ------------------------------------------------------------------ measurement properties
    pk = {'K1': 'K1_formal_jobs_log', 'K2': 'K2_private_va_share', 'K3': 'K3_literacy', 'K4': 'K4_daycare_coverage',
          'K6': 'K6_sewage_coverage', 'K7': 'K7_homicide_rate'}
    noise_var = np.zeros((N, K)); sig_var = np.zeros((N, K)); innov_var = np.zeros((N, K))
    term_var = np.zeros(K); rho = np.zeros(K)
    for k, kn in enumerate(KN):
        r = props[pk[kn]]
        se2 = np.array(r['se2_by_class'], dtype=float)
        if kn == 'K3':
            sig = np.full(6, r['signal_var']); sa2 = 0.3 * sig; rh = np.full(6, 0.95); sb2 = 0.014 * sig
        else:
            sig = np.array(r['sf2_by_class'], float) + np.array(r['sa2_by_class'], float) + np.array(r['sb2_by_class'], float)
            sa2 = np.array(r['sa2_by_class'], float); rh = np.array(r['rho_by_class'], float); sb2 = np.array(r['sb2_by_class'], float)
        fix = lambda v: np.where(np.isfinite(v), v, np.nanmean(v))
        se2, sig, sa2, rh, sb2 = fix(se2), fix(sig), fix(sa2), fix(rh), fix(sb2)
        noise_var[:, k] = se2[c['cls']]; sig_var[:, k] = sig[c['cls']]
        innov_var[:, k] = sa2[c['cls']] * (1 - rh[c['cls']] ** 2)
        nn = np.array(r['n_by_class'], float)
        term_var[k] = (sb2 * nn).sum() / nn.sum(); rho[k] = (rh * nn).sum() / nn.sum()
    noise_var[:, 5] = np.maximum(y[:, 5], 2.0) * 1e5 / c['pop']            # Poisson (rule-side approximation)
    c['noise_sd'] = np.sqrt(noise_var); c['sig_var'] = sig_var; c['innov_sd'] = np.sqrt(innov_var)
    c['term_sd'] = np.sqrt(term_var); c['rho'] = rho
    c['sd_unit'] = np.sqrt(sig_var.mean(0))
    g = y * ORIENT
    c['floor0'] = np.stack([np.percentile(g[c['grp'] == gg], 20, axis=0) for gg in range(3)])
    zp = (np.log(c['pop']) - np.log(c['pop']).mean()) / np.log(c['pop']).std()
    zh = (c['higher_ed'] - c['higher_ed'].mean()) / c['higher_ed'].std()
    zg = (np.log(c['gdp_pc']) - np.log(c['gdp_pc']).mean()) / np.log(c['gdp_pc']).std()
    ci = 0.4 * zp + 0.4 * zh + 0.2 * zg
    c['cap_index'] = ci / ci.std()
    c['capCE'] = float(np.mean(norm.cdf(c['cap_index'][c['uf'] == 'CE'] / np.sqrt(1.25))))   # as in 19_calibrate.py
    v = 0.4 + c['bf_share']
    c['vul0'] = np.clip(Calib().vul_mean * v / v.mean(), 0.01, 0.6)
    parties = sorted(set(party) | {'MISSAO'} | set(FP_SHARE_SQ) | set(FEFC_SQ_RAW))
    c['parties'] = parties
    c['pidx0'] = np.array([parties.index(p) for p in party])
    NP = len(parties)
    strength = np.full((5, NP), 0.5)
    for ri in range(5):
        strength[ri] += np.bincount(c['pidx0'][c['reg_idx'] == ri], minlength=NP)
    strength[:, parties.index('OUTROS')] = 0.5
    strength[:, parties.index('MISSAO')] = 1e-6
    c['party_reg_strength'] = strength / strength.sum(1, keepdims=True)
    return c


# =========================================================================== status-quo party funds (2025/2024 shares)
FP_SHARE_SQ = {'PL': 0.1706, 'PT': 0.1247, 'UNIAO': 0.0951, 'REPUBLICANOS': 0.0779, 'PSD': 0.0748, 'PP': 0.0731,
               'MDB': 0.0690, 'PSB': 0.0383, 'PDT': 0.0357, 'PODEMOS': 0.0469, 'PSDB': 0.0316, 'PSOL': 0.0338,
               'AVANTE': 0.0208, 'SOLIDARIEDADE': 0.0222, 'PRD': 0.0257, 'CIDADANIA': 0.0133, 'PCDOB': 0.0137,
               'PV': 0.0105, 'REDE': 0.0108}
FEFC_SQ_RAW = {'PL': 886.8, 'PT': 619.8, 'UNIAO': 536.5, 'PSD': 420.9, 'PP': 417.2, 'MDB': 404.6,
               'REPUBLICANOS': 343.9, 'PODEMOS': 236.6, 'PDT': 173.9, 'PSDB': 147.9, 'PSB': 147.6, 'PSOL': 126.8,
               'SOLIDARIEDADE': 88.5, 'AVANTE': 72.5, 'PRD': 71.8, 'CIDADANIA': 60.2, 'PCDOB': 55.9, 'PV': 45.2,
               'NOVO': 37.1, 'REDE': 35.9, 'AGIR': 3.4, 'MOBILIZA': 3.4, 'DC': 3.4, 'PMB': 3.4, 'PRTB': 3.4}


def sq_shares(parties, missao=0.0):
    fp = np.array([FP_SHARE_SQ.get(p, 0.0) for p in parties], float); fp /= fp.sum()
    fe = np.array([FEFC_SQ_RAW.get(p, 0.0) for p in parties], float); fe /= fe.sum()
    im = parties.index('MISSAO')
    fp = fp * (1 - missao); fp[im] = missao
    fe = fe * (1 - missao); fe[im] = missao
    return fp, fe


# =========================================================================== uncertain parameters (uniform priors)
PRIORS = {
    'delta_K1': (0.0, 0.03), 'delta_K2': (0.0, 0.03), 'delta_K3': (0.02, 2.0), 'delta_K4': (0.02, 0.30),
    'delta_K6': (0.01, 0.10), 'delta_K7': (0.0, 0.06),
    'gam_K1': (0.05, 0.35), 'gam_K2': (0.1, 0.5), 'gam_K3': (0.15, 0.5), 'gam_K4': (0.05, 0.3),
    'gam_K6': (0.2, 0.6), 'gam_K7': (0.05, 0.4),
    'S2': (1.5, 3.0), 'S3': (2.0, 6.0),
    'kappa_money': (0.2, 1.0), 'kappa_party': (0.0, 0.5),
    'rhoA': (0.50, 0.95), 'phi_comp': (0.0, 0.4), 'xi_unscored': (0.0, 0.3), 'cap_slope': (0.3, 1.0),
    'chi_comm': (0.1, 0.5), 'beta_TA': (0.0, 0.40), 'ta_other': (0.0, 0.3), 'ta_quality': (0.25, 1.0), 'tut_cap': (0.0, 0.2), 'tut_drag': (0.0, 0.02),
    'w_sq': (0.4, 0.7), 'w_lrg': (0.15, 0.35), 'w_gen': (0.3, 0.6),
    'cost_sewer': (2500, 5000), 'cost_slot': (7000, 14000), 'mu_lit': (0.2, 1.0), 'cost_job': (60000, 140000),
    'kappa_cl': (0.2, 1.0), 'eta_emp': (0.2, 1.0), 'beta_info': (0.0, 0.10),
    'rec_party': (0.0, 0.3), 'det_entry': (0.0, 0.2), 'tau_turn': (0.02, 0.50), 'rho_dis': (0.5, 0.95), 'eta_funds': (0.0, 0.3),
    'switch_pts': (0.0, 1.0),
    # added in v3: electoral accountability, career and pay incentives, selection by money (Section 7)
    'kappa_el': (0.0, 1.0), 'beta_perf': (0.0, 0.30), 'zeta_curse': (0.0, 0.10), 'sel_pay': (0.0, 0.30),
    'v_office': (2.0, 5.0),
}
BETA_REF = 0.14          # electoral return per SD of measured performance estimated for 2020-24 (Section 7.2)
P_WIN_VAR = 0.224        # p(1-p) at the re-election rate of eligible incumbents who run (0.66)
PNAMES = list(PRIORS)


def draw_params(R, rng):
    return {k: rng.uniform(lo, hi, R) for k, (lo, hi) in PRIORS.items()}


def params_from_unit(Umat):
    return {k: lo + Umat[:, j] * (hi - lo) for j, (k, (lo, hi)) in enumerate(PRIORS.items())}


@dataclass
class Design:
    name: str = 'Status quo'
    law: bool = False              # scorecard computed and published
    sanctions: bool = False        # alert -> tutelage -> ineligibility
    fpm: bool = False              # performance tranche of the FPM
    amend: bool = False            # amendments tied to approved programmes; disqualified municipalities via consortia
    composite_rule: bool = False   # redesign: bands from a shrunk composite value-added score
    capacity: bool = False         # federal commissioners
    party: bool = False            # party funds by mayors' points
    placebo: bool = False          # rules computed, nobody responds, no consequences
    tol_mult: float = 1.0
    far_sd: float = 1.0
    no_improve_rule: bool = True
    window: int = 1
    shrink: bool = False
    posterior_rule: bool = False
    stage3_exclude: tuple = ()
    points_rule: str = 'raw'       # 'raw' | 'va'
    tranche: float = 0.10
    tranche_floor: float = 1.0     # maximum loss as a share of the municipality's FPM (1 = none)
    tranche_basis: str = 'fpm'     # bonus proportional to points x own FPM ('fpm') or points x population ('pop')
    em_condition: str = 'consortium'
    em_tie: float = 0.7
    comm_mode: str = 'all'         # 'all' | 'targeted'
    comm_ramp: int = 5570          # commissioners deployed per year (as proposed: all at once)
    comm_target: int = 5570
    party_rule: str = 'points'     # 'points' | 'bands'
    party_share: float = 1.0
    missao_fp_sq: float = 0.0
    missao_open_seat: float = 0.0
    bans_results: bool = True      # False: no ban for results (red band or no improvement); flags and tutelage unchanged
    bonus: float = 0.0             # scenario B: personal bonus, in annual salaries per SD of the bonus score (0 = none)
    term_mult: float = 1.0         # sensitivity: scale of the mayor-term component (1 = estimated lower bound)
    em_leak: float = 0.0           # sensitivity: share of tied amendment money that leaks back to discretionary channels
    # ---- v4 scenario settings; the defaults reproduce v3 exactly. Each can also be passed per draw in P (overrides).
    impl_lambda: float = 0.0       # implementation complementarity: share of the potential benefit of LRG money and technical
                                   # assistance lost by an unsupervised, low-capacity administration with no incentive
                                   # (scenarios A, B, C, D = 0, 0.25, 0.5, 0.75)
    impl_jstar: float = 1.0        # incentive (alert units) that closes 63% of the implementation gap
    impl_sup: float = 1.0          # supervision (a commissioner present, or tutelage with co-signature), in alert units
    beta_mult: float = 1.0         # electoral scenarios: voters' reward for measured performance x this factor (0 = none)
    manip_scale: float = 1.0       # manipulation scenarios: manipulated share of the response x this factor
    manip_audit: float = 0.0       # independent audits remove this share of the manipulation
    manip_subst: float = 0.0       # share of the manipulation forgone (against the central case) redirected to real effort
    impl_jref: float = 1.75        # reference situation of the v3 productivity of LRG money and assistance: a mayor facing the
    impl_supref: float = 1.0       # median incentive of the LRG as proposed (alert units per indicator), supervised
    lame_rule: str = 'none'        # a mayor banned during the mandate responds to no incentive ('none', v3) or still to money,
                                   # party funds and a bonus ('money')
    threat_v3: bool = False        # True reproduces v3, where the ban's weight entered the incentive even where no ban could
                                   # follow (designs without bans for results, indicators excluded from bans)
    # ---- v5 sensitivity settings on the LRG as proposed; the defaults reproduce v4 exactly
    ban_threat: bool = True        # the threat of a ban for results enters mayors' incentives (deterrence)
    ban_execute: bool = True       # bans for results are applied (ineligibility, lame-duck mandate, deterrence of entry)
    s3_mult: float = 1.0           # intensity of the threat: weight of a ban in the mayor's objective x this factor
    eff_cap: float = 4.0           # saturation of effort, a* = delta I / (1 + I / eff_cap) (inf: linear response)
    delta_mult: float = 1.0        # responsiveness of real effort to incentives x this factor (no recalibration)
    amend_disq: bool = True        # tied amendments of municipalities classified for tutelage go through consortia
    pmult: tuple = ()              # v5: ((parameter, factor), ...) multiplies calibrated parameters (what-would-it-take runs)


def poisson_from_u(lam, u):
    out = np.empty_like(lam)
    small = lam < 30
    out[small] = poisson.ppf(u[small], lam[small])
    z = norm.ppf(np.clip(u[~small], 1e-9, 1 - 1e-9))
    out[~small] = np.maximum(np.round(lam[~small] + np.sqrt(lam[~small]) * z), 0)
    return out


def term_base_year(yr):
    return 2026 if yr <= 2028 else 2028 + 4 * ((yr - 2029) // 4)


def smoothed(d, yhist, yr):
    R, N, _ = yhist[yr].shape
    out = np.empty((R, N, K))
    for k in range(K):
        dy = yr - (LAG[k] - 1)
        out[:, :, k] = np.mean([yhist[x][:, :, k] for x in range(dy - d.window + 1, dy + 1) if x in yhist], axis=0)
    return out


def true_lagged(qhist, yr):
    R, N, _ = qhist[yr].shape
    out = np.empty((R, N, K))
    for k in range(K):
        out[:, :, k] = qhist[yr - (LAG[k] - 1)][:, :, k]
    return out


def evaluate(c, d, yhist, qhist, yr, mb_y, mb_q, yellow_prev, red_prev, stage2_prev, trend, lam=None):
    sdu = c['sd_unit']
    ym = smoothed(d, yhist, yr) * ORIENT
    qm = true_lagged(qhist, yr) * ORIENT
    nsd_eff = c['noise_sd'] / np.sqrt(d.window)
    if d.shrink:
        sig = c['sig_var']; B = sig / (sig + nsd_eff ** 2)
        gm = np.zeros_like(ym)
        for gg in range(3):
            m = c['grp'] == gg
            gm[:, m] = ym[:, m].mean(1, keepdims=True)
        ypost = gm + B[None] * (ym - gm); psd = np.sqrt((1 - B) * sig)[None]
    else:
        ypost = ym; psd = nsd_eff[None]
    fl = c['floor0'][c['grp']][None] + (trend * ORIENT)[None, None, :] * (yr - 2026)
    mb = mb_y * ORIENT; mbq = mb_q * ORIENT
    ty = yr - term_base_year(yr)
    path = np.where(mb >= fl, mb + (trend * ORIENT)[None, None, :] * ty, mb + (fl - mb) * min(ty / 4, 1))
    pathq = np.where(mbq >= fl, mbq + (trend * ORIENT)[None, None, :] * ty, mbq + (fl - mbq) * min(ty / 4, 1))
    tol = d.tol_mult * np.sqrt(2) * nsd_eff[None]
    far = fl - d.far_sd * sdu[None, None, :]
    if d.posterior_rule:
        below = norm.cdf((fl - ypost) / np.maximum(psd, 1e-9)) > 0.5
        below_c = norm.cdf((fl - ypost) / np.maximum(psd, 1e-9)) > 0.8
        off = norm.cdf((path - ypost) / np.maximum(np.sqrt(psd ** 2 + nsd_eff[None] ** 2), 1e-9)) > 0.8
        farb = norm.cdf((far - ypost) / np.maximum(psd, 1e-9)) > 0.95
    else:
        below = ym < fl; below_c = below; off = ym < path - tol; farb = ym < far
    rk = farb & off
    if d.stage3_exclude:
        rk[:, :, list(d.stage3_exclude)] = False
    red_now = rk.any(2)
    if d.composite_rule:
        # value added against the expected path, shrunk, combined across indicators (one test, not twelve)
        dlt = (ym - mb) - (trend * ORIENT)[None, None, :] * ty          # change against the national pace
        sdp = np.zeros_like(dlt)
        for gg in range(3):
            m = c['grp'] == gg
            sdp[:, m] = dlt[:, m].std(1, keepdims=True)
        z = dlt / np.maximum(sdp, 1e-9)
        Z = (z * W_POINTS).sum(2) / np.sqrt((W_POINTS ** 2).sum())
        pb = norm.cdf((fl - ypost) / np.maximum(psd, 1e-9))
        conf_below = pb > 0.9
        ctrl = np.ones(K, bool)
        if d.stage3_exclude:
            ctrl[list(d.stage3_exclude)] = False
        yellow = (Z < -0.84) | conf_below[:, :, ctrl].any(2)
        orange = yellow & ((conf_below.sum(2) >= 2) | (Z < -1.64))
        red_now = red_now & (Z < -1.64)
        stage2 = orange & yellow_prev
    else:
        yellow = below.any(2) | (off & ~below).any(2)
        orange = (below_c.sum(2) >= 2) | (below_c & off).any(2)
        stage2 = orange | (yellow & yellow_prev)
    red = red_now & red_prev
    stage3 = red & stage2_prev
    # error-free counterparts (same rule on true values, no tolerance needed beyond the rule's)
    belowt = qm < fl; offt = qm < pathq
    yellow_t = belowt.any(2) | (offt & ~belowt).any(2)
    rkt = (qm < far) & offt
    if d.stage3_exclude:
        rkt[:, :, list(d.stage3_exclude)] = False
    red_t = rkt.any(2)
    # the same reading with an average mayor in office (mayor-term component removed)
    if lam is not None:
        qa = qm - lam * ORIENT
        rka = (qa < far) & (qa < pathq)
        if d.stage3_exclude:
            rka[:, :, list(d.stage3_exclude)] = False
        red_avg = rka.any(2)
    else:
        red_avg = red_t
    if d.points_rule == 'raw':
        imp = (ym - mb) / sdu
    else:
        exp_ = mb + (trend * ORIENT)[None, None, :] * ty
        relc = c['sig_var'] / (c['sig_var'] + 2 * nsd_eff ** 2)
        imp = relc[None] * (ym - exp_) / sdu
    pts = (np.clip(imp, -2, 2) * W_POINTS).sum(2)
    pts_true = (np.clip((qm - mbq - (trend * ORIENT)[None, None, :] * ty * (d.points_rule == 'va')) / sdu, -2, 2) * W_POINTS).sum(2)
    return dict(yellow=yellow, stage2=stage2, red=red, red_now=red_now, stage3=stage3, pts=pts, pts_true=pts_true, rk=rk,
                yellow_t=yellow_t, red_t=red_t, red_avg=red_avg)


def no_improvement(c, d, yhist, qhist, yr, mb_y, mb_q, lam=None):
    ym = smoothed(d, yhist, yr) * ORIENT
    qm = true_lagged(qhist, yr) * ORIENT
    tol = d.tol_mult * np.sqrt(2) * (c['noise_sd'] / np.sqrt(d.window))[None]
    keep = [k for k in range(K) if k not in d.stage3_exclude]
    ni = ~(((ym - mb_y * ORIENT) > tol)[:, :, keep].any(2))
    ni_t = ~(((qm - mb_q * ORIENT) > 0)[:, :, keep].any(2))
    # the same test with an average mayor in office (the baseline keeps the component of the mayor in office then)
    ni_a = ni_t if lam is None else ~(((qm - lam * ORIENT - mb_q * ORIENT) > 0)[:, :, keep].any(2))
    if d.posterior_rule:
        z = (ym - mb_y * ORIENT) / (np.sqrt(2) * c['noise_sd'] / np.sqrt(d.window))[None]
        ni = ~((norm.cdf(z) > 0.05)[:, :, keep].any(2))       # ban only if confident that nothing improved
    return ni, ni_t, ni_a


def pressure(c, d, P, yr, y, stage2, inel, trend):
    """Marginal expected incentive created by each LRG instrument on each indicator (alert units).
    The electoral incentive and the information effect of the scorecard are computed in simulate()."""
    R, N, _ = y.shape
    ym = y * ORIENT
    fl = c['floor0'][c['grp']][None] + (trend * ORIENT)[None, None, :] * (yr + 1 - 2026)
    s = np.sqrt(2) * c['noise_sd'][None]
    ref = np.sqrt(2) * np.median(c['noise_sd'], axis=0)[None, None, :]
    z = (fl - (ym + (trend * ORIENT)[None, None, :])) / s
    dens = norm.pdf(z) / norm.pdf(0) * np.minimum(ref / s, 3.0)       # change in the chance of a flag per SD, relative
    comp = {}
    if d.sanctions:
        if d.threat_v3:
            comp['S'] = dens * (1 + P['S2'][:, None, None] + P['S3'][:, None, None] * (~inel)[:, :, None])
        else:                              # v4: the ban weighs only where a ban for results can follow
            bmask = np.ones(K)
            if d.stage3_exclude:
                bmask[list(d.stage3_exclude)] = 0.0
            bmask = bmask * float(d.bans_results and d.ban_threat)      # v5: deterrence can be switched off on its own
            s3 = P['S3'] if d.s3_mult == 1.0 else d.s3_mult * P['S3']   # v5: intensity of the threat
            comp['S'] = dens * (1 + P['S2'][:, None, None] + s3[:, None, None] * (~inel)[:, :, None] * bmask[None, None, :])
    if d.fpm:
        stake_f = np.clip(c['fpm_pc'] / np.median(c['fpm_pc'][c['fpm_pc'] > 0]), 0.2, 3.0)
        comp['F'] = P['kappa_money'][:, None, None] * (d.tranche / 0.10) * stake_f[None, :, None] * (W_POINTS / W_POINTS.mean())[None, None, :]
    if d.amend:
        em_pc = c['em_share'] / c['pop']
        stake_e = np.clip(em_pc / np.median(em_pc), 0.2, 3.0)
        comp['A'] = 0.5 * P['kappa_money'][:, None, None] * dens * stake_e[None, :, None]
    if d.party:
        stake = np.clip(c['pop'] / c['pop'].sum() * 1000, 0.02, 3.0)
        comp['P'] = P['kappa_party'][:, None, None] * stake[None, :, None] * d.party_share * np.ones((1, 1, K))
    if d.bonus > 0:
        # a bonus of b salaries a year per SD of the score against the electoral reward of v_office terms' pay
        # times the electoral return BETA_REF x p(1-p): the ratio of the two marginal incentives
        ratio = d.bonus / (P['v_office'] * BETA_REF * P_WIN_VAR)
        comp['B'] = (P['kappa_el'] * ratio)[:, None, None] * (W_POINTS / W_POINTS.mean())[None, None, :] * np.ones((1, N, 1))
    return comp


# =========================================================================== main simulation
def simulate(c, P, d, seed, cal=Calib(), common_shocks=False):
    if d.pmult:                                                       # v5: scaled parameters (the caller's P is untouched)
        P = dict(P)
        for nm_, fac_ in d.pmult:
            P[nm_] = P[nm_] * fac_
    R = len(P['S2']); N = c['N']; NP = len(c['parties'])
    pop = c['pop']; sdu = c['sd_unit']; nsd = c['noise_sd']; trend = np.array(cal.trend)
    beh = d.law and not d.placebo
    deltas = np.stack([P['delta_' + k] for k in KN], 1)[:, None, :]
    if d.delta_mult != 1.0:                                           # v5: what-would-it-take sensitivity
        deltas = deltas * d.delta_mult
    gams = np.stack([P['gam_' + k] for k in KN], 1)[:, None, :]
    execute = bool(d.bans_results and d.ban_execute)                  # v5: bans for results are applied
    col = lambda name: P[name][:, None]
    # ---------------------------------------------------------------- v4 scenario settings (P overrides the design)
    sc3 = lambda name: (P[name][:, None, None] if name in P else getattr(d, name))
    impl_on = ('impl_lambda' in P) or d.impl_lambda > 0
    manip_on = any(k in P for k in ('manip_scale', 'manip_audit', 'manip_subst')) or d.manip_scale != 1.0 \
        or d.manip_audit > 0 or d.manip_subst > 0
    bperf = col('beta_perf') if ('beta_mult' not in P and d.beta_mult == 1.0) else \
        col('beta_perf') * (P['beta_mult'][:, None] if 'beta_mult' in P else d.beta_mult)
    ratio_m = ratio_ta = 1.0
    if impl_on:
        lam3 = sc3('impl_lambda')
        ratio_m = np.ones((R, 1, K)); ratio_ta = np.ones((R, 1, K))

        def iota_of(J, sup, capv, th):
            # implementation quality: share of the potential benefit of LRG money and assistance that is realised
            fail = lam3 * (1 - 0.5 * capv)[:, :, None] * np.exp(-(J + d.impl_sup * sup[:, :, None]) / d.impl_jstar) \
                * np.exp(-0.25 * th)[:, :, None]
            return np.clip(1 - fail, 0.0, 1.0)
    # ---------------------------------------------------------------- initial latent state (identical across designs)
    r0 = np.random.default_rng([seed, 0, 0])
    R1 = 1 if common_shocks else R
    rep = (lambda a: np.repeat(a, R, axis=0)) if common_shocks else (lambda a: a)
    theta = rep(r0.standard_normal((R1, N)))
    lam = d.term_mult * c['term_sd'] * (np.sqrt(0.5) * theta[:, :, None] + np.sqrt(0.5) * rep(r0.standard_normal((R1, N, K))))
    rel = c['sig_var'] / (c['sig_var'] + nsd ** 2)
    gmean = np.zeros_like(c['y_obs0'])
    for gg in range(3):
        m = c['grp'] == gg
        gmean[m] = c['y_obs0'][m].mean(0)
    q0 = (gmean + rel * (c['y_obs0'] - gmean))[None] + np.sqrt(np.maximum((1 - rel) * c['sig_var'], 0))[None] * rep(r0.standard_normal((R1, N, K)))
    q0[:, :, 4] = c['y_obs0'][None, :, 4]
    drift = 0.5 * rep(r0.standard_normal((R1, N, K))) * (c['innov_sd'] / np.sqrt(np.maximum(1 - c['rho'] ** 2, 1e-3)))
    perm = q0 - drift - lam
    sewer_bias = cal.sewer_bias_sd * rep(r0.standard_normal((R1, N)))
    cap0 = norm.cdf(c['cap_index'][None] + 0.5 * rep(r0.standard_normal((R1, N))))
    pidx = np.repeat(c['pidx0'][None], R, 0)
    term_limited = np.repeat(c['term_limited0'][None], R, 0)
    # ---------------------------------------------------------------- state
    A = np.zeros((R, N, K)); Am = np.zeros((R, N, K)); Ata = np.zeros((R, N, K)); G = np.zeros((R, N, K))
    Am_v = np.zeros((R, N, K)); Am_a = np.zeros((R, N, K))           # money stocks: net transfers / tied amendments
    disc_delta = np.zeros((R, N))                                    # change in discretionary money per capita (EMA)
    TAW = np.zeros((R, 1, K)); TAW[:, 0, 2] = 1.0; TAW[:, 0, 3] = P['ta_other']; TAW[:, 0, 4] = P['ta_other']
    f_eff = lambda pp: pp / (1 + pp / d.eff_cap)                     # v5: saturation as a setting (4 in v3-v4)
    U = np.zeros((R, N)); disrupt = np.zeros((R, N, K)); cap = cap0.copy()
    commissioned = np.zeros((R, N), bool); n_comm = 0
    yellow_prev = np.zeros((R, N), bool); red_prev = np.zeros((R, N), bool); stage2_prev = np.zeros((R, N), bool)
    stage2 = np.zeros((R, N), bool); inel = np.zeros((R, N), bool); lame = np.zeros((R, N), bool)
    points = np.zeros((R, N)); pts_true = np.zeros((R, N))
    fp_sq, fe_sq = sq_shares(c['parties'], d.missao_fp_sq)
    fe_prev = np.repeat(fe_sq[None], R, 0); fe_share = fe_prev.copy()
    disc = np.ones((R, N)); vul = np.repeat(c['vul0'][None], R, 0)
    yhist, qhist = {}, {}
    mb_y = mb_q = None
    new_mayor_flag = np.zeros((R, N), bool)
    TT = len(YEARS)
    o = dict(
        q=np.zeros((TT, R, K)), qpw=np.zeros((TT, R, K)), y=np.zeros((TT, R, K)), U=np.zeros((TT, R)),
        flag=np.zeros((TT, R)), stage2=np.zeros((TT, R)), stage3=np.zeros((TT, R)), stage3_wrong=np.zeros((TT, R)),
        stage3_ni=np.zeros((TT, R)), stage3_place=np.zeros((TT, R)), flag_wrong=np.zeros((TT, R)), red=np.zeros((TT, R)), red_wrong=np.zeros((TT, R)),
        red_true=np.zeros((TT, R)), red_true_hit=np.zeros((TT, R)),
        money_reg=np.zeros((TT, R, 5)), money_gdpq=np.zeros((TT, R, 5)), money_corr_gdp=np.zeros((TT, R)),
        money_losers=np.zeros((TT, R)), em_lost=np.zeros((TT, R)),
        comm=np.zeros((TT, R)), cap=np.zeros((TT, R)), theta=np.zeros((TT, R)), thetapw=np.zeros((TT, R)), turnover=np.zeros((TT, R)),
        incumb_run=np.zeros((TT, R)), incumb_win=np.zeros((TT, R)), reelect_elig=np.zeros((TT, R)), fp=np.zeros((TT, R, NP)), fe=np.zeros((TT, R, NP)),
        mayors=np.zeros((TT, R, NP)), mayors_pop=np.zeros((TT, R, NP)), disc=np.zeros((TT, R)), vul=np.zeros((TT, R)),
        pts_corr=np.full((TT, R), np.nan), inel_reg=np.zeros((R, 5)), inel_cls=np.zeros((R, 6)),
        inel_wrong_cls=np.zeros((R, 6)), stage2_reg=np.zeros((R, 5)), stage2_cls=np.zeros((R, 6)),
        ban_k_grp=np.zeros((R, 3, K)), ban_red_grp=np.zeros((R, 3)),
        ban_n=np.zeros(R), ban_theta_neg=np.zeros(R), ban_theta_sum=np.zeros(R),
        q_reg=np.zeros((TT, R, 5)), q_cls=np.zeros((TT, R, 6)), q_capq=np.zeros((TT, R, 5)),
        ch_eff=np.zeros((TT, R)), ch_vol=np.zeros((TT, R)), ch_alloc=np.zeros((TT, R)), ch_ta=np.zeros((TT, R)),
        ch_sel=np.zeros((TT, R)), ch_dis=np.zeros((TT, R)), ch_man=np.zeros((TT, R)),
        ch_eff_pw=np.zeros((TT, R)), ch_vol_pw=np.zeros((TT, R)), ch_alloc_pw=np.zeros((TT, R)), ch_ta_pw=np.zeros((TT, R)),
        ch_sel_pw=np.zeros((TT, R)), ch_dis_pw=np.zeros((TT, R)),
        mei=np.zeros((R, 7, 6)), bonus_cost=np.zeros((TT, R)), elig=np.zeros((TT, R)),
        iota_m=np.ones((TT, R)), iota_ta=np.ones((TT, R)), ratio_m=np.ones((TT, R)), ratio_ta=np.ones((TT, R)),
    )
    muni = dict(stage2_years=np.zeros((R, N)), inel=np.zeros((R, N)), money=np.zeros((R, N)), flag_years=np.zeros((R, N)))
    capq = np.clip((cap0.mean(0) * 5).astype(int), 0, 4)
    for ti, yr in enumerate(YEARS):
        rg = np.random.default_rng([seed, int(yr), 1])
        e_noise = rep(rg.standard_normal((R1, N, K))); e_drift = rep(rg.standard_normal((R1, N, K)))
        u_run = rep(rg.random((R1, N))); u_win = rep(rg.random((R1, N))); u_party = rep(rg.random((R1, N))); u_stay = rep(rg.random((R1, N)))
        u_sw = rep(rg.random((R1, N))); u_swd = rep(rg.random((R1, N))); th_new = rep(rg.standard_normal((R1, N)))
        e_lam = rep(rg.standard_normal((R1, N, K))); u_pois = rep(rg.random((R1, N))); u_comm = rep(rg.random((R1, N)))
        # ------------------------------------------------------------ true quality q_t
        drift = c['rho'] * drift + c['innov_sd'] * e_drift
        tv = trend * (yr - 2024); tv[2] = 1.2 * min(yr - 2024, 6) + 0.5 * max(yr - 2030, 0)
        q = perm + drift + lam + tv + (A + Am + Ata) * ORIENT - disrupt * ORIENT * sdu
        q[:, :, 2] = np.clip(q[:, :, 2], 0, 100); q[:, :, 3] = np.clip(q[:, :, 3], 0, 160)
        q[:, :, 4] = np.clip(q[:, :, 4], 0, 100); q[:, :, 5] = np.maximum(q[:, :, 5], 0)
        # ------------------------------------------------------------ measurement y_t
        y = q + G * ORIENT + nsd * e_noise
        y[:, :, 4] = np.clip(q[:, :, 4] + sewer_bias + nsd[:, 4] * e_noise[:, :, 4] + G[:, :, 4], 0, 100)
        y[:, :, 5] = poisson_from_u(np.maximum(q[:, :, 5] - G[:, :, 5], 0) * pop / 1e5, u_pois) / pop * 1e5
        y[:, :, 2] = np.clip(y[:, :, 2], 0, 100)
        yhist[yr] = y; qhist[yr] = q
        if yr == 2026:
            mb_y, mb_q = y.copy(), q.copy()
        # ------------------------------------------------------------ elections (October), info up to data t-1
        new_mayor_flag[:] = False
        if yr in ELECTIONS:
            use_inel = inel & d.sanctions & beh
            elig = ~term_limited & ~use_inel
            runs = elig & (u_run < cal.p_run)
            # voters reward measured performance over the mandate (estimated return, Section 7.2) and, with the
            # law, also the published score (information effect)
            yprev = yhist.get(yr - 1, y)
            perf = (np.clip((yprev - mb_y) * ORIENT / sdu, -2, 2) * W_POINTS).sum(2)
            zperf = (perf - perf.mean(1, keepdims=True)) / (perf.std(1, keepdims=True) + 1e-9)
            info = bperf * zperf
            if beh:
                zs = (points - points.mean(1, keepdims=True)) / (points.std(1, keepdims=True) + 1e-9)
                info = info + col('beta_info') * zs
            cl = col('kappa_cl') * (vul * disc / c['vul0'].mean() - 1)
            pw = 1 / (1 + np.exp(-(np.log(cal.p_win / (1 - cal.p_win)) + cl + info)))
            wins = runs & (u_win < pw)
            o['incumb_run'][ti] = runs.mean(1); o['incumb_win'][ti] = wins.sum(1) / np.maximum(runs.sum(1), 1)
            o['reelect_elig'][ti] = wins.sum(1) / np.maximum(elig.sum(1), 1)
            new = ~wins
            ratio = (fe_share + 1e-4) / (fe_prev + 1e-4)
            st = c['party_reg_strength'][c['reg_idx']][None] * ratio[:, None, :] ** P['eta_funds'][:, None, None]
            if d.missao_open_seat > 0:
                im = c['parties'].index('MISSAO')
                st[:, :, im] = 0
                st = st / st.sum(2, keepdims=True) * (1 - d.missao_open_seat)
                st[:, :, im] = d.missao_open_seat
            st = st / st.sum(2, keepdims=True)
            drawp = np.minimum((np.cumsum(st, 2) < u_party[:, :, None]).sum(2), NP - 1)
            newp = np.where(u_stay < cal.stay_party_open, pidx, drawp)
            turn = new & (newp != pidx)
            pidx = np.where(new, newp, pidx)
            shift = np.zeros((R, N))
            if beh and d.party:
                shift += col('rec_party') * np.minimum(pop / pop.sum() * 1000, 1.0)[None] * d.party_share
            # more discretionary money attracts worse candidates (Brollo et al., 2013): shift per +10% of revenue
            shift -= col('zeta_curse') * 10 * disc_delta / c['rev_pc'][None]
            if beh and d.bonus > 0:                                  # higher expected pay attracts better candidates
                shift += col('sel_pay') * d.bonus * 0.4
            if beh and d.sanctions:
                past = o['stage3'][:ti].sum(0)
                wr = np.where(past > 0, o['stage3_wrong'][:ti].sum(0) / np.maximum(past, 1e-9), 0)
                risk = past * wr                                         # wrongful bans per mayor so far
                shift -= col('det_entry') * np.clip(risk[:, None] * 10, 0, 1)
            theta = np.where(new, th_new + shift, theta)
            lam = np.where(new[:, :, None], d.term_mult * c['term_sd'] * (np.sqrt(0.5) * theta[:, :, None] + np.sqrt(0.5) * e_lam), lam)
            term_limited = wins.copy()
            inel = np.where(new, False, inel); lame = np.where(new, False, lame)
            disrupt += col('tau_turn')[:, :, None] * turn[:, :, None] * np.array([0, 0, 1, 0.5, 0, 0])   # change of ruling party
            o['turnover'][ti] = turn.mean(1)
            new_mayor_flag = new
            fe_prev = fe_share.copy()
            reset_base = True
        else:
            reset_base = False
        # ------------------------------------------------------------ evaluation of data year t (early t+1)
        if d.law and yr >= 2027:
            ev = evaluate(c, d, yhist, qhist, yr, mb_y, mb_q, yellow_prev, red_prev, stage2_prev, trend, lam)
            stage2 = ev['stage2']
            o['flag'][ti] = ev['yellow'].mean(1); o['stage2'][ti] = stage2.mean(1)
            o['flag_wrong'][ti] = (ev['yellow'] & ~ev['yellow_t']).sum(1) / np.maximum(ev['yellow'].sum(1), 1)
            o['red'][ti] = ev['red'].mean(1); o['red_wrong'][ti] = (ev['red'] & ~ev['red_t']).sum(1) / np.maximum(ev['red'].sum(1), 1)
            o['red_true'][ti] = ev['red_t'].mean(1)
            o['red_true_hit'][ti] = (ev['red'] & ev['red_t']).sum(1) / np.maximum(ev['red_t'].sum(1), 1)
            muni['flag_years'] += ev['yellow']; muni['stage2_years'] += stage2
            for ri in range(5):
                o['stage2_reg'][:, ri] += stage2[:, c['reg_idx'] == ri].mean(1)
            for ci in range(6):
                o['stage2_cls'][:, ci] += stage2[:, c['cls'] == ci].mean(1)
            if d.sanctions:
                cand = ev['stage3'] & ~inel & ~new_mayor_flag & execute
                if yr >= 2029:                     # which indicators trigger red-band bans, by population group
                    for gg in range(3):
                        mg = c['grp'] == gg
                        o['ban_red_grp'][:, gg] += cand[:, mg].sum(1)
                        o['ban_k_grp'][:, gg, :] += (cand[:, mg][:, :, None] & ev['rk'][:, mg, :]).sum(1)
                wrong = cand & ~ev['red_t']
                place = cand & ev['red_t'] & ev['red_avg']
                if d.no_improve_rule and execute and yr in (2031, 2035):
                    ni, ni_t, ni_a = no_improvement(c, d, yhist, qhist, yr, mb_y, mb_q, lam)
                    add = ni & ~inel & ~cand & ~new_mayor_flag
                    o['stage3_ni'][ti] = add.mean(1)
                    wrong = wrong | (add & ~ni_t)
                    place = place | (add & ni_t & ni_a)
                    cand = cand | add
                o['stage3'][ti] = cand.mean(1); o['stage3_wrong'][ti] = wrong.mean(1)
                if yr >= 2029:
                    o['ban_n'] += cand.sum(1); o['ban_theta_neg'] += (cand & (theta < 0)).sum(1)
                    o['ban_theta_sum'] += (cand * theta).sum(1)
                o['stage3_place'][ti] = place.mean(1)
                ss = 1.0 if yr >= 2029 else 0.0
                for ri in range(5):
                    o['inel_reg'][:, ri] += ss * cand[:, c['reg_idx'] == ri].sum(1)
                for ci in range(6):
                    o['inel_cls'][:, ci] += ss * cand[:, c['cls'] == ci].sum(1)
                    o['inel_wrong_cls'][:, ci] += ss * wrong[:, c['cls'] == ci].sum(1)
                muni['inel'] += cand
                inel = inel | cand; lame = lame | (cand & beh)
            yellow_prev, red_prev, stage2_prev = ev['yellow'], ev['red_now'], stage2
            points, pts_true = ev['pts'], ev['pts_true']
            o['pts_corr'][ti] = np.array([np.corrcoef(points[r], pts_true[r])[0, 1] for r in range(R)])
        if reset_base:
            mb_y, mb_q = y.copy(), q.copy()
        # ------------------------------------------------------------ money for t+1
        money = np.zeros((R, N)); em_gain = np.zeros((R, N))
        if beh and (d.fpm or d.amend) and yr >= 2027:
            fpm = c['fpm_pc'][None]
            w = np.maximum(points, 0) * (pop * c['fpm_pc'] if d.tranche_basis == 'fpm' else pop)
            pool = d.tranche * (c['fpm_pc'] * pop).sum()
            bonus = pool * w / np.maximum(w.sum(1, keepdims=True), 1e-9) / pop
            net = (bonus - d.tranche * fpm) * d.fpm
            if d.fpm and d.tranche_floor < 1.0:
                capped = np.maximum(net, -d.tranche_floor * fpm)
                extra = ((capped - net) * pop).sum(1, keepdims=True)
                posm = np.maximum(capped, 0) * pop
                capped = capped - np.where(capped > 0, posm / np.maximum(posm.sum(1, keepdims=True), 1e-9) * extra / pop, 0)
                net = capped
            money = net
            em_pc = cal.emendas_mun * c['em_share'] / pop
            em_gain = em_pc[None] * d.em_tie * (1 - d.em_leak) * (col('w_sq') - col('w_lrg')) * d.amend
            disq = stage2 & (d.amend and d.amend_disq)
            if d.amend and d.em_condition == 'redirect':
                lost = em_pc[None] * disq
                pool_e = (lost * pop).sum(1, keepdims=True)
                okm = (~disq) * c['em_share'][None]
                money = money - lost * (1 - col('w_sq')) + pool_e * okm / np.maximum(okm.sum(1, keepdims=True), 1e-12) / pop * (1 - col('w_lrg'))
                o['em_lost'][ti] = pool_e[:, 0] / cal.emendas_mun
            disc = 1 - (cal.em_share_of_discretion * d.em_tie * (1 - d.em_leak) + 0.25 * disq) * d.amend
            for ri in range(5):
                o['money_reg'][ti, :, ri] = (money[:, c['reg_idx'] == ri] * pop[c['reg_idx'] == ri]).sum(1) / 1e9
            for qi in range(5):
                o['money_gdpq'][ti, :, qi] = (money[:, c['gdp_q'] == qi] * pop[c['gdp_q'] == qi]).sum(1) / 1e9
            lg = np.log(c['gdp_pc'])
            o['money_corr_gdp'][ti] = np.array([np.corrcoef(money[r], lg)[0, 1] for r in range(R)])
            o['money_losers'][ti] = (money < -1).mean(1)
        else:
            disc = np.ones((R, N))
        muni['money'] += money
        disc_now = money - (cal.emendas_mun * c['em_share'] / pop)[None] * d.em_tie * (1 - d.em_leak) * (d.amend and beh and yr >= 2027)
        disc_delta = 0.75 * disc_delta + 0.25 * disc_now
        prod_v = (1 - col('w_gen')) * money
        prod_a = em_gain
        # (the money stocks are updated below, once the implementation quality of the year is known)
        if beh and d.bonus > 0 and yr >= 2027:
            zb = (points - points.mean(1, keepdims=True)) / (points.std(1, keepdims=True) + 1e-9)
            o['bonus_cost'][ti] = (d.bonus * c['salary'][None] * np.maximum(zb, 0)).sum(1) / 1e9
        # ------------------------------------------------------------ capacity (commissioners from 2028)
        ta_flow = None
        if beh and d.capacity and yr >= 2027:
            n_new = min(d.comm_ramp, d.comm_target - n_comm)
            if n_new > 0:
                score = np.where(commissioned, -np.inf, (-cap0 if d.comm_mode == 'targeted' else u_comm))
                idx = np.argsort(-score, axis=1)[:, :n_new]
                np.put_along_axis(commissioned, idx, True, axis=1)
                n_comm += n_new
            dil = min(1.0, 1000 / max(d.comm_ramp, 1)) ** 0.3
            gap = 1 - cap0
            cap = cap0 + gap * col('chi_comm') * commissioned * dil
            ta_flow = (col('beta_TA') * col('ta_quality'))[:, :, None] * (gap * commissioned * dil)[:, :, None] * TAW * sdu
        else:
            cap = cap0.copy()
        if beh and d.sanctions:
            cap = np.where(stage2, np.minimum(cap + col('tut_cap') * (1 - cap), 1), cap)
        o['comm'][ti] = n_comm; o['cap'][ti] = cap.mean(1)
        # ------------------------------------------------------------ incentives for t+1 (equation 4 of the article, S7.2 of the Supplementary Material)
        if yr >= 2026:
            elig = ~term_limited & ~inel                                  # mayors who can run again
            o['elig'][ti] = elig.mean(1)
            pel0 = col('kappa_el') * bperf / BETA_REF * elig                   # electoral incentive (status quo)
            pel = pel0 + (col('kappa_el') * col('beta_info') / BETA_REF * elig if (beh and d.law) else 0.0)
            comp = pressure(c, d, P, yr, y, stage2, inel, trend) if beh else {}
            plrg = sum(comp.values()) if comp else 0.0
        # ------------------------------------------------------------ implementation quality of programmes (v4)
        if impl_on and yr >= 2026:
            Jk = pel[:, :, None] + (plrg if not np.isscalar(plrg) else np.zeros((1, 1, K)))
            Jk = np.where(lame[:, :, None], (plrg - comp.get('S', 0.0)) if (d.lame_rule == 'money' and comp) else 0.0, Jk)
            sup = (commissioned | (stage2 & bool(d.sanctions and beh))).astype(float)
            iota = iota_of(Jk, sup, cap, theta)                                  # (R, N, K)
            # the v3 productivity of LRG money and assistance is what they deliver to a mayor in the reference situation
            # (the median incentive of the LRG as proposed, supervised), with the same capacity and competence
            iota_ref = iota_of(np.full((1, 1, 1), d.impl_jref), np.full((R, N), d.impl_supref), cap, theta)
            ratio_m = ratio_ta = iota / np.maximum(iota_ref, 1e-6)
            wm = np.array([0, 0, 0.20, 0.25, 0.35, 0]) / 0.80                    # money uses: literacy, daycare, sewage
            o['iota_m'][ti] = (iota * wm).sum(2).mean(1)
            o['ratio_m'][ti] = (ratio_m * wm).sum(2).mean(1)
            ncm = np.maximum(commissioned.sum(1), 1)
            o['iota_ta'][ti] = np.where(commissioned.any(1), (iota[:, :, 2] * commissioned).sum(1) / ncm, 1.0)
            o['ratio_ta'][ti] = np.where(commissioned.any(1), (ratio_ta[:, :, 2] * commissioned).sum(1) / ncm, 1.0)
        # ------------------------------------------------------------ money and assistance stocks
        for Ms, pv in ((Am_v, prod_v), (Am_a, prod_a)):
            if impl_on:
                Ms[:, :, 4] += 0.35 * (pv * ratio_m[:, :, 4]) / col('cost_sewer') * 100 * (1 - q[:, :, 4] / 100)
                Ms[:, :, 3] = 0.25 * (pv * ratio_m[:, :, 3]) / col('cost_slot') / 0.075 * 100
                edu = 0.20 * (pv * ratio_m[:, :, 2])
            else:
                Ms[:, :, 4] += 0.35 * pv / col('cost_sewer') * 100 * (1 - q[:, :, 4] / 100)
                Ms[:, :, 3] = 0.25 * pv / col('cost_slot') / 0.075 * 100
                edu = 0.20 * pv
            Ms[:, :, 2] = 0.8 * Ms[:, :, 2] + np.sign(edu) * col('mu_lit') * np.log1p(np.abs(edu) / 10.0)
        # formal jobs respond to net changes in local spending (transfers), not to its reallocation between uses
        Am_v[:, :, 0] = np.log1p(np.maximum(money * 100 / col('cost_job') / np.exp(c['y_obs0'][None, :, 0]), -0.5))
        Am = Am_v + Am_a
        if ta_flow is not None:
            Ata = 0.95 * Ata + (ta_flow * ratio_ta if impl_on else ta_flow)
        # ------------------------------------------------------------ behaviour for t+1
        if yr >= 2026:
            eff = deltas * f_eff(pel[:, :, None] + plrg) * (~lame)[:, :, None]
            if d.lame_rule == 'money' and comp:                # banned mayors still respond to money, party funds, bonus
                eff = np.where(lame[:, :, None], deltas * f_eff(np.maximum(plrg - comp.get('S', 0.0), 0)), eff)
            eff0 = deltas * f_eff(pel0[:, :, None] * np.ones((1, 1, K))) * (~lame)[:, :, None]
            effl = np.maximum(eff - eff0, 0)                                   # effort induced by the LRG
            capm = 1 - col('cap_slope') * (1 - cap)
            real = np.maximum(eff * capm[:, :, None] * (1 + col('phi_comp')[:, :, None] * theta[:, :, None]), 0)
            gam = np.clip(gams * (1.5 - cap)[:, :, None], 0.02, 0.9)
            if manip_on:                       # v4 manipulation scenarios: scale, audits and substitution towards real effort
                gam_c = gam
                gam = np.clip(sc3('manip_scale') * gam_c, 0.0, 0.9)
                keep = 1 - sc3('manip_audit')
                forgone = effl * np.maximum(gam_c / (1 - gam_c) - keep * gam / (1 - gam), 0)
                real = real + sc3('manip_subst') * forgone * capm[:, :, None] * (1 + col('phi_comp')[:, :, None] * theta[:, :, None])
            rA = col('rhoA')[:, :, None]
            A = rA * A + (1 - rA) * real * sdu
            if beh and d.sanctions:
                A = A - stage2[:, :, None] * col('tut_drag')[:, :, None] * sdu * SERV * (1 - rA)
            G = effl * gam / (1 - gam) * sdu
            if manip_on:
                G = G * keep
            U = 0.9 * U - col('xi_unscored') * effl.mean(2) / np.maximum(deltas.mean(2), 1e-9) * 0.05
            if yr == 2030:
                parts = [pel0, pel - pel0] + [comp[k].mean(2) if k in comp else np.zeros((R, N)) for k in ('S', 'F', 'A', 'P', 'B')]
                for j, pj in enumerate(parts):
                    pj = np.broadcast_to(pj, (R, N))
                    for ci in range(6):
                        o['mei'][:, j, ci] = pj[:, c['cls'] == ci].mean(1)
        # ------------------------------------------------------------ clientelism and party switching
        jr = np.exp(q[:, :, 0] - c['y_obs0'][None, :, 0] - trend[0] * (yr - 2024))
        vul = np.clip(c['vul0'][None] * jr ** (-col('eta_emp')), 0.005, 0.8)
        haz = cal.switch_hazard * (1 + col('switch_pts') * np.maximum(points, 0) * (beh and d.party))
        sw = u_sw < np.clip(haz, 0, 0.9)
        cnt = np.stack([np.bincount(pidx[r], minlength=NP) for r in range(R)]).astype(float)
        cnt[:, c['parties'].index('OUTROS')] = 0
        cnt = cnt * ((fe_share + 1e-4) / (fe_sq[None] + 1e-4)) ** col('eta_funds')
        cum = np.cumsum(cnt / cnt.sum(1, keepdims=True), 1)
        dest = np.minimum((cum[:, None, :] < u_swd[:, :, None]).sum(2), NP - 1)
        pidx = np.where(sw, dest, pidx)
        # ------------------------------------------------------------ party funds
        fp_share = np.repeat(fp_sq[None], R, 0); fe_share = np.repeat(fe_sq[None], R, 0)
        if beh and d.party and yr >= 2027:
            if d.party_rule == 'points':
                wt = np.maximum(points, 0) * pop
            else:
                wt = np.where(red_prev, 0.0, np.where(stage2, 0.2, np.where(yellow_prev, 0.5, 1.0))) * pop
            lrg = np.stack([np.bincount(pidx[r], weights=wt[r], minlength=NP) for r in range(R)])
            lrg = lrg / np.maximum(lrg.sum(1, keepdims=True), 1e-12)
            fp_share = (1 - d.party_share) * fp_sq[None] + d.party_share * lrg
            fe_share = (1 - 0.5 * d.party_share) * fe_sq[None] + 0.5 * d.party_share * lrg
        o['fp'][ti] = fp_share; o['fe'][ti] = fe_share
        o['mayors'][ti] = np.stack([np.bincount(pidx[r], minlength=NP) for r in range(R)]) / N
        o['mayors_pop'][ti] = np.stack([np.bincount(pidx[r], weights=pop, minlength=NP) for r in range(R)]) / pop.sum()
        # ------------------------------------------------------------ records
        wpop = pop[None] / pop.sum()
        for nm, arr in (('eff', A * ORIENT / sdu), ('vol', Am_v * ORIENT / sdu), ('alloc', Am_a * ORIENT / sdu),
                        ('ta', Ata * ORIENT / sdu), ('sel', lam * ORIENT / sdu), ('dis', -disrupt)):
            mk = arr.mean(2)
            o['ch_' + nm][ti] = mk.mean(1); o['ch_' + nm + '_pw'][ti] = (mk * wpop).sum(1)
        o['ch_man'][ti] = (G * ORIENT / sdu).mean((1, 2))
        disrupt *= col('rho_dis')[:, :, None]
        qs = q * ORIENT / sdu
        o['q'][ti] = qs.mean(1); o['qpw'][ti] = (qs * pop[None, :, None]).sum(1) / pop.sum()
        o['y'][ti] = (y * ORIENT / sdu).mean(1); o['U'][ti] = U.mean(1)
        o['theta'][ti] = theta.mean(1); o['thetapw'][ti] = (theta * pop[None]).sum(1) / pop.sum()
        o['disc'][ti] = disc.mean(1); o['vul'][ti] = vul.mean(1)
        for ri in range(5):
            o['q_reg'][ti, :, ri] = qs[:, c['reg_idx'] == ri].mean((1, 2))
        for ci in range(6):
            o['q_cls'][ti, :, ci] = qs[:, c['cls'] == ci].mean((1, 2))
        for qi in range(5):
            o['q_capq'][ti, :, qi] = qs[:, capq == qi].mean((1, 2))
    o['muni'] = muni
    o['q_final'] = (qhist[2035] * ORIENT / sdu).astype(np.float32)
    o['pidx_final'] = pidx
    return o
