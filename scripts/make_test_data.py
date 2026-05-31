"""
Generate a small synthetic dMRI dataset that mimics the HCP folder structure.

Requires only numpy + nibabel — no dipy needed.

Usage:
    python scripts/make_test_data.py
    python scripts/make_test_data.py --subject 100307 --outdir data/hcp
"""

import argparse
import struct
import numpy as np
import nibabel as nib
from pathlib import Path


# ---------------------------------------------------------------------------
# Gradient table
# ---------------------------------------------------------------------------

def make_gradient_table(n_per_shell: int = 30):
    """Return (bvals, bvecs) for a two-shell acquisition + b=0 volumes."""
    rng = np.random.default_rng(42)

    # Generate approximately uniform directions using golden-ratio spacing
    def golden_sphere(n):
        golden = np.pi * (3 - np.sqrt(5))
        idx    = np.arange(n)
        y      = 1 - 2 * idx / (n - 1)
        r      = np.sqrt(np.maximum(1 - y**2, 0))
        theta  = golden * idx
        x      = np.cos(theta) * r
        z      = np.sin(theta) * r
        dirs   = np.column_stack([x, y, z])
        # Normalise
        norms  = np.linalg.norm(dirs, axis=1, keepdims=True)
        return dirs / np.maximum(norms, 1e-10)

    bvals_list, bvecs_list = [], []

    # b=0 volumes (no diffusion gradient)
    n_b0 = 10
    bvals_list.append(np.zeros(n_b0))
    bvecs_list.append(np.zeros((n_b0, 3)))

    # Two shells
    dirs = golden_sphere(n_per_shell * 2)
    for i, bval in enumerate([1000, 2000]):
        d = dirs[i * n_per_shell:(i + 1) * n_per_shell]
        bvals_list.append(np.full(n_per_shell, bval))
        bvecs_list.append(d)

    return np.concatenate(bvals_list), np.vstack(bvecs_list)


# ---------------------------------------------------------------------------
# Signal model (Stejskal-Tanner, no dipy)
# ---------------------------------------------------------------------------

def tensor_signal(bvals: np.ndarray, bvecs: np.ndarray,
                  evals: np.ndarray, evecs: np.ndarray,
                  S0: float = 1000.0) -> np.ndarray:
    """
    Exact diffusion tensor signal:  S = S0 * exp(-b * g^T D g)
    evals: (3,)  eigenvalues
    evecs: (3,3) eigenvectors as columns
    """
    D = evecs @ np.diag(evals) @ evecs.T          # diffusion tensor 3x3
    n = len(bvals)
    signal = np.zeros(n)
    for i in range(n):
        b = bvals[i]
        g = bvecs[i]
        if b < 1:                                  # b=0 volume
            signal[i] = S0
        else:
            signal[i] = S0 * np.exp(-b * (g @ D @ g))
    return signal


def evecs_from_direction(direction: np.ndarray) -> np.ndarray:
    """Build eigenvector matrix with principal axis along *direction*."""
    d = direction / (np.linalg.norm(direction) + 1e-10)
    tmp = np.array([1., 0., 0.]) if abs(d[0]) < 0.9 else np.array([0., 1., 0.])
    e2 = np.cross(d, tmp);  e2 /= np.linalg.norm(e2)
    e3 = np.cross(d, e2);   e3 /= np.linalg.norm(e3)
    return np.column_stack([d, e2, e3])


def two_fibre_signal(bvals, bvecs, evals, dir1, dir2,
                     f1: float = 0.5, S0: float = 1000.0) -> np.ndarray:
    """Partial volume mix of two single-tensor signals."""
    s1 = tensor_signal(bvals, bvecs, evals, evecs_from_direction(dir1), S0)
    s2 = tensor_signal(bvals, bvecs, evals, evecs_from_direction(dir2), S0)
    return f1 * s1 + (1 - f1) * s2


# ---------------------------------------------------------------------------
# Phantom volume
# ---------------------------------------------------------------------------

def build_phantom(shape=(30, 30, 30),
                  bvals: np.ndarray = None,
                  bvecs: np.ndarray = None) -> np.ndarray:
    """
    Four-region phantom:
      z < 10           : isotropic (CSF-like, FA ≈ 0)
      10 ≤ z < 20, x<15: single fibre Left-Right  (FA ≈ 0.7)
      10 ≤ z < 20, x≥15: single fibre Sup-Inf     (FA ≈ 0.7)
      z ≥ 20           : crossing fibres LR × AP  (apparent FA ≈ 0.35)
    """
    nx, ny, nz = shape
    n_vols     = len(bvals)
    vol        = np.zeros((*shape, n_vols), dtype=np.float32)

    evals_wm  = np.array([1.4e-3, 0.35e-3, 0.35e-3])   # FA ≈ 0.7
    evals_iso = np.array([0.9e-3,  0.9e-3, 0.9e-3])    # FA ≈ 0

    dir_lr = np.array([1., 0., 0.])
    dir_ap = np.array([0., 1., 0.])
    dir_si = np.array([0., 0., 1.])

    rng = np.random.default_rng(7)
    noise_sigma = 1000 / 30   # SNR ≈ 30 at b=0

    # Pre-compute signals for each region (constant across voxels in region)
    sig_csf      = tensor_signal(bvals, bvecs, evals_iso, evecs_from_direction(dir_lr), S0=800)
    sig_wm_lr    = tensor_signal(bvals, bvecs, evals_wm,  evecs_from_direction(dir_lr))
    sig_wm_si    = tensor_signal(bvals, bvecs, evals_wm,  evecs_from_direction(dir_si))
    sig_crossing = two_fibre_signal(bvals, bvecs, evals_wm, dir_lr, dir_ap)

    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if z < 10:
                    base = sig_csf
                elif z < 20 and x < 15:
                    base = sig_wm_lr
                elif z < 20:
                    base = sig_wm_si
                else:
                    base = sig_crossing

                noise = rng.normal(0, noise_sigma, n_vols).astype(np.float32)
                vol[x, y, z, :] = np.maximum(base + noise, 0)

    return vol


def build_mask(shape=(30, 30, 30)) -> np.ndarray:
    mask = np.ones(shape, dtype=np.uint8)
    for axis in range(3):
        idx = [slice(None)] * 3
        for edge in [0, -1]:
            idx[axis] = edge
            mask[tuple(idx)] = 0
    return mask


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(subject: str, outdir: Path, n_per_shell: int = 30):
    print(f'Generating synthetic HCP-like data for subject {subject} ...')

    bvals, bvecs = make_gradient_table(n_per_shell)
    n_b0    = int((bvals < 50).sum())
    n_b1000 = int(((bvals > 900) & (bvals < 1100)).sum())
    n_b2000 = int((bvals > 1900).sum())
    print(f'  Gradient table: {len(bvals)} volumes '
          f'(b=0×{n_b0}  b=1000×{n_b1000}  b=2000×{n_b2000})')

    diff_dir = outdir / subject / 'T1w' / 'Diffusion'
    diff_dir.mkdir(parents=True, exist_ok=True)
    t1_dir   = outdir / subject / 'T1w'

    # Build DWI phantom
    print('  Building phantom (30×30×30) ... ', end='', flush=True)
    mask = build_mask()
    vol  = build_phantom(bvals=bvals, bvecs=bvecs)

    # Replace background voxels with pure thermal noise (no tissue signal).
    # Real scanners have noise everywhere, but no tissue signal outside the head.
    # This makes background_std ≈ noise_sigma, so SNR = brain_mean / noise_sigma ≈ 30.
    noise_sigma = 1000.0 / 30.0
    rng_bg  = np.random.default_rng(99)
    bg_bool = ~mask.astype(bool)           # uint8 ~mask does bitwise NOT (wrong); cast first
    n_bg    = bg_bool.sum()
    bg_noise = np.abs(rng_bg.normal(0, noise_sigma, (n_bg, len(bvals)))).astype(np.float32)
    vol[bg_bool] = bg_noise
    print('done')

    # 2 mm isotropic affine
    affine = np.diag([2., 2., 2., 1.])
    affine[:3, 3] = -np.array(vol.shape[:3], dtype=float)

    # Save DWI
    dwi_path = diff_dir / 'data.nii.gz'
    nib.save(nib.Nifti1Image(vol, affine), str(dwi_path))
    print(f'  Saved: {dwi_path}  {vol.shape}')

    # bvals / bvecs  (FSL convention: bvecs rows = x, y, z; shape 3×N)
    np.savetxt(str(diff_dir / 'bvals'), bvals[np.newaxis, :], fmt='%.0f')
    np.savetxt(str(diff_dir / 'bvecs'), bvecs.T, fmt='%.6f')
    print(f'  Saved: bvals ({len(bvals)} values), bvecs (3×{len(bvals)})')

    # Brain mask
    mask_path = diff_dir / 'nodif_brain_mask.nii.gz'
    nib.save(nib.Nifti1Image(mask, affine), str(mask_path))
    print(f'  Saved: {mask_path}')

    # Synthetic T1w (Gaussian blob)
    xx, yy, zz = np.mgrid[:30, :30, :30]
    t1 = np.exp(-((xx-15)**2 + (yy-15)**2 + (zz-15)**2) / 80) * 1200
    t1 = t1.astype(np.float32)
    t1_path = t1_dir / 'T1w_acpc_dc_restore_brain.nii.gz'
    nib.save(nib.Nifti1Image(t1, affine), str(t1_path))
    print(f'  Saved: {t1_path}')

    # Fake parcellation (84 labels)
    mni_dir = outdir / subject / 'MNINonLinear' / 'ROIs'
    mni_dir.mkdir(parents=True, exist_ok=True)
    rng  = np.random.default_rng(0)
    parc = rng.integers(1, 85, size=(30, 30, 30)).astype(np.int32)
    parc[~mask.astype(bool)] = 0
    nib.save(nib.Nifti1Image(parc, affine), str(mni_dir / 'Atlas_ROIs.2.nii.gz'))
    print(f'  Saved: Atlas_ROIs.2.nii.gz  (84 parcels)')

    print()
    print('=== Synthetic dataset ready ===')
    print(f'  Location : {outdir / subject}')
    print()
    print('  Note: this is a 30×30×30 phantom — results will look different')
    print('  from real HCP data but all code paths will execute correctly.')
    print('  Replace with real HCP data when you are ready for real results.')
    print()

    # Quick sanity check
    loaded = nib.load(str(dwi_path)).get_fdata()
    print(f'  Sanity check: data.nii.gz  shape={loaded.shape}  '
          f'max={loaded.max():.0f}  min={loaded.min():.0f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',     default='100307')
    parser.add_argument('--outdir',      default='./data/hcp')
    parser.add_argument('--n_per_shell', type=int, default=30)
    args = parser.parse_args()
    generate(args.subject, Path(args.outdir), args.n_per_shell)
