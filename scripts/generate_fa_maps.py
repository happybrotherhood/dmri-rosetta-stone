"""
generate_fa_maps.py
-------------------
Headless generation of (a) per-tool brain masks and (b) DTI FA/MD maps for
whichever toolkits are available on the current machine, writing to the exact
paths that `compute_fa_comparison.py` expects:

    data/hcp/<subject>/dti/fsl_dti_FA.nii.gz   (FSL dtifit,  if `dtifit` on PATH)
    data/hcp/<subject>/dti/fsl_dti_MD.nii.gz
    data/hcp/<subject>/dti/mrt_FA.nii.gz       (MRtrix3,     if `dwi2tensor` on PATH)
    data/hcp/<subject>/dti/mrt_MD.nii.gz
    data/hcp/<subject>/dti/dipy_FA.nii.gz      (DIPY,        if dipy importable)
    data/hcp/<subject>/dti/dipy_MD.nii.gz

    data/hcp/<subject>/dti/mask_fsl.nii.gz     (FSL bet)
    data/hcp/<subject>/dti/mask_mrtrix.nii.gz  (MRtrix3 dwi2mask)
    data/hcp/<subject>/dti/mask_dipy.nii.gz    (DIPY median_otsu)

Two distinct mask families are produced on purpose:

  * the *per-tool* masks above are each toolkit's own brain-extraction output,
    and are compared against one another by Dice coefficient (paper Table 3,
    Figure 4);
  * a single *shared* mask (shared_brain_mask.nii.gz, built with median_otsu)
    is fed to all three tensor fits, so that the FA/MD comparison isolates
    tensor-fitting differences from brain-masking differences.

This mirrors the logic in app/app.py Steps 1 and 4 so the paper's numbers can
be produced without launching the Streamlit UI.

Usage:
    python scripts/generate_fa_maps.py --subject stanford
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import nibabel as nib

ROOT = Path(__file__).parent.parent


def data_dir(subject: str) -> Path:
    return ROOT / "data" / "hcp" / subject / "T1w" / "Diffusion"


def best_shell_sel(bvals: np.ndarray, preferred: int = 1000):
    """b=0 + the shell closest to `preferred`. Matches app/app.py."""
    shells = np.unique(np.round(bvals, -2).astype(int))
    nonzero = shells[shells > 100]
    if nonzero.size == 0:
        raise ValueError("No non-zero b-value shells found")
    target = int(nonzero[np.argmin(np.abs(nonzero - preferred))])
    tol = max(100, int(target * 0.12))
    sel = (bvals < 50) | ((bvals > target - tol) & (bvals < target + tol))
    return sel, target


def prepare_input(dd: Path, dti: Path, shell: int | None) -> dict:
    """Resolve the exact data/bvals/bvecs every toolkit will be given.

    The single-tensor model assumes monoexponential signal decay, which does
    not hold across multiple b-value shells. FSL `dtifit` and MRtrix3
    `dwi2tensor` silently use every volume they are handed, whereas DIPY
    requires the shell to be chosen explicitly. Left alone, that asymmetry
    would mean the three toolkits fit different data, and any inter-tool
    difference would confound tensor fitting with shell selection.

    Passing --shell extracts b=0 plus one non-zero shell up front and hands
    the identical subset to all three tools, so the comparison isolates the
    fitting stage. For single-shell data no subsetting is needed.
    """
    bvals = np.loadtxt(str(dd / "bvals"))
    shells = sorted(int(s) for s in np.unique(np.round(bvals, -2)) if s > 100)

    if shell is None:
        if len(shells) > 1:
            print(f"WARNING: data is multi-shell (b = {shells}) but no --shell "
                  f"given.\n         All volumes will be fitted, which violates "
                  f"the single-tensor\n         model and confounds this "
                  f"comparison. Pass --shell <b-value>.")
        return {"data": dd / "data.nii.gz", "bvals": dd / "bvals",
                "bvecs": dd / "bvecs", "label": f"all {bvals.size} volumes"}

    if shell not in shells:
        sys.exit(f"Requested shell b={shell} not present. Available: {shells}")

    sel = (bvals < 50) | (np.abs(np.round(bvals, -2) - shell) < 1)
    n = int(sel.sum())
    print(f"Extracting shared single-shell subset: b=0 + b={shell} "
          f"({n} of {bvals.size} volumes)")

    img = nib.load(str(dd / "data.nii.gz"))
    sub = img.get_fdata(dtype=np.float32)[..., sel]
    bvecs = np.loadtxt(str(dd / "bvecs"))
    if bvecs.shape[0] != 3:
        bvecs = bvecs.T

    out = {"data": dti / "subset_data.nii.gz", "bvals": dti / "subset.bvals",
           "bvecs": dti / "subset.bvecs", "label": f"b=0 + b={shell}, {n} volumes"}
    nib.save(nib.Nifti1Image(sub, img.affine), str(out["data"]))
    np.savetxt(str(out["bvals"]), bvals[sel][None, :], fmt="%g")
    np.savetxt(str(out["bvecs"]), bvecs[:, sel], fmt="%.6f")
    return out


def run(cmd, label):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  !! {label} failed:\n{r.stderr}")
        return False
    return True


def make_b0_mean(dd: Path, dti: Path) -> Path:
    """Mean of all b<50 volumes — the input every brain-extraction tool sees."""
    out = dti / "b0_mean.nii.gz"
    if out.exists():
        return out
    from dipy.io.gradients import read_bvals_bvecs
    bv, _ = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
    img = nib.load(str(dd / "data.nii.gz"))
    b0 = img.get_fdata()[..., bv < 50].mean(axis=-1).astype(np.float32)
    nib.save(nib.Nifti1Image(b0, img.affine), str(out))
    print(f"  saved {out.name}")
    return out


def gen_mask_fsl(b0: Path, dti: Path) -> bool:
    """FSL bet — signal-intensity-based deformable surface model."""
    if not shutil.which("bet"):
        print("FSL: bet not on PATH — skipping mask")
        return False
    print("FSL: generating mask_fsl.nii.gz (bet)")
    ok = run(["bet", str(b0), str(dti / "mask_fsl_tmp"), "-m", "-n", "-f", "0.3"], "bet")
    if not ok:
        return False
    # bet writes <out>_mask.nii.gz when -m is given
    produced = dti / "mask_fsl_tmp_mask.nii.gz"
    if not produced.exists():
        print("  !! bet produced no mask file")
        return False
    produced.replace(dti / "mask_fsl.nii.gz")
    return True


def gen_mask_mrtrix(dd: Path, dti: Path) -> bool:
    """MRtrix3 dwi2mask — operates on the full DWI series, not just b=0."""
    if not shutil.which("dwi2mask"):
        print("MRtrix3: dwi2mask not on PATH — skipping mask")
        return False
    print("MRtrix3: generating mask_mrtrix.nii.gz (dwi2mask)")
    mif = dti / "dwi_raw.mif"
    if not mif.exists():
        if not run(["mrconvert", str(dd / "data.nii.gz"), str(mif),
                    "-fslgrad", str(dd / "bvecs"), str(dd / "bvals"), "-force"],
                   "mrconvert"):
            return False
    return run(["dwi2mask", str(mif), str(dti / "mask_mrtrix.nii.gz"), "-force"],
               "dwi2mask")


def gen_mask_dipy(dd: Path, dti: Path) -> bool:
    """DIPY median_otsu — median filtering followed by Otsu thresholding."""
    try:
        from dipy.segment.mask import median_otsu
        from dipy.io.gradients import read_bvals_bvecs
    except ImportError:
        print("DIPY: not importable — skipping mask")
        return False
    print("DIPY: generating mask_dipy.nii.gz (median_otsu)")
    bv, _ = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
    img = nib.load(str(dd / "data.nii.gz"))
    b0idx = list(np.where(bv < 50)[0])
    _, bm = median_otsu(img.get_fdata(), vol_idx=b0idx,
                        median_radius=2, numpass=1, dilate=1)
    nib.save(nib.Nifti1Image(bm.astype(np.uint8), img.affine),
             str(dti / "mask_dipy.nii.gz"))
    return True


def gen_mrtrix(inp: dict, dti: Path, mask: Path) -> bool:
    if not shutil.which("dwi2tensor"):
        print("MRtrix3: dwi2tensor not on PATH — skipping")
        return False
    print("MRtrix3: generating mrt_FA.nii.gz")
    # separate from dwi_raw.mif, which holds the full series used for masking
    mif = dti / "dwi_fit.mif"
    if not run(["mrconvert", str(inp["data"]), str(mif),
                "-fslgrad", str(inp["bvecs"]), str(inp["bvals"]), "-force"],
               "mrconvert"):
        return False
    tensor = dti / "mrt_tensor.mif"
    if not run(["dwi2tensor", str(mif), str(tensor), "-mask", str(mask), "-force"],
               "dwi2tensor"):
        return False
    return run(["tensor2metric", str(tensor),
                "-fa", str(dti / "mrt_FA.nii.gz"),
                "-adc", str(dti / "mrt_MD.nii.gz"),
                "-mask", str(mask), "-force"], "tensor2metric")


def gen_dipy(inp: dict, dti: Path, mask: Path) -> bool:
    try:
        from dipy.reconst.dti import (TensorModel, fractional_anisotropy,
                                       mean_diffusivity)
        from dipy.io.gradients import read_bvals_bvecs
        from dipy.core.gradients import gradient_table
    except ImportError:
        print("DIPY: not importable — skipping")
        return False
    print("DIPY: generating dipy_FA.nii.gz")
    # Shell selection already happened in prepare_input, so every volume here
    # is fitted -- exactly the volumes FSL and MRtrix3 receive.
    bv, bvc = read_bvals_bvecs(str(inp["bvals"]), str(inp["bvecs"]))
    img = nib.load(str(inp["data"]))
    data = img.get_fdata()
    msk = nib.load(str(mask)).get_fdata().astype(bool)
    gtab = gradient_table(bv, bvc)
    fit = TensorModel(gtab, fit_method="WLS").fit(data, mask=msk)
    FA = fractional_anisotropy(fit.evals).astype(np.float32)
    MD = mean_diffusivity(fit.evals).astype(np.float32)
    nib.save(nib.Nifti1Image(np.nan_to_num(FA), img.affine), str(dti / "dipy_FA.nii.gz"))
    nib.save(nib.Nifti1Image(np.nan_to_num(MD), img.affine), str(dti / "dipy_MD.nii.gz"))
    return True


def gen_fsl(inp: dict, dti: Path, mask: Path) -> bool:
    if not shutil.which("dtifit"):
        print("FSL: dtifit not on PATH — skipping (use Docker for FSL)")
        return False
    print("FSL: generating fsl_dti_FA.nii.gz")
    return run(["dtifit",
                "--data=" + str(inp["data"]),
                "--mask=" + str(mask),
                "--bvecs=" + str(inp["bvecs"]),
                "--bvals=" + str(inp["bvals"]),
                "--out=" + str(dti / "fsl_dti"),
                "--wls", "--save_tensor"], "dtifit")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject", default="stanford")
    ap.add_argument("--shell", type=int, default=None,
                    help="b-value of the single non-zero shell to fit. Required "
                         "for multi-shell data so that all three toolkits "
                         "receive identical input.")
    args = ap.parse_args()

    dd = data_dir(args.subject)
    dti = ROOT / "data" / "hcp" / args.subject / "dti"
    dti.mkdir(parents=True, exist_ok=True)

    if not (dd / "data.nii.gz").exists():
        sys.exit(f"No data at {dd}. Download Stanford HARDI first.")

    # Build ONE correct, shared brain mask for all tools (fair comparison).
    # The shipped nodif_brain_mask.nii.gz for Stanford is partial (~39k voxels
    # vs ~190k real brain) and corrupts FA, so we regenerate with median_otsu.
    mask = dti / "shared_brain_mask.nii.gz"
    if not mask.exists():
        try:
            from dipy.segment.mask import median_otsu
            from dipy.io.gradients import read_bvals_bvecs
        except ImportError:
            sys.exit("DIPY required to build the shared brain mask. Install dipy.")
        print("Building shared brain mask with median_otsu ...")
        bv, _ = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
        img = nib.load(str(dd / "data.nii.gz"))
        b0idx = list(np.where(bv < 50)[0])
        _, bm = median_otsu(img.get_fdata(), vol_idx=b0idx,
                            median_radius=2, numpass=1, dilate=1)
        nib.save(nib.Nifti1Image(bm.astype(np.uint8), img.affine), str(mask))
        print(f"  saved {mask} ({int(bm.sum()):,} voxels)")

    print(f"Subject: {args.subject}\nData: {dd}\nShared mask: {mask}\n")

    # ── Per-tool brain masks (Dice analysis, paper Table 3 / Figure 4) ────────
    print("--- Brain extraction (per-tool masks) ---")
    b0 = make_b0_mean(dd, dti)
    masks = {
        "FSL": gen_mask_fsl(b0, dti),
        "MRtrix3": gen_mask_mrtrix(dd, dti),
        "DIPY": gen_mask_dipy(dd, dti),
    }

    # ── Tensor fits: ONE shared mask AND one shared volume subset, so the
    #    comparison isolates the fitting stage from masking and shell choice.
    print("\n--- DTI fitting (shared mask, shared volumes) ---")
    inp = prepare_input(dd, dti, args.shell)
    print(f"Fitting input: {inp['label']}\n")
    results = {
        "FSL": gen_fsl(inp, dti, mask),
        "MRtrix3": gen_mrtrix(inp, dti, mask),
        "DIPY": gen_dipy(inp, dti, mask),
    }

    print("\nSummary:")
    print(f"  {'tool':<10}{'mask':<12}{'tensor fit'}")
    for k in ("FSL", "MRtrix3", "DIPY"):
        print(f"  {k:<10}{('OK' if masks[k] else 'skipped'):<12}"
              f"{'OK' if results[k] else 'skipped'}")
    n = sum(results.values())
    print(f"\n{n} tensor fit(s) available in {dti}")
    if n >= 2:
        print("Now run: python scripts/compute_fa_comparison.py --subject " + args.subject)
    if not results["FSL"]:
        print("\nNOTE: FSL is unavailable on this machine, so the paper's FSL rows\n"
              "      cannot be filled. Run this script inside the project Docker\n"
              "      image (which bundles FSL 6.0.7) to complete Table 3.")


if __name__ == "__main__":
    main()
