"""
make_fig1_design.py
-------------------
Draw Figure 1: the design of the tensor-fitting comparison.

What needs a figure is which inputs are held identical, which estimators are
varied, and which ground truths each arm is scored against; that is hard to
hold in the head from text alone. Brain extraction, which the paper reports
only in the Supplementary Material, is left out.

The layout follows the data-flow convention used in this literature (e.g. the
QSIPrep and fMRIPrep workflow figures): data enters at the top, arrows carry
it downward through processing, and the tool responsible for each step is
named on the step. Toolkit colours match Figure 2 so the same tool is the
same colour throughout the paper.

Usage:
    python scripts/make_fig1_design.py

Outputs:
    figures/fig1_design.png   (300 dpi)
    figures/fig1_design.pdf   (vector)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = Path(__file__).parent.parent
FIG_DIR = ROOT / "figures"

INK = "#1A1A1A"
RULE = "#6E6E6E"
SHARED = "#B00020"          # marks what is held identical, and measured weights
C = {"FSL": "#2166AC", "MRtrix3": "#1A9850", "DIPY": "#D6604D"}

MONO = {"family": "DejaVu Sans Mono"}


def box(ax, x, y, w, h, *, lw=1.0, ec=INK, fc="white", ls="-", z=2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                           linewidth=lw, linestyle=ls, zorder=z))


def text(ax, x, y, s, *, size=9, weight="normal", color=INK, ha="center",
         va="center", mono=False, style="normal", z=5):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha,
            va=va, zorder=z, linespacing=1.45, style=style,
            **(MONO if mono else {}))


def arrow(ax, p0, p1, *, color=INK, lw=1.0, ls="-", z=4):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10,
                                 color=color, linewidth=lw, linestyle=ls,
                                 shrinkA=1, shrinkB=1, zorder=z))


def main():
    FIG_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.0, 8.6))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(-0.85, 8.35)
    ax.axis("off")
    cx = 4.5

    # ── Input ────────────────────────────────────────────────────────────────
    box(ax, 1.25, 7.25, 6.5, 1.0, lw=1.3)
    text(ax, cx, 8.02, "Two open dMRI datasets  (no credentials required)",
         size=10, weight="bold")
    text(ax, cx, 7.73, "Stanford HARDI — 10 b = 0 + 150 directions at b = 2000 s/mm²",
         size=8.6)
    text(ax, cx, 7.46,
         "Sherbrooke 3-shell — fitted subset: 1 b = 0 + 64 directions at b = 1000 s/mm²",
         size=8.6)
    arrow(ax, (cx, 7.25), (cx, 6.95))

    # ── Held identical ───────────────────────────────────────────────────────
    box(ax, 1.55, 6.15, 5.9, 0.8, ec=SHARED, lw=1.5)
    text(ax, cx, 6.74, "held identical across every arm", size=9,
         weight="bold", color=SHARED)
    text(ax, cx, 6.42,
         "one brain mask  ·  one volume subset  ·  no preprocessing\n",
         size=8.6)
    text(ax, cx, 6.30, "(MP-PCA denoising tested separately, applied once for all)",
         size=7.6, color=RULE, style="italic")

    # ── Arms ─────────────────────────────────────────────────────────────────
    arms = [("FSL", "dtifit\n--wls", "measured"),
            ("MRtrix3", "dwi2tensor\n-iter 0", "measured"),
            ("MRtrix3", "dwi2tensor\n(default)", "predicted"),
            ("DIPY", "WLS\n(default)", "predicted"),
            ("FSL", "dtifit\n(default)", "unweighted"),
            ("DIPY", "NLLS\nRESTORE", "non-linear")]
    w, gap = 1.3, 0.14
    x0 = cx - (len(arms) * w + (len(arms) - 1) * gap) / 2
    for i, (tool, cmd, fam) in enumerate(arms):
        x = x0 + i * (w + gap)
        arrow(ax, (cx, 6.15), (x + w / 2, 5.62), color=C[tool], lw=0.9)
        box(ax, x, 4.62, w, 1.0, ec=C[tool], lw=1.5)
        text(ax, x + w / 2, 5.40, tool, size=8.8, weight="bold", color=C[tool])
        text(ax, x + w / 2, 5.07, cmd, size=7.6, mono=True)
        text(ax, x + w / 2, 4.76, fam, size=7.8, style="italic",
             color=SHARED if fam == "measured" else RULE)
        arrow(ax, (x + w / 2, 4.62), (cx, 4.20), color=C[tool], lw=0.9)

    # ── Maps, admissibility, statistics ──────────────────────────────────────
    box(ax, 2.6, 3.66, 3.8, 0.54)
    text(ax, cx, 3.93, "FA and MD maps, one set per arm", size=9)
    arrow(ax, (cx, 3.66), (cx, 3.34))

    box(ax, 2.2, 2.66, 4.6, 0.68, ec=SHARED, lw=1.2, ls=(0, (4, 2)))
    text(ax, cx, 3.12, "physically admissible voxels only",
         size=9, weight="bold", color=SHARED)
    text(ax, cx, 2.84, "FA in [0, 1]      0 < MD ≤ 3.0 × 10⁻³ mm²/s", size=8.6)
    arrow(ax, (cx, 2.66), (cx, 2.34))

    box(ax, 2.3, 1.62, 4.4, 0.72)
    text(ax, cx, 2.13, "Pearson r  ·  mean absolute error", size=9)
    text(ax, cx, 1.83, "Bland–Altman bias and 95% limits", size=9)
    arrow(ax, (cx, 1.62), (cx, 1.34))
    text(ax, cx, 1.18, "Tables 2–5, 8, 9  ·  Figure 2", size=9.5, weight="bold")

    # ── Ground truth ─────────────────────────────────────────────────────────
    for xb, title, body, ref in (
            (0.25, "Phantoms with known eigenvalues",
             "Rician noise at SNR 30, 20 and 10\nthe five linear-fit arms",
             "Table 6"),
            (4.65, "Simulations on the real gradient tables",
             "idealised tensors, and each voxel's own fitted tensor\nRician noise at the measured noise level",
             "Table 7  ·  Tables S3–S5")):
        box(ax, xb, -0.30, 4.1, 1.2, ec=RULE, lw=1.0, ls=(0, (3, 2)))
        text(ax, xb + 2.05, 0.68, title, size=8.8, weight="bold", color=INK)
        text(ax, xb + 2.05, 0.30, body, size=7.8, color=RULE)
        text(ax, xb + 2.05, -0.12, ref, size=8.8, weight="bold", color=INK)

    # ── Execution environment ────────────────────────────────────────────────
    ax.plot([0.3, 8.7], [-0.48, -0.48], color=RULE, lw=0.8,
            ls=(0, (5, 3)), zorder=1)
    text(ax, cx, -0.70,
         "All steps run inside one container: FSL 6.0.7  ·  MRtrix3 3.0.8  "
         "·  DIPY 1.12.1",
         size=8.6, color=RULE)

    for ext, dpi in (("png", 300), ("pdf", None)):
        out = FIG_DIR / f"fig1_design.{ext}"
        fig.savefig(str(out), dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
