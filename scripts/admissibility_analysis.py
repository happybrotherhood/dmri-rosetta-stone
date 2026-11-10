"""
admissibility_analysis.py
-------------------------
Phase-1 revisions requested by both reviewers, on the fits written by
fit_all_arms.py (data/hcp/<subject>/arms/).

1. Admissibility on the eigenvalues (R1 S3, R2 point 3). The published
   criterion, FA in [0, 1] and 0 < MD <= 3.0 um^2/ms, does not exclude a
   tensor with one negative eigenvalue (1.0, 1.0, -0.1 gives FA 0.776 and
   MD 0.633), nor one with a very large eigenvalue offset by a small one. A
   tensor is now admissible when all eigenvalues are >= 0 and the largest is
   <= 3.0 um^2/ms. Failures are counted by type, for every arm, and for DIPY
   both before and after its eigenvalue clipping; the unclipped DIPY values
   come from the reimplementation in tensor_estimators.py, which reproduces
   DIPY's maps.

2. Where inadmissible voxels lie (R1 S3): isolated or clustered, at the
   brain edge, in CSF, in voxels with low or non-positive measurements.

3. Tables 2, 3 and 5 on a voxel set defined without any tensor estimator
   (R2 point 3): white matter from two-channel FSL FAST (mean b = 0 and
   mean DWI), PVE >= 0.5, with PVE >= 0.9 as a sensitivity check.
   Within it, a pair is compared on the voxels admissible in both arms, and
   the number each arm loses is stated. The same pairs are also summarised
   over every voxel of the mask, with no exclusion, by robust statistics.

4. FSL --wls against MRtrix3 -iter 0 in detail (R2 point 4): quantiles and
   maxima of the differences in FA, MD and all six tensor components, after
   bringing both into one frame, and what the voxels that differ have in
   common.

Usage:
    python scripts/admissibility_analysis.py

Outputs:
    admissibility_analysis.txt
    data/hcp/<subject>/arms/inadmissible_<arm>.nii.gz   failure type per voxel
"""
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.stats import pearsonr

sys.path.insert(0, str(Path(__file__).parent))
import tensor_estimators as te  # noqa: E402
from arms import tissue  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls", "dipy_nlls", "dipy_restore"]
LABEL = {"fsl_ols": "FSL default (OLS)", "fsl_wls": "FSL --wls", "mrt_iwls": "MRtrix3 default (IWLS)",
         "mrt_wls": "MRtrix3 -iter 0", "dipy_wls": "DIPY WLS (default)", "dipy_nlls": "DIPY NLLS",
         "dipy_restore": "DIPY RESTORE", "dipy_wls_raw": "DIPY WLS, unclipped"}
LMAX = 3.0          # um^2/ms
COMP = ["Dxx", "Dyy", "Dzz", "Dxy", "Dxz", "Dyz"]
# failure codes written to inadmissible_<arm>.nii.gz
CODE = {"negative eigenvalue": 1, "largest eigenvalue > 3": 2}


def load(d, name):
    return np.nan_to_num(np.asarray(nib.load(str(d / name)).dataobj, dtype=np.float64))


def stats(a, b):
    d = a - b
    return pearsonr(a, b)[0] if a.size > 2 else np.nan, np.abs(d).mean(), d.mean()


def main():
    out = ROOT / "admissibility_analysis.txt"
    lines = []

    def w(s=""):
        print(s, flush=True)
        lines.append(s)

    w("Phase-1 analyses: eigenvalue admissibility, independent voxel set, implementation agreement")
    w("MD and eigenvalues in um^2/ms. Admissible = all eigenvalues >= 0 and largest <= 3.0.")
    for subj in ("stanford", "sherbrooke"):
        base = ROOT / "data" / "hcp" / subj
        d = base / "arms"
        brain = load(base / "dti", "shared_brain_mask.nii.gz") > 0
        A = {}
        for a in ARMS:
            ev = np.stack([load(d, f"{a}_L{i}.nii.gz") for i in (1, 2, 3)], -1) * 1e3
            A[a] = {"FA": load(d, f"{a}_FA.nii.gz"), "MD": load(d, f"{a}_MD.nii.gz") * 1e3,
                    "ev": ev, "T": load(d, f"{a}_tensor.nii.gz") * 1e3}

        # DIPY WLS before clipping, from the reimplementation, over the brain
        data_p, bvals, bvecs = te.load_protocol(subj)
        X = te.design(bvals, bvecs)
        data = np.asarray(nib.load(str(data_p)).dataobj, dtype=np.float32)
        Y = data[brain].astype(np.float64)
        beta = te.fit(X, Y, "predicted")
        ev_raw = np.zeros(brain.shape + (3,))
        ev_raw[brain] = np.linalg.eigvalsh(te.tensor(beta))[:, ::-1] * 1e3
        fa_raw, md_raw = np.zeros(brain.shape), np.zeros(brain.shape)
        fa_raw[brain], md_raw[brain] = te.fa_md(ev_raw[brain][:, ::-1] / 1e3)
        A["dipy_wls_raw"] = {"FA": fa_raw, "MD": md_raw, "ev": ev_raw}
        # check: clipping the reimplementation reproduces DIPY's own FA
        fa_clip, _ = te.fa_md(te.eigenvalues(X, beta, "predicted"))
        repro = np.abs(fa_clip - A["dipy_wls"]["FA"][brain])

        sig = load(base / "dti_denoised", "noise_map.nii.gz")
        nonpos = np.zeros(brain.shape, bool)
        nonpos[brain] = (Y <= 0).any(1)
        low = np.zeros(brain.shape, bool)
        low[brain] = (Y < 0.5 * sig[brain][:, None]).any(1)

        wm_pve, csf_pve = tissue(subj)
        wm = brain & (wm_pve >= 0.5)
        wm90 = brain & (wm_pve >= 0.9)
        edge = brain & (ndimage.distance_transform_edt(brain) <= 2)

        w()
        w("=" * 96)
        w(f"{subj}: {int(brain.sum()):,} brain voxels; independent white matter (two-channel FAST, "
          f"WM PVE >= 0.5): {int(wm.sum()):,} voxels ({int(wm90.sum()):,} at PVE >= 0.9)")
        w(f"  median FSL --wls FA in that mask {np.median(A['fsl_wls']['FA'][wm]):.3f}; "
          f"overlap with FA > 0.2 in FSL --wls: {100 * np.mean(A['fsl_wls']['FA'][wm] > 0.2):.1f}% of the mask")
        w(f"  reimplemented DIPY WLS, clipped, against DIPY's FA over the brain: "
          f"mean |dFA| {repro.mean():.2e}, 99.9th percentile {np.percentile(repro, 99.9):.2e}")
        w("=" * 96)

        # ---------------------------------------------------------------- 1
        w("1. Inadmissible fits by type, % of voxels (brain / independent white matter)")
        w(f"  {'arm':<24}{'lambda_min<0':>15}{'lambda_max>3':>15}{'MD<=0':>13}{'FA>1':>13}"
          f"{'any (new)':>15}{'old rule':>13}{'missed by old':>15}")
        inadm = {}
        for a in ARMS + ["dipy_wls_raw"]:
            ev, fa, md = A[a]["ev"], A[a]["FA"], A[a]["MD"]
            neg, big = ev.min(-1) < 0, ev.max(-1) > LMAX
            bad = neg | big
            old = ~((fa >= 0) & (fa <= 1) & (md > 0) & (md <= LMAX))
            inadm[a] = bad & brain
            cells = []
            for m in (neg, big, md <= 0, fa > 1, bad, old, bad & ~old):
                cells.append(f"{100 * m[brain].mean():.2f}/{100 * m[wm].mean():.2f}")
            w(f"  {LABEL[a]:<24}" + "".join(f"{c:>15}" if i in (0, 1, 4, 6) else f"{c:>13}"
                                            for i, c in enumerate(cells)))
            if a in ARMS:
                code = np.zeros(brain.shape, np.uint8)
                code[neg & brain] = CODE["negative eigenvalue"]
                code[big & ~neg & brain] = CODE["largest eigenvalue > 3"]
                nib.save(nib.Nifti1Image(code, nib.load(str(d / f"{a}_FA.nii.gz")).affine),
                         str(d / f"inadmissible_{a}.nii.gz"))

        # ---------------------------------------------------------------- 2
        w("2. Where the inadmissible voxels lie (brain)")
        w(f"  {'arm':<24}{'voxels':>8}{'clusters':>10}{'isolated':>10}{'in >=10':>9}{'edge':>8}"
          f"{'CSF':>8}{'<=0 meas':>10}{'<0.5 sigma':>12}")
        base_rate = (f"  {'(all brain voxels)':<24}{'':>8}{'':>10}{'':>10}{'':>9}"
                     f"{100 * edge[brain].mean():>7.1f}%{100 * (csf_pve[brain] >= 0.5).mean():>7.1f}%"
                     f"{100 * nonpos[brain].mean():>9.1f}%{100 * low[brain].mean():>11.1f}%")
        for a in ARMS + ["dipy_wls_raw"]:
            m = inadm[a]
            n = int(m.sum())
            if not n:
                w(f"  {LABEL[a]:<24}{0:>8}")
                continue
            lab, k = ndimage.label(m, structure=np.ones((3, 3, 3)))
            sizes = np.bincount(lab[m])
            iso = 100 * np.sum(sizes == 1) / n
            big10 = 100 * sizes[sizes >= 10].sum() / n
            w(f"  {LABEL[a]:<24}{n:>8,}{k:>10,}{iso:>9.1f}%{big10:>8.1f}%{100 * edge[m].mean():>7.1f}%"
              f"{100 * (csf_pve[m] >= 0.5).mean():>7.1f}%{100 * nonpos[m].mean():>9.1f}%"
              f"{100 * low[m].mean():>11.1f}%")
        w(base_rate)

        # ---------------------------------------------------------------- 3
        w("3. Tables 2, 3 and 5 on the independent white-matter mask")
        w("   Each pair uses the mask voxels admissible in both arms; 'lost' = voxels removed for each arm.")
        w(f"  {'pair':<46}{'n':>8}{'lost a/b':>13}{'FA r':>8}{'FA MAE':>9}{'FA diff':>9}"
          f"{'MD r':>8}{'MD MAE':>9}{'MD diff':>9}")
        ok = {a: wm & ~inadm[a] for a in ARMS}

        def row(a, b, sel, label=None):
            fr = stats(A[a]["FA"][sel], A[b]["FA"][sel])
            mr = stats(A[a]["MD"][sel], A[b]["MD"][sel])
            lost = f"{int((wm & inadm[a]).sum())}/{int((wm & inadm[b]).sum())}"
            w(f"  {label or (LABEL[a] + ' vs ' + LABEL[b]):<46}{int(sel.sum()):>8,}{lost:>13}"
              f"{fr[0]:>8.4f}{fr[1]:>9.4f}{fr[2]:>+9.4f}{mr[0]:>8.4f}{mr[1]:>9.4f}{mr[2]:>+9.4f}")

        w("  Table 2 (weighted fits as usually set up)")
        for a, b in (("fsl_wls", "mrt_iwls"), ("fsl_wls", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            row(a, b, ok[a] & ok[b])
        w("  Table 3 (estimator matched)")
        for a, b in (("fsl_wls", "mrt_wls"), ("fsl_wls", "dipy_wls"), ("mrt_wls", "dipy_wls")):
            row(a, b, ok[a] & ok[b])
        common = wm.copy()
        for a in ARMS:
            common &= ok[a]
        w(f"  Table 5 (every arm against FSL --wls, one voxel set: admissible in all seven arms, "
          f"{int(common.sum()):,} voxels)")
        for a in ARMS:
            if a != "fsl_wls":
                row(a, "fsl_wls", common)
        for a, b in (("fsl_ols", "mrt_iwls"), ("fsl_ols", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            row(a, b, common, "Defaults: " + LABEL[a] + " vs " + LABEL[b])
        common90 = wm90.copy()
        for a in ARMS:
            common90 &= ~inadm[a]
        w(f"  Sensitivity, WM PVE >= 0.9 ({int(common90.sum()):,} voxels admissible in all seven arms)")
        for a in ("fsl_ols", "mrt_iwls", "mrt_wls", "dipy_wls"):
            row(a, "fsl_wls", common90)
        row("fsl_ols", "mrt_iwls", common90, "Defaults: " + LABEL["fsl_ols"] + " vs " + LABEL["mrt_iwls"])
        w("  Every mask voxel, nothing excluded: median |difference| and 95th / 99th percentile")
        for a, b in (("fsl_wls", "mrt_iwls"), ("fsl_wls", "mrt_wls"), ("fsl_wls", "dipy_wls"),
                     ("mrt_iwls", "dipy_wls"), ("fsl_ols", "mrt_iwls")):
            dfa = np.abs(A[a]["FA"][wm] - A[b]["FA"][wm])
            dmd = np.abs(A[a]["MD"][wm] - A[b]["MD"][wm])
            w(f"  {LABEL[a] + ' vs ' + LABEL[b]:<46}FA {np.median(dfa):.4f} / {np.percentile(dfa, 95):.4f} / "
              f"{np.percentile(dfa, 99):.4f}   MD {np.median(dmd):.4f} / {np.percentile(dmd, 95):.4f} / "
              f"{np.percentile(dmd, 99):.4f}")

        # ---------------------------------------------------------------- 4
        w("4. FSL --wls against MRtrix3 -iter 0 (implementation agreement)")
        F, M = A["fsl_wls"], A["mrt_wls"]
        # frame: the sign of each off-diagonal component that makes FSL's tensor match MRtrix3's
        sign = np.ones(6)
        for i in (3, 4, 5):
            sign[i] = 1 if np.median(np.abs(F["T"][wm][:, i] - M["T"][wm][:, i])) <= \
                np.median(np.abs(-F["T"][wm][:, i] - M["T"][wm][:, i])) else -1
        w(f"  frame: FSL's tensor matches MRtrix3's after multiplying (Dxy, Dxz, Dyz) by {tuple(int(v) for v in sign[3:])}"
          f" (FSL stores tensors in its voxel frame, with x reversed for images with a positive "
          f"determinant; MRtrix3 in scanner coordinates)")
        for name, sel in (("brain", brain), ("independent white matter", wm)):
            both = sel & ~inadm["fsl_wls"] & ~inadm["mrt_wls"]
            w(f"  {name}, admissible in both ({int(both.sum()):,} voxels): quantiles of |difference| "
              f"50 / 95 / 99 / 99.9 / max")
            pairs = [("FA", F["FA"], M["FA"]), ("MD", F["MD"], M["MD"])]
            pairs += [(c, F["T"][..., i] * sign[i], M["T"][..., i]) for i, c in enumerate(COMP)]
            for c, x, y in pairs:
                dd = np.abs(x[both] - y[both])
                q = np.percentile(dd, [50, 95, 99, 99.9])
                r = pearsonr(x[both], y[both])[0]
                w(f"    {c:<4} {q[0]:.2e} / {q[1]:.2e} / {q[2]:.2e} / {q[3]:.2e} / {dd.max():.2e}"
                  f"   1 - r = {1 - r:.1e}")
        # the voxels that differ
        diff = np.abs(F["FA"] - M["FA"])
        t3 = brain & (F["FA"] > 0.2) & (M["FA"] > 0.2) & (A["dipy_wls"]["FA"] > 0.2) & \
            (F["FA"] <= 1) & (M["FA"] <= 1)
        far = t3 & (diff > 1e-3)
        w(f"  Table 3's voxel set (FA > 0.2 in the three toolkits, FA <= 1 in the pair): "
          f"{int(far.sum())} voxels differ by more than 0.001 in FA")
        rest = far & ~nonpos
        w(f"    with a measurement <= 0: {int((far & nonpos).sum())}; without one: {int(rest.sum())}, "
          f"of which {int((rest & low).sum())} have a measurement below 0.5 sigma, "
          f"{int((rest & edge).sum())} lie within 2 voxels of the brain edge, "
          f"{int((rest & (inadm['fsl_wls'] | inadm['mrt_wls'])).sum())} are inadmissible in either fit")
        if rest.sum():
            idx = np.argwhere(rest)
            ymin = data[rest].min(1)
            w(f"    those {int(rest.sum())}: |dFA| median {np.median(diff[rest]):.4f}, max {diff[rest].max():.4f}; "
              f"smallest measurement / sigma median {np.median(ymin / np.maximum(sig[rest], 1e-9)):.2f}; "
              f"smallest eigenvalue (FSL) median {np.median(F['ev'][rest].min(-1)):.4f} um^2/ms")
            w(f"    first voxels (i, j, k): {[tuple(int(v) for v in x) for x in idx[:5]]}")
        all_far = brain & (diff > 1e-3)
        w(f"  Over the whole brain: {int(all_far.sum()):,} voxels differ by more than 0.001 in FA "
          f"({100 * all_far[brain].mean():.2f}%); {100 * nonpos[all_far].mean():.1f}% of them contain a "
          f"measurement <= 0 and {100 * low[all_far].mean():.1f}% one below 0.5 sigma")

    out.write_text("\n".join(lines) + "\n")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
