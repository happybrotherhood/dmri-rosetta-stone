"""
Fit all seven arms to one dataset and keep everything admissibility needs.

The fits behind Tables 2-5 were written by generate_fa_maps.py as FA and MD
maps only. Judging admissibility on the eigenvalues (all >= 0, largest
<= 3.0 um^2/ms), comparing the six tensor components, and defining a voxel
set independently of the estimators all need more, so this script refits the
seven arms on the same input and saves, for each:

    <arm>_FA, <arm>_MD, <arm>_L1..L3      eigenvalues, descending, mm^2/s
    <arm>_tensor                          Dxx Dyy Dzz Dxy Dxz Dyz, mm^2/s,
                                          in the toolkit's own frame

It also segments the brain with FSL FAST, using the mean b = 0 and the mean
diffusion-weighted image as two channels, which gives a white-matter mask
that no tensor estimator has touched. One channel alone (b = 0) labelled
about two thirds of the brain as white matter.

Inputs are those of the published tables: the whole Stanford series, and
the b = 0 + b = 1000 subset of Sherbrooke, with the shared median_otsu mask.

Run inside the project container:

    docker run --rm -v "$PWD":/work -w /work --entrypoint python \
        dmri-rosetta scripts/fit_all_arms.py --subject stanford

Output: data/hcp/<subject>/arms/
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls", "dipy_nlls", "dipy_restore"]
INPUT = {"stanford": ("T1w/Diffusion/data.nii.gz", "T1w/Diffusion/bvals", "T1w/Diffusion/bvecs"),
         "sherbrooke": ("dti/subset_data.nii.gz", "dti/subset.bvals", "dti/subset.bvecs")}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def save(arr, ref, path):
    nib.save(nib.Nifti1Image(np.nan_to_num(arr).astype(np.float32), ref.affine), str(path))


def fit_fsl(dwi, bval, bvec, mask, d, wls):
    tag = "fsl_wls" if wls else "fsl_ols"
    cmd = ["dtifit", f"--data={dwi}", f"--mask={mask}", f"--bvecs={bvec}", f"--bvals={bval}",
           f"--out={d / tag}", "--save_tensor"]
    if wls:
        cmd.append("--wls")
    run(cmd)
    # dtifit stores the upper triangle as Dxx Dxy Dxz Dyy Dyz Dzz; reorder to Dxx Dyy Dzz Dxy Dxz Dyz
    t = nib.load(str(d / f"{tag}_tensor.nii.gz"))
    save(t.get_fdata(dtype=np.float32)[..., [0, 3, 5, 1, 2, 4]], t, d / f"{tag}_tensor.nii.gz")
    for f in d.glob(f"{tag}_*.nii.gz"):
        if f.name.split("_")[-1].split(".")[0] not in ("FA", "MD", "L1", "L2", "L3", "tensor"):
            f.unlink()


def fit_mrtrix(dwi, bval, bvec, mask, d, iters):
    tag = "mrt_wls" if iters == 0 else "mrt_iwls"
    mif, tensor = d / "dwi.mif", d / f"{tag}_tensor.mif"
    if not mif.exists():
        run(["mrconvert", str(dwi), str(mif), "-fslgrad", str(bvec), str(bval), "-quiet"])
    cmd = ["dwi2tensor", str(mif), str(tensor), "-mask", str(mask), "-quiet", "-force"]
    if iters is not None:
        cmd += ["-iter", str(iters)]
    run(cmd)
    run(["tensor2metric", str(tensor), "-mask", str(mask), "-quiet", "-force",
         "-fa", str(d / f"{tag}_FA.nii.gz"), "-adc", str(d / f"{tag}_MD.nii.gz"),
         "-value", str(d / f"{tag}_L.nii.gz"), "-num", "1,2,3"])
    # MRtrix3 stores tensors as Dxx Dyy Dzz Dxy Dxz Dyz, in scanner coordinates
    run(["mrconvert", str(tensor), str(d / f"{tag}_tensor.nii.gz"), "-quiet", "-force"])
    L = nib.load(str(d / f"{tag}_L.nii.gz"))
    ev = L.get_fdata(dtype=np.float32)
    for i in range(3):
        save(ev[..., i], L, d / f"{tag}_L{i + 1}.nii.gz")
    (d / f"{tag}_L.nii.gz").unlink()
    tensor.unlink()


def fit_dipy(img, bvals, bvecs, mask, d, method):
    from dipy.core.gradients import gradient_table
    from dipy.reconst.dti import TensorModel
    tag = f"dipy_{method.lower()}"
    gtab = gradient_table(bvals, bvecs=bvecs)
    m = nib.load(str(mask)).get_fdata().astype(bool)
    fit = TensorModel(gtab, fit_method=method).fit(img.get_fdata(dtype=np.float32), mask=m)
    save(fit.fa, img, d / f"{tag}_FA.nii.gz")
    save(fit.md, img, d / f"{tag}_MD.nii.gz")
    for i in range(3):
        save(fit.evals[..., i], img, d / f"{tag}_L{i + 1}.nii.gz")
    q = fit.quadratic_form   # from DIPY's clipped eigenvalues, in the frame of the b-vectors given
    save(np.stack([q[..., 0, 0], q[..., 1, 1], q[..., 2, 2], q[..., 0, 1], q[..., 0, 2], q[..., 1, 2]], -1),
         img, d / f"{tag}_tensor.nii.gz")


def fast_wm(img, bvals, mask, d):
    """Two-channel FAST (mean b = 0, mean DWI): an estimator-free tissue segmentation."""
    m = nib.load(str(mask)).get_fdata() > 0
    x = img.get_fdata(dtype=np.float32)
    save(x[..., bvals < 50].mean(-1) * m, img, d / "b0_brain.nii.gz")
    save(x[..., bvals >= 50].mean(-1) * m, img, d / "dwi_brain.nii.gz")
    run(["fast", "-S", "2", "-n", "3", "-o", str(d / "fast"),
         str(d / "b0_brain.nii.gz"), str(d / "dwi_brain.nii.gz")])
    for f in d.glob("fast_*"):
        if not f.name.startswith("fast_pve_"):
            f.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", required=True, choices=INPUT)
    ap.add_argument("--arms", nargs="*", default=ARMS, choices=ARMS,
                    help="arms to fit; give none to redo only the segmentation")
    args = ap.parse_args()
    for tool in ("dtifit", "dwi2tensor", "fast"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not on PATH — run inside the project container")

    base = ROOT / "data" / "hcp" / args.subject
    dwi, bval, bvec = (base / p for p in INPUT[args.subject])
    mask = base / "dti" / "shared_brain_mask.nii.gz"
    d = base / "arms"
    d.mkdir(exist_ok=True)
    img = nib.load(str(dwi))
    bvals, bvecs = np.loadtxt(bval), np.loadtxt(bvec)
    if bvecs.shape[0] != 3:
        bvecs = bvecs.T

    fast_wm(img, bvals, mask, d)
    for arm in args.arms:
        print(f"{args.subject}: {arm}", flush=True)
        if arm.startswith("fsl"):
            fit_fsl(dwi, bval, bvec, mask, d, wls=arm == "fsl_wls")
        elif arm.startswith("mrt"):
            fit_mrtrix(dwi, bval, bvec, mask, d, iters=0 if arm == "mrt_wls" else None)
        else:
            fit_dipy(img, bvals, bvecs.T, mask, d, arm.split("_")[1].upper())
    if (d / "dwi.mif").exists():
        (d / "dwi.mif").unlink()
    print("done")


if __name__ == "__main__":
    main()
