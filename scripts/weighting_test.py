"""
weighting_test.py
-----------------
Test whether the weighting scheme, rather than the toolkit, explains the
differences between tensor fits.

The toolkits document two different ways of deriving the weights for a
weighted least-squares fit to the log-signal:

    empirical    weights from the measured signal
                 (MRtrix3 dwi2tensor, first step; FSL dtifit --wls)
    predicted    weights from the signal predicted by an initial OLS fit
                 (DIPY fit_method="WLS", following Chung et al. 2006;
                  MRtrix3's default repeats this twice as IWLS)

If that is the operative difference, then giving DIPY empirical weights
should move it onto FSL, and the toolkit label should stop mattering. This
script runs DIPY both ways on the same data used for the paper and compares
each against the FSL fit.

Usage:
    python scripts/weighting_test.py --subject stanford

Outputs:
    weighting_test_<subject>.txt
"""

import argparse
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.stats import pearsonr

ROOT = Path(__file__).parent.parent


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subject", default="stanford")
    return p.parse_args()


def fa_md(dtiparams):
    """dtiparams packs 3 eigenvalues then 9 eigenvector components per voxel."""
    from dipy.reconst.dti import fractional_anisotropy, mean_diffusivity
    evals = np.asarray(dtiparams)[..., :3]
    return (np.nan_to_num(fractional_anisotropy(evals)),
            np.nan_to_num(mean_diffusivity(evals)))


def agreement(a, b, valid):
    r, _ = pearsonr(a[valid], b[valid])
    d = a[valid] - b[valid]
    return r, float(np.mean(np.abs(d))), float(np.mean(d))


def main():
    args = parse_args()
    subj = args.subject
    dti = ROOT / "data" / "hcp" / subj / "dti_iter0"
    if not dti.exists():
        sys.exit(f"No matched-estimator run at {dti}. Generate it first with "
                 f"--mrtrix-iter 0.")

    from dipy.core.gradients import gradient_table
    from dipy.io.gradients import read_bvals_bvecs
    from dipy.reconst import dti as dti_mod

    # The same subset every toolkit was given.
    base = dti if (dti / "subset_data.nii.gz").exists() else None
    if base is not None:
        data_p, bval_p, bvec_p = (dti / "subset_data.nii.gz",
                                  dti / "subset.bvals", dti / "subset.bvecs")
    else:
        dd = ROOT / "data" / "hcp" / subj / "T1w" / "Diffusion"
        data_p, bval_p, bvec_p = dd / "data.nii.gz", dd / "bvals", dd / "bvecs"

    img = nib.load(str(data_p))
    data = img.get_fdata(dtype=np.float32)
    bv, bvec = read_bvals_bvecs(str(bval_p), str(bvec_p))
    gtab = gradient_table(bv, bvec)
    mask = nib.load(str(dti / "shared_brain_mask.nii.gz")).get_fdata().astype(bool)

    design = dti_mod.design_matrix(gtab)

    # DIPY multiplies the design matrix by the weights, so a voxel measured as
    # zero would contribute an all-zero row and make the system singular. Its
    # default weights come from exp(), which is never zero, so the problem only
    # appears once empirical weights are supplied. Clipping the signal to a
    # small positive floor avoids it, and both arms are given the identical
    # clipped data so the comparison stays fair.
    flat = np.maximum(data[mask], 1.0)

    print("Fitting DIPY with its default WLS weights (predicted signal) ...")
    ev_pred, _ = dti_mod.wls_fit_tensor(design, flat)

    print("Fitting DIPY with empirical weights (measured signal) ...")
    ev_emp, _ = dti_mod.wls_fit_tensor(design, flat, weights=flat ** 2)

    fa_pred, md_pred = fa_md(ev_pred)
    fa_emp, md_emp = fa_md(ev_emp)

    fsl_fa = np.nan_to_num(
        nib.load(str(dti / "fsl_dti_FA.nii.gz")).get_fdata(dtype=np.float32))[mask]
    fsl_md = np.nan_to_num(
        nib.load(str(dti / "fsl_dti_MD.nii.gz")).get_fdata(dtype=np.float32))[mask]

    # White matter, restricted to physically admissible values in every arm.
    wm = (fsl_fa > 0.2) & (fa_pred > 0.2) & (fa_emp > 0.2)
    ok = wm & (fsl_fa <= 1) & (fa_pred <= 1) & (fa_emp <= 1)

    out = ROOT / f"weighting_test_{subj}.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")
        w(f"Does the weighting scheme explain the difference?  ({subj})")
        w("=" * 68)
        w(f"White matter voxels compared: {int(ok.sum()):,}")
        w()
        w("Each DIPY variant against the FSL --wls fit of the same data:")
        w(f"  {'DIPY weights':<34}{'FA r':>9}{'FA MAE':>10}{'FA bias':>10}")
        for label, fa in (("predicted signal (DIPY default)", fa_pred),
                          ("empirical signal (as FSL/MRtrix3)", fa_emp)):
            r, mae, bias = agreement(fa, fsl_fa, ok)
            w(f"  {label:<34}{r:>9.4f}{mae:>10.4f}{bias:>+10.4f}")
        w()
        w(f"  {'DIPY weights':<34}{'MD r':>9}{'MD MAE':>10}{'MD bias':>10}")
        for label, md in (("predicted signal (DIPY default)", md_pred),
                          ("empirical signal (as FSL/MRtrix3)", md_emp)):
            r, mae, bias = agreement(md * 1e3, fsl_md * 1e3, ok)
            w(f"  {label:<34}{r:>9.4f}{mae:>10.4f}{bias:>+10.4f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
