"""
Fetch DIPY's Stanford HARDI dataset — real brain dMRI, no credentials needed.
Downloads ~50 MB on first run; cached in ~/.dipy for subsequent runs.

Usage:
    python scripts/fetch_sample_data.py [--outdir data/hcp] [--subject stanford]
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import nibabel as nib


def fetch(outdir: Path, subject: str) -> Path:
    try:
        from dipy.data import get_fnames
        from dipy.segment.mask import median_otsu
    except ImportError:
        print("ERROR: dipy not installed. Run: pip install dipy", file=sys.stderr)
        sys.exit(1)

    print("Fetching Stanford HARDI dataset (~50 MB, cached after first download)...")
    fdwi, fbval, fbvec = get_fnames("stanford_hardi")

    dd = outdir / subject / "T1w" / "Diffusion"
    dd.mkdir(parents=True, exist_ok=True)

    shutil.copy(fdwi,  str(dd / "data.nii.gz"))
    shutil.copy(fbval, str(dd / "bvals"))
    shutil.copy(fbvec, str(dd / "bvecs"))

    print("Computing brain mask with median_otsu...")
    img    = nib.load(str(dd / "data.nii.gz"))
    data   = img.get_fdata(dtype=np.float32)
    bvals  = np.loadtxt(str(dd / "bvals"))
    b0_idx = list(np.where(bvals < 50)[0])
    _, mask = median_otsu(data, vol_idx=b0_idx, median_radius=2, numpass=1, dilate=1)
    nib.save(nib.Nifti1Image(mask.astype(np.uint8), img.affine),
             str(dd / "nodif_brain_mask.nii.gz"))

    print(f"\nDone. Data in: {dd}")
    return dd


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir",  default="./data/hcp")
    p.add_argument("--subject", default="stanford")
    args = p.parse_args()
    fetch(Path(args.outdir), args.subject)
