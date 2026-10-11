"""
22_scenarios.py -- v4 scenario analyses: summarises the runs of 03_run_designs.py under alternative assumptions.

Runs (output/designs_metrics_<TAG>.npz), each with the same calibrated draws and random shocks as the main run:
  main      designs_metrics.npz (base scenario, 400 draws)
  sc_iB, sc_iC, sc_iD       implementation of LRG money and assistance depends on mayors' incentives and supervision
                            (complementarity weak, moderate, strong; scenario A = main)
  sc_lameM, sc_iDlameM      banned mayors keep responding to money, party funds and a bonus (with A and with D)
  sc_eN, sc_eH2, sc_eH4     voters' reward for measured performance: none, x2, x4 (main = calibrated)
  sc_m0, sc_m0s, sc_mL, sc_mH, sc_mA, sc_mAs   manipulation: none, none with the effort redirected to real improvement,
                            x0.5, x1.5, audits removing 60%, audits with redirection (main = calibrated shares)
  cv_<variant>              calibration variants of 19_calibrate.py (wide, noCE, noRD, noEL, noFPM, trans50, indep, v3) and,
                            in v5, saturation of effort (cap2, cap8, lin), each recalibrated
  sc_dm15, sc_dm2, sc_dm3   v5: responsiveness of effort x1.5, x2, x3 (no recalibration)
  sc_km2, sc_km3            v5: weight of money x2, x3 (no recalibration)
Writes output/scenarios.json.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, glob
import numpy as np

OUT = _ROOT + '/output'


def q3(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return None
    return dict(med=float(np.median(a)), p5=float(np.percentile(a, 5)), p95=float(np.percentile(a, 95)), mean=float(a.mean()))


def summarise(z):
    keys = sorted(set(k.split('__')[0] for k in z.files))
    g = lambda d, m: z[f'{d}__{m}'] if f'{d}__{m}' in z.files else None
    out = {}
    ref = g('F11111', 'eff_comp')
    refpw = g('F11111', 'effpw_comp')
    for d in keys:
        e = g(d, 'eff_comp')
        if e is None:
            continue
        r = dict(eff=q3(e), effpw=q3(g(d, 'effpw_comp')), cosmetic=q3(g(d, 'meas_comp') - e),
                 effort=q3(g(d, 'ch_eff')), alloc=q3(g(d, 'ch_alloc')), ta=q3(g(d, 'ch_ta')), vol=q3(g(d, 'ch_vol')),
                 iota_m=q3(g(d, 'iota_m')), iota_ta=q3(g(d, 'iota_ta')), ratio_m=q3(g(d, 'ratio_m')), ratio_ta=q3(g(d, 'ratio_ta')),
                 bans=q3(g(d, 'bans_per100_term')), tutelage=q3(g(d, 'tutelage')), unscored=q3(g(d, 'U_2036')),
                 fiscal_bn=q3(g(d, 'comm_cost_bn') + g(d, 'bonus_cost')),
                 incumb_win=q3(g(d, 'incumb_win')), reelect_elig=q3(g(d, 'reelect_elig')), turnover=q3(g(d, 'turnover')),
                 wrongful=q3(g(d, 'wrongful')), ban_theta_neg=q3(g(d, 'ban_theta_neg')))
        # v4: channel shares of the real effect, manipulation and disruption, attributable bans, literacy
        real = sum(g(d, 'ch_' + ch) for ch in ('eff', 'vol', 'alloc', 'ta', 'sel', 'dis'))
        den = np.where(np.abs(real) > 1e-6, real, np.nan)
        r.update(share_effort=q3(g(d, 'ch_eff') / den), share_moneycap=q3((g(d, 'ch_alloc') + g(d, 'ch_ta') + g(d, 'ch_vol')) / den),
                 man=q3(g(d, 'ch_man')), dis=q3(g(d, 'ch_dis')), lit=q3(g(d, 'eff_K')[:, 2]),
                 attributable=q3(1 - np.nan_to_num(g(d, 'wrongful')) - np.nan_to_num(g(d, 'place_driven'))) if g(d, 'place_driven') is not None else None,
                 thetapw=q3(g(d, 'thetapw_2033')), comm_cost_bn=q3(g(d, 'comm_cost_bn')), bonus_cost=q3(g(d, 'bonus_cost')))
        if ref is not None:
            r['ratio_to_AP'] = q3(e / np.where(np.abs(ref) > 1e-6, ref, np.nan))
            r['ratio_to_AP_pw'] = q3(g(d, 'effpw_comp') / np.where(np.abs(refpw) > 1e-6, refpw, np.nan))
        out[d] = r
    # contributions of each instrument added alone to the published scorecard (main effects) and their ranking
    if g('F00000', 'eff_comp') is not None:
        base = g('F00000', 'eff_comp'); basem = g('F00000', 'meas_comp')
        me = {}
        for p, k in zip('SFACP', ['F10000', 'F01000', 'F00100', 'F00010', 'F00001']):
            if g(k, 'eff_comp') is not None:
                me[p] = dict(eff=q3(g(k, 'eff_comp') - base), meas=q3(g(k, 'meas_comp') - basem),
                             cosmetic=q3((g(k, 'meas_comp') - g(k, 'eff_comp')) - (basem - base)))
        if me and all(g(k, 'eff_comp') is not None for k in ['F10000', 'F01000', 'F00100', 'F00010', 'F00001']):
            arr = np.stack([g(k, 'eff_comp') - base for k in ['F10000', 'F01000', 'F00100', 'F00010', 'F00001']], 1)
            rank = (-arr).argsort(1).argsort(1) + 1                      # 1 = largest real effect, per draw
            for j, p in enumerate('SFACP'):
                me[p]['rank_med'] = float(np.median(rank[:, j]))
                me[p]['share_rank1'] = float((rank[:, j] == 1).mean())
        if me:
            out['_main_effects'] = me
    return out


res = {}
files = {'main': OUT + '/designs_metrics.npz'}
_main = np.load(files['main']) if _os.path.exists(files['main']) else None
for f in sorted(glob.glob(OUT + '/designs_metrics_sc_*.npz')) + sorted(glob.glob(OUT + '/designs_metrics_cv_*.npz')):
    files[_os.path.basename(f)[len('designs_metrics_'):-4]] = f
class _First:                                   # the main run restricted to its first n draws (comparable with the scenarios)
    def __init__(self, z, n):
        self.z, self.n, self.files = z, n, z.files

    def __getitem__(self, k):
        a = self.z[k]
        return a[:self.n] if (a.ndim >= 1 and a.shape[0] == self.z['W0__eff_comp'].shape[0]) else a


NS = 120                                       # draws of the scenario runs (the first NS draws of the main run)
for f_ in list(files.values())[1:]:
    if _os.path.exists(f_):
        NS = int(np.load(f_)['W0__eff_comp'].shape[0]); break
if _main is not None:
    res['mainS'] = summarise(_First(_main, NS))
res['_meta'] = dict(n_scenario_draws=NS, n_main_draws=int(_main['W0__eff_comp'].shape[0]) if _main is not None else None)
for tag, f in files.items():
    if _os.path.exists(f):
        z_ = np.load(f)
        res[tag] = summarise(z_)
        # the same design against the proposal of the main run (same draws and shocks): how the scenario moves levels
        # (the scenario runs use the first NS draws and the same seeds as the main run)
        if _main is not None and 'F11111__eff_comp' in _main.files and tag.startswith('sc_'):
            for d_ in res[tag]:
                if not d_.startswith('_') and f'{d_}__eff_comp' in z_.files:
                    e_ = z_[f'{d_}__eff_comp']; ref_ = _main['F11111__eff_comp'][:len(e_)]
                    res[tag][d_]['ratio_to_AP_main'] = q3(e_ / np.where(np.abs(ref_) > 1e-6, ref_, np.nan))
        print(tag, 'designs:', len([k for k in res[tag] if not k.startswith('_')]))
json.dump(res, open(OUT + '/scenarios.json', 'w'), indent=1)
# a compact view: how much of the LRG's real effect is kept without bans, without sanctions, with threat or execution only
for tag, r in res.items():
    if tag.startswith('_'):
        continue
    line = [f'{tag:10s}']
    for d in ['F11111', 'AP_nb', 'F01111', 'AP_th', 'AP_ex']:
        if d in r and r[d].get('ratio_to_AP'):
            line.append(f"{d}={r[d]['eff']['med']:.3f}({100 * r[d]['ratio_to_AP']['med']:.0f}%)")
    print(' '.join(line))
