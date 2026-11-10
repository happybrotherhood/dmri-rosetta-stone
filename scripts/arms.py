"""
arms.py
-------
The voxel set and admissibility rule of the revised analysis, shared by
every script that reads the fits of fit_all_arms.py.

    white matter   two-channel FSL FAST (mean b = 0, mean DWI), WM PVE >= 0.5,
                   inside the shared median_otsu brain mask. No tensor
                   estimator is involved, so the voxel set is the same for
                   every arm and cannot favour one of them.
    admissible     all three eigenvalues >= 0 and the largest <= 3.0 um^2/ms
                   (free water at body temperature). Judged on the
                   eigenvalues because FA in [0, 1] with 0 < MD <= 3.0 does
                   not exclude a tensor with a negative eigenvalue.
"""
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LMAX = 3.0   # um^2/ms
WM_PVE = 0.5


def load(path):
    return np.nan_to_num(np.asarray(nib.load(str(path)).dataobj, dtype=np.float64))


def arm_dir(subj, denoised=False, tag=None):
    """arms/, arms_denoised/, or arms_<tag>/ (e.g. tag="b2000" for another shell selection)."""
    name = f"arms_{tag}" if tag else ("arms_denoised" if denoised else "arms")
    return ROOT / "data" / "hcp" / subj / name


def brain_mask(subj):
    return load(ROOT / "data" / "hcp" / subj / "dti" / "shared_brain_mask.nii.gz") > 0


def tissue(subj):
    """White-matter and CSF partial-volume maps from the two-channel FAST run.

    On the T2-weighted b = 0 image white matter is the darkest class; CSF has
    the least diffusion-weighted signal.
    """
    d = arm_dir(subj)
    brain = brain_mask(subj)
    b0, dwi = load(d / "b0_brain.nii.gz"), load(d / "dwi_brain.nii.gz")
    pve = [load(d / f"fast_pve_{i}.nii.gz") for i in range(3)]
    cls = [brain & (p >= 0.5) for p in pve]
    wm = pve[int(np.argmin([b0[c].mean() for c in cls]))]
    csf = pve[int(np.argmin([dwi[c].mean() for c in cls]))]
    return wm, csf


def wm_mask(subj, pve=WM_PVE):
    return brain_mask(subj) & (tissue(subj)[0] >= pve)


def load_arm(subj, arm, denoised=False, tensor=False, tag=None):
    """FA, MD (um^2/ms), eigenvalues (um^2/ms) and optionally the tensor of one arm."""
    d = arm_dir(subj, denoised, tag)
    out = {"FA": load(d / f"{arm}_FA.nii.gz"), "MD": load(d / f"{arm}_MD.nii.gz") * 1e3,
           "ev": np.stack([load(d / f"{arm}_L{i}.nii.gz") for i in (1, 2, 3)], -1) * 1e3}
    if tensor:
        out["T"] = load(d / f"{arm}_tensor.nii.gz") * 1e3
    return out


def admissible(ev):
    return (ev.min(-1) >= 0) & (ev.max(-1) <= LMAX)
