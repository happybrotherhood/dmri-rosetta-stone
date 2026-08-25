"""
Fetch a real, open-access dMRI dataset from DIPY — no credentials needed.
Downloads on first run; cached in ~/.dipy for subsequent runs.

Available datasets (all real human acquisitions):

    stanford    Stanford HARDI     single shell, b = 2000            ~50 MB
    sherbrooke  Sherbrooke 3-shell three shells, b = 1000/2000/3500  ~40 MB

The two come from different sites and protocols, so running the inter-tool
comparison on both provides an independent replication rather than a second
look at the same acquisition.

Usage:
    python scripts/fetch_sample_data.py --subject stanford
    python scripts/fetch_sample_data.py --subject sherbrooke
"""
import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
import nibabel as nib

# subject label -> DIPY fetcher name
DATASETS = {
    "stanford": "stanford_hardi",
    "sherbrooke": "sherbrooke_3shell",
}


def fetch(outdir: Path, subject: str) -> Path:
    try:
        from dipy.data import get_fnames
        from dipy.segment.mask import median_otsu
    except ImportError:
        print("ERROR: dipy not installed. Run: pip install dipy", file=sys.stderr)
        sys.exit(1)

    if subject not in DATASETS:
        sys.exit(f"Unknown subject '{subject}'. Choose from: "
                 f"{', '.join(DATASETS)}")

    name = DATASETS[subject]
    print(f"Fetching {name} (cached after first download)...")
    fdwi, fbval, fbvec = get_fnames(name)

    dd = outdir / subject / "T1w" / "Diffusion"
    dd.mkdir(parents=True, exist_ok=True)

    shutil.copy(fdwi,  str(dd / "data.nii.gz"))
    shutil.copy(fbval, str(dd / "bvals"))
    shutil.copy(fbvec, str(dd / "bvecs"))

    img = nib.load(str(dd / "data.nii.gz"))
    bvals = np.loadtxt(str(dd / "bvals"))
    shells = np.unique(np.round(bvals, -2).astype(int))
    print(f"  shape {img.shape}, shells {shells.tolist()}")

    print("Computing brain mask with median_otsu...")
    data = img.get_fdata(dtype=np.float32)
    b0_idx = list(np.where(bvals < 50)[0])
    _, mask = median_otsu(data, vol_idx=b0_idx, median_radius=2, numpass=1, dilate=1)
    nib.save(nib.Nifti1Image(mask.astype(np.uint8), img.affine),
             str(dd / "nodif_brain_mask.nii.gz"))

    print(f"\nDone. Data in: {dd}")
    return dd


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir",  default="./data/hcp")
    p.add_argument("--subject", default="stanford", choices=sorted(DATASETS))
    args = p.parse_args()
    fetch(Path(args.outdir), args.subject)
