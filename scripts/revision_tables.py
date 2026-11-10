"""
revision_tables.py
------------------
Tables 2, 3, 4, 5, 8 and 9 of the revised manuscript, on the voxel set and
admissibility rule of arms.py: FAST white matter, and tensors whose
eigenvalues are all >= 0 with the largest <= 3.0 um^2/ms.

    Table 2   weighted fits as usually set up: FSL --wls, MRtrix3 default,
              DIPY WLS default
    Table 3   the same with the estimator matched (MRtrix3 -iter 0), with
              Bland-Altman limits of agreement
    Table 4   DIPY's WLS code with its default (predicted-signal) weights and
              with measured-signal weights, each against FSL --wls
    Table 5   every estimator against FSL --wls, and the defaults against one
              another, on one voxel set admissible in all seven arms
    Table 8   Table 2's differences before and after MP-PCA denoising
    Table 9   inadmissible fits by type, before and after denoising

A pair is compared on the white-matter voxels admissible in both arms, and
each table states how many voxels each arm loses to the rule. The difference
is always the first arm minus the second. MD in um^2/ms.

Usage:
    python scripts/revision_tables.py

Outputs:
    revision_tables.txt
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, str(Path(__file__).parent))
from arms import ROOT, admissible, brain_mask, load_arm, wm_mask  # noqa: E402

LABEL = {"fsl_ols": "FSL default (OLS)", "fsl_wls": "FSL --wls", "mrt_iwls": "MRtrix3 default (IWLS)",
         "mrt_wls": "MRtrix3 -iter 0", "dipy_wls": "DIPY WLS (default)", "dipy_nlls": "DIPY NLLS",
         "dipy_restore": "DIPY RESTORE", "dipy_wls_measured": "DIPY WLS, measured weights"}
SEVEN = ["fsl_ols", "fsl_wls", "mrt_iwls", "mrt_wls", "dipy_wls", "dipy_nlls", "dipy_restore"]


def compare(A, a, b, sel):
    out = {}
    for m in ("FA", "MD"):
        x, y = A[a][m][sel], A[b][m][sel]
        d = x - y
        out[m] = (pearsonr(x, y)[0], np.abs(d).mean(), d.mean(), 1.96 * d.std())
    return out


def main():
    lines = []

    def w(s=""):
        print(s)
        lines.append(s)

    w("Revised Tables 2, 3, 4, 5, 8 and 9")
    w("Voxels: FAST white matter (two-channel, PVE >= 0.5). Admissible: eigenvalues >= 0, largest <= 3.0.")
    w("Difference = first arm minus second. MD in um^2/ms. LoA = 1.96 SD of the difference.")
    hdr = f"  {'comparison':<44}{'n':>8}{'FA r':>8}{'FA MAE':>9}{'FA diff':>9}{'MD r':>8}{'MD MAE':>9}{'MD diff':>9}"

    for subj in ("stanford", "sherbrooke"):
        wm = wm_mask(subj)
        A = {a: load_arm(subj, a) for a in SEVEN + ["dipy_wls_measured"]}
        D = {a: load_arm(subj, a, denoised=True) for a in ("fsl_wls", "mrt_iwls", "dipy_wls")}
        ok = {a: wm & admissible(A[a]["ev"]) for a in A}
        okd = {a: wm & admissible(D[a]["ev"]) for a in D}
        w()
        w("=" * 100)
        w(f"{subj}: {int(wm.sum()):,} white-matter voxels")
        w("  voxels each arm loses to the admissibility rule: "
          + ", ".join(f"{LABEL[a]} {int((wm & ~admissible(A[a]['ev'])).sum()):,}" for a in A))
        w("=" * 100)

        def row(T, a, b, sel, label=None, loa=False):
            c = compare(T, a, b, sel)
            s = (f"  {label or LABEL[a] + ' vs ' + LABEL[b]:<44}{int(sel.sum()):>8,}"
                 f"{c['FA'][0]:>8.4f}{c['FA'][1]:>9.4f}{c['FA'][2]:>+9.4f}"
                 f"{c['MD'][0]:>8.4f}{c['MD'][1]:>9.4f}{c['MD'][2]:>+9.4f}")
            if loa:
                s += f"   LoA FA +/-{c['FA'][3]:.4f}, MD +/-{c['MD'][3]:.4f}"
            w(s)

        w("Table 2. Weighted fits as usually set up")
        w(hdr)
        for a, b in (("fsl_wls", "mrt_iwls"), ("fsl_wls", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            row(A, a, b, ok[a] & ok[b])

        w("Table 3. Estimator matched (MRtrix3 -iter 0)")
        w(hdr)
        for a, b in (("fsl_wls", "mrt_wls"), ("fsl_wls", "dipy_wls"), ("mrt_wls", "dipy_wls")):
            row(A, a, b, ok[a] & ok[b], loa=True)

        sel4 = ok["fsl_wls"] & ok["dipy_wls"] & ok["dipy_wls_measured"]
        w(f"Table 4. DIPY's WLS with each source of weights, against FSL --wls "
          f"(admissible in all three: {int(sel4.sum()):,} voxels)")
        w(hdr)
        row(A, "dipy_wls", "fsl_wls", sel4, "DIPY, predicted-signal weights (default)")
        row(A, "dipy_wls_measured", "fsl_wls", sel4, "DIPY, measured-signal weights (as FSL)")

        common = wm.copy()
        for a in SEVEN:
            common &= ok[a]
        sd = A["fsl_wls"]["FA"][common].std()
        w(f"Table 5. Every estimator against FSL --wls, one voxel set admissible in all seven arms "
          f"({int(common.sum()):,} voxels; SD of reference FA {sd:.4f})")
        w(hdr + f"{'MAE/SD':>8}")
        for a in SEVEN:
            if a == "fsl_wls":
                continue
            c = compare(A, a, "fsl_wls", common)
            w(f"  {LABEL[a]:<44}{int(common.sum()):>8,}{c['FA'][0]:>8.4f}{c['FA'][1]:>9.4f}{c['FA'][2]:>+9.4f}"
              f"{c['MD'][0]:>8.4f}{c['MD'][1]:>9.4f}{c['MD'][2]:>+9.4f}{c['FA'][1] / sd:>8.2f}")
        for a, b in (("fsl_ols", "mrt_iwls"), ("fsl_ols", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            c = compare(A, a, b, common)
            w(f"  {'Defaults: ' + LABEL[a] + ' vs ' + LABEL[b]:<44}{int(common.sum()):>8,}"
              f"{c['FA'][0]:>8.4f}{c['FA'][1]:>9.4f}{c['FA'][2]:>+9.4f}"
              f"{c['MD'][0]:>8.4f}{c['MD'][1]:>9.4f}{c['MD'][2]:>+9.4f}{c['FA'][1] / sd:>8.2f}")

        w("Table 8. Mean difference before and after MP-PCA denoising (each on its own admissible voxels)")
        w(f"  {'comparison':<44}{'FA raw':>9}{'FA den.':>9}{'MD raw':>9}{'MD den.':>9}{'n raw':>9}{'n den.':>9}")
        for a, b in (("fsl_wls", "mrt_iwls"), ("fsl_wls", "dipy_wls"), ("mrt_iwls", "dipy_wls")):
            s1, s2 = ok[a] & ok[b], okd[a] & okd[b]
            r, dn = compare(A, a, b, s1), compare(D, a, b, s2)
            w(f"  {LABEL[a] + ' vs ' + LABEL[b]:<44}{r['FA'][2]:>+9.4f}{dn['FA'][2]:>+9.4f}"
              f"{r['MD'][2]:>+9.4f}{dn['MD'][2]:>+9.4f}{int(s1.sum()):>9,}{int(s2.sum()):>9,}")

        w("Table 9. Inadmissible fits: white-matter voxels (% of white matter) / % of the whole brain")
        brain = brain_mask(subj)
        w(f"  {'arm':<26}{'data':<10}{'any':>24}{'lambda_min < 0':>24}{'lambda_max > 3':>24}")
        for tag, T in (("raw", A), ("denoised", D)):
            for a in ("fsl_wls", "mrt_iwls", "dipy_wls"):
                ev = T[a]["ev"]
                cells = []
                for m in (~admissible(ev), ev.min(-1) < 0, ev.max(-1) > 3.0):
                    cells.append(f"{int((wm & m).sum()):,} ({100 * (wm & m).sum() / wm.sum():.2f}%) / "
                                 f"{100 * (brain & m).sum() / brain.sum():.2f}%")
                w(f"  {LABEL[a]:<26}{tag:<10}{cells[0]:>24}{cells[1]:>24}{cells[2]:>24}")

    out = ROOT / "revision_tables.txt"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
