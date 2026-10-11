"""
12_figures_sim.py -- figures from the national simulation (v5: the LRG as proposed is the only policy evaluated).
Main text
  fig_sanctions     flags, tutelage and bans under the rules as proposed and single changes to them
  fig_effects       effects indicator by indicator: true and measured, natural units, and which instrument moves each
  fig_shapley       what each instrument contributes (Shapley values over the 2^5 factorial), six outcomes
  fig_channels      where the improvement comes from: channels by design and by instrument
  fig_money         where the performance money goes
  fig_parties       party funds and mayors in 2036; a new party
  fig_tranche       doses of the FPM tranche
  fig_bans          the ban for results: deterrence against execution, and the intensity of the threat
  fig_complement    the marginal effect of each instrument depends on the others (factorial), scenarios A and D
  fig_plausibility  what would it take for the behavioural response to be larger, and what the evidence says
  fig_sobol         which assumptions drive which results
  fig_power         minimum detectable effects of a factorial pilot
Appendix
  fig_bonus         a personal bonus for mayors on the LRG's scorecard: a theoretical benchmark
Supplementary material
  fig_whobanned, fig_selection, fig_mei, fig_families, fig_saturation
usage: python 12_figures_sim.py [names...]
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json, math, itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter, NullLocator, FuncFormatter
sys.path.insert(0, _ROOT + '/code')
import lrgstyle as st
import lrg2_sim as S

st.setup()
OUT = _ROOT + '/output'
M = np.load(OUT + '/designs_metrics.npz')
T5 = json.load(open(OUT + '/v5_tests.json')) if _os.path.exists(OUT + '/v5_tests.json') else {}
SC = json.load(open(OUT + '/scenarios.json')) if _os.path.exists(OUT + '/scenarios.json') else {}
c = S.load()
parties = c['parties']
g = lambda key, mk: M[f'{key}__{mk}']
has = lambda key: f'{key}__eff_comp' in M.files
med = lambda a: float(np.nanmedian(a))
pct = lambda a, q: float(np.nanpercentile(a, q))
PILL = ['S', 'F', 'A', 'C', 'P']
PILL_NAMES = {'S': 'Sanctions', 'F': 'FPM tranche', 'A': 'Tied amendments', 'C': 'Commissioners', 'P': 'Party funds',
              'I': 'Published scorecard'}
PILL_COL = dict(st.INSTR)
AP = 'F11111'
CLS = ['<5k', '5–10k', '10–20k', '20–50k', '50–100k', '>100k']
REGN = ['North', 'Northeast', 'Southeast', 'South', 'Centre-W.']
KN = S.KN
KLAB = {'K1': 'Formal jobs', 'K2': 'Non-public value added', 'K3': 'Literacy', 'K4': 'Daycare and preschool',
        'K6': 'Sewage', 'K7': 'Homicides (fewer)'}
W = 7.2                                                         # every figure is drawn at the width it is printed


def shapley(fn):
    n = 5; phi = {p: 0.0 for p in PILL}
    for j, pj in enumerate(PILL):
        others = [i for i in range(n) if i != j]
        for k in range(n):
            for T in itertools.combinations(others, k):
                wgt = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
                b0 = [1 if i in T else 0 for i in range(n)]; b1 = b0.copy(); b1[j] = 1
                phi[pj] = phi[pj] + wgt * (fn('F' + ''.join(map(str, b1))) - fn('F' + ''.join(map(str, b0))))
    return phi


interval = st.interval


def clean_x(ax):
    ax.grid(axis='y', visible=False)


def clean_y(ax):
    ax.grid(axis='x', visible=False)


# =========================================================================== flags, tutelage and bans
def fig_sanctions():
    designs = [('WP', 'Placebo: rules,\nno response'), (AP, 'As proposed'), ('V_literal', 'No statistical\ntolerance'),
               ('V_far15', 'Red band at\n1.5 SD'), ('V_noNI', 'Without the “no\nimprovement” rule')]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, 6.0))
    x = np.arange(len(designs))
    for i, (k, lab) in enumerate(designs):
        f_, t_ = 100 * g(k, 'flag'), 100 * g(k, 'tutelage')
        a1.bar(i - 0.19, med(f_), width=0.36, color=st.BAND['yellow'])
        a1.bar(i + 0.19, med(t_), width=0.36, color=st.BAND['orange'])
        for xx, v in ((i - 0.19, f_), (i + 0.19, t_)):
            a1.plot([xx] * 2, [pct(v, 5), pct(v, 95)], color=st.INK2, lw=1)
            a1.text(xx, med(v) / 2, f'{med(v):.0f}', ha='center', va='center', fontsize=7.4, color=st.INK, fontweight='semibold')
    a1.set_xticks(x); a1.set_xticklabels([l for _, l in designs], fontsize=7.8)
    a1.set_ylabel('% of municipality-years, 2027–2036')
    clean_y(a1)
    a1.set_ylim(0, 118); a1.set_yticks(range(0, 101, 20))
    a1.legend(handles=[Patch(color=st.BAND['yellow'], label='flagged (yellow or worse)'), Patch(color=st.BAND['orange'], label='classified for tutelage')],
              fontsize=7.6, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.02))
    a1.set_title('Flags and tutelage')
    st.panel_label(a1, 'a')
    for i, (k, lab) in enumerate(designs):
        b = g(k, 'bans_per100_term'); w = np.nan_to_num(g(k, 'wrongful')); pl = np.nan_to_num(g(k, 'place_driven'))
        tot = med(b); wr = med(b * w); pd_ = med(b * pl); rest = max(tot - wr - pd_, 0)
        a2.bar(i, wr, width=0.6, color=st.PLUM)
        a2.bar(i, pd_, bottom=wr, width=0.6, color=st.GRAYBAR)
        a2.bar(i, rest, bottom=wr + pd_, width=0.6, color=st.INDIGO)
        a2.plot([i, i], [pct(b, 5), pct(b, 95)], color=st.INK2, lw=1)
        a2.text(i, pct(b, 95) + 0.6, f'{tot:.1f}', ha='center', fontsize=7.8, color=st.INK, fontweight='semibold')
    a2.set_xticks(x); a2.set_xticklabels([l for _, l in designs], fontsize=7.8)
    a2.set_ylabel('Mayors banned per 100, per mandate'); clean_y(a2)
    top = max(pct(g(k, 'bans_per100_term'), 95) for k, _ in designs)
    a2.set_ylim(0, top * 1.45)
    a2.legend(handles=[Patch(color=st.PLUM, label='wrongful: not triggered without\nmeasurement error'),
                       Patch(color=st.GRAYBAR, label='structural: triggered also with\nan average mayor in office'),
                       Patch(color=st.INDIGO, label='attributable to the mayor')], fontsize=7.2, loc='upper center', ncol=3,
              bbox_to_anchor=(0.5, 1.02), handlelength=1.2, columnspacing=1.4)
    a2.set_title('Eight-year bans for results')
    st.panel_label(a2, 'b')
    plt.tight_layout(h_pad=1.8)
    st.save(fig, 'fig_sanctions')


# =========================================================================== indicator by indicator
def fig_effects():
    BI = T5['by_indicator']
    fig = plt.figure(figsize=(W, 5.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.05], wspace=0.08)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1], sharey=a1)
    rows = KN
    y = np.arange(len(rows))[::-1]
    for yi, k in zip(y, rows):
        e = g(AP, 'eff_K')[:, KN.index(k)]; m_ = g(AP, 'meas_K')[:, KN.index(k)]
        interval(a1, med(e), yi + 0.12, pct(e, 5), pct(e, 95), st.INDIGO, ms=6)
        a1.plot([med(m_)], [yi - 0.14], marker='D', ms=5, mfc='white', mec=st.GOLD_DK, mew=1.3, ls='')
        b = BI[k]; u = b['unit']; v = b['eff_nat']['med']
        txt = (f'{v:+.1f}%' if u == '%' else (f'{v:+.2f} {u}' if k in ('K2', 'K7') else f'{v:+.1f} {u}'))
        a1.text(max(med(e), 0.0) + 0.012, yi + 0.36, txt, va='center', ha='left', fontsize=7.6, color=st.INDIGO,
                fontweight='semibold')
    st.zero_line(a1)
    a1.set_yticks(y); a1.set_yticklabels([KLAB[k] for k in rows], fontsize=8.2)
    a1.set_xlabel('Effect against the status quo, 2029–36 (SD)')
    a1.set_title('True and measured effects', pad=12)
    clean_x(a1)
    a1.legend(handles=[Line2D([], [], color=st.INDIGO, marker='o', mec='white', label='true (median, 5–95%)'),
                       Line2D([], [], color=st.GOLD_DK, marker='D', mfc='white', ls='', label='measured (median)')],
              fontsize=7.2, loc='lower right')
    st.panel_label(a1, 'a')
    # (b) which instrument moves each indicator: Shapley values by indicator
    order = ['I'] + PILL
    for yi, k in zip(y, rows):
        left_p = left_n = 0.0
        vals = [('I', BI[k]['scorecard_sd']['med'])] + [(p, BI[k]['shapley_sd'][p]['med']) for p in PILL]
        for p, v in vals:
            if v >= 0:
                a2.barh(yi, v, left=left_p, color=PILL_COL[p], height=0.62, edgecolor='white', linewidth=0.8); left_p += v
            else:
                a2.barh(yi, v, left=left_n, color=PILL_COL[p], height=0.62, edgecolor='white', linewidth=0.8); left_n += v
    st.zero_line(a2)
    plt.setp(a2.get_yticklabels(), visible=False)
    a2.set_xlabel('Shapley contribution (SD)')
    a2.set_title('Which instrument moves each indicator', pad=12)
    clean_x(a2)
    a2.legend(handles=[Patch(color=PILL_COL[p], label=PILL_NAMES[p]) for p in order], fontsize=7.0, loc='lower right', ncol=1,
              handlelength=1.0)
    st.panel_label(a2, 'b')
    st.save(fig, 'fig_effects')


# =========================================================================== Shapley, six outcomes
def fig_shapley():
    outs = [('eff_comp', lambda k: g(k, 'eff_comp'), 'True effect on the\nsix indicators (SD)'),
            ('cosm', lambda k: g(k, 'meas_comp') - g(k, 'eff_comp'), 'Measured minus\ntrue (SD)'),
            ('bans', lambda k: g(k, 'bans_per100_term'), 'Bans per 100 mayors\nper mandate'),
            ('fp', lambda k: 100 * g(k, 'fp_big6'), 'Six largest parties’\nshare of the FP (pp)'),
            ('win', lambda k: 100 * g(k, 'incumb_win'), 'Re-election of incumbents\nwho run (pp)'),
            ('theta', lambda k: g(k, 'thetapw_2033'), 'Competence of mayors,\n2033–36, pop.-weighted (SD)')]
    fig, axes = plt.subplots(2, 3, figsize=(W, 5.3))
    names = dict(PILL_NAMES, T='Total, as proposed')
    cols = dict(PILL_COL, T=st.INK)
    for ax, (key, fn, title) in zip(axes.ravel(), outs):
        ph = shapley(lambda kk: fn(kk))
        vals = {p: med(ph[p]) for p in PILL}
        vals['I'] = med(fn('F00000') - fn('W0'))
        vals['T'] = med(fn(AP) - fn('W0'))
        order = ['I'] + PILL + ['T']
        yy = np.array([7, 6, 5, 4, 3, 2, 0.6])
        for yi, p in zip(yy, order):
            ax.barh(yi, vals[p], color=cols[p], height=0.64)
        st.zero_line(ax, lw=0.8)
        ax.axhline(1.3, color=st.GRID, lw=0.8)
        ax.set_yticks(yy); ax.set_yticklabels([names[p] for p in order] if ax in axes[:, 0] else [], fontsize=7.4)
        ax.set_title(title, fontsize=8.4)
        clean_x(ax)
        ax.tick_params(axis='x', labelsize=7.2)
        lo, hi = ax.get_xlim(); ax.set_xlim(min(lo, 0), hi)
    plt.tight_layout(h_pad=1.4, w_pad=0.8)
    st.save(fig, 'fig_shapley')


# =========================================================================== channels
CHN = [('eff', 'Effort'), ('vol', 'Money volume (tranche)'), ('alloc', 'Allocation (tied amendments)'), ('ta', 'Technical assistance'),
       ('sel', 'Selection'), ('dis', 'Disruption')]
CHC = dict(st.CHANNEL)


def _stack(ax, y, getv, lw=0.9):
    left_pos, left_neg = 0.0, 0.0
    for ch, _ in CHN:
        v = getv(ch)
        if v >= 0:
            ax.barh(y, v, left=left_pos, color=CHC[ch], height=0.62, edgecolor='white', linewidth=lw); left_pos += v
        else:
            ax.barh(y, v, left=left_neg, color=CHC[ch], height=0.62, edgecolor='white', linewidth=lw); left_neg += v
    return left_pos


def fig_channels():
    designs = [('F11111', 'As proposed'), ('AP_nb', 'Without bans for results'), ('F01111', 'Without performance sanctions'),
               ('F10000', 'Sanctions alone'), ('F01000', 'FPM tranche alone'), ('F00100', 'Tied amendments alone'),
               ('F00010', 'Commissioners alone'), ('F00001', 'Party funds alone')]
    fig, axs = plt.subplots(2, 1, figsize=(W, 7.0), gridspec_kw={'height_ratios': [1.45, 1.0], 'hspace': 0.42})
    ax = axs[0]
    for i, (k, lab) in enumerate(designs):
        y = len(designs) - 1 - i
        top = _stack(ax, y, lambda ch: med(g(k, 'ch_' + ch)))
        man = med(g(k, 'ch_man'))
        ax.plot([top, top + man], [y, y], color=st.GOLD_DK, lw=1.2, ls=':')
        ax.plot([top + man], [y], marker='|', ms=11, mew=2.0, color=st.GOLD_DK)
    st.zero_line(ax, lw=0.8)
    ax.axhline(len(designs) - 3.5, color=st.GRID, lw=0.9)
    ax.set_yticks(range(len(designs))); ax.set_yticklabels([l for _, l in designs][::-1], fontsize=8)
    ax.set_xlabel('Change in true quality, 2029–36 (SD, average of the six indicators)')
    ax.set_title('By design')
    clean_x(ax)
    st.panel_label(ax, 'a')
    ax = axs[1]
    for i, pll in enumerate(PILL):
        y = len(PILL) - 1 - i
        _stack(ax, y, lambda ch: med(shapley(lambda kk, ch=ch: g(kk, 'ch_' + ch))[pll]))
    st.zero_line(ax, lw=0.8)
    ax.set_yticks(range(len(PILL))); ax.set_yticklabels([PILL_NAMES[x] for x in PILL][::-1], fontsize=8)
    ax.set_xlabel('Shapley contribution to the effect of the LRG as proposed (SD)')
    ax.set_title('By instrument, as proposed')
    clean_x(ax)
    st.panel_label(ax, 'b')
    hs = [Patch(color=CHC[ch], label=lab) for ch, lab in CHN] + \
         [Line2D([0], [0], color=st.GOLD_DK, marker='|', ms=10, mew=2, ls=':', label='+ manipulation (measured only)')]
    fig.legend(handles=hs, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.02), fontsize=7.4, columnspacing=1.2)
    plt.subplots_adjust(bottom=0.13)
    st.save(fig, 'fig_channels')


# =========================================================================== money
def fig_money():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.5))
    for ax, key, labs, title in [(a1, 'money_reg', REGN, 'By region'),
                                 (a2, 'money_gdpq', ['Poorest\nfifth', '2', '3', '4', 'Richest\nfifth'], 'By income per capita')]:
        x = np.arange(len(labs))
        for j, (k, colr, lab) in enumerate([(AP, st.GOLD, 'tranche by points × own FPM (as proposed)'),
                                            ('V_poptranche', st.INDIGO, 'tranche by points × population (variant)')]):
            v = g(k, key)
            m_ = np.nanmedian(v, 0); lo = np.nanpercentile(v, 5, 0); hi = np.nanpercentile(v, 95, 0)
            xx = x + (j - 0.5) * 0.36
            ax.bar(xx, m_, width=0.34, color=colr, label=lab, edgecolor=st.GOLD_DK if colr == st.GOLD else colr, linewidth=0.6)
            for a_, l_, h_ in zip(xx, lo, hi):
                ax.plot([a_, a_], [l_, h_], color=st.INK2, lw=0.8)
        st.zero_line(ax, axis='y', lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=7.4)
        clean_y(ax); ax.set_title(title)
    a1.set_ylabel('Net federal money, R$ billion a year')
    h_, l_ = a1.get_legend_handles_labels()
    fig.legend(h_, l_, loc='lower center', ncol=2, fontsize=7.4, bbox_to_anchor=(0.5, -0.04))
    st.panel_label(a1, 'a'); st.panel_label(a2, 'b')
    plt.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    st.save(fig, 'fig_money')


# =========================================================================== parties
def fig_parties():
    show = ['PSD', 'MDB', 'PP', 'UNIAO', 'PL', 'REPUBLICANOS', 'PSB', 'PSDB', 'PT', 'PODEMOS', 'PDT', 'PSOL']
    idx = [parties.index(p) for p in show]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.9), gridspec_kw={'width_ratios': [1.3, 1]})
    y = np.arange(len(show))[::-1]
    for j, (k, colr, lab, off) in enumerate([('W0', st.GRAYBAR, 'status quo', 0.15), (AP, st.INDIGO, 'LRG as proposed', -0.15)]):
        v = 100 * g(k, 'fp_2036')[:, idx]
        for i in range(len(show)):
            interval(a1, med(v[:, i]), y[i] + off, pct(v[:, i], 5), pct(v[:, i], 95), colr if k != 'W0' else st.MUTED,
                     ms=5, face=None if k != 'W0' else st.GRAYBAR)
    a1.set_yticks(y); a1.set_yticklabels([p.replace('REPUBLICANOS', 'REPUBLIC.') for p in show], fontsize=7.6)
    a1.set_xlabel('Share of the Fundo Partidário in 2036 (%)'); clean_x(a1)
    a1.legend(handles=[Line2D([], [], color=st.MUTED, marker='o', mfc=st.GRAYBAR, mec='white', label='status quo'),
                       Line2D([], [], color=st.INDIGO, marker='o', mec='white', label='LRG as proposed')], fontsize=7.2, loc='lower right')
    a1.set_title('Who gets the party funds')
    st.panel_label(a1, 'a')
    yrs = S.YEARS
    for k, colr, lab in [('W0_missao', st.MUTED, 'status quo'), ('V_missao', st.INDIGO, 'LRG as proposed')]:
        v = 100 * g(k, 'fp_missao')                       # (T, R)
        a2.plot(yrs, np.nanmedian(v, 1), color=colr, lw=2, label=lab)
        a2.fill_between(yrs, np.nanpercentile(v, 5, 1), np.nanpercentile(v, 95, 1), color=colr, alpha=0.14, lw=0)
    a2.set_xlim(2025, 2036); a2.set_ylim(0, None)
    a2.set_ylabel('New party’s share of the Fundo Partidário (%)')
    a2.set_title('A new party with 3% of the vote')
    a2.legend(fontsize=7.2, loc='lower right')
    st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=1.6)
    st.save(fig, 'fig_parties')


# =========================================================================== doses of the FPM tranche
def fig_tranche():
    fig, ax = plt.subplots(figsize=(W * 0.62, 3.4))
    tr = [(2.5, 'F_t025'), (5, 'F_t050'), (10, 'F01000'), (20, 'F_t200')]
    xs = [t for t, _ in tr]
    base = g('F00000', 'eff_comp'); basep = g('F00000', 'effpw_comp')
    e = [med(g(k, 'eff_comp') - base) for _, k in tr]
    ep = [med(g(k, 'effpw_comp') - basep) for _, k in tr]
    lo = [pct(g(k, 'eff_comp') - base, 5) for _, k in tr]; hi = [pct(g(k, 'eff_comp') - base, 95) for _, k in tr]
    ax.fill_between(xs, lo, hi, color=st.GOLD, alpha=0.18, lw=0)
    ax.plot(xs, e, 'o-', color=st.GOLD_DK, label='average municipality (5–95%)', mec='white')
    ax.plot(xs, ep, 's--', color=st.INDIGO, label='weighted by population', mec='white')
    for x_, (_, k), y_ in zip(xs, tr, hi):
        ax.annotate(f"{100 * med(g(k, 'money_losers')):.0f}% lose\nmoney", (x_, y_), xytext=(0, 5), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7, color=st.INK2)
    ax.set_xscale('log'); ax.set_xticks(xs); ax.set_xticklabels([f'{t:g}%' for t in xs])
    ax.xaxis.set_minor_locator(NullLocator()); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(xs[0] / 1.35, xs[-1] * 1.35)
    ax.set_ylim(min(min(lo), min(ep)) - 0.01, max(hi) * 1.32)
    ax.set_xlabel('Share of the FPM paid by points'); ax.set_ylabel('Change in the six indicators (SD)')
    ax.legend(loc='upper left', fontsize=7.2)
    st.save(fig, 'fig_tranche')


# =========================================================================== the ban: deterrence against execution, intensity
def fig_bans():
    te = T5['threat_exec']['main']; ints = T5['intensity']
    fig = plt.figure(figsize=(W, 6.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], width_ratios=[1.1, 1.0], hspace=0.6, wspace=0.42)
    a1 = fig.add_subplot(gs[0, :]); a2 = fig.add_subplot(gs[1, 0]); a3 = fig.add_subplot(gs[1, 1])
    # (a) levels: five designs, real effect and effort channel
    rows = [('F11111', 'As proposed'), ('AP_th', 'Threatened, never executed'),
            ('AP_ex', 'Executed, not anticipated'), ('AP_nb', 'No bans for results'),
            ('F01111', 'No performance sanctions')]
    for i, (k, lab) in enumerate(rows):
        y = len(rows) - 1 - i
        e = g(k, 'eff_comp'); ef = g(k, 'ch_eff')
        interval(a1, med(e), y + 0.14, pct(e, 5), pct(e, 95), st.INDIGO, ms=6)
        interval(a1, med(ef), y - 0.16, pct(ef, 5), pct(ef, 95), st.PERI, ms=5.5, marker='s')
        a1.text(pct(e, 95) + 0.004, y + 0.14, f'{med(e):.3f}', va='center', fontsize=7.4, color=st.INDIGO)
        a1.text(pct(ef, 95) + 0.004, y - 0.16, f'{med(ef):.3f}', va='center', fontsize=7.4, color=st.PERI)
    a1.set_yticks(range(len(rows))); a1.set_yticklabels([l for _, l in rows][::-1], fontsize=8)
    st.zero_line(a1, lw=0.8)
    a1.set_xlabel('Effect against the status quo, 2029–36 (SD, average of the six indicators)')
    a1.set_title('The LRG with and without the ban for results')
    a1.legend(handles=[Line2D([], [], color=st.INDIGO, marker='o', mec='white', label='real effect'),
                       Line2D([], [], color=st.PERI, marker='s', mec='white', label='of which: effort')],
              fontsize=7.4, loc='lower right', ncol=2, bbox_to_anchor=(1.0, 1.0), borderaxespad=0.2)
    clean_x(a1)
    st.panel_label(a1, 'a')
    # (b) decomposition of what the ban adds
    comp = [('deterrence', 'Deterrence:\nthreat alone'), ('execution', 'Execution:\nbans alone'),
            ('interaction', 'Interaction'), ('ban_total', 'Ban as\nproposed')]
    x = np.arange(len(comp))
    for j, (o, colr, lab) in enumerate([('eff', st.INDIGO, 'real effect'), ('effort', st.PERI, 'effort')]):
        d_ = te['decomp'][o]
        vals = [d_[k]['med'] for k, _ in comp]; lo = [d_[k]['p5'] for k, _ in comp]; hi = [d_[k]['p95'] for k, _ in comp]
        xx = x + (j - 0.5) * 0.36
        a2.bar(xx, vals, width=0.34, color=colr, label=lab)
        for a_, l_, h_ in zip(xx, lo, hi):
            a2.plot([a_, a_], [l_, h_], color=st.INK2, lw=0.9)
    st.zero_line(a2, axis='y', lw=0.8)
    a2.set_xticks(x); a2.set_xticklabels([l for _, l in comp], fontsize=7.4)
    a2.set_ylabel('SD, against no bans for results'); clean_y(a2)
    a2.set_title('What the ban adds')
    a2.legend(fontsize=7.2, loc='lower right')
    st.panel_label(a2, 'b')
    # (c) intensity of the threat
    labs = ['0', '0.5', '1', '2', '4', '8']
    xs = np.array([0.25, 0.5, 1, 2, 4, 8])
    for key, colr, mk, lab in [('lrg', st.INDIGO, 'o', 'LRG as proposed'), ('alone', st.PLUM, 's', 'sanctions alone')]:
        ys = [ints[l_][key]['vs_x1']['med'] if ints.get(l_, {}).get(key) else np.nan for l_ in labs]
        lo = [ints[l_][key]['vs_x1']['p5'] if ints.get(l_, {}).get(key) else np.nan for l_ in labs]
        hi = [ints[l_][key]['vs_x1']['p95'] if ints.get(l_, {}).get(key) else np.nan for l_ in labs]
        a3.fill_between(xs, lo, hi, color=colr, alpha=0.12, lw=0)
        a3.plot(xs, ys, marker=mk, color=colr, label=lab, mec='white', ms=5.5)
    st.zero_line(a3, axis='y', lw=0.8)
    a3.set_xscale('log', base=2); a3.set_xticks(xs); a3.set_xticklabels(['×0'] + [f'×{l}' for l in labs[1:]])
    a3.xaxis.set_minor_locator(NullLocator())
    sal = [ints[l_]['salary_equiv']['med'] for l_ in labs]
    for x_, s_ in zip(xs[1:], sal[1:]):
        a3.text(x_, 1.0, f'{s_:.1f}', transform=a3.get_xaxis_transform(), ha='center', va='bottom', fontsize=6.6, color=st.MUTED)
    a3.text(0.25, 1.0, 'salaries:', transform=a3.get_xaxis_transform(), ha='center', va='bottom', fontsize=6.6, color=st.MUTED)
    a3.set_xlabel('Weight of a ban (× calibrated)')
    a3.set_ylabel('Real effect against ×1 (SD)')
    a3.set_title('Intensity of the threat', pad=16)
    a3.legend(fontsize=7.2, loc='lower right')
    st.panel_label(a3, 'c', y=1.12)
    st.save(fig, 'fig_bans')


# =========================================================================== complementarity
def fig_complement():
    CA = T5['complementarity']['A']; CD = (T5['complementarity'] or {}).get('D')
    fig = plt.figure(figsize=(W, 5.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1.0], hspace=0.62)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1])
    # (a) the marginal effect of sanctions in each of the 16 configurations of the other instruments
    ctx = CA['S']['contexts']
    keys = sorted(ctx, key=lambda k: (k.count('-') * -1, k))
    keys = sorted(ctx, key=lambda k: (4 - k.count('-'), ('F' in k), ('A' in k), k))
    x = np.arange(len(keys))
    for j, (CC, colr, lab, off) in enumerate([(CA, st.PLUM, 'scenario A (η = 0)', -0.13), (CD, st.INDIGO, 'scenario D (η = 0.75)', 0.13)]):
        if not CC:
            continue
        cx = CC['S']['contexts']
        for i, k in enumerate(keys):
            q = cx[k]['eff']
            interval(a1, i + off, q['med'], q['p5'], q['p95'], colr, horizontal=False, ms=4.6, lw=1.2)
        a1.plot([], [], color=colr, marker='o', label=lab)
    for i, k in enumerate(keys):
        if 'F' in k:
            a1.axvspan(i - 0.5, i + 0.5, color=st.GOLD_PAL, alpha=0.10, lw=0)
    st.zero_line(a1, axis='y', lw=0.8)
    a1.set_xticks(x); a1.set_xticklabels(['none' if set(k) == {'-'} else k.replace('-', '') for k in keys], fontsize=7, rotation=0)
    a1.set_xlim(-0.6, len(keys) - 0.4)
    a1.set_ylabel('Real effect of adding\nsanctions (SD)')
    a1.set_xlabel('Other instruments already in place (F tranche, A amendments, C commissioners, P party funds; shaded: with the tranche)', fontsize=7.6)
    a1.set_title('Sanctions add less where the tranche already presses')
    a1.legend(fontsize=7.2, loc='upper right', ncol=2)
    clean_y(a1)
    st.panel_label(a1, 'a')
    # (b) every instrument: marginal effect by number of other instruments, relative to its effect alone
    for j, p in enumerate(PILL):
        cx = CA[p]['contexts']
        by_n = {}
        for k, v in cx.items():
            by_n.setdefault(4 - k.count('-'), []).append(v['eff']['med'])
        ns = sorted(by_n)
        alone = by_n[0][0]
        a2.plot(ns, [np.mean(by_n[n_]) for n_ in ns], marker='o', color=PILL_COL[p], label=PILL_NAMES[p], mec='white', ms=6)
    st.zero_line(a2, axis='y', lw=0.8)
    a2.set_xticks([0, 1, 2, 3, 4]); a2.set_xticklabels(['alone', '1 other', '2 others', '3 others', 'all others'])
    a2.set_ylabel('Average real effect of\nadding it (SD)')
    a2.set_title('Every instrument, by how many others are in place (scenario A)')
    a2.legend(fontsize=7.0, loc='upper center', ncol=5, bbox_to_anchor=(0.5, -0.17), columnspacing=1.0, handlelength=1.6)
    clean_y(a2)
    st.panel_label(a2, 'b')
    st.save(fig, 'fig_complement')


# =========================================================================== what would it take
def fig_plausibility():
    WW = T5['what_would_it_take']; SV = T5['saturation_variants']
    rows = [('dm1', 'Calibrated model', None), ('dm15', 'Effort response ×1.5', None), ('dm2', 'Effort response ×2', None),
            ('dm3', 'Effort response ×3', None), ('km2', 'Weight of money ×2', None), ('km3', 'Weight of money ×3', None),
            ('cap2', 'Stronger saturation (cap 2), recalibrated', 'sat'), ('cap8', 'Weaker saturation (cap 8), recalibrated', 'sat'),
            ('lin', 'No saturation (linear), recalibrated', 'sat')]
    fig = plt.figure(figsize=(W, 4.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 0.85, 0.75], wspace=0.1)
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1], sharey=a1); a3 = fig.add_subplot(gs[2], sharey=a1)
    y = np.arange(len(rows))[::-1]
    ref = WW['dm1']['lrg']['eff']['med']
    for yi, (k, lab, kind) in zip(y, rows):
        r = (SV.get(k, {}) if kind == 'sat' else WW.get(k, {})).get('lrg')
        if not r:
            continue
        interval(a1, r['eff']['med'], yi + 0.13, r['eff']['p5'], r['eff']['p95'], st.INDIGO, ms=5.5)
        interval(a1, r['effort']['med'], yi - 0.15, r['effort']['p5'], r['effort']['p95'], st.PERI, ms=5, marker='s')
    a1.axvline(ref, color=st.INDIGO, lw=0.8, ls=(0, (3, 2)), alpha=0.7)
    a1.set_yticks(y); a1.set_yticklabels([l for _, l, _ in rows], fontsize=7.8)
    a1.axhline(y[5] - 0.5, color=st.GRID, lw=0.9); a1.axhline(y[0] - 0.5, color=st.GRID, lw=0.9)
    a1.set_xlabel('LRG as proposed, 2029–36 (SD)')
    a1.set_title('The response of the LRG', fontsize=9.2)
    a1.legend(handles=[Line2D([], [], color=st.INDIGO, marker='o', mec='white', label='real effect'),
                       Line2D([], [], color=st.PERI, marker='s', mec='white', label='effort')], fontsize=7.0, loc='upper right')
    clean_x(a1)
    st.panel_label(a1, 'a')
    # (b) the evidence: likelihood relative to the calibrated model (saturation: Bayes factor from the recalibration)
    ev0 = SV.get('main', {}).get('log_evidence')
    for yi, (k, lab, kind) in zip(y, rows):
        if kind == 'sat':
            le = SV.get(k, {}).get('log_evidence')
            v = math.exp(le - ev0) if (le is not None and ev0 is not None) else np.nan
        else:
            v = WW.get(k, {}).get('lr_posterior', np.nan)
        a2.barh(yi, v, color=st.TEAL if v >= 1 / 3 else st.PLUM, height=0.56)
        a2.text(v - 0.03, yi, f'{v:.2f}', va='center', ha='right', fontsize=7.2, color='white', fontweight='semibold')
    a2.axvline(1, color=st.INK2, lw=0.8, zorder=0.5)
    a2.axvline(1 / 3, color=st.PLUM, lw=0.8, ls=(0, (3, 2)), zorder=0.5)
    a2.set_xlim(0, 1.45)
    plt.setp(a2.get_yticklabels(), visible=False)
    a2.set_xlabel('Likelihood of the evidence,\nrelative to the\ncalibrated model')
    a2.set_title('What the evidence says', fontsize=9.2)
    clean_x(a2)
    st.panel_label(a2, 'b')
    # (c) the binding moment: Ceara's rule alone (target 0.06 pupil SD)
    tg = WW['dm1']['M1']['target']; se = WW['dm1']['M1']['se']
    a3.axvspan(tg - 1.96 * se, tg + 1.96 * se, color=st.GOLD_PAL, alpha=0.22, lw=0)
    a3.axvline(tg, color=st.GOLD_DK, lw=1.0)
    for yi, (k, lab, kind) in zip(y, rows):
        if kind == 'sat':
            continue
        m1 = WW.get(k, {}).get('M1')
        if m1:
            interval(a3, m1['med'], yi, m1['p5'], m1['p95'], st.INK2, ms=4.6, lw=1.2)
    plt.setp(a3.get_yticklabels(), visible=False)
    a3.set_xlabel('Ceará’s rule alone:\nimplied effect\n(pupil SD)')
    a3.set_title('Ceará, implied', fontsize=9.2)
    clean_x(a3)
    st.panel_label(a3, 'c')
    st.save(fig, 'fig_plausibility')


# =========================================================================== Sobol
def fig_sobol():
    s = pd.read_csv(OUT + '/sobol.csv')
    outs = [('eff_true', 'True\neffect'), ('eff_pw', 'True effect\n(pop.-\nweighted)'), ('gap_meas', 'Measured\nminus true'),
            ('unscored', 'Unscored\ntasks'), ('theta', 'Mayors’\ncompetence'), ('nb_ratio', 'Share kept\nwithout\nbans'),
            ('ns_ratio', 'Share kept\nwithout\nsanctions'), ('threat_gain', 'Deterrence\nof bans')]
    outs = [o for o in outs if o[0] in set(s.output)]
    groups = list(dict.fromkeys(s.group))
    mat = np.array([[s[(s.output == o) & (s.group == gname)].ST.iloc[0] for o, _ in outs] for gname in groups])
    mat = np.clip(mat, 0, 1)
    order = np.argsort(-mat.max(1))
    mat = mat[order]; groups = [groups[i] for i in order]
    fig, ax = plt.subplots(figsize=(W, 0.27 * len(groups) + 1.3))
    im = ax.imshow(mat, cmap=st.CMAP_SEQ, vmin=0, vmax=1, aspect='auto')
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if mat[i, j] >= 0.05:
                ax.text(j, i, f'{mat[i, j]:.2f}', ha='center', va='center', fontsize=7,
                        color='white' if mat[i, j] > 0.5 else st.INK)
    ax.set_xticks(range(len(outs))); ax.set_xticklabels([o for _, o in outs], fontsize=7.2)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(groups))); ax.set_yticklabels(groups, fontsize=7.6)
    ax.tick_params(length=0); ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.ax.tick_params(labelsize=7); cb.outline.set_visible(False)
    cb.set_label('Total-effect Sobol index', fontsize=7.5)
    st.save(fig, 'fig_sobol')


# =========================================================================== pilot
def fig_power():
    PW = json.load(open(OUT + '/pilot_power.json'))
    NS = PW['N']
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.6), gridspec_kw={'wspace': 0.28})
    for ax, k, lab in [(axs[0], 'composite', 'Composite of four indicators'), (axs[1], 'lit', 'Literacy')]:
        ax.plot(NS, PW['mde_main'][k], 'o-', color=st.INDIGO, label='Main effect (incentive or assistance)', mec='white')
        ax.plot(NS, PW['mde_inter'][k], 's--', color=st.MUTED, label='Interaction', mec='white')
        cols = {'incentive (effort part of the FPM tranche), two years': (st.GOLD_DK, '-'),
                'technical assistance (commissioners), two years': (st.TEAL, '-'),
                'technical assistance (commissioners), four years': (st.TEAL, '--')}
        for j, (nm, v) in enumerate(PW.get('sim_effects_2yr', {}).items()):
            if k in v:
                col_, ls_ = cols.get(nm, (st.GRAYBAR, '-'))
                ax.axhline(v[k][1], color=col_, lw=1.5, ls=ls_, label='Simulated: ' + nm)
                xe = NS[-1] * (1.2 + 0.14 * j)
                ax.errorbar([xe], [v[k][1]], yerr=[[v[k][1] - v[k][0]], [v[k][2] - v[k][1]]], fmt='o', ms=4,
                            color=col_, ecolor=col_, elinewidth=1.4, capsize=2.5)
        ax.set_xscale('log'); ax.set_xticks(NS); ax.set_xticklabels([f'{n:,}' for n in NS], fontsize=7)
        ax.set_xlim(NS[0] / 1.15, NS[-1] * 1.75)
        ax.xaxis.set_minor_locator(NullLocator()); ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel('Municipalities in the pilot (four arms)'); ax.set_ylabel('Minimum detectable effect (SD)')
        ax.set_title(lab); ax.set_ylim(bottom=0)
    axs[0].legend(loc='upper center', bbox_to_anchor=(1.12, -0.22), ncol=2, fontsize=7.0)
    st.panel_label(axs[0], 'a'); st.panel_label(axs[1], 'b')
    st.save(fig, 'fig_power')


# =========================================================================== appendix: a personal bonus
def fig_bonus():
    fig, ax = plt.subplots(figsize=(W * 0.66, 3.4))
    ks = [('B025', '0.25'), ('B05', '0.5'), ('B10', '1')]
    base = g('F00000', 'eff_comp'); basem = g('F00000', 'meas_comp')
    for i, (k, lab) in enumerate(ks):
        e = g(k, 'eff_comp') - base; m_ = g(k, 'meas_comp') - basem
        ax.bar(i, med(e), color=st.INDIGO, width=0.55, label='real' if i == 0 else None)
        ax.bar(i, med(m_) - med(e), bottom=med(e), color='white', edgecolor=st.GOLD_DK, hatch='////', lw=0.8, width=0.55,
               label='cosmetic' if i == 0 else None)
        ax.text(i, med(m_) + 0.003, f"R$ {med(g(k, 'bonus_cost')):.2f} bn a year", ha='center', fontsize=7.4, color=st.INK2)
    for k_, lab_, ls_ in [('F10000', 'sanctions alone (real)', (0, (4, 2))), ('F01000', 'FPM tranche alone (real)', (0, (1, 2)))]:
        v = med(g(k_, 'eff_comp') - base)
        ax.axhline(v, color=st.PLUM if k_ == 'F10000' else st.GOLD_DK, ls=ls_, lw=1.0)
        ax.text(2.42, v, lab_, va='bottom', ha='right', fontsize=7, color=st.INK2)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([f'{l} salary per SD' for _, l in ks])
    ax.set_ylabel('Change in the six indicators, 2029–36 (SD)')
    ax.legend(loc='upper left', fontsize=7.4)
    clean_y(ax)
    st.save(fig, 'fig_bonus')


# =========================================================================== supplementary figures
def fig_whobanned():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 3.3), gridspec_kw={'width_ratios': [1.2, 1]}, sharey=True)
    for ax, key, labs, title in [(a1, 'bans_cls_per100', CLS, 'By population'), (a2, 'bans_reg_per100', REGN, 'By region')]:
        x = np.arange(len(labs))
        v = g(AP, key); wv = g(AP, 'wrong_cls') if key == 'bans_cls_per100' else None
        m_ = np.nanmedian(v, 0); lo = np.nanpercentile(v, 5, 0); hi = np.nanpercentile(v, 95, 0)
        ax.bar(x, m_, width=0.6, color=st.INDIGO)
        if wv is not None:
            ax.bar(x, m_ * np.nanmedian(wv, 0), width=0.6, color=st.PLUM)
        for a_, l_, h_ in zip(x, lo, hi):
            ax.plot([a_, a_], [l_, h_], color=st.INK2, lw=0.9)
        ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=7, rotation=30, ha='right', rotation_mode='anchor')
        clean_y(ax); ax.set_title(title)
    a1.set_ylabel('Mayors banned per 100, per mandate')
    a1.legend(handles=[Patch(color=st.PLUM, label='wrongful'), Patch(color=st.INDIGO, label='other')], fontsize=7.2, loc='upper right')
    st.panel_label(a1, 'a'); st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=1.5)
    st.save(fig, 'fig_whobanned')


def fig_selection():
    designs = [('F00001', 'Party funds alone'), ('F10000', 'Sanctions alone'), ('F00100', 'Tied amendments alone'),
               ('AP_nb', 'As proposed, no bans'), ('AP_th', 'As proposed, bans never executed'), (AP, 'As proposed')]
    designs = [d_ for d_ in designs if has(d_[0])]
    fig, axes = plt.subplots(1, 3, figsize=(W, 3.2))
    specs = [('thetapw_2033', 'Competence of mayors\nin office, 2033–36\n(SD, pop.-weighted)', 1),
             ('turnover', 'Change of ruling party\nat each election (pp)', 100),
             ('incumb_win', 'Re-election of\nincumbents who run (pp)', 100)]
    for ax, (mk, title, sc) in zip(axes, specs):
        y = np.arange(len(designs))[::-1]
        for yi, (k, lab) in zip(y, designs):
            v = sc * (g(k, mk) - g('W0', mk))
            interval(ax, med(v), yi, pct(v, 5), pct(v, 95), st.INDIGO if k == AP else st.INK2)
        st.zero_line(ax, lw=0.8)
        ax.set_yticks(y); ax.set_yticklabels([l for _, l in designs] if ax is axes[0] else [], fontsize=7.2)
        ax.set_title(title, fontsize=8.2); clean_x(ax); ax.tick_params(axis='x', labelsize=7)
    plt.tight_layout(w_pad=0.8)
    st.save(fig, 'fig_selection')


def fig_mei():
    me = g(AP, 'mei')                                   # (R, 7, 6)
    srcs = [(0, 'Elections (status quo)', st.GRAYBAR), (1, 'Published score', st.MUTED), (2, 'Sanctions', PILL_COL['S']),
            (3, 'FPM tranche', PILL_COL['F']), (4, 'Tied amendments', PILL_COL['A']), (5, 'Party funds', PILL_COL['P'])]
    fig, ax = plt.subplots(figsize=(W, 3.6))
    x = np.arange(6); w = 0.13
    for j, (si, lab, col) in enumerate(srcs):
        vals = [med(me[:, si, ci]) for ci in range(6)]
        ax.bar(x + (j - 2.5) * w, vals, width=w * 0.92, color=col, label=lab)
    ax.set_yscale('log')
    ax.set_xticks(x); ax.set_xticklabels(CLS)
    ax.set_xlabel('Municipal population'); ax.set_ylabel('Incentive on an indicator\n(alert units, log scale)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=7.4)
    clean_y(ax)
    st.save(fig, 'fig_mei')


def fig_families():
    """Supplement: the main ratios and the ban decomposition in every scenario family (first 120 draws)."""
    fams = [(t, l) for t, l in [('mainS', 'Main (first 120 draws)'), ('cv_wide', 'Calibration: wider priors'),
                                ('cv_noCE', 'Calibration: no Ceará'), ('cv_noRD', 'Calibration: no discontinuities'),
                                ('cv_noEL', 'Calibration: no electoral return'), ('cv_noFPM', 'Calibration: no FPM brackets'),
                                ('cv_trans50', 'Calibration: Ceará ×2'), ('cv_indep', 'Calibration: independent targets'),
                                ('cv_v3', 'Calibration: earlier likelihood'), ('cv_cap2', 'Saturation cap 2 (recal.)'),
                                ('cv_cap8', 'Saturation cap 8 (recal.)'), ('cv_lin', 'No saturation (recal.)'),
                                ('sc_eN', 'Voters’ reward ×0'), ('sc_eH2', 'Voters’ reward ×2'), ('sc_eH4', 'Voters’ reward ×4'),
                                ('sc_m0', 'No manipulation'), ('sc_m0s', 'No manipulation, redirected'), ('sc_mL', 'Manipulation ×0.5'),
                                ('sc_mH', 'Manipulation ×1.5'), ('sc_mA', 'Audits'), ('sc_mAs', 'Audits, redirected'),
                                ('sc_iB', 'Implementation η = 0.25'), ('sc_iC', 'Implementation η = 0.5'), ('sc_iD', 'Implementation η = 0.75'),
                                ('sc_lameM', 'Banned mayors respond to money'), ('sc_iDlameM', '… and η = 0.75')] if t in SC]
    fam = T5['threat_exec'].get('families', {})
    fig, axs = plt.subplots(1, 2, figsize=(W, 0.22 * len(fams) + 1.4), sharey=True, gridspec_kw={'wspace': 0.08})
    y = np.arange(len(fams))[::-1]
    for yi, (t, lab) in zip(y, fams):
        r = SC[t]
        for k_, colr, off in [('AP_nb', st.INDIGO, 0.14), ('F01111', st.GOLD_DK, -0.14)]:
            q = (r.get(k_) or {}).get('ratio_to_AP')
            if q:
                interval(axs[0], 100 * q['med'], yi + off, 100 * q['p5'], 100 * q['p95'], colr, ms=4.3, lw=1.1)
        f_ = fam.get(t) if t != 'mainS' else {'eff': T5['threat_exec']['mainS']['decomp']['eff']}
        if f_:
            for k_, colr, off in [('deterrence', st.TEAL, 0.14), ('execution', st.PLUM, -0.14)]:
                q = f_['eff'][k_]
                interval(axs[1], q['med'], yi + off, q['p5'], q['p95'], colr, ms=4.3, lw=1.1)
    axs[0].axvline(100, color=st.INK2, lw=0.8, ls=(0, (3, 2)))
    st.zero_line(axs[1], lw=0.8)
    axs[0].set_yticks(y); axs[0].set_yticklabels([l for _, l in fams], fontsize=7)
    axs[0].set_xlabel('% of the LRG’s real effect kept')
    axs[1].set_xlabel('SD, against no bans for results')
    axs[0].set_title('Without bans / without sanctions', fontsize=8.6)
    axs[1].set_title('Deterrence and execution of bans', fontsize=8.6)
    axs[0].legend(handles=[Line2D([], [], color=st.INDIGO, marker='o', ms=4.3, lw=1.1, label='no bans for results'),
                           Line2D([], [], color=st.GOLD_DK, marker='o', ms=4.3, lw=1.1, label='no performance sanctions')],
                  fontsize=6.8, loc='upper center', bbox_to_anchor=(0.5, -0.095), ncol=1, frameon=False)
    axs[1].legend(handles=[Line2D([], [], color=st.TEAL, marker='o', ms=4.3, lw=1.1, label='deterrence (threat alone)'),
                           Line2D([], [], color=st.PLUM, marker='o', ms=4.3, lw=1.1, label='execution (bans alone)')],
                  fontsize=6.8, loc='upper center', bbox_to_anchor=(0.5, -0.095), ncol=1, frameon=False)
    for a in axs:
        clean_x(a)
    st.save(fig, 'fig_families')


def fig_saturation():
    """Supplement: the effort rule under four saturations and the incentives the LRG creates."""
    SAT = T5.get('saturation', {})
    fig, ax = plt.subplots(figsize=(W * 0.66, 3.3))
    I = np.linspace(0, 4, 200)
    for cap, colr, lab in [(2.0, st.PLUM, 'cap 2'), (4.0, st.INDIGO, 'cap 4 (calibrated model)'), (8.0, st.TEAL, 'cap 8'), (np.inf, st.GOLD_DK, 'linear')]:
        ax.plot(I, I / (1 + I / cap), color=colr, lw=2 if cap == 4.0 else 1.4, label=lab)
    for key, lab in [('I_elect', 'elections'), ('I_others', '+ money, amendments,\nparty funds'), ('I_sanctions', '+ sanctions')]:
        pass
    if SAT:
        ie = SAT['I_elect']['med']; io = SAT['I_others']['med']; isn = SAT['I_sanctions']['med']
        lo, hi = sorted([ie + isn, ie + io])
        marks = [(ie, 'elections'), (ie + isn, 'elections +\nsanctions'), (ie + io, 'elections +\nother\ninstruments'),
                 (ie + io + isn, 'LRG as\nproposed')]
        for x_, lab in marks:
            ax.axvline(x_, color=st.MUTED, lw=0.8, ls=(0, (2, 2)))
            left_of = abs(x_ - lo) < 1e-9 and hi - lo < 0.5      # of two close lines, label the left one on its left, lower down
            ax.text(x_ - 0.05 if left_of else x_ + 0.05, 3.35 if left_of else 3.95, lab, fontsize=6.4, color=st.INK2,
                    ha='right' if left_of else 'left', va='top')
    ax.set_ylim(-0.1, 4.2)
    ax.set_xlabel('Marginal expected incentive (alert units, municipal average)')
    ax.set_ylabel('Effort per unit of responsiveness')
    ax.legend(fontsize=7, loc='lower right')
    st.save(fig, 'fig_saturation')


if __name__ == '__main__':
    which = sys.argv[1:] or ['fig_sanctions', 'fig_effects', 'fig_shapley', 'fig_channels', 'fig_money', 'fig_parties',
                             'fig_tranche', 'fig_bans', 'fig_complement', 'fig_plausibility', 'fig_sobol', 'fig_power',
                             'fig_bonus', 'fig_whobanned', 'fig_selection', 'fig_mei', 'fig_families', 'fig_saturation']
    for w in which:
        globals()[w]()
        print('saved', w)
