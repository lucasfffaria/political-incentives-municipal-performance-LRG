"""
21_figures_behaviour.py -- figures for Section 7 (how mayors respond to incentives; calibration).
fig_careers      career incentives (RD 2020 and panel) and electoral returns to performance
fig_bunching     population counts bunch just above the FPM brackets in census years
fig_calibration  prior and posterior of the calibrated parameters; fit of the targets
usage: python 21_figures_behaviour.py [names...]
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, _ROOT + '/code')
import lrgstyle as st
import lrg2_sim as S

st.setup()
OUT = _ROOT + '/output'
IE = json.load(open(OUT + '/incentive_estimates.json'))
FR = json.load(open(OUT + '/fpm_rd.json'))
CAL = json.load(open(OUT + '/calibration.json'))
LAB = {'day': 'Daycare and preschool', 'ideb': 'IDEB (learning)', 'lit': 'Literacy (2024 level)', 'jobs': 'Formal jobs',
       'sew': 'Sewage coverage', 'va': 'Non-public value added'}


def fig_careers():
    """v4: (a) close races in which the incumbent ran, with the range of alternative specifications; (b) open seats
    (party continuity, a new eligible mayor on both sides); (c) bounds on the electoral incentive; (d) voters' reward."""
    fig, axs = plt.subplots(2, 2, figsize=(11.0, 7.6), gridspec_kw={'wspace': 0.12, 'hspace': 0.62, 'width_ratios': [1.15, 1]})
    rd = {r['var']: r for r in IE['rd']}
    rob = pd.DataFrame(IE['rd_robustness'])
    opn = pd.DataFrame(IE['rd_open'])
    order = ['day', 'ideb', 'lit', 'jobs', 'sew', 'va']
    var_of = lambda k: {'lit': 'lit_24'}.get(k, k + '_21')
    ax = axs[0, 0]
    for i, k in enumerate(order):
        y = len(order) - 1 - i
        v = var_of(k)
        rr = rob[rob['var'] == v]
        if len(rr):
            ax.plot([rr.coef.min(), rr.coef.max()], [y + 0.12, y + 0.12], color=st.BLUE, lw=6, alpha=0.22, solid_capstyle='butt')
        o = rd[v]
        ax.plot(o['ci_rb'], [y + 0.12, y + 0.12], color=st.BLUE, lw=1.5)
        ax.plot([o['coef']], [y + 0.12], 'o', color=st.BLUE, ms=5)
        if k != 'lit':
            pl = rd[k + '_17']
            ax.plot(pl['ci_rb'], [y - 0.18, y - 0.18], color=st.MUTED, lw=1.2)
            ax.plot([pl['coef']], [y - 0.18], 'o', color='white', mec=st.MUTED, mew=1.2, ms=4.3)
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([LAB[k] for k in order][::-1])
    ax.set_xlabel('Lame duck minus new first-term mayor (SD)')
    ax.set_title('Incumbent ran, 2020: same mayor and party vs new mayor', fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=st.BLUE, marker='o', lw=1.5, label='2021–24, 95% CI'),
                       Line2D([0], [0], color=st.BLUE, lw=6, alpha=0.22, label='Range over 9 specifications'),
                       Line2D([0], [0], color=st.MUTED, marker='o', mfc='white', lw=1.2, label='2017–20 (placebo)')],
              loc='upper center', bbox_to_anchor=(0.42, -0.17), ncol=3, fontsize=7.6)
    st.panel_label(ax, 'a')
    ax = axs[0, 1]
    for i, k in enumerate(order):
        y = len(order) - 1 - i
        v = var_of(k)
        a = opn[(opn['var'] == v) & (opn.design == 'open seat, party, pre-trend adjusted')]
        u = opn[(opn['var'] == v) & (opn.design == 'open seat, party')]
        if len(a):
            a = a.iloc[0]
            ax.plot(a.ci_rb, [y + 0.12, y + 0.12], color=st.ORANGE, lw=1.5); ax.plot([a.coef], [y + 0.12], 'o', color=st.ORANGE, ms=5)
        if len(u):
            ax.plot([u.iloc[0].coef], [y + 0.12], 'D', color='white', mec=st.ORANGE, mew=1.2, ms=4.3)
        pl = opn[(opn['var'] == k + '_17') & (opn.design == 'open seat, party')]
        if len(pl):
            pl = pl.iloc[0]
            ax.plot(pl.ci_rb, [y - 0.18, y - 0.18], color=st.MUTED, lw=1.2)
            ax.plot([pl.coef], [y - 0.18], 'o', color='white', mec=st.MUTED, mew=1.2, ms=4.3)
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([])
    ax.set_xlabel('Outgoing party kept minus lost (SD)')
    ax.set_title(f"Open seats, 2020: new eligible mayor on both sides (n = {IE['open_n']})", fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=st.ORANGE, marker='o', lw=1.5, label='2021–24, previous trend controlled'),
                       Line2D([0], [0], color='white', marker='D', mec=st.ORANGE, lw=0, label='Not controlled'),
                       Line2D([0], [0], color=st.MUTED, marker='o', mfc='white', lw=1.2, label='2017–20 (placebo)')],
              loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=3, fontsize=7.6)
    st.panel_label(ax, 'b')
    ax = axs[1, 0]
    dec = pd.DataFrame(IE['decomposition'])
    dec = dec[dec.version == 'adjusted']
    o5 = ['day', 'ideb', 'jobs', 'sew', 'va']
    for i, k in enumerate(o5):
        y = len(o5) - 1 - i
        r = dec[dec['var'] == k + '_21'].iloc[0]
        ax.plot([r.E_lo_ci, r.E_hi_ci], [y, y], color=st.VIOLET, lw=1.2)
        ax.plot([r.E_lo, r.E_hi], [y, y], color=st.VIOLET, lw=7, alpha=0.45, solid_capstyle='butt')
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_yticks(range(len(o5))); ax.set_yticklabels([LAB[k] for k in o5][::-1])
    ax.set_xlabel('Effect of being able to run again (SD over the mandate)')
    ax.set_title('What the two designs imply for the electoral incentive', fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=st.VIOLET, lw=7, alpha=0.45, label='Bounds: person continuity 0 to max'),
                       Line2D([0], [0], color=st.VIOLET, lw=1.2, label='With sampling error (95%)')],
              loc='upper center', bbox_to_anchor=(0.42, -0.17), ncol=2, fontsize=7.6)
    st.panel_label(ax, 'c')
    ax = axs[1, 1]
    er = pd.DataFrame(IE['electoral_returns'])
    rows = [('composite (SD of composite)', 'All indicators'), ('z_day', 'Daycare'), ('z_ideb', 'IDEB'), ('z_jobs', 'Formal jobs')]
    for i, (v, lab) in enumerate(rows):
        y = len(rows) - 1 - i
        for yr, col, dy in [(2020, st.VIOLET, 0.13), (2024, st.AQUA, -0.13)]:
            o = er[(er.year == yr) & (er['var'] == v)]
            if len(o):
                o = o.iloc[0]
                ax.plot([o.coef_pp - 1.96 * o.se_pp, o.coef_pp + 1.96 * o.se_pp], [y + dy, y + dy], color=col, lw=1.5)
                ax.plot([o.coef_pp], [y + dy], 'o', color=col, ms=5)
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[1] for r in rows][::-1])
    ax.yaxis.tick_right()
    ax.set_xlabel('Re-election, percentage points per SD')
    ax.set_title('Voters’ reward for measured performance (association)', fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=st.VIOLET, marker='o', lw=1.5, label='2020'),
                       Line2D([0], [0], color=st.AQUA, marker='o', lw=1.5, label='2024')],
              loc='upper center', bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=7.6)
    st.panel_label(ax, 'd')
    st.save(fig, 'fig_careers')


def fig_bunching():
    b = pd.DataFrame(FR['bunching'])
    fig, axs = plt.subplots(1, 2, figsize=(10.4, 3.6), gridspec_kw={'width_ratios': [1.6, 1.0], 'wspace': 0.3})
    ax = axs[0]
    x = np.arange(len(b))
    ratio = b.above_1pct / b.below_1pct
    cols = [st.RED if k == 'count' else st.GRAYBAR for k in b.kind]
    ax.bar(x, ratio, color=cols, width=0.72)
    ax.axhline(1, color=st.INK2, lw=0.8, ls='--')
    ax.set_xticks(x[::2]); ax.set_xticklabels(b.year.astype(int)[::2], rotation=0)
    ax.set_ylabel('Municipalities 0–1% above a bracket\nper municipality 0–1% below')
    ax.set_title('Population counts that reset the FPM bunch above the brackets', fontsize=10)
    for xi, (r_, k) in enumerate(zip(ratio, b.kind)):
        if k == 'count':
            ax.text(xi, r_ + 0.12, f'{r_:.1f}', ha='center', fontsize=8, color=st.INK)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=st.RED, label='Census or count'),
                       plt.Rectangle((0, 0), 1, 1, color=st.GRAYBAR, label='Intercensal estimate')], loc='upper right', fontsize=8)
    st.panel_label(ax, 'a')
    # pooled histogram, 2010 count against 2019 estimate
    pp = pd.read_csv(_ROOT + '/data/raw/social/populacao/ibge_pop_municipios_2000_2025.csv')
    P = pp.pivot_table(index='code_muni', columns='year', values='pop')
    T = np.array([10189, 13585, 16981, 23773, 30565, 37357, 44149])
    ax = axs[1]
    bins = np.arange(-5, 5.01, 0.5)
    for yr, col, lab in [(2019, st.GRAYBAR, '2019 estimate'), (2010, st.RED, '2010 Census')]:
        p_ = P[yr].dropna()
        r = []
        for t in T:
            rr = 100 * (p_ - t) / t
            r += list(rr[(rr >= -5) & (rr < 5)])
        h, e = np.histogram(r, bins=bins)
        ax.step(e[:-1], h, where='post', color=col, lw=1.8, label=lab)
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_xlabel('Distance to the nearest bracket (%)'); ax.set_ylabel('Municipalities per 0.5% bin')
    ax.set_title('Seven brackets pooled', fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    st.panel_label(ax, 'b')
    st.save(fig, 'fig_bunching')


def fig_calibration():
    """v4: (a) what the evidence pins down: posterior 90% intervals of key parameters under alternative calibrations,
    on the scale of the main prior range; (b) fit of the targets, out-of-sample predictions of the targets left out
    (leave-one-group-out) and statistics never used for weighting."""
    VARS = [('main', 'Main calibration', st.BLUE), ('v3', 'v3 likelihood', st.MUTED), ('wide', 'Wider priors', st.ORANGE),
            ('noCE', 'Without Ceará', st.AQUA), ('noRD', 'Without the RDs', st.VIOLET), ('noEL', 'Without electoral return', st.YELLOW),
            ('trans50', 'Ceará twice national', st.RED)]
    cals = {v: json.load(open(OUT + ('/calibration.json' if v == 'main' else f'/calibration_{v}.json'))) for v, _, _ in VARS}
    show = [('delta_K3', 'δ learning'), ('delta_K4', 'δ daycare'), ('beta_TA', 'Assistance (PAIC)'), ('ta_quality', 'Commissioners’ share'),
            ('kappa_money', 'Money pressure'), ('kappa_el', 'Electoral pressure'), ('beta_perf', 'Voters’ reward β'),
            ('tau_turn', 'Disruption τ'), ('rho_dis', 'Persistence of disruption'), ('w_lrg', 'Waste of tied money')]
    fig = plt.figure(figsize=(11.2, 6.9))
    gs = fig.add_gridspec(1, 2, wspace=0.62, width_ratios=[1.0, 1.15])
    ax = fig.add_subplot(gs[0, 0])
    nv = len(VARS)
    for i, (k, lab) in enumerate(show):
        y = len(show) - 1 - i
        lo0, hi0 = S.PRIORS[k]
        for j, (v, vl, colr) in enumerate(VARS):
            pr = cals[v]['params'][k]
            yy = y + 0.36 - j * 0.72 / (nv - 1)
            a, b, m = [(x - lo0) / (hi0 - lo0) for x in (pr['post_p5'], pr['post_p95'], pr['post_med'])]
            ax.plot([a, b], [yy, yy], color=colr, lw=1.4)
            ax.plot([m], [yy], 'o', color=colr, ms=3.2)
    ax.axvspan(0, 1, color=st.GRAYBAR, alpha=0.12, lw=0)
    ax.set_yticks(range(len(show))); ax.set_yticklabels([l for _, l in show][::-1], fontsize=8.5)
    ax.set_xlabel('Position in the main prior range (0 = lower, 1 = upper bound)')
    ax.set_title('What the evidence pins down: 90% posterior intervals', fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=c_, marker='o', ms=3.2, lw=1.4, label=l_) for _, l_, c_ in VARS],
              loc='upper center', bbox_to_anchor=(0.45, -0.09), ncol=3, fontsize=7.4)
    st.panel_label(ax, 'a')
    ax = fig.add_subplot(gs[0, 1])
    main = cals['main']
    held = {}
    for v, blk in [('noCE', 'CE'), ('noRD', 'RD'), ('noRD', 'RDo'), ('noEL', 'EL')]:
        for f_ in cals[v]['fit']:
            if f_['block'] == blk:
                held[f_['moment']] = f_
    try:
        for f_ in json.load(open(OUT + '/calibration_noFPM.json'))['fit']:
            if f_['block'] == 'FPM':
                held[f_['moment']] = f_
    except FileNotFoundError:
        pass
    SHORT = {'day_21': 'daycare', 'ideb_21': 'IDEB', 'jobs_21': 'jobs', 'sew_21': 'sewage', 'va_21': 'value added'}
    rows = []
    for f_ in main['fit']:
        nm = f_['moment']
        if nm.startswith('M3o'):
            lab = 'Open seats: ' + SHORT[nm.split(': ')[1]]
        elif nm.startswith('M3'):
            lab = 'Incumbent ran: ' + SHORT[nm.split(': ')[1]]
        elif nm.startswith('M5'):
            lab = 'FPM: ' + ('daycare' if 'daycare' in nm else 'jobs')
        else:
            lab = {'M1': 'Ceará: rule', 'M2': 'Ceará: rule + PAIC', 'M4': 'Electoral return'}[nm[:2]]
        rows.append((lab, f_['target'], f_['se'], (f_['post_p5'], f_['post_med'], f_['post_p95']), held.get(nm)))
    for ch in main['checks']:
        if ch['check'].startswith('panel'):
            lab = 'Panel FE: ' + ch['check'].split(', ')[1].replace('day', 'daycare').replace('ideb', 'IDEB')
        else:
            lab = 'Literacy 2024: ' + ('incumbent ran' if 'incumbent' in ch['check'] else 'open seats')
        rows.append((lab + ' †', ch['estimate'], ch['se'], (ch['post_p5'], ch['post_med'], ch['post_p95']), None))
    for pth in main['ceara_path']:
        if pth['year'] in (2011, 2015, 2019):
            rows.append((f"Ceará {pth['year']} (Ponne) †", pth['observed_pupil_sd'], np.nan, (pth['post_p5'], pth['post_med'], pth['post_p95']), None))
    for i, (lab, tg, se, mm, ho) in enumerate(rows):
        y = len(rows) - 1 - i
        if np.isfinite(se):
            ax.plot([tg - 1.96 * se, tg + 1.96 * se], [y + 0.22, y + 0.22], color=st.ORANGE, lw=1.4)
        ax.plot([tg], [y + 0.22], 's', color=st.ORANGE, ms=4)
        ax.plot([mm[0], mm[2]], [y, y], color=st.BLUE, lw=1.4); ax.plot([mm[1]], [y], 'o', color=st.BLUE, ms=3.8)
        if ho is not None:
            ax.plot([ho['post_p5'], ho['post_p95']], [y - 0.22, y - 0.22], color=st.AQUA, lw=1.4)
            ax.plot([ho['post_med']], [y - 0.22], 'o', color=st.AQUA, ms=3.8)
    ax.axvline(0, color=st.INK2, lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.6)
    ax.set_xlabel('Estimate (own units)')
    ax.set_title('Fit, out-of-sample prediction and validation', fontsize=9.5)
    ax.legend(handles=[Line2D([0], [0], color=st.ORANGE, marker='s', lw=1.4, label='Estimate ±1.96 SE'),
                       Line2D([0], [0], color=st.BLUE, marker='o', lw=1.4, label='Main calibration, 90%'),
                       Line2D([0], [0], color=st.AQUA, marker='o', lw=1.4, label='Target left out, 90%')],
              loc='upper center', bbox_to_anchor=(0.4, -0.09), ncol=2, fontsize=7.4)
    st.panel_label(ax, 'b')
    st.save(fig, 'fig_calibration')


if __name__ == '__main__':
    names = sys.argv[1:] or ['fig_careers', 'fig_bunching', 'fig_calibration']
    for n in names:
        globals()[n]()
        print('saved', n)
