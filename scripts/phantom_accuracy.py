"""
phantom_accuracy.py
-------------------
Measure each toolkit's tensor fit against a known ground truth, at several
noise levels.

The comparison on real data can only say that toolkits differ; with no true
tensor to compare against it cannot say which is closer to correct. This
script scores fits of synthetic phantoms, whose generating eigenvalues are
known exactly, against those eigenvalues.

The phantom (scripts/make_test_data.py, Rician noise, 10 b = 0 volumes and
30 directions at b = 1000 s/mm^2 after shell selection) contains three
regions. Two have a well-defined single-tensor ground truth:

    isotropic     evals 0.9, 0.9, 0.9      -> FA 0.0000, MD 0.90 um^2/ms
    single fibre  evals 1.4, 0.35, 0.35    -> FA 0.7071, MD 0.70 um^2/ms

The third is a crossing-fibre region, where no single tensor is correct by
construction; it is excluded rather than scored.

One phantom is generated per SNR, and each is fitted three times so that
every arm is present:

    python scripts/make_test_data.py   --subject phantom_rician_snr10 --snr 10 --outdir data/hcp
    python scripts/generate_fa_maps.py --subject phantom_rician_snr10 --shell 1000
    python scripts/generate_fa_maps.py --subject phantom_rician_snr10 --shell 1000 --mrtrix-iter 0
    python scripts/generate_fa_maps.py --subject phantom_rician_snr10 --shell 1000 --mrtrix-iter 0 --fsl-ols

Usage:
    python scripts/phantom_accuracy.py [--snr 30 20 10]

Outputs:
    phantom_accuracy.txt
"""

import argparse
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).parent.parent
SUBJECT = "phantom_rician_snr{snr:g}"

# Ground truth, in the units the toolkits report (mm^2/s).
EVALS_ISO = np.array([0.9e-3, 0.9e-3, 0.9e-3])
EVALS_WM = np.array([1.4e-3, 0.35e-3, 0.35e-3])


def fa_of(evals: np.ndarray) -> float:
    m = evals.mean()
    return float(np.sqrt(1.5) * np.sqrt(((evals - m) ** 2).sum())
                 / np.sqrt((evals ** 2).sum()))


TRUTH = {
    "isotropic":    dict(z=(0, 10),  fa=fa_of(EVALS_ISO), md=EVALS_ISO.mean()),
    "single fibre": dict(z=(10, 20), fa=fa_of(EVALS_WM),  md=EVALS_WM.mean()),
}

# (label, source of weights, run directory, file prefix)
ARMS = [
    ("FSL dtifit --wls",        "measured",   "dti",              "fsl_dti"),
    ("MRtrix3 -iter 0",         "measured",   "dti_iter0",        "mrt"),
    ("DIPY WLS",                "predicted",  "dti",              "dipy"),
    ("MRtrix3 default (IWLS)",  "predicted",  "dti",              "mrt"),
    ("FSL default (OLS)",       "unweighted", "dti_iter0_fslols", "fsl_dti"),
]


def load(subject: str, sub_dir: str, name: str):
    p = ROOT / "data" / "hcp" / subject / sub_dir / name
    if not p.exists():
        return None
    return np.nan_to_num(nib.load(str(p)).get_fdata(dtype=np.float32))


def score(subject: str):
    rows = []
    for label, weights, sub_dir, prefix in ARMS:
        fa = load(subject, sub_dir, f"{prefix}_FA.nii.gz")
        md = load(subject, sub_dir, f"{prefix}_MD.nii.gz")
        mask = load(subject, sub_dir, "shared_brain_mask.nii.gz")
        if fa is None or md is None or mask is None:
            print(f"  skipping {label}: maps not found in {subject}/{sub_dir}/")
            continue
        for region, spec in TRUTH.items():
            z0, z1 = spec["z"]
            sl = np.s_[:, :, z0:z1]
            # Trim each region's outer shell: two voxels in-plane and one slice
            # through-plane, so no scored voxel sits at a region boundary.
            core = np.s_[2:-2, 2:-2, 1:-1]
            inside = mask[sl][core].ravel() > 0
            f = fa[sl][core].ravel()[inside]
            m = md[sl][core].ravel()[inside] * 1e3
            fa_err = f - spec["fa"]
            md_err = m - spec["md"] * 1e3
            rows.append(dict(
                arm=label, weights=weights, region=region, n=f.size,
                fa_bias=fa_err.mean(), fa_se=fa_err.std(ddof=1) / np.sqrt(f.size),
                fa_rmse=float(np.sqrt((fa_err ** 2).mean())),
                md_bias=md_err.mean(), md_se=md_err.std(ddof=1) / np.sqrt(m.size),
                md_rmse=float(np.sqrt((md_err ** 2).mean())),
            ))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snr", type=float, nargs="+", default=[30, 20, 10])
    args = ap.parse_args()

    results = {}
    for snr in args.snr:
        subject = SUBJECT.format(snr=snr)
        if not (ROOT / "data" / "hcp" / subject).exists():
            sys.exit(f"No phantom {subject}. See the usage notes at the top.")
        results[snr] = score(subject)

    out = ROOT / "phantom_accuracy.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")

        w("Accuracy against a known ground truth (synthetic phantom, Rician noise)")
        w("=" * 96)
        w("Fitted input: 10 b=0 + 30 directions at b=1000. SNR is that of one b=0 volume.")
        w("Bias is estimate minus truth; SE is its standard error across voxels.")
        w("Crossing-fibre region excluded: no single tensor is correct there.")
        for snr, rows in results.items():
            for region, spec in TRUTH.items():
                sel = [r for r in rows if r["region"] == region]
                if not sel:
                    continue
                w()
                w(f"SNR {snr:g}  {region.upper()}   true FA = {spec['fa']:.4f}, "
                  f"true MD = {spec['md']*1e3:.4f} um^2/ms   (n = {sel[0]['n']:,} voxels)")
                w(f"  {'arm':<25}{'weights':<12}{'FA bias':>9}{'SE':>8}{'FA RMSE':>9}"
                  f"{'MD bias':>10}{'SE':>8}{'MD RMSE':>9}")
                for r in sel:
                    w(f"  {r['arm']:<25}{r['weights']:<12}{r['fa_bias']:>+9.4f}"
                      f"{r['fa_se']:>8.4f}{r['fa_rmse']:>9.4f}{r['md_bias']:>+10.4f}"
                      f"{r['md_se']:>8.4f}{r['md_rmse']:>9.4f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
