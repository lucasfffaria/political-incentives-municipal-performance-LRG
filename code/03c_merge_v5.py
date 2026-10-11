"""
03c_merge_v5.py -- v5: assembles the draw-level results the article and the supplementary material use.

main      output/designs_metrics.npz = the v4 main run (kept as designs_metrics_v4full.npz) without the redesign family
          (ROB, ROB_nb, ROB_nS, ROB_nb_bon, ROB_nb_sup) and without the v4 personal bonus (B00-B10, computed on the
          redesign's scorecard), plus the v5 supplements v5A and v5B (400 draws, the same seeds, hence the same shocks).
families  each designs_metrics_<family>_v5.npz (first 120 draws, the same seeds) is added to designs_metrics_<family>.npz
          and the redesign family is dropped; fD (the full factorial under implementation scenario D) is added to sc_iD.
          The v4 family files are kept in output/v4_families/.
Checks    the status-quo arrays and the parameter draws of every supplement must equal those of the file it joins
          (common random numbers); the script stops otherwise.
usage: python 03c_merge_v5.py
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import glob, shutil
import numpy as np
import pandas as pd

OUT = _ROOT + '/output'
DROP = {'ROB', 'ROB_nb', 'ROB_nS', 'ROB_nb_bon', 'ROB_nb_sup', 'B00', 'B025', 'B05', 'B10'}
SQ = ['W0__params', 'W0__turnover', 'W0__incumb_win', 'W0__theta_2033', 'W0__fp_2036', 'W0__mayors_2036', 'W0__disc_2036']


def same_world(a, b, label):
    for k in SQ:
        if k in a.files and k in b.files:
            x, y = a[k], b[k]
            n = min(x.shape[0], y.shape[0])
            if not np.array_equal(np.nan_to_num(x[:n], nan=-9), np.nan_to_num(y[:n], nan=-9)):
                raise SystemExit(f'{label}: {k} differs -- not the same draws and shocks')


def merge(base_file, add_files, out_file, drop):
    z = np.load(base_file)
    flat = {k: z[k] for k in z.files if k.split('__')[0] not in drop}
    for f in add_files:
        a = np.load(f)
        same_world(z, a, _os.path.basename(f))
        for k in a.files:
            if k.split('__')[0] == 'W0':
                continue                                 # the status quo of the base file is kept (identical)
            if k.split('__')[0] in drop and k.split('__')[0] not in ('B025', 'B05', 'B10'):
                continue
            flat[k] = a[k]
    np.savez_compressed(out_file, **flat)
    return sorted({k.split('__')[0] for k in flat})


if __name__ == '__main__':
    # ---------------------------------------------------------------- main run
    v4 = OUT + '/designs_metrics_v4full.npz'
    adds = [OUT + f'/designs_metrics_{t}.npz' for t in ('v5A', 'v5B') if _os.path.exists(OUT + f'/designs_metrics_{t}.npz')]
    keys = merge(v4, adds, OUT + '/designs_metrics.npz', DROP)
    print('main:', len(keys), 'designs from', [_os.path.basename(f) for f in [v4] + adds])
    s = pd.read_csv(OUT + '/designs_summary_v4full.csv')
    s = s[~s.design.isin(DROP)]
    for t in ('v5A', 'v5B'):
        p_ = OUT + f'/designs_summary_{t}.csv'
        if _os.path.exists(p_):
            s = pd.concat([s, pd.read_csv(p_)])
    s.drop_duplicates('design', keep='last').to_csv(OUT + '/designs_summary.csv', index=False)
    # ---------------------------------------------------------------- scenario families
    bk = OUT + '/v4_families'; parts = OUT + '/v5_parts'
    _os.makedirs(bk, exist_ok=True); _os.makedirs(parts, exist_ok=True)
    # the supplements leave output/ (where 22_scenarios.py would read them as families of their own)
    for f in glob.glob(OUT + '/designs_metrics_*_v5.npz') + glob.glob(OUT + '/designs_metrics_fD.npz'):
        tag = _os.path.basename(f)[len('designs_metrics_'):-4]
        log = OUT + f'/run_{tag}.log'                   # a run is complete once its log says so (the file is written first)
        if _os.path.exists(log) and 'saved; total' not in open(log).read():
            print('still running, left for later:', tag)
            continue
        shutil.move(f, parts + '/' + _os.path.basename(f))
    sups = {}
    for f in sorted(glob.glob(parts + '/designs_metrics_*_v5.npz')):
        sups.setdefault(_os.path.basename(f)[len('designs_metrics_'):-len('_v5.npz')], []).append(f)
    if _os.path.exists(parts + '/designs_metrics_fD.npz'):
        sups.setdefault('sc_iD', []).append(parts + '/designs_metrics_fD.npz')
    for fam, extra in sups.items():
        base = OUT + f'/designs_metrics_{fam}.npz'
        if not _os.path.exists(bk + f'/designs_metrics_{fam}.npz'):
            shutil.copy(base, bk + f'/designs_metrics_{fam}.npz')
        keys = merge(bk + f'/designs_metrics_{fam}.npz', extra, base, DROP)
        print(f'{fam}: {len(keys)} designs, added from', [_os.path.basename(x) for x in extra])
    # families without a v5 supplement still lose the redesign family
    for f in sorted(glob.glob(OUT + '/designs_metrics_sc_*.npz')) + sorted(glob.glob(OUT + '/designs_metrics_cv_*.npz')):
        if f.endswith('_v5.npz'):
            continue
        z = np.load(f)
        if any(k.split('__')[0] in DROP for k in z.files):
            fam = _os.path.basename(f)[len('designs_metrics_'):-4]
            if not _os.path.exists(bk + f'/designs_metrics_{fam}.npz'):
                shutil.copy(f, bk + f'/designs_metrics_{fam}.npz')
            keys = merge(bk + f'/designs_metrics_{fam}.npz', [], f, DROP)
            print(f'{fam}: {len(keys)} designs (redesign dropped)')
