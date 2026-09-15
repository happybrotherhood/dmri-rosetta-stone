"""
fa_bias_by_fa.py
----------------
Break the real-data difference between weighting schemes down by anisotropy.

The FA offset between measured-signal weighting (FSL --wls) and
predicted-signal weighting (DIPY WLS) has opposite signs on the two datasets,
while the MD offset has the same sign on both. A single white-matter mean
hides whether that reversal is uniform or depends on how anisotropic the
voxel is; this script reports the offset within bins of FA.

Pairs compared, each on the input the paper already reports:

    unprocessed   dti_iter0/      FSL --wls  vs  DIPY WLS
    denoised      dti_denoised/   FSL --wls  vs  DIPY WLS

Voxels: FA > 0.2 in both fits and physically admissible in both. The bin is
set by the mean FA of the pair, so neither arm defines it.

Usage:
    python scripts/fa_bias_by_fa.py

Outputs:
    fa_bias_by_fa.txt
"""

from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).parent.parent
EDGES = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0]
RUNS = [("unprocessed", "dti_iter0"), ("denoised", "dti_denoised")]


def load(p: Path) -> np.ndarray:
    return np.nan_to_num(nib.load(str(p)).get_fdata(dtype=np.float32))


def main():
    out = ROOT / "fa_bias_by_fa.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")
        w("Measured-signal minus predicted-signal weighting, by FA bin")
        w("(FSL dtifit --wls minus DIPY WLS; MD in um^2/ms)")
        w("=" * 72)
        for subj in ("stanford", "sherbrooke"):
            for label, sub in RUNS:
                d = ROOT / "data" / "hcp" / subj / sub
                fa_m, fa_p = load(d / "fsl_dti_FA.nii.gz"), load(d / "dipy_FA.nii.gz")
                md_m = load(d / "fsl_dti_MD.nii.gz") * 1e3
                md_p = load(d / "dipy_MD.nii.gz") * 1e3
                ok = ((fa_m > 0.2) & (fa_p > 0.2) & (fa_m <= 1) & (fa_p <= 1)
                      & (md_m > 0) & (md_p > 0) & (md_m <= 3) & (md_p <= 3))
                mean_fa = (fa_m + fa_p) / 2
                w()
                w(f"{subj}, {label}  (n = {int(ok.sum()):,})")
                w(f"  {'FA bin':<12}{'n':>9}{'FA diff':>10}{'MD diff':>10}")
                for lo, hi in zip(EDGES[:-1], EDGES[1:]):
                    sel = ok & (mean_fa >= lo) & (mean_fa < hi)
                    if sel.sum() == 0:
                        continue
                    w(f"  {lo:.1f}-{hi:.1f}{'':<5}{int(sel.sum()):>9,}"
                      f"{float(np.mean(fa_m[sel] - fa_p[sel])):>+10.4f}"
                      f"{float(np.mean(md_m[sel] - md_p[sel])):>+10.4f}")
                w(f"  {'all':<12}{int(ok.sum()):>9,}"
                  f"{float(np.mean(fa_m[ok] - fa_p[ok])):>+10.4f}"
                  f"{float(np.mean(md_m[ok] - md_p[ok])):>+10.4f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
