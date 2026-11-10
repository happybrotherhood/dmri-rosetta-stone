"""
Estimator differences against test-retest variability on MASiVar.

Reads the fits written by fit_test_retest.py and asks the question Reviewer 1
(S5) put: are the differences between tensor-fitting estimators small or large
compared with how much the same measure varies when the same person is scanned
again?

For every scan, one white-matter mask is used for all five arms: voxels inside
the shared brain mask whose tensor is admissible in every arm (all eigenvalues
>= 0, largest <= 3.0 um^2/ms) and whose FA exceeds 0.2 in every arm. Each arm
is then summarised by its mean FA and MD over that mask, so the arms are
compared on identical voxels.

Variability, for a fixed estimator, is decomposed with the MASiVar design:

    within session     Cohort I, repeated scans in one session
    between sessions   Cohort I, session means; Cohort II, repeat sessions
                       on the same scanner (scanners 1A and 1B)
    between scanners   Cohort II, one session per scanner, per subject
    between subjects   Cohort II, the five subjects on the same scanner

Each is reported as a coefficient of variation (SD / mean, %), and set
against the estimator offset of the same scans (arm minus reference, % of the
reference mean).

A systematic offset that were the same in every scan would cancel in any
comparison made with one estimator. The offset is therefore also reported as
it varies: its spread across scans, its mean on each scanner, and the change
it makes to between-scanner variability.

--source prequal repeats everything on MASiVar's PreQual-preprocessed scans
(fit_test_retest.py --source prequal); SNR is then taken from the raw version
of each scan, because a noise map made after denoising no longer describes
the noise.

Output (repository root): test_retest_b<shell>[_prequal].txt
and a per-scan table test_retest_scans_b<shell>[_prequal].tsv
"""
import argparse
import re
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "masivar" / "derivatives" / "rosetta"
ARMS = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls"]
LABEL = {"fsl_ols": "FSL default (OLS)", "fsl_wls": "FSL --wls (measured)",
         "mrt_iwls": "MRtrix3 default (IWLS)", "mrt_wls": "MRtrix3 -iter 0 (measured)",
         "dipy_wls": "DIPY WLS (predicted)"}
LMAX = 3.0e-3   # mm^2/s, free water at body temperature


def load(d, name):
    return nib.load(str(d / name)).get_fdata(dtype=np.float32)


def scan_summary(d, raw):
    brain = load(d, "mask.nii.gz") > 0
    A = {a: {k: load(d, f"{a}_{k}.nii.gz") for k in ("FA", "MD", "L1", "L2", "L3")} for a in ARMS}
    wm = brain.copy()
    row = {"brain": int(brain.sum())}
    for a in ARMS:
        ev = np.stack([A[a]["L1"], A[a]["L2"], A[a]["L3"]])
        ok = (ev.min(0) >= 0) & (ev.max(0) <= LMAX)
        row[f"{a}_negeig"] = int((brain & (ev.min(0) < 0)).sum())
        row[f"{a}_inadm"] = int((brain & ~ok).sum())
        wm &= ok & (A[a]["FA"] > 0.2)
    row["wm"] = int(wm.sum())
    for a in ARMS:
        row[f"{a}_FA"] = float(A[a]["FA"][wm].mean())
        row[f"{a}_MD"] = float(A[a]["MD"][wm].mean() * 1e3)   # um^2/ms
    row["voxel_mm"] = "x".join(f"{z:.1f}" for z in nib.load(str(d / "mask.nii.gz")).header.get_zooms()[:3])
    if not (d / "noise.nii.gz").exists():
        row["snr_b0"] = float("nan")   # preprocessed scan; filled in from the raw scan
        return row
    # SNR of the single b = 0 volume over white matter, against the MP-PCA sigma
    img = nib.load(str(raw))
    bvals = np.loadtxt(str(raw)[: -len(".nii.gz")] + ".bval")
    b0 = np.asarray(img.dataobj[..., int(np.argmin(bvals))], dtype=np.float32)
    sigma = np.median(load(d, "noise.nii.gz")[wm])
    # MP-PCA needs spatially independent noise. Scans stored at an interpolated
    # in-plane resolution (site 2, 0.94 mm) violate this and return sigma = 0 in
    # most voxels; their SNR is left undefined rather than reported as infinite.
    row["snr_b0"] = float(b0[wm].mean() / sigma) if sigma > 0 else float("nan")
    return row


def cov(x):
    x = np.asarray(x, float)
    return 100 * x.std(ddof=1) / x.mean() if x.size > 1 else np.nan


def pooled_cov(groups):
    """Pooled within-group CoV (%): root mean of within-group variances over the grand mean."""
    gs = [np.asarray(g, float) for g in groups if len(g) > 1]
    if not gs:
        return np.nan
    var = sum(((g - g.mean()) ** 2).sum() for g in gs) / sum(g.size - 1 for g in gs)
    return 100 * np.sqrt(var) / np.concatenate(gs).mean()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shell", default="1000")
    ap.add_argument("--ref", default="fsl_wls", choices=ARMS)
    ap.add_argument("--source", default="raw", choices=["raw", "prequal"])
    args = ap.parse_args()
    tag = f"b{args.shell}" + ("" if args.source == "raw" else f"_{args.source}")
    base = DER / tag

    rows = []
    for done in sorted(base.glob("sub-*/ses-*/run-*/done")):
        d = done.parent
        sub, ses, rn = d.parts[-3], d.parts[-2], d.parts[-1]
        raw = ROOT / "data" / "masivar" / done.read_text().strip()
        m = re.match(r"ses-s(\d)([AB]?)x(\d)", ses)
        r = {"sub": sub, "ses": ses, "run": rn, "cohort": "I" if sub.startswith("sub-cIs") else "II",
             "scanner": m.group(1) + m.group(2), "repeat": int(m.group(3))}
        r.update(scan_summary(d, raw))
        rows.append(r)
    if args.source != "raw":
        raw_tsv = ROOT / f"test_retest_scans_b{args.shell}.tsv"
        if not raw_tsv.exists():
            raise SystemExit(f"Run the raw analysis first: {raw_tsv} is needed for SNR")
        lines = [l.split("\t") for l in raw_tsv.read_text().splitlines()]
        idx = {c: i for i, c in enumerate(lines[0])}
        snr_raw = {(l[idx["sub"]], l[idx["ses"]], l[idx["run"]]): float(l[idx["snr_b0"]]) for l in lines[1:]}
        for r in rows:
            r["snr_b0"] = snr_raw.get((r["sub"], r["ses"], r["run"]), float("nan"))

    cols = list(rows[0].keys())
    with open(ROOT / f"test_retest_scans_{tag}.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(f"{r[c]:.5f}" if isinstance(r[c], float) else str(r[c]) for c in cols) + "\n")

    out = []
    p = out.append
    src = "unprocessed" if args.source == "raw" else "PreQual-preprocessed (SNR from the raw scans)"
    p(f"MASiVar, b = {args.shell} s/mm^2, {src}; {len(rows)} scans "
      f"({sum(r['cohort'] == 'I' for r in rows)} Cohort I, {sum(r['cohort'] == 'II' for r in rows)} Cohort II)")
    p("White matter: FA > 0.2 and admissible eigenvalues in all five arms, per scan. MD in um^2/ms.")
    snrs = np.array([r["snr_b0"] for r in rows])
    p(f"Median WM voxels per scan {np.median([r['wm'] for r in rows]):,.0f}; "
      f"b = 0 SNR {np.nanmin(snrs):.1f}-{np.nanmax(snrs):.1f} "
      f"(undefined for {int(np.isnan(snrs).sum())} scans with interpolated voxels, where MP-PCA fails)")
    p("")

    I = [r for r in rows if r["cohort"] == "I"]
    II = [r for r in rows if r["cohort"] == "II"]
    for metric in ("FA", "MD"):
        p(f"=== {metric}: variability for a fixed estimator (CoV, %) ===")
        p(f"{'arm':<28}{'within ses':>11}{'between ses':>12}{'betw ses II':>12}{'betw scanner':>13}{'betw subject':>13}")
        for a in ARMS:
            k = f"{a}_{metric}"
            within = pooled_cov([[r[k] for r in I if r["ses"] == s] for s in sorted({r["ses"] for r in I})])
            between = cov([np.mean([r[k] for r in I if r["ses"] == s]) for s in sorted({r["ses"] for r in I})])
            rep = pooled_cov([[r[k] for r in II if r["sub"] == s and r["scanner"] == sc]
                              for s in sorted({r["sub"] for r in II}) for sc in ("1A", "1B")])
            first = [r for r in II if r["repeat"] == 1]
            scan = pooled_cov([[r[k] for r in first if r["sub"] == s] for s in sorted({r["sub"] for r in first})])
            subj = np.nanmean([cov([r[k] for r in first if r["scanner"] == sc])
                               for sc in sorted({r["scanner"] for r in first})])
            p(f"{LABEL[a]:<28}{within:>11.2f}{between:>12.2f}{rep:>12.2f}{scan:>13.2f}{subj:>13.2f}")
        p("")
        p(f"=== {metric}: estimator offset, arm minus {LABEL[args.ref]} (% of reference mean) ===")
        p(f"{'arm':<28}{'mean %':>9}{'min %':>9}{'max %':>9}{'mean abs':>10}")
        for a in ARMS:
            pct = np.array([100 * (r[f"{a}_{metric}"] - r[f"{args.ref}_{metric}"]) / r[f"{args.ref}_{metric}"] for r in rows])
            ab = np.array([r[f"{a}_{metric}"] - r[f"{args.ref}_{metric}"] for r in rows])
            p(f"{LABEL[a]:<28}{pct.mean():>+9.2f}{pct.min():>+9.2f}{pct.max():>+9.2f}{np.abs(ab).mean():>10.4f}")
        p("Between toolkit defaults (% of the second):")
        for a, b in (("fsl_ols", "mrt_iwls"), ("fsl_ols", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            pct = np.array([100 * (r[f"{a}_{metric}"] - r[f"{b}_{metric}"]) / r[f"{b}_{metric}"] for r in rows])
            p(f"  {LABEL[a]} vs {LABEL[b]}: mean {pct.mean():+.2f}%, range {pct.min():+.2f} to {pct.max():+.2f}%")
        p("")

    p("=== The offset is not constant: how it varies between scans ===")
    p("Offset between weighting schemes = FSL --wls (measured) minus DIPY WLS (predicted);")
    p("between defaults = FSL default (OLS) minus MRtrix3 default (IWLS). Cohort II, first session per scanner.")
    first = [r for r in II if r["repeat"] == 1]
    scanners = sorted({r["scanner"] for r in first})
    for metric in ("FA", "MD"):
        ref_mean = np.mean([r[f"dipy_wls_{metric}"] for r in rows])
        for name, a, b in (("weighting schemes", "fsl_wls", "dipy_wls"), ("defaults", "fsl_ols", "mrt_iwls")):
            off = np.array([r[f"{a}_{metric}"] - r[f"{b}_{metric}"] for r in rows])
            per = {sc: np.mean([r[f"{a}_{metric}"] - r[f"{b}_{metric}"] for r in first if r["scanner"] == sc])
                   for sc in scanners}
            spread = max(per.values()) - min(per.values())
            p(f"{metric}, {name}: across all scans SD {off.std(ddof=1):.4f} "
              f"({100 * off.std(ddof=1) / ref_mean:.2f}% of mean {metric}); "
              f"per scanner " + ", ".join(f"{sc} {v:+.4f}" for sc, v in per.items())
              + f"; largest difference between scanners {spread:.4f} ({100 * spread / ref_mean:.2f}%)")
        bs = {a: pooled_cov([[r[f"{a}_{metric}"] for r in first if r["sub"] == s]
                             for s in sorted({r["sub"] for r in first})]) for a in ARMS}
        subj = np.nanmean([cov([r[f"dipy_wls_{metric}"] for r in first if r["scanner"] == sc]) for sc in scanners])
        p(f"{metric}: between-scanner CoV {bs['fsl_wls']:.2f}% with measured-signal weighting against "
          f"{min(bs[a] for a in ('fsl_ols', 'mrt_iwls', 'dipy_wls')):.2f}-"
          f"{max(bs[a] for a in ('fsl_ols', 'mrt_iwls', 'dipy_wls')):.2f}% with the three defaults "
          f"(ratio {bs['fsl_wls'] / bs['dipy_wls']:.2f}); between-subject CoV {subj:.2f}%")
        p("")

    p("=== Offset between weighting schemes against scan SNR ===")
    snr = np.array([r["snr_b0"] for r in rows])
    try:
        from scipy.stats import spearmanr
        for metric in ("FA", "MD"):
            off = np.array([r[f"fsl_wls_{metric}"] - r[f"dipy_wls_{metric}"] for r in rows])
            ok = np.isfinite(snr)
            rho, pv = spearmanr(snr[ok], off[ok])
            p(f"{metric} (FSL --wls minus DIPY WLS): Spearman rho with b = 0 SNR = {rho:+.3f} "
              f"(p = {pv:.2g}, n = {int(ok.sum())})")
    except ImportError:
        p("scipy not available")
    p("")
    p("=== Admissibility (brain mask, % of voxels) ===")
    for a in ARMS:
        inad = np.array([100 * r[f"{a}_inadm"] / r["brain"] for r in rows])
        neg = np.array([100 * r[f"{a}_negeig"] / r["brain"] for r in rows])
        p(f"{LABEL[a]:<28} inadmissible {inad.mean():.2f}% (range {inad.min():.2f}-{inad.max():.2f}); "
          f"negative eigenvalue {neg.mean():.2f}%")

    text = "\n".join(out)
    (ROOT / f"test_retest_{tag}.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
