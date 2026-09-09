"""
phantom_accuracy.py
-------------------
Measure each toolkit's tensor fit against a known ground truth.

The comparison on real data can only say that toolkits differ; with no true
tensor to compare against it cannot say which is closer to correct. This
script fits the same synthetic phantom with all three, where the eigenvalues
that generated the signal are known exactly, and reports the error against
them.

The phantom (scripts/make_test_data.py) contains three regions. Two have a
well-defined single-tensor ground truth:

    isotropic     evals 0.9, 0.9, 0.9      -> FA 0.0000, MD 0.90 um^2/ms
    single fibre  evals 1.4, 0.35, 0.35    -> FA 0.7071, MD 0.70 um^2/ms

The third is a crossing-fibre region, where no single tensor is correct by
construction; it is excluded rather than scored.

Estimators are matched deliberately: FSL --wls, MRtrix3 -iter 0 and DIPY WLS
are the same algorithm. MRtrix3's default (two IWLS reweightings) is scored
as a fourth arm, since that is what a user gets without passing options.

Usage:
    python scripts/phantom_accuracy.py

Outputs:
    phantom_accuracy.txt
"""

import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).parent.parent
SUBJ = "phantom"
DD = ROOT / "data" / "hcp" / SUBJ / "T1w" / "Diffusion"

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

ARMS = [
    ("FSL dtifit --wls",        "dti_iter0", "fsl_dti"),
    ("MRtrix3 -iter 0 (WLS)",   "dti_iter0", "mrt"),
    ("DIPY WLS",                "dti_iter0", "dipy"),
    ("MRtrix3 default (IWLS)",  "dti",       "mrt"),
]


def load(sub_dir: str, prefix: str, metric: str):
    p = ROOT / "data" / "hcp" / SUBJ / sub_dir / f"{prefix}_{metric}.nii.gz"
    if not p.exists():
        return None
    return np.nan_to_num(nib.load(str(p)).get_fdata(dtype=np.float32))


def main():
    if not (DD / "data.nii.gz").exists():
        sys.exit(f"No phantom at {DD}. Run:\n"
                 f"  python scripts/make_test_data.py --subject {SUBJ} "
                 f"--outdir data/hcp")

    rows = []
    for label, sub_dir, prefix in ARMS:
        fa = load(sub_dir, prefix, "FA")
        md = load(sub_dir, prefix, "MD")
        if fa is None or md is None:
            print(f"skipping {label}: maps not found in {sub_dir}/")
            continue
        for region, spec in TRUTH.items():
            z0, z1 = spec["z"]
            sl = np.s_[:, :, z0:z1]
            # Trim the outer shell of each region: voxels at a region boundary
            # mix two tissue types and have no single ground truth.
            f = fa[sl][2:-2, 2:-2, 1:-1].ravel()
            m = md[sl][2:-2, 2:-2, 1:-1].ravel() * 1e3
            rows.append(dict(
                arm=label, region=region, n=f.size,
                fa_true=spec["fa"], fa_mean=f.mean(),
                fa_bias=f.mean() - spec["fa"],
                fa_rmse=float(np.sqrt(((f - spec["fa"]) ** 2).mean())),
                md_true=spec["md"] * 1e3, md_mean=m.mean(),
                md_bias=m.mean() - spec["md"] * 1e3,
                md_rmse=float(np.sqrt(((m - spec["md"] * 1e3) ** 2).mean())),
            ))

    if not rows:
        sys.exit("No results. Fit the phantom first with generate_fa_maps.py.")

    out = ROOT / "phantom_accuracy.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s)
            fh.write(s + "\n")

        w("Accuracy against a known ground truth (synthetic phantom)")
        w("=" * 72)
        w("Estimators matched: FSL --wls, MRtrix3 -iter 0 and DIPY WLS are the")
        w("same algorithm. MRtrix3's default is listed separately.")
        w("Crossing-fibre region excluded: no single tensor is correct there.")
        for region in TRUTH:
            spec = TRUTH[region]
            w()
            w(f"{region.upper()}   true FA = {spec['fa']:.4f}, "
              f"true MD = {spec['md']*1e3:.4f} um^2/ms")
            w(f"  {'arm':<26}{'FA mean':>9}{'FA bias':>10}{'FA RMSE':>9}"
              f"{'MD mean':>10}{'MD bias':>10}{'MD RMSE':>9}")
            for r in [r for r in rows if r["region"] == region]:
                w(f"  {r['arm']:<26}{r['fa_mean']:>9.4f}{r['fa_bias']:>+10.4f}"
                  f"{r['fa_rmse']:>9.4f}{r['md_mean']:>10.4f}"
                  f"{r['md_bias']:>+10.4f}{r['md_rmse']:>9.4f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
