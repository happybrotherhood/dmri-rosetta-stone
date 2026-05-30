"""
Download HCP subject data from AWS S3.

Usage:
    python download_hcp.py --subject 100307 --outdir ./data/hcp

You need an HCP account + AWS credentials. Set them once with:
    aws configure   (or export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)

HCP data access: https://db.humanconnectome.org/
"""

import argparse
import boto3
import os
import sys
from pathlib import Path

HCP_BUCKET = "hcp-openaccess"

# Minimally preprocessed DWI files for a single subject
DWI_FILES = [
    "{subject}/T1w/Diffusion/data.nii.gz",
    "{subject}/T1w/Diffusion/bvals",
    "{subject}/T1w/Diffusion/bvecs",
    "{subject}/T1w/Diffusion/nodif_brain_mask.nii.gz",
    "{subject}/T1w/T1w_acpc_dc_restore_brain.nii.gz",
    "{subject}/MNINonLinear/ROIs/Atlas_ROIs.2.nii.gz",
]


def download_subject(subject: str, outdir: Path, dry_run: bool = False):
    s3 = boto3.client("s3")
    outdir.mkdir(parents=True, exist_ok=True)

    for template in DWI_FILES:
        key = template.format(subject=subject)
        local_path = outdir / key
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if local_path.exists():
            print(f"  [skip]  {key}  (already downloaded)")
            continue

        print(f"  [fetch] s3://{HCP_BUCKET}/{key}")
        if not dry_run:
            try:
                s3.download_file(HCP_BUCKET, key, str(local_path))
            except Exception as e:
                print(f"    ERROR: {e}", file=sys.stderr)

    print(f"\nDone. Data in: {outdir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", default="100307",
                        help="HCP subject ID (default: 100307)")
    parser.add_argument("--outdir", default="./data/hcp",
                        help="Local output directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print files to download without downloading")
    args = parser.parse_args()

    download_subject(args.subject, Path(args.outdir), dry_run=args.dry_run)
