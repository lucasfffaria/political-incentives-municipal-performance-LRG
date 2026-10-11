"""
03b_merge_runs.py -- merge the parts of 03_run_designs.py run in parallel processes (designs_metrics_<tag>.npz and
designs_summary_<tag>.csv) into output/designs_metrics.npz and output/designs_summary.csv.
usage: python 03b_merge_runs.py TAG1 TAG2 ...
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import sys
import numpy as np
import pandas as pd

OUT = _ROOT + '/output'
flat, rows = {}, []
for tag in sys.argv[1:]:
    z = np.load(f'{OUT}/designs_metrics_{tag}.npz')
    for k in z.files:
        if k not in flat:
            flat[k] = z[k]
    rows.append(pd.read_csv(f'{OUT}/designs_summary_{tag}.csv'))
np.savez_compressed(OUT + '/designs_metrics.npz', **flat)
pd.concat(rows).drop_duplicates('design').to_csv(OUT + '/designs_summary.csv', index=False)
print('merged', len(flat), 'arrays;', sum(len(r) for r in rows), 'summary rows')
