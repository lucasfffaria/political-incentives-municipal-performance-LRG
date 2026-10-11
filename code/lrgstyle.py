"""Shared figure style for the LRG article (v5): static, print-first, white page.

Palette: "Ouro Cosmico" (gold #f9c900, periwinkle #9aa3ff, ink #1a1b22 / #06060a, lavender white #e9ecff), adapted
for print. Its two hues are stepped into the lightness band that marks need on a white page and extended with two
jewel tones of the same family (teal, plum) and a bronze, so that up to six series stay distinguishable. The
categorical orders below were checked with the dataviz validator (OKLCH lightness band, chroma floor, adjacent CVD
separation >= 12, normal-vision separation >= 16); gold sits below 3:1 contrast on white, so gold marks always carry
a direct label or a dark outline. The LRG's own colour bands (green / yellow / orange / red) are status semantics and
keep a separate status palette."""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------- surfaces and ink (palette darks and light)
SURFACE = '#ffffff'
INK0 = '#06060a'          # palette: deepest
INK = '#1a1b22'           # palette: dark surface, used as ink
INK2 = '#3d3f4b'
MUTED = '#7b7e8c'
GRID = '#e4e6ef'
AXIS = '#b9bcca'
TINT = '#e9ecff'          # palette: lavender white (highlight bands, table headers, boxes)
TINT2 = '#f5f6fd'
GRAYBAR = '#c3c6d3'       # status quo / reference bars
# ---------------------------------------------------------------- palette accents and their print steps
GOLD_PAL = '#f9c900'      # palette gold (fills with a label, highlights)
PERI_PAL = '#9aa3ff'      # palette periwinkle
INDIGO = '#3f42a8'
GOLD = '#d4a800'
PLUM = '#8b306a'
TEAL = '#009494'
BRONZE = '#8f520d'
PERI = '#7479de'
GOLD_DK = '#9a7a00'       # gold for lines and text on white
CAT = [INDIGO, GOLD, PLUM, TEAL, BRONZE, PERI]          # validated order (adjacent pairs)
# the five LRG instruments and the published scorecard (validated in the order S, F, A, C, P)
INSTR = {'S': PLUM, 'F': GOLD, 'A': INDIGO, 'C': TEAL, 'P': BRONZE, 'I': GRAYBAR}
# mechanisms (validated in the order eff, vol, alloc, ta, sel, dis)
CHANNEL = {'eff': PERI, 'vol': GOLD, 'alloc': INDIGO, 'ta': TEAL, 'sel': BRONZE, 'dis': PLUM}
# sequential ramps (one hue, light to dark) and a diverging pair with a neutral midpoint
SEQ = ['#f3f4ff', '#e1e4ff', '#c8cdfb', '#acb3f4', '#9098e9', '#757dd9', '#5c63c4', '#4a4fb0', '#3f42a8', '#323590',
       '#262874', '#1b1c56', '#121339']
SEQ_GOLD = ['#fffaeb', '#fff1c4', '#ffe48d', '#fbd24f', '#f0bf00', '#d4a800', '#b28d00', '#8e7000', '#6a5400']
DIV_NEG = BRONZE; DIV_MID = '#f2f2f5'; DIV_POS = INDIGO
CMAP_SEQ = LinearSegmentedColormap.from_list('lrg_seq', ['#ffffff'] + SEQ[1:])
CMAP_GOLD = LinearSegmentedColormap.from_list('lrg_gold', SEQ_GOLD)
CMAP_DIV = LinearSegmentedColormap.from_list('lrg_div', ['#6b3d08', BRONZE, '#d9b77e', DIV_MID, '#a9aef0', INDIGO, '#1b1c56'])
# LRG bands: status semantics only (good / warning / serious / critical)
BAND = {'green': '#2f9466', 'yellow': '#e8b800', 'orange': '#dd7a2c', 'red': '#b8344a'}
# legacy names used by the v1-v4 scripts, mapped onto the new palette
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = INDIGO, BRONZE, TEAL, GOLD, PLUM, TEAL, PERI, PLUM

for f in ['/usr/share/fonts/opentype/inter/Inter-Regular.otf', '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
          '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
          '/usr/share/fonts/opentype/inter/Inter-Italic.otf', '/usr/share/fonts/opentype/inter/Inter-Light.otf']:
    try:
        fm.fontManager.addfont(f)
    except Exception:
        pass


def setup():
    mpl.rcParams.update({
        'font.family': 'Inter', 'font.size': 9.2, 'axes.titlesize': 10.2, 'axes.titleweight': 'semibold',
        'axes.titlecolor': INK, 'axes.labelsize': 9.0, 'axes.labelcolor': INK2, 'axes.edgecolor': AXIS,
        'axes.linewidth': 0.8, 'axes.facecolor': SURFACE, 'figure.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
        'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.7, 'grid.linestyle': '-',
        'axes.axisbelow': True, 'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.labelcolor': INK2,
        'ytick.labelcolor': INK2, 'xtick.major.size': 0, 'ytick.major.size': 0, 'xtick.labelsize': 8.3,
        'ytick.labelsize': 8.3, 'legend.frameon': False, 'legend.fontsize': 8.2, 'legend.handlelength': 1.4,
        'lines.linewidth': 2.0, 'lines.solid_capstyle': 'round', 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.titlelocation': 'left', 'axes.titlepad': 9, 'figure.dpi': 110,
        'savefig.dpi': 300, 'text.color': INK, 'mathtext.fontset': 'dejavusans', 'axes.unicode_minus': True,
        'patch.linewidth': 0.0, 'hatch.color': GOLD_DK, 'hatch.linewidth': 0.7,
        'axes.prop_cycle': mpl.cycler(color=CAT),
    })


def panel_label(ax, s, x=-0.02, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=11.5, fontweight='bold', color=INDIGO, va='bottom', ha='right')


def save(fig, name, outdir=(_ROOT + '/figures')):
    fig.savefig(f'{outdir}/{name}.png', dpi=300, bbox_inches='tight')
    fig.savefig(f'{outdir}/{name}.pdf', bbox_inches='tight')
    plt.close(fig)


def note(fig, text, y=-0.02):
    fig.text(0.0, y, text, fontsize=7.4, color=MUTED, ha='left', va='top', wrap=True)


def zero_line(ax, axis='x', lw=0.9):
    (ax.axvline if axis == 'x' else ax.axhline)(0, color=INK2, lw=lw, zorder=1)


def interval(ax, x, y, lo, hi, color, horizontal=True, ms=5.5, marker='o', lw=1.6, face=None, z=3):
    """A median with its 5-95% interval: a line with a round cap and a marker with a white ring."""
    if horizontal:
        ax.plot([lo, hi], [y, y], color=color, lw=lw, solid_capstyle='round', zorder=z, alpha=0.9)
        ax.plot([x], [y], marker=marker, ms=ms, color=color, mfc=face or color, mec='white', mew=1.1, zorder=z + 1, ls='')
    else:
        ax.plot([x, x], [lo, hi], color=color, lw=lw, solid_capstyle='round', zorder=z, alpha=0.9)
        ax.plot([x], [y], marker=marker, ms=ms, color=color, mfc=face or color, mec='white', mew=1.1, zorder=z + 1, ls='')
