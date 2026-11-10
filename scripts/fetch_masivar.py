"""
Fetch the MASiVar test-retest scans used for the between-session comparison.

MASiVar (Cai et al., 2021, Magn Reson Med, doi 10.1002/mrm.28926) is distributed on
OpenNeuro as ds003416 under CC0 — no registration or credentials are needed.
Only the unprocessed (raw BIDS) diffusion scans are fetched, because every
arm of the comparison fits unprocessed data; the PreQual derivatives are not
used.

Cohorts fetched:

    I   one adult, repeated scans within and between sessions on one scanner
    II  five adults, each scanned on up to four scanners at three sites

Each 96-direction scan holds one b = 0 volume and 96 directions at a single
b-value, so a scan is a complete single-shell DTI acquisition by itself.

Usage:
    python scripts/fetch_masivar.py                      # b = 1000 only
    python scripts/fetch_masivar.py --shells 1000 1500   # add b = 1500
    python scripts/fetch_masivar.py --dry-run            # list, do not download
    python scripts/fetch_masivar.py --prequal            # PreQual-preprocessed scans

--prequal fetches the same scans as preprocessed by MASiVar's own pipeline,
PreQual v1.0.0 (MP-PCA denoising, topup or Synb0-DisCo, eddy with slice
imputation, inter-scan intensity normalisation), for a sensitivity analysis
on preprocessed data. Using the dataset's own preprocessing, rather than one
chosen here, keeps the preprocessing outside the comparison.
"""
import argparse
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BUCKET = "https://s3.amazonaws.com/openneuro.org"
DATASET = "ds003416"
SNAPSHOT = "2.0.2"   # OpenNeuro snapshot checked on 2026-11-10; S3 serves the latest
SUBJECTS = r"sub-c(Is1|IIs0\d)"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def list_keys(prefix):
    """Every object under prefix, as (key, size, etag)."""
    keys, token = [], None
    while True:
        url = f"{BUCKET}?list-type=2&max-keys=1000&prefix={urllib.parse.quote(prefix)}"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        root = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
        for c in root.findall("s:Contents", NS):
            keys.append((c.find("s:Key", NS).text, int(c.find("s:Size", NS).text),
                         c.find("s:ETag", NS).text.strip('"')))
        nxt = root.find("s:NextContinuationToken", NS)
        if nxt is None:
            return keys
        token = nxt.text


def select(keys, shells, prefix=""):
    pattern = re.compile(
        rf"^{DATASET}/{re.escape(prefix)}{SUBJECTS}/ses-[^/]+/dwi/[^/]+_acq-b({'|'.join(shells)})n96[^/]*_dwi\.(nii\.gz|bval|bvec)$")
    return [k for k in keys if pattern.match(k[0])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", type=Path, default=Path("data/masivar"))
    ap.add_argument("--shells", nargs="+", default=["1000"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prequal", action="store_true",
                    help="fetch the PreQual v1.0.0 derivatives instead of the raw scans")
    args = ap.parse_args()

    prefix = "derivatives/prequal-v1.0.0/" if args.prequal else ""
    files = []
    for sub in ["sub-cIs1"] + [f"sub-cIIs0{i}" for i in range(5)]:
        files += select(list_keys(f"{DATASET}/{prefix}{sub}/"), args.shells, prefix)
    total = sum(s for _, s, _ in files)
    print(f"{len(files)} files, {total / 1e9:.2f} GB (OpenNeuro {DATASET}, snapshot {SNAPSHOT})")

    args.outdir.mkdir(parents=True, exist_ok=True)
    with open(args.outdir / ("manifest_prequal.tsv" if args.prequal else "manifest.tsv"), "w") as m:
        m.write("path\tbytes\tetag\n")
        for key, size, etag in files:
            m.write(f"{key[len(DATASET) + 1:]}\t{size}\t{etag}\n")
    if args.dry_run:
        return

    for i, (key, size, _) in enumerate(files, 1):
        dest = args.outdir / key[len(DATASET) + 1:]
        if dest.exists() and dest.stat().st_size == size:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(f"{BUCKET}/{urllib.parse.quote(key)}", tmp)
        if tmp.stat().st_size != size:
            sys.exit(f"size mismatch for {key}")
        tmp.rename(dest)
        print(f"[{i}/{len(files)}] {dest}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
