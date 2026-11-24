"""
make_fig1_design.py
-------------------
Draw Figure 1: the design of the tensor-fitting comparison, as revised.

What needs a figure is which inputs are held identical, which estimators are
varied, on which voxels the arms are compared, and against which references
each arm is scored; that is hard to hold in the head from text alone. Brain
extraction, which the paper reports only in the Supplementary Material, is
left out.

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
    figures/fig1_design.tif   (300 dpi, 2126 px wide, LZW)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from PIL import Image

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
    fig, ax = plt.subplots(figsize=(9.0, 9.6))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(-0.95, 9.3)
    ax.axis("off")
    cx = 4.5

    # ── Input ────────────────────────────────────────────────────────────────
    box(ax, 1.0, 7.95, 7.0, 1.25, lw=1.3)
    text(ax, cx, 8.97, "Open dMRI data  (no credentials required)",
         size=10, weight="bold")
    text(ax, cx, 8.68, "Stanford HARDI: 10 b = 0 + 150 directions at b = 2000 s/mm²",
         size=8.6)
    text(ax, cx, 8.41,
         "Sherbrooke 3-shell: fitted subset: 1 b = 0 + 64 directions at b = 1000 s/mm²",
         size=8.6)
    text(ax, cx, 8.14,
         "MASiVar test-retest: 38 scans of six adults on four scanners, b = 1000 s/mm²",
         size=8.6)
    arrow(ax, (cx, 7.95), (cx, 7.65))

    # ── Held identical ───────────────────────────────────────────────────────
    box(ax, 1.55, 6.85, 5.9, 0.8, ec=SHARED, lw=1.5)
    text(ax, cx, 7.44, "held identical across every arm", size=9,
         weight="bold", color=SHARED)
    text(ax, cx, 7.12,
         "one brain mask  ·  one volume subset  ·  no preprocessing\n",
         size=8.6)
    text(ax, cx, 7.00,
         "(MP-PCA denoising, the other Sherbrooke shells and PreQual tested separately)",
         size=7.4, color=RULE, style="italic")

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
        arrow(ax, (cx, 6.85), (x + w / 2, 6.32), color=C[tool], lw=0.9)
        box(ax, x, 5.32, w, 1.0, ec=C[tool], lw=1.5)
        text(ax, x + w / 2, 6.10, tool, size=8.8, weight="bold", color=C[tool])
        text(ax, x + w / 2, 5.77, cmd, size=7.6, mono=True)
        text(ax, x + w / 2, 5.46, fam, size=7.8, style="italic",
             color=SHARED if fam == "measured" else RULE)
        arrow(ax, (x + w / 2, 5.32), (cx, 4.90), color=C[tool], lw=0.9)

    # ── Maps, voxel set, statistics ──────────────────────────────────────────
    box(ax, 2.4, 4.36, 4.2, 0.54)
    text(ax, cx, 4.63, "FA, MD and eigenvalues, one set per arm", size=9)
    arrow(ax, (cx, 4.36), (cx, 4.04))

    box(ax, 1.5, 3.08, 6.0, 0.96, ec=SHARED, lw=1.2, ls=(0, (4, 2)))
    text(ax, cx, 3.84, "one voxel set for every arm", size=9, weight="bold",
         color=SHARED)
    text(ax, cx, 3.56,
         "white matter from a FAST tissue segmentation, defined without any tensor fit",
         size=8.4)
    text(ax, cx, 3.28,
         "admissible tensors only: all eigenvalues ≥ 0, largest ≤ 3.0 µm²/ms",
         size=8.4)
    arrow(ax, (cx, 3.08), (cx, 2.76))

    box(ax, 2.3, 2.04, 4.4, 0.72)
    text(ax, cx, 2.55, "Pearson r  ·  mean absolute error", size=9)
    text(ax, cx, 2.25, "Bland–Altman bias and 95% limits", size=9)
    arrow(ax, (cx, 2.04), (cx, 1.76))
    text(ax, cx, 1.60, "Tables 2–5, 8, 9  ·  Figure 2", size=9.5, weight="bold")

    # ── References each arm is scored against ────────────────────────────────
    wb, gb = 2.86, 0.10
    xs = cx - (3 * wb + 2 * gb) / 2
    for k, (title, body, ref) in enumerate((
            ("Phantoms, known eigenvalues",
             "Rician and non-central χ noise, SNR 30, 20, 10\n"
             "crossing fibres, partial volume, b-matrix errors",
             "Table 6  ·  Tables S13–S15"),
            ("Simulations on real gradient tables",
             "idealised and each voxel's own fitted tensor\n"
             "Rician noise at each voxel's measured σ",
             "Table 7  ·  Tables S3–S5  ·  Figure 4"),
            ("Repeated scans, four scanners",
             "variability within and between session\n"
             "and between scanner, against the estimator offset",
             "Table 10  ·  Figure 3"))):
        xb = xs + k * (wb + gb)
        box(ax, xb, -0.30, wb, 1.42, ec=RULE, lw=1.0, ls=(0, (3, 2)))
        text(ax, xb + wb / 2, 0.88, title, size=7.8, weight="bold", color=INK)
        text(ax, xb + wb / 2, 0.40, body, size=6.5, color=RULE)
        text(ax, xb + wb / 2, -0.10, ref, size=7.6, weight="bold", color=INK)

    # ── Execution environment ────────────────────────────────────────────────
    ax.plot([0.3, 8.7], [-0.52, -0.52], color=RULE, lw=0.8,
            ls=(0, (5, 3)), zorder=1)
    text(ax, cx, -0.76,
         "All steps run inside one container: FSL 6.0.7  ·  MRtrix3 3.0.8  "
         "·  DIPY 1.12.1",
         size=8.6, color=RULE)

    for ext, dpi in (("png", 300), ("pdf", None)):
        out = FIG_DIR / f"fig1_design.{ext}"
        fig.savefig(str(out), dpi=dpi, bbox_inches="tight", facecolor="white")
        print(f"  {out}")
    plt.close(fig)

    im = Image.open(FIG_DIR / "fig1_design.png").convert("RGB")
    width = 2126
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(FIG_DIR / "fig1_design.tif", dpi=(300, 300), compression="tiff_lzw")
    print(f"  {FIG_DIR / 'fig1_design.tif'}")


if __name__ == "__main__":
    main()
