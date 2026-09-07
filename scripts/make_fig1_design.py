"""
make_fig1_design.py
-------------------
Draw Figure 1: the design of the inter-tool comparison.

This replaces an earlier figure that diagrammed the Docker build. That
information is one paragraph of prose and did not need a figure. What does
need one is the comparison design, because its whole point is which inputs
are held identical and which are deliberately left to each tool — and that is
hard to hold in the head from text alone.

The layout follows the data-flow convention used in this literature (e.g. the
QSIPrep and fMRIPrep workflow figures): data enters at the top, arrows carry
it downward through processing, and the tool responsible for each step is
named on the step. Toolkit colours match Figures 3 and 4 so the same tool is
the same colour throughout the paper.

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
RULE = "#7A7A7A"
SHARED = "#B00020"          # marks what is held identical across tools
C = {"FSL": "#2166AC", "MRtrix3": "#1A9850", "DIPY": "#D6604D"}

MONO = {"family": "DejaVu Sans Mono"}


def box(ax, x, y, w, h, *, lw=1.0, ec=INK, fc="white", ls="-", z=2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                           linewidth=lw, linestyle=ls, zorder=z))


def text(ax, x, y, s, *, size=8.5, weight="normal", color=INK, ha="center",
         va="center", mono=False, style="normal", z=5):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha,
            va=va, zorder=z, linespacing=1.5, style=style,
            **(MONO if mono else {}))


def arrow(ax, p0, p1, *, color=INK, lw=1.0, ls="-", z=4):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10,
                                 color=color, linewidth=lw, linestyle=ls,
                                 shrinkA=1, shrinkB=1, zorder=z))


def main():
    FIG_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.5, 8.4))
    ax.set_xlim(0, 10.5)
    ax.set_ylim(0, 8.4)
    ax.axis("off")

    # ── Input ────────────────────────────────────────────────────────────────
    box(ax, 2.55, 7.32, 5.4, 0.95, lw=1.3)
    text(ax, 5.25, 8.06, "Open dMRI dataset  (no credentials required)",
         size=9, weight="bold")
    text(ax, 5.25, 7.79, "Stanford HARDI — 160 volumes, b = 2000", size=7.5)
    text(ax, 5.25, 7.54,
         "Sherbrooke 3-shell — 193 volumes, b = 1000 / 2000 / 3500", size=7.5)

    arrow(ax, (3.6, 7.32), (2.6, 7.05))
    arrow(ax, (6.9, 7.32), (7.6, 7.05))

    # ── Left branch: brain extraction ────────────────────────────────────────
    text(ax, 2.6, 6.88, "Brain extraction compared", size=9, weight="bold")
    text(ax, 2.6, 6.62, "each tool on the input it is designed for",
         size=7.4, style="italic", color=RULE)

    inputs = [("FSL", "bet", "mean b = 0"),
              ("MRtrix3", "dwi2mask", "full DWI series"),
              ("DIPY", "median_otsu", "full series, b = 0 idx")]
    for i, (tool, cmd, inp) in enumerate(inputs):
        y = 6.05 - i * 0.62
        box(ax, 0.30, y, 4.6, 0.5, ec=C[tool], lw=1.4)
        text(ax, 0.52, y + 0.25, tool, size=8, weight="bold", color=C[tool],
             ha="left")
        text(ax, 1.68, y + 0.25, cmd, size=7.8, mono=True, ha="left")
        text(ax, 2.92, y + 0.25, f"←  {inp}", size=6.9, color=RULE,
             ha="left")

    arrow(ax, (2.6, 4.35), (2.6, 4.02))
    box(ax, 0.95, 3.42, 3.3, 0.6)
    text(ax, 2.6, 3.72, "Dice similarity coefficient\nbetween each pair",
         size=8)
    arrow(ax, (2.6, 3.42), (2.6, 3.09))
    text(ax, 2.6, 2.91, "Table 3  ·  Figure 4", size=8.5, weight="bold")

    # ── Right branch: tensor fitting ─────────────────────────────────────────
    text(ax, 7.6, 6.88, "Tensor fitting compared", size=9, weight="bold")
    text(ax, 7.6, 6.62, "every tool given identical input",
         size=7.4, style="italic", color=SHARED)

    box(ax, 5.55, 5.72, 4.1, 0.78, ec=SHARED, lw=1.5)
    text(ax, 7.6, 6.30, "held identical across all three tools",
         size=7.6, weight="bold", color=SHARED)
    text(ax, 7.6, 6.05,
         "one brain mask (median_otsu)  ·  one volume subset\n"
         "b = 0 + a single non-zero shell  ·  no preprocessing",
         size=7.4)

    for i, (tool, cmd) in enumerate([("FSL", "dtifit"),
                                     ("MRtrix3", "dwi2tensor"),
                                     ("DIPY", "TensorModel")]):
        x = 5.55 + i * 1.42
        arrow(ax, (7.6, 5.72), (x + 0.55, 5.28), color=C[tool])
        box(ax, x, 4.72, 1.1, 0.56, ec=C[tool], lw=1.4)
        text(ax, x + 0.55, 5.08, tool, size=7.4, weight="bold", color=C[tool])
        text(ax, x + 0.55, 4.88, cmd, size=7.2, mono=True)
        arrow(ax, (x + 0.55, 4.72), (7.6, 4.34), color=C[tool])

    box(ax, 5.9, 3.78, 3.4, 0.54)
    text(ax, 7.6, 4.05, "FA and MD maps, one set per tool", size=8)
    arrow(ax, (7.6, 3.78), (7.6, 3.42))

    box(ax, 5.55, 2.82, 4.1, 0.6, ec=SHARED, lw=1.2, ls=(0, (4, 2)))
    text(ax, 7.6, 3.24, "physically admissible voxels only",
         size=7.8, weight="bold", color=SHARED)
    text(ax, 7.6, 2.99, "FA in [0, 1]      0 < MD ≤ 3.0 × 10⁻³ mm²/s",
         size=7.4)
    arrow(ax, (7.6, 2.82), (7.6, 2.46))

    box(ax, 5.7, 1.80, 3.8, 0.66)
    text(ax, 7.6, 2.30, "Pearson r  ·  Spearman ρ  ·  MAE", size=8)
    text(ax, 7.6, 2.03, "Bland–Altman bias and 95% limits", size=8)
    arrow(ax, (7.6, 1.80), (7.6, 1.44))
    text(ax, 7.6, 1.26, "Tables 3 and 4  ·  Figure 3", size=8.5,
         weight="bold")

    # ── Execution environment ────────────────────────────────────────────────
    ax.plot([0.35, 10.15], [0.82, 0.82], color=RULE, lw=0.8,
            ls=(0, (5, 3)), zorder=1)
    text(ax, 5.25, 0.55,
         "All steps run inside one container: FSL 6.0.7  ·  MRtrix3 3.0.4  "
         "·  DIPY  —  nothing installed on the host",
         size=8, color=RULE)

    for ext, dpi in (("png", 300), ("pdf", None)):
        out = FIG_DIR / f"fig1_design.{ext}"
        fig.savefig(str(out), dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
