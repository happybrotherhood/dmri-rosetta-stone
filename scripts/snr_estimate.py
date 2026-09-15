"""
snr_estimate.py
---------------
Measure the signal-to-noise ratio of the two real datasets.

The paper attributes part of the difference between weighting schemes to
noise, and the phantom varies SNR deliberately. Comparing the two requires
the real data to be placed on the same scale, rather than described as
"noisier" from its acquisition parameters alone.

The noise level is taken from the MP-PCA noise map that MRtrix3 dwidenoise
writes when the denoised run is generated (generate_fa_maps.py --denoise).
It is an estimate of the Gaussian-equivalent standard deviation per voxel,
made from the full series before shell selection.

For each dataset, over white matter (FA > 0.2 in the FSL --wls fit):

    SNR b0      mean single b = 0 volume signal / median noise sigma
    SNR shell   mean diffusion-weighted signal of the fitted shell / sigma

Usage:
    python scripts/snr_estimate.py

Outputs:
    snr_estimate.txt
"""

from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).parent.parent
DATASETS = {"stanford": None, "sherbrooke": 1000}   # fitted shell, None = all


def estimate(subject: str, shell):
    dd = ROOT / "data" / "hcp" / subject / "T1w" / "Diffusion"
    sigma = nib.load(str(ROOT / "data" / "hcp" / subject / "dti_denoised"
                         / "noise_map.nii.gz")).get_fdata(dtype=np.float32)
    fa = np.nan_to_num(nib.load(str(ROOT / "data" / "hcp" / subject / "dti_iter0"
                                    / "fsl_dti_FA.nii.gz")).get_fdata(dtype=np.float32))
    mask = nib.load(str(ROOT / "data" / "hcp" / subject / "dti_iter0"
                        / "shared_brain_mask.nii.gz")).get_fdata() > 0
    wm = mask & (fa > 0.2) & (fa <= 1) & (sigma > 0)

    bvals = np.loadtxt(str(dd / "bvals"))
    data = nib.load(str(dd / "data.nii.gz")).get_fdata(dtype=np.float32)
    b0 = bvals < 50
    dw = bvals > 50 if shell is None else np.abs(np.round(bvals, -2) - shell) < 1

    s_b0 = data[..., b0][wm].mean(axis=-1)
    s_dw = data[..., dw][wm].mean(axis=-1)
    sig = float(np.median(sigma[wm]))
    return dict(n_wm=int(wm.sum()), n_b0=int(b0.sum()), n_dw=int(dw.sum()),
                shell=int(np.round(bvals[dw].mean(), -2)), sigma=sig,
                s_b0=float(s_b0.mean()), s_dw=float(s_dw.mean()),
                snr_b0=float(s_b0.mean() / sig), snr_dw=float(s_dw.mean() / sig))


def main():
    out = ROOT / "snr_estimate.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")
        w("Signal-to-noise ratio of the real datasets (white matter, FA > 0.2)")
        w("=" * 72)
        w("Noise sigma: median of the MRtrix3 dwidenoise MP-PCA noise map.")
        w()
        w(f"  {'dataset':<12}{'b0 vols':>8}{'shell':>7}{'DW vols':>8}"
          f"{'sigma':>9}{'SNR b0':>9}{'SNR shell':>11}")
        for subj, shell in DATASETS.items():
            r = estimate(subj, shell)
            w(f"  {subj:<12}{r['n_b0']:>8}{r['shell']:>7}{r['n_dw']:>8}"
              f"{r['sigma']:>9.1f}{r['snr_b0']:>9.1f}{r['snr_dw']:>11.1f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
