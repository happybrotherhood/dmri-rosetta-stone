"""
Fit every linear tensor-fitting arm to each MASiVar test-retest scan.

Run inside the project container, which provides FSL, MRtrix3 and DIPY:

    docker run --rm --platform linux/amd64 -v "$PWD":/work -w /work \
        --entrypoint python dmri-rosetta scripts/fit_test_retest.py

Each scan (one b = 0 volume and 96 directions at one b-value, unprocessed) is
given unchanged to five arms, with one shared brain mask:

    fsl_ols    dtifit                 OLS                  FSL default
    fsl_wls    dtifit --wls           WLS, measured signal
    mrt_iwls   dwi2tensor             WLS + 2 IWLS         MRtrix3 default
    mrt_wls    dwi2tensor -iter 0     WLS, measured signal
    dipy_wls   TensorModel("WLS")     WLS, predicted signal DIPY default

For each arm the three eigenvalues are saved alongside FA and MD, so that
admissibility can be judged on the eigenvalues (all >= 0, largest <= 3.0
um^2/ms) rather than on FA and MD. The MP-PCA noise map of each scan is
saved too, so that the offset between weighting schemes can be related to
the SNR of the scan.

With --source prequal the same arms are fitted to MASiVar's PreQual-
preprocessed scans (fetch_masivar.py --prequal). No noise map is made for
those: after MP-PCA denoising it would no longer describe the noise, so their
SNR is taken from the raw version of the same scan. --delete-input removes
each preprocessed scan once it has been fitted, to save disk space.

Output: data/masivar/derivatives/rosetta/b<shell>[_prequal]/<sub>/<ses>/<run>/
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "masivar"
OUT = RAW / "derivatives" / "rosetta"
ARMS = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(cmd)}\n{r.stderr[-2000:]}")


def save(arr, ref, path):
    nib.save(nib.Nifti1Image(np.nan_to_num(arr).astype(np.float32), ref.affine), str(path))


def shared_mask(img, bvals, out):
    from dipy.segment.mask import median_otsu
    _, m = median_otsu(img.get_fdata(dtype=np.float32), vol_idx=list(np.where(bvals < 50)[0]),
                       median_radius=2, numpass=1, dilate=1)
    nib.save(nib.Nifti1Image(m.astype(np.uint8), img.affine), str(out))


def fit_fsl(dwi, bval, bvec, mask, d, wls):
    tag = "fsl_wls" if wls else "fsl_ols"
    cmd = ["dtifit", f"--data={dwi}", f"--mask={mask}", f"--bvecs={bvec}",
           f"--bvals={bval}", f"--out={d / tag}"]
    if wls:
        cmd.append("--wls")
    run(cmd)
    # keep FA, MD and eigenvalues; drop the vectors, S0 and MO dtifit also writes
    for f in d.glob(f"{tag}_*.nii.gz"):
        if f.name.split("_")[-1].split(".")[0] not in ("FA", "MD", "L1", "L2", "L3"):
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
    L = nib.load(str(d / f"{tag}_L.nii.gz"))
    ev = L.get_fdata(dtype=np.float32)
    for i in range(3):
        save(ev[..., i], L, d / f"{tag}_L{i + 1}.nii.gz")
    (d / f"{tag}_L.nii.gz").unlink()
    tensor.unlink()


def fit_dipy(img, bvals, bvecs, mask, d):
    from dipy.core.gradients import gradient_table
    from dipy.reconst.dti import TensorModel
    gtab = gradient_table(bvals, bvecs=bvecs)
    m = nib.load(str(mask)).get_fdata().astype(bool)
    fit = TensorModel(gtab, fit_method="WLS").fit(img.get_fdata(dtype=np.float32), mask=m)
    save(fit.fa, img, d / "dipy_wls_FA.nii.gz")
    save(fit.md, img, d / "dipy_wls_MD.nii.gz")
    for i in range(3):
        save(fit.evals[..., i], img, d / f"dipy_wls_L{i + 1}.nii.gz")


SOURCES = {"raw": RAW, "prequal": RAW / "derivatives" / "prequal-v1.0.0"}


def scans(shell, src):
    pat = re.compile(rf"(sub-[^_]+)_(ses-[^_]+)_acq-b{shell}n96[^_]*_(run-\d+)_dwi\.nii\.gz$")
    for f in sorted(src.glob(f"sub-*/ses-*/dwi/*_acq-b{shell}n96*_dwi.nii.gz")):
        m = pat.search(f.name)
        if m:
            yield f, m.groups()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shell", default="1000")
    ap.add_argument("--only", help="regex on <sub>_<ses>_<run> to restrict the scans fitted")
    ap.add_argument("--source", default="raw", choices=SOURCES)
    ap.add_argument("--delete-input", action="store_true")
    args = ap.parse_args()
    raw_source = args.source == "raw"
    for tool in ("dtifit", "dwi2tensor", "dwidenoise"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not on PATH — run inside the project container")

    todo = [(f, g) for f, g in scans(args.shell, SOURCES[args.source])
            if not args.only or re.search(args.only, "_".join(g))]
    print(f"{len(todo)} scans at b = {args.shell}")
    for i, (f, (sub, ses, rn)) in enumerate(todo, 1):
        d = OUT / (f"b{args.shell}" + ("" if raw_source else f"_{args.source}")) / sub / ses / rn
        if (d / "done").exists():
            continue
        d.mkdir(parents=True, exist_ok=True)
        stem = str(f)[: -len(".nii.gz")]
        bval, bvec = Path(stem + ".bval"), Path(stem + ".bvec")
        img = nib.load(str(f))
        bvals, bvecs = np.loadtxt(bval), np.loadtxt(bvec)
        if bvecs.shape[0] != 3:
            bvecs = bvecs.T
        mask = d / "mask.nii.gz"
        shared_mask(img, bvals, mask)
        if raw_source:
            # noise map from the scan's own series; for SNR only, the fits use raw data
            run(["dwidenoise", str(f), str(d / "denoised_unused.nii.gz"), "-noise", str(d / "noise.nii.gz"),
                 "-mask", str(mask), "-quiet", "-force"])
            (d / "denoised_unused.nii.gz").unlink()
        fit_fsl(f, bval, bvec, mask, d, wls=False)
        fit_fsl(f, bval, bvec, mask, d, wls=True)
        fit_mrtrix(f, bval, bvec, mask, d, iters=None)
        fit_mrtrix(f, bval, bvec, mask, d, iters=0)
        (d / "dwi.mif").unlink()
        fit_dipy(img, bvals, bvecs.T, mask, d)
        (d / "done").write_text(f"{f.relative_to(RAW)}\n")
        if args.delete_input:
            for g in (f, bval, bvec):
                g.unlink()
        print(f"[{i}/{len(todo)}] {sub} {ses} {rn}", flush=True)


if __name__ == "__main__":
    main()
