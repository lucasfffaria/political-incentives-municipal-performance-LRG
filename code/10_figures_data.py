"""
10_figures_data.py -- figures that use real data only (no simulation).
fig_maps        Brazil today: six municipal maps
fig_variance    what each indicator measures (variance shares) and how reliable a one-year change is
fig_validity    two official sewage measures; population denominators
fig_amendments  what amendments buy, where they go, to whom
fig_partyday1   party funds on day one, and the Chamber arithmetic
fig_viability   own-tax share by size and the merger exercise
usage: python 10_figures_data.py [names...]
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
sys.path.insert(0, _ROOT + '/code')
import lrgstyle as st

st.setup()
DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'; TAB = _ROOT + '/tables'
_os.makedirs(_ROOT + '/figures', exist_ok=True)
b = pd.read_csv(DER + '/municipios_base.csv')
LAB = ['<5k', '5–10k', '10–20k', '20–50k', '50–100k', '>100k']


def geo():
    g = gpd.read_file(_ROOT + '/data/raw/geo/geojs-100-mun.json')
    g['cod_ibge'] = g.id.astype(int)
    g = g.merge(b, on='cod_ibge', how='left').to_crs(5880)
    return g


def fig_maps():
    g = geo()
    g['jobs'] = g.K1_formal_jobs_2024
    g['sewer'] = 100 * g.sh_sewer_census
    g['pix_pc'] = g.pix_plan_2025 / g.pop2024
    fed = pd.read_csv(DER + '/federalism_muni.csv').set_index('cod_ibge')
    g['owntax'] = 100 * g.cod_ibge.map(fed.own_tax_hat)
    panels = [('K3_literacy_2024', 'Literacy at the end of 2nd grade\n2024, % of children', [30, 50, 60, 70, 80], 'seq', False),
              ('sewer', 'Sewer connection\n2022 Census, % of households', [5, 20, 40, 60, 80], 'seq', False),
              ('hom_rate_2022', 'Homicides\n2022, per 100,000 inhabitants', [5, 15, 30, 50, 80], 'neg', False),
              ('jobs', 'Private formal jobs\n2024, per 100 inhabitants', [3, 6, 10, 15, 25], 'seq', False),
              ('owntax', 'Own taxes\n2024, % of current revenue', [5, 7.5, 10, 15, 25], 'seq', True),
              ('pix_pc', 'Discretionary amendments\n2025, R$ per capita', [1, 25, 75, 150, 300], 'seq', False)]
    fig, axes = plt.subplots(2, 3, figsize=(7.3, 6.2))
    seqc = ['#f3f4ff', '#c8cdfb', '#9098e9', '#5c63c4', '#3f42a8', '#1b1c56']        # palette: periwinkle to indigo
    negc = ['#fff8e0', '#ffe48d', '#f0bf00', '#c99400', '#8f520d', '#4f2c06']        # palette: gold to bronze (more is worse)
    for ax, (col, title, brks, kind, imputed) in zip(axes.ravel(), panels):
        cols = seqc if kind == 'seq' else negc
        cmap = mcolors.ListedColormap(cols)
        norm_ = mcolors.BoundaryNorm([-1e9] + brks + [1e9], cmap.N)
        g.plot(column=col, ax=ax, cmap=cmap, norm=norm_, linewidth=0, missing_kwds={'color': '#e4e6ee'}, rasterized=True)
        ax.set_axis_off()
        ax.set_title(title, fontsize=8.0, loc='left', color=st.INK, pad=2, linespacing=1.25)
        handles = [Patch(facecolor=cols[0], label=f'< {brks[0]:g}')] + \
                  [Patch(facecolor=cols[i + 1], label=f'{brks[i]:g}–{brks[i + 1]:g}') for i in range(len(brks) - 1)] + \
                  [Patch(facecolor=cols[-1], label=f'≥ {brks[-1]:g}')]
        ax.legend(handles=handles, loc='lower left', fontsize=6.2, handlelength=0.9, handleheight=0.8,
                  borderaxespad=0.0, bbox_to_anchor=(0.0, -0.02), labelspacing=0.25)
    plt.subplots_adjust(wspace=0.02, hspace=0.12)
    st.save(fig, 'fig_maps')


def fig_variance():
    P = json.load(open(OUT + '/indicator_properties.json'))
    names = [('K1_formal_jobs_log', 'Formal jobs (K1)'), ('K2_private_va_share', 'Non-public value added (K2)'),
             ('K4_daycare_coverage', 'Daycare/preschool (K4)'), ('K6_sewage_coverage', 'Sewage, self-reported (K6)'),
             ('E_ideb', 'IDEB (book scorecard)'), ('K3_literacy', 'Literacy, 2nd grade (K3)'),
             ('K7_homicide_rate', 'Homicide rate (K7)')]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.3, 3.6), gridspec_kw={'width_ratios': [1.05, 1]})
    y = np.arange(len(names))[::-1]
    for yi, (k, lab) in zip(y, names):
        r = P[k]
        # smallest municipalities (<5k): signal vs noise, and term share
        if 'share_noise_by_class' in r:
            noise = r['share_noise_by_class'][0]; term = r['share_term_by_class'][0]
        else:
            noise = 1 - r['rel_level_by_class'][0]; term = 0.014 * (1 - noise)
        place = 1 - noise - term
        a1.barh(yi, place, color=st.GRAYBAR, height=0.62, edgecolor='white', linewidth=1)
        a1.barh(yi, term, left=place, color=st.BLUE, height=0.62, edgecolor='white', linewidth=1)
        a1.barh(yi, noise, left=place + term, color=st.GOLD, height=0.62, edgecolor='white', linewidth=1)
        a1.text(1.01, yi, f'{100 * noise:.0f}%', va='center', fontsize=7.5, color=st.INK2)
    a1.set_yticks(y); a1.set_yticklabels([n for _, n in names], fontsize=8)
    a1.set_xlim(0, 1.12); a1.set_xticks([0, 0.25, 0.5, 0.75, 1]); a1.set_xticklabels(['0', '25', '50', '75', '100%'])
    a1.grid(axis='y', visible=False)
    a1.set_title('Municipalities under 5,000 inhabitants', fontsize=9)
    a1.legend(handles=[Patch(color=st.GRAYBAR, label='persistent place'), Patch(color=st.BLUE, label='mayoral term'),
                       Patch(color=st.GOLD, label='noise of one reading')], loc='upper center',
              bbox_to_anchor=(0.45, -0.1), ncol=3, fontsize=7.5, handlelength=1.0)
    st.panel_label(a1, 'a')
    show = [('K1_formal_jobs_log', 'Formal jobs (K1)', st.INDIGO, 'o'), ('K4_daycare_coverage', 'Daycare (K4)', st.GOLD_DK, 's'),
            ('K6_sewage_coverage', 'Sewage, self-reported (K6)', st.TEAL, 'D'), ('E_ideb', 'IDEB', st.PERI, '^'),
            ('K7_homicide_rate', 'Homicides (K7)', st.PLUM, 'v')]
    for k, lab, colr, mk in show:
        r = P[k]
        xs = np.array(r['pop_median_by_class'], float); ys = np.array(r['rel_change_by_class'], float)
        ok = np.isfinite(xs) & np.isfinite(ys)
        a2.plot(xs[ok], ys[ok], color=colr, lw=1.6, marker=mk, ms=4.5, label=lab)
    a2.set_xscale('log'); a2.set_ylim(-0.02, 1.05); a2.set_xlim(1500, 1e6)
    a2.set_xticks([1e3, 1e4, 1e5, 1e6]); a2.set_xticklabels(['1k', '10k', '100k', '1M'])
    a2.set_xlabel('Municipal population (log scale)')
    a2.set_ylabel('Signal share of a one-year change', fontsize=8.5)
    a2.set_title('Reliability of a one-year change, by size class', fontsize=9)
    a2.legend(loc='upper center', fontsize=7.0, bbox_to_anchor=(0.5, -0.22), ncol=2, columnspacing=1.0)
    st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=1.5)
    st.save(fig, 'fig_variance')


def fig_validity():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.3, 3.3))
    ok = b.sewer_snis_2022.notna()
    a1.scatter(100 * b.loc[ok, 'sh_sewer_census'], b.loc[ok, 'sewer_snis_2022'], s=3, color=st.BLUE, alpha=0.35, lw=0)
    a1.plot([0, 100], [0, 100], color=st.INK2, lw=1, ls=(0, (3, 2)))
    a1.set_xlim(0, 100); a1.set_ylim(0, 100)
    a1.set_xlabel('Census 2022: households on a sewer network (%)')
    a1.set_ylabel('SNIS 2022: population served (%)')
    nz = ((~ok) & (b.sh_sewer_census > 0.2)).sum()
    a1.set_title('Two official sewage measures', fontsize=9)
    st.panel_label(a1, 'a')
    pe = (b.pop2021 / b.pop2022 - 1) * 100
    cls = pd.cut(b.pop2022, [0, 5e3, 1e4, 2e4, 5e4, 1e5, np.inf], labels=LAB)
    data = [pe[cls == l].clip(-40, 60).values for l in LAB]
    bp = a2.boxplot(data, vert=True, widths=0.55, showfliers=False, patch_artist=True,
                    medianprops=dict(color=st.INK, lw=1.4), whiskerprops=dict(color=st.MUTED),
                    capprops=dict(color=st.MUTED), boxprops=dict(facecolor=st.TINT, edgecolor=st.INDIGO))
    a2.axhline(0, color=st.INK2, lw=0.9, ls=(0, (3, 2)))
    a2.set_xticklabels(LAB, fontsize=7.5)
    a2.set_ylabel('IBGE 2021 estimate vs 2022 Census (%)')
    a2.set_title('Error of the population denominator', fontsize=9)
    st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=2)
    st.save(fig, 'fig_validity')


def fig_amendments():
    A = json.load(open(OUT + '/amendments.json'))
    ar = pd.read_csv(TAB + '/T_amendments_area.csv')
    tr = {'Urbanismo': 'Urban works', 'Agricultura': 'Agriculture', 'Saúde': 'Health', 'Desporto e Lazer': 'Sport and leisure',
          'Comércio e Serviços': 'Commerce and services', 'Assistência Social': 'Social assistance', 'Educação': 'Education',
          'Not reported': 'Not reported', 'Saneamento': 'Sanitation', 'Cultura': 'Culture', 'Segurança Pública': 'Public security',
          'Gestão Ambiental': 'Environment', 'Transporte': 'Transport', 'Habitação': 'Housing'}
    ar = ar.head(12)
    fig = plt.figure(figsize=(7.3, 4.3))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[1, 1], hspace=0.65, wspace=0.55)
    a1 = fig.add_subplot(gs[:, 0]); a2 = fig.add_subplot(gs[0, 1]); a3 = fig.add_subplot(gs[1, 1])
    yy = np.arange(len(ar))[::-1]
    colors = [st.BRONZE if a in ('Urbanismo', 'Desporto e Lazer') else (st.TEAL if a in ('Saneamento', 'Educação') else st.GRAYBAR) for a in ar.area]
    a1.barh(yy, 100 * ar.share, color=colors, height=0.65)
    for yi, s in zip(yy, ar.share):
        a1.text(100 * s + 0.6, yi, f'{100 * s:.1f}%', va='center', fontsize=7.2, color=st.INK2)
    a1.set_yticks(yy); a1.set_yticklabels([tr.get(a, a) for a in ar.area], fontsize=7.8)
    a1.set_xlim(0, 48); a1.grid(axis='y', visible=False)
    a1.set_xlabel('Share of 2025 discretionary amendments (%)')
    a1.set_title('What the money buys', fontsize=9)
    st.panel_label(a1, 'a')
    pc = A['per_capita_by_size']
    a2.bar(range(6), list(pc.values()), color=st.BLUE, width=0.62)
    a2.set_xticks(range(6)); a2.set_xticklabels(LAB, fontsize=6.8, rotation=35, ha='right', rotation_mode='anchor')
    a2.set_ylabel('R$ per capita', fontsize=8)
    a2.set_title('Where it goes: municipal size', fontsize=9)
    a2.grid(axis='x', visible=False)
    st.panel_label(a2, 'b')
    al = pd.read_csv(TAB + '/T_amendments_alignment.csv', index_col=0).head(8)
    short = {'REPUBLICANOS': 'REP', 'PODEMOS': 'PODE', 'UNIAO': 'UNIÃO'}
    xx = np.arange(len(al))
    a3.bar(xx - 0.18, 100 * al.exp_same_cnt, width=0.36, color=st.GRAYBAR, label='expected')
    a3.bar(xx + 0.18, 100 * al.obs_same, width=0.36, color=st.PLUM, label='observed')
    a3.set_xticks(xx); a3.set_xticklabels([short.get(p, p) for p in al.index], fontsize=6.6, rotation=35, ha='right', rotation_mode='anchor')
    a3.set_ylabel('% to own-party mayors', fontsize=8)
    a3.set_title("To whom: author's own party", fontsize=9)
    a3.set_ylim(0, 60)
    a3.legend(fontsize=6.6, loc='upper left', ncol=2, handlelength=1.0, columnspacing=0.8)
    a3.grid(axis='x', visible=False)
    st.panel_label(a3, 'c')
    st.save(fig, 'fig_amendments')


def fig_partyday1():
    df = pd.read_csv(TAB + '/T_party_funds.csv', index_col=0)
    df = df[df.fp_now > 10].sort_values('fp_now')
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.3, 4.0), gridspec_kw={'width_ratios': [1.35, 1]})
    yy = np.arange(len(df))
    for yi, (p, r) in zip(yy, df.iterrows()):
        colr = st.TEAL if r.fp_lrg > r.fp_now else st.PLUM
        a1.plot([r.fp_now, r.fp_lrg], [yi, yi], color=colr, lw=1.6, alpha=0.8)
        a1.scatter([r.fp_now], [yi], s=22, color=st.GRAYBAR, zorder=3, edgecolor='white', lw=0.6)
        a1.scatter([r.fp_lrg], [yi], s=26, color=colr, zorder=4, edgecolor='white', lw=0.6)
    a1.set_yticks(yy); a1.set_yticklabels(df.index.str.replace('REPUBLICANOS', 'REPUBLIC.'), fontsize=7.6)
    a1.set_xlabel('Fundo Partidário, R$ million per year')
    a1.grid(axis='y', visible=False)
    a1.legend(handles=[Line2D([], [], marker='o', ls='', color=st.GRAYBAR, label='current rule (2025)'),
                       Line2D([], [], marker='o', ls='', color=st.TEAL, label='LRG rule: gains'),
                       Line2D([], [], marker='o', ls='', color=st.PLUM, label='LRG rule: loses')],
              loc='lower right', fontsize=7.2)
    a1.set_title('Day one: mayors × population, no quality weights', fontsize=8.6)
    st.panel_label(a1, 'a')
    J = json.load(open(OUT + '/party_funds.json'))
    s = J['shares']
    cats = ['Six largest\nmunicipal parties', 'Left parties']
    now = [100 * s['big6']['fp_now'], 100 * s['left']['fp_now']]
    lrg = [100 * s['big6']['fp_lrg'], 100 * s['left']['fp_lrg']]
    xx = np.arange(2)
    a2.bar(xx - 0.2, now, width=0.38, color=st.GRAYBAR, label='current rule')
    a2.bar(xx + 0.2, lrg, width=0.38, color=st.BLUE, label='LRG rule')
    for x, v1, v2 in zip(xx, now, lrg):
        a2.text(x - 0.2, v1 + 1.5, f'{v1:.0f}%', ha='center', fontsize=7.5, color=st.INK2)
        a2.text(x + 0.2, v2 + 1.5, f'{v2:.0f}%', ha='center', fontsize=7.5, color=st.INK2)
    a2.set_xticks(xx); a2.set_xticklabels(cats, fontsize=7.8)
    a2.set_ylim(0, 92); a2.set_ylabel('Share of the Fundo Partidário (%)')
    a2.grid(axis='x', visible=False)
    a2.legend(fontsize=7.2, loc='upper right')
    ch = J['chamber']
    a2.set_title(f"Parties that gain hold {ch['seats_parties_gaining']} of 513 seats", fontsize=8.6)
    st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=2)
    st.save(fig, 'fig_partyday1')


def fig_viability():
    fed = pd.read_csv(DER + '/federalism_muni.csv').set_index('cod_ibge')
    bb = b.set_index('cod_ibge').join(fed)
    cls = pd.cut(bb.pop2024, [0, 5e3, 1e4, 2e4, 5e4, 1e5, np.inf], labels=LAB)
    J = json.load(open(OUT + '/federalism.json'))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.3, 3.4), gridspec_kw={'width_ratios': [1.2, 1]})
    rng = np.random.default_rng(1)
    for i, l in enumerate(LAB):
        v = 100 * bb.loc[cls == l, 'own_tax_hat'].clip(0, 0.6)
        obsm = bb.loc[cls == l, 'own_tax_share_2024'].notna()
        x = i + rng.uniform(-0.28, 0.28, len(v))
        a1.scatter(x[obsm.values], v[obsm.values], s=2.2, color=st.BLUE, alpha=0.35, lw=0)
        a1.scatter(x[~obsm.values], v[~obsm.values], s=2.2, color=st.MUTED, alpha=0.35, lw=0)
        a1.plot([i - 0.32, i + 0.32], [v.median()] * 2, color=st.INK, lw=1.6)
    a1.axhline(10, color=st.PLUM, lw=1.1, ls=(0, (4, 2)))
    a1.text(5.45, 11.5, '10% (PEC 188)', fontsize=7.2, color=st.PLUM, ha='right',
            bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    a1.set_xticks(range(6)); a1.set_xticklabels(LAB, fontsize=7.5)
    a1.set_ylabel('Own taxes / current revenue, 2024 (%)'); a1.set_ylim(0, 60)
    a1.grid(axis='x', visible=False)
    a1.legend(handles=[Line2D([], [], marker='o', ls='', color=st.BLUE, label='reported (SICONFI)'),
                       Line2D([], [], marker='o', ls='', color=st.MUTED, label='imputed')], fontsize=7, loc='upper left')
    a1.set_title('Who would fail the fiscal test', fontsize=9)
    st.panel_label(a1, 'a')
    m = J['mergers']
    regs = ['N', 'NE', 'SE', 'S', 'CO']
    ab = [m['by_region'][r] for r in regs]
    tot = [int((b.region == r).sum()) for r in regs]
    xx = np.arange(5)
    a2.bar(xx, tot, color=st.GRAYBAR, width=0.6, label='municipalities')
    a2.bar(xx, ab, color=st.BRONZE, width=0.6, label='absorbed under PEC 188 test')
    for x, v, t in zip(xx, ab, tot):
        a2.text(x, t + 25, f'{100 * v / t:.0f}%', ha='center', fontsize=7.5, color=st.INK2)
    a2.set_xticks(xx); a2.set_xticklabels(['North', 'Northeast', 'Southeast', 'South', 'Centre-West'], fontsize=7.2)
    a2.set_ylim(0, 2000); a2.grid(axis='x', visible=False)
    a2.legend(fontsize=7, loc='upper left', bbox_to_anchor=(0.0, 1.0))
    a2.set_ylim(0, 2300)
    a2.set_title('Merger exercise by region', fontsize=9)
    st.panel_label(a2, 'b')
    plt.tight_layout(w_pad=2)
    st.save(fig, 'fig_viability')


if __name__ == '__main__':
    which = sys.argv[1:] or ['fig_maps', 'fig_variance', 'fig_validity', 'fig_amendments', 'fig_partyday1', 'fig_viability']
    for w in which:
        globals()[w]()
        print('saved', w)
