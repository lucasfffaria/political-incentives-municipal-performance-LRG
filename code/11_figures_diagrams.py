"""
11_figures_diagrams.py -- the LRG's theory of change (fig_theory) and the same diagram with the assessment of the
evidence on each link (fig_verdict). Link strengths in fig_verdict come from output/verdict.json (written by
15_verdict.py); without it only fig_theory is drawn.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys, json
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
sys.path.insert(0, _ROOT + '/code')
import lrgstyle as st

st.setup()
OUT = _ROOT + '/output'

PILLARS = [('P_score', 'Scorecard, published\nten indicators,\nfloors and paths'),
           ('P_sanc', 'Sanctions\nalert, tutelage,\n8-year ban'),
           ('P_fpm', 'FPM tranche\nmore federal money\nfor points'),
           ('P_amend', 'Amendments\nonly for performers,\ntied to programmes'),
           ('P_cap', 'Commissioners\nready-made policies,\nconsortia'),
           ('P_party', 'Party funds\nby mayors\u2019 points\n\u00d7 population')]
CHANNELS = [('C_voters', 'Voters learn\nwho performs'),
            ('C_effort', 'Effort and money\non scored services'),
            ('C_select', 'Parties recruit and\nsupport managers'),
            ('C_fuel', 'Less discretionary\nmoney for clientelism')]
RESULTS = [('R_serv', 'Better services\nliteracy, daycare,\nsanitation, safety'),
           ('R_econ', 'Local economy\nformal jobs,\nprivate value added'),
           ('R_dep', 'Less dependence\non politicians'),
           ('R_brasilia', 'Fewer bought votes,\nfewer brokerage deputies')]
LINKS = [('P_score', 'C_voters'), ('P_score', 'C_effort'), ('P_sanc', 'C_effort'), ('P_sanc', 'C_select'),
         ('P_fpm', 'C_effort'), ('P_amend', 'C_effort'), ('P_amend', 'C_fuel'), ('P_cap', 'C_effort'),
         ('P_party', 'C_select'),
         ('C_effort', 'R_serv'), ('C_select', 'R_serv'), ('C_voters', 'R_serv'), ('R_serv', 'R_econ'), ('C_effort', 'R_econ'),
         ('R_econ', 'R_dep'), ('C_fuel', 'R_brasilia'), ('R_dep', 'R_brasilia')]


def draw(name, verdict=None):
    fig, ax = plt.subplots(figsize=(7.3, 5.3))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    pos = {}
    colx = [(0.006, 0.255), (0.37, 0.625), (0.735, 0.994)]
    heads = ['What the law does', 'What it is meant to change', 'What it is meant to deliver']
    for (x0, x1), h in zip(colx, heads):
        ax.text(x0, 0.985, h, fontsize=8.6, fontweight='semibold', color=st.INDIGO, va='top')
    def boxes(items, x0, x1, ytop, ybot, face):
        n = len(items); hgt = (ytop - ybot) / n
        for i, (k, lab) in enumerate(items):
            yc = ytop - (i + 0.5) * hgt
            bh = hgt * 0.78
            ax.add_patch(FancyBboxPatch((x0, yc - bh / 2), x1 - x0, bh, boxstyle='round,pad=0.004,rounding_size=0.012',
                                        fc=face, ec=st.AXIS, lw=0.8))
            head, _, rest = lab.partition('\n')
            nl = rest.count('\n') + 1 if rest else 0
            lh = 0.025; hh = 0.030
            ytop_t = yc + (hh + nl * lh) / 2
            ax.text(x0 + 0.012, ytop_t, head, fontsize=7.2, va='top', ha='left', color=st.INK, fontweight='semibold')
            if rest:
                ax.text(x0 + 0.012, ytop_t - hh, rest, fontsize=6.9, va='top', ha='left', color=st.INK2, linespacing=1.25)
            pos[k] = (x0, x1, yc, bh)
    boxes(PILLARS, *colx[0], 0.94, 0.02, st.TINT)
    boxes(CHANNELS, *colx[1], 0.86, 0.10, '#f4f4f7')
    boxes(RESULTS, *colx[2], 0.86, 0.10, '#fdf6dc')
    style = {'strong': (st.BAND['green'], '-', 2.2), 'partial': (st.BAND['yellow'], '-', 1.8), 'weak': ('#a3a6b4', (0, (4, 2.5)), 1.3),
             'contrary': (st.BAND['red'], (0, (1.5, 1.5)), 1.9), None: (st.INK2, '-', 1.0)}
    for a, b_ in LINKS:
        xa0, xa1, ya, _ = pos[a]; xb0, xb1, yb, _ = pos[b_]
        same_col = abs(xa0 - xb0) < 1e-6
        if same_col:
            start, end = ((xa0 + xa1) / 2 + 0.06, ya - pos[a][3] / 2), ((xb0 + xb1) / 2 + 0.06, yb + pos[b_][3] / 2)
            rad = 0.0
        else:
            start, end = (xa1, ya), (xb0, yb)
            rad = 0.0
        v = (verdict or {}).get(f'{a}->{b_}')
        colr, ls, lw = style[v]
        arr = FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=8, color=colr, lw=lw, linestyle=ls,
                              connectionstyle=f'arc3,rad={rad}', shrinkA=1, shrinkB=2)
        ax.add_patch(arr)
    if verdict:
        items = [('strong', 'supported, sizeable'), ('partial', 'supported, small'), ('weak', 'weak or unproven'),
                 ('contrary', 'contradicted')]
        x = 0.02
        for k, lab in items:
            colr, ls, lw = style[k]
            ax.plot([x, x + 0.04], [-0.035, -0.035], color=colr, lw=2, ls=ls, transform=ax.transAxes, clip_on=False)
            ax.text(x + 0.047, -0.035, lab, fontsize=7.2, va='center', color=st.INK2, transform=ax.transAxes)
            x += 0.245
    st.save(fig, name)


if __name__ == '__main__':
    draw('fig_theory')
    if _os.path.exists(OUT + '/verdict.json'):
        draw('fig_verdict', json.load(open(OUT + '/verdict.json'))['links'])
    print('done')
