"""
estimator_comparison.py
-----------------------
Compare every fitted estimator against the measured-signal weighted fit, on
one voxel set per dataset.

The runs already on disk (generate_fa_maps.py) give six estimators on
identical input:

    FSL dtifit --wls            dti_iter0/fsl_dti          reference
    MRtrix3 dwi2tensor -iter 0  dti_iter0/mrt
    FSL dtifit (OLS)            dti_iter0_fslols/fsl_dti   toolkit default
    MRtrix3 dwi2tensor          dti/mrt                    toolkit default
    DIPY WLS                    dti_iter0/dipy             toolkit default
    DIPY NLLS                   dti_iter0_dipyNLLS/dipy
    DIPY RESTORE                dti_iter0_dipyRESTORE/dipy

Every statistic is computed on the same voxels: FA > 0.2 and FA and MD
physically admissible in all seven arms. Comparing estimators on different
voxel sets makes the same pair report slightly different numbers in
different tables, which is avoided here.

Bias is arm minus reference. MAE / SD divides the FA mean absolute
difference by the standard deviation of reference FA over the same voxels.

Also reports, for the default runs, how much the plausibility restriction
changes MRtrix3-vs-DIPY MD agreement.

Usage:
    python scripts/estimator_comparison.py

Outputs:
    estimator_comparison.txt
"""

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.stats import pearsonr

ROOT = Path(__file__).parent.parent
MD_MAX = 3.0   # um^2/ms

REFERENCE = ("FSL --wls", "dti_iter0", "fsl_dti")
ARMS = [
    ("MRtrix3 -iter 0",         "dti_iter0",             "mrt"),
    ("FSL default (OLS)",       "dti_iter0_fslols",      "fsl_dti"),
    ("MRtrix3 default (IWLS)",  "dti",                   "mrt"),
    ("DIPY WLS (default)",      "dti_iter0",             "dipy"),
    ("DIPY NLLS",               "dti_iter0_dipyNLLS",    "dipy"),
    ("DIPY RESTORE",            "dti_iter0_dipyRESTORE", "dipy"),
]
DEFAULT_PAIRS = [("FSL default (OLS)", "MRtrix3 default (IWLS)"),
                 ("FSL default (OLS)", "DIPY WLS (default)"),
                 ("MRtrix3 default (IWLS)", "DIPY WLS (default)")]


def load(subj, sub_dir, prefix, metric):
    p = ROOT / "data" / "hcp" / subj / sub_dir / f"{prefix}_{metric}.nii.gz"
    arr = np.nan_to_num(nib.load(str(p)).get_fdata(dtype=np.float32))
    return arr * 1e3 if metric == "MD" else arr


def compare(a, b, sel):
    d = a[sel] - b[sel]
    return float(pearsonr(a[sel], b[sel])[0]), float(np.abs(d).mean()), float(d.mean())


def main():
    out = ROOT / "estimator_comparison.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")
        w("Every estimator against FSL dtifit --wls, on one voxel set per dataset")
        w("(bias = arm minus reference; MD in um^2/ms)")
        w("=" * 92)
        for subj in ("stanford", "sherbrooke"):
            maps = {lbl: (load(subj, d, p, "FA"), load(subj, d, p, "MD"))
                    for lbl, d, p in [REFERENCE] + ARMS}
            sel = np.ones(maps[REFERENCE[0]][0].shape, bool)
            for fa, md in maps.values():
                sel &= (fa > 0.2) & (fa <= 1) & (md > 0) & (md <= MD_MAX)
            ref_fa, ref_md = maps[REFERENCE[0]]
            sd = float(ref_fa[sel].std(ddof=1))
            w()
            w(f"{subj}  (n = {int(sel.sum()):,} voxels; SD of reference FA = {sd:.4f})")
            w(f"  {'arm':<25}{'FA r':>8}{'FA MAE':>9}{'FA bias':>9}{'MAE/SD':>8}"
              f"{'MD r':>8}{'MD MAE':>9}{'MD bias':>9}")
            for lbl, _, _ in ARMS:
                fa, md = maps[lbl]
                r, mae, bias = compare(fa, ref_fa, sel)
                rm, maem, biasm = compare(md, ref_md, sel)
                w(f"  {lbl:<25}{r:>8.4f}{mae:>9.4f}{bias:>+9.4f}{mae / sd:>8.2f}"
                  f"{rm:>8.4f}{maem:>9.4f}{biasm:>+9.4f}")
            w()
            w("  Toolkit defaults against one another (same voxels; bias = first minus second)")
            for a, b in DEFAULT_PAIRS:
                r, mae, bias = compare(maps[a][0], maps[b][0], sel)
                rm, maem, biasm = compare(maps[a][1], maps[b][1], sel)
                w(f"  {a + ' vs ' + b:<48}{r:>8.4f}{mae:>9.4f}{bias:>+9.4f}"
                  f"{mae / sd:>8.2f}{rm:>8.4f}{maem:>9.4f}{biasm:>+9.4f}")

            # Plausibility restriction, on the default run as reported in Table 2.
            fa_m, md_m = load(subj, "dti", "mrt", "FA"), load(subj, "dti", "mrt", "MD")
            fa_d, md_d = load(subj, "dti", "dipy", "FA"), load(subj, "dti", "dipy", "MD")
            fa_f = load(subj, "dti", "fsl_dti", "FA")
            wm = (fa_m > 0.2) & (fa_d > 0.2) & (fa_f > 0.2)
            ok = wm & (md_m > 0) & (md_m <= MD_MAX) & (md_d > 0) & (md_d <= MD_MAX)
            r_raw, mae_raw, _ = compare(md_m, md_d, wm)
            r_ok, mae_ok, _ = compare(md_m, md_d, ok)
            w()
            w(f"  MRtrix3 vs DIPY MD, default run: all WM voxels r = {r_raw:.4f}, "
              f"MAE = {mae_raw:.4f} (n = {int(wm.sum()):,});")
            w(f"  admissible only r = {r_ok:.4f}, MAE = {mae_ok:.4f} (n = {int(ok.sum()):,})")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
