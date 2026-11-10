"""
shell_comparison.py
-------------------
The Sherbrooke comparison repeated with its b = 2000 s/mm^2 shell and with
both shells together (Reviewer 1, S1 and S2), on the fits of
fit_all_arms.py --shells.

    b1000        1 b = 0 + 64 directions at b = 1000   (the manuscript)
    b2000        1 b = 0 + 64 directions at b = 2000   (Stanford's b-value)
    b1000_2000   1 b = 0 + 128 directions, both shells (multi-shell input)

For each input: every arm against FSL --wls and the defaults against one
another on FAST white matter admissible in all seven arms; the agreement of
FSL --wls with MRtrix3 -iter 0; inadmissible fits per arm; and the SNR of
the diffusion-weighted volumes.

Usage:
    python scripts/shell_comparison.py

Outputs:
    shell_comparison.txt
"""
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, str(Path(__file__).parent))
from arms import ROOT, admissible, arm_dir, load, load_arm, wm_mask  # noqa: E402

SUBJ = "sherbrooke"
INPUTS = [("b1000", None), ("b2000", "b2000"), ("b1000_2000", "b1000_2000")]
SEVEN = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls", "dipy_nlls", "dipy_restore"]
LABEL = {"fsl_ols": "FSL default (OLS)", "fsl_wls": "FSL --wls", "mrt_iwls": "MRtrix3 default (IWLS)",
         "mrt_wls": "MRtrix3 -iter 0", "dipy_wls": "DIPY WLS (default)", "dipy_nlls": "DIPY NLLS",
         "dipy_restore": "DIPY RESTORE"}


def dw_snr(tag, wm):
    d = arm_dir(SUBJ, tag=tag) if tag else ROOT / "data" / "hcp" / SUBJ / "dti"
    bv = np.loadtxt(d / "subset.bvals")
    data = np.asarray(nib.load(str(d / "subset_data.nii.gz")).dataobj, dtype=np.float32)
    sig = np.median(load(ROOT / "data" / "hcp" / SUBJ / "dti_denoised" / "noise_map.nii.gz")[wm])
    out = {}
    for b in sorted(set(np.round(bv[bv > 50], -2).astype(int))):
        out[b] = data[..., np.round(bv, -2) == b][wm].mean() / sig
    return out


def main():
    lines = []

    def w(s=""):
        print(s)
        lines.append(s)

    wm = wm_mask(SUBJ)
    w("Sherbrooke: single shells and multi-shell input. FAST white matter; admissible = eigenvalues >= 0, "
      "largest <= 3.0. MD in um^2/ms; difference = arm minus reference.")
    for name, tag in INPUTS:
        A = {a: load_arm(SUBJ, a, tag=tag) for a in SEVEN}
        ok = {a: wm & admissible(A[a]["ev"]) for a in SEVEN}
        common = wm.copy()
        for a in SEVEN:
            common &= ok[a]
        snr = dw_snr(tag, wm)
        w()
        w("=" * 100)
        w(f"{name}: DW SNR " + ", ".join(f"b = {b}: {v:.1f}" for b, v in snr.items())
          + f"; {int(common.sum()):,} voxels admissible in all seven arms of {int(wm.sum()):,}")
        w("=" * 100)
        w(f"  {'arm':<40}{'inadm %':>9}{'FA mean':>9}{'MD mean':>9}{'FA r':>8}{'FA MAE':>9}{'FA diff':>9}"
          f"{'MD r':>8}{'MD MAE':>9}{'MD diff':>9}")
        ref = A["fsl_wls"]
        for a in SEVEN:
            x, y = A[a], ref
            fr = pearsonr(x["FA"][common], y["FA"][common])[0]
            mr = pearsonr(x["MD"][common], y["MD"][common])[0]
            w(f"  {LABEL[a] + ' vs FSL --wls':<40}{100 * (wm & ~ok[a]).sum() / wm.sum():>9.2f}"
              f"{x['FA'][common].mean():>9.4f}{x['MD'][common].mean():>9.4f}"
              f"{fr:>8.4f}{np.abs(x['FA'][common] - y['FA'][common]).mean():>9.4f}"
              f"{(x['FA'][common] - y['FA'][common]).mean():>+9.4f}"
              f"{mr:>8.4f}{np.abs(x['MD'][common] - y['MD'][common]).mean():>9.4f}"
              f"{(x['MD'][common] - y['MD'][common]).mean():>+9.4f}")
        for a, b in (("fsl_ols", "mrt_iwls"), ("fsl_ols", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            x, y = A[a], A[b]
            w(f"  {'Defaults: ' + LABEL[a] + ' vs ' + LABEL[b]:<40}{'':>9}{'':>9}{'':>9}"
              f"{pearsonr(x['FA'][common], y['FA'][common])[0]:>8.4f}"
              f"{np.abs(x['FA'][common] - y['FA'][common]).mean():>9.4f}"
              f"{(x['FA'][common] - y['FA'][common]).mean():>+9.4f}"
              f"{pearsonr(x['MD'][common], y['MD'][common])[0]:>8.4f}"
              f"{np.abs(x['MD'][common] - y['MD'][common]).mean():>9.4f}"
              f"{(x['MD'][common] - y['MD'][common]).mean():>+9.4f}")
        both = ok["fsl_wls"] & ok["mrt_wls"]
        d = np.abs(A["fsl_wls"]["FA"][both] - A["mrt_wls"]["FA"][both])
        w(f"  FSL --wls vs MRtrix3 -iter 0 ({int(both.sum()):,} voxels): |dFA| median {np.median(d):.1e}, "
          f"99.9th pct {np.percentile(d, 99.9):.1e}, max {d.max():.1e}; "
          f"negative eigenvalues FSL {int((wm & (A['fsl_wls']['ev'].min(-1) < 0)).sum()):,}, "
          f"MRtrix3 {int((wm & (A['mrt_wls']['ev'].min(-1) < 0)).sum()):,}")

    out = ROOT / "shell_comparison.txt"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
