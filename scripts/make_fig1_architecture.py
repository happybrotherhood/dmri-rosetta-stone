"""
make_fig1_architecture.py
-------------------------
Draw Figure 1 of the dMRI Rosetta Stone paper: the two-stage Docker build and
the runtime path from the user's browser to the three toolkits.

The diagram is generated rather than drawn by hand so that it stays in step
with the Dockerfile and can be regenerated at any resolution the journal asks
for.

Usage:
    python scripts/make_fig1_architecture.py

Outputs:
    figures/fig1_architecture.png   (300 dpi)
    figures/fig1_architecture.pdf   (vector)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).parent.parent
FIG_DIR = ROOT / "figures"

# Muted, print-safe palette; distinguishable in greyscale by lightness.
C_STAGE1 = "#DCE9F5"
C_STAGE2 = "#EFF3F7"
C_FSL = "#2166AC"
C_MRTRIX = "#1A9850"
C_DIPY = "#D6604D"
C_APP = "#F6E3B4"
C_HOST = "#E8E8E8"
EDGE = "#44515E"


def box(ax, x, y, w, h, label, facecolor, *, fontsize=9, weight="normal",
        textcolor="#1B252F", radius=0.02, lw=1.1, edgecolor=EDGE, zorder=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, zorder=zorder))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=textcolor,
            zorder=zorder + 1, linespacing=1.45)


def arrow(ax, xy_from, xy_to, *, style="-|>", color=EDGE, lw=1.3, ls="-",
          rad=0.0, zorder=5):
    ax.add_patch(FancyArrowPatch(
        xy_from, xy_to, arrowstyle=style, mutation_scale=13,
        color=color, linewidth=lw, linestyle=ls, zorder=zorder,
        connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))


def main():
    FIG_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 7.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.9)
    ax.axis("off")

    # ── Build time ───────────────────────────────────────────────────────────
    ax.text(0.15, 6.35, "BUILD TIME", fontsize=10, fontweight="bold",
            color="#5A6673")

    box(ax, 0.15, 4.75, 2.55, 1.25,
        "Stage 1\nmrtrix3/mrtrix3:latest\n\nMRtrix3 3.0.4 binaries",
        C_STAGE1, fontsize=9)

    box(ax, 3.55, 4.6, 6.3, 1.55, "", C_STAGE2, radius=0.03)
    ax.text(3.75, 5.97, "Stage 2  —  ubuntu:22.04", fontsize=9.5,
            fontweight="bold", color="#1B252F", va="top")

    box(ax, 3.8, 4.78, 1.75, 0.72,
        "FSL 6.0.7\nvia fslinstaller.py", "#FFFFFF", fontsize=8.5)
    box(ax, 5.72, 4.78, 1.75, 0.72,
        "MRtrix3 3.0.4\ncopied from Stage 1", "#FFFFFF", fontsize=8.5)
    box(ax, 7.64, 4.78, 2.0, 0.72,
        "Python stack (pip)\nStreamlit · DIPY · nibabel\nnumpy · scipy · matplotlib",
        "#FFFFFF", fontsize=7.6)

    # Route the COPY arrow over the top of Stage 2 so it does not cross the
    # FSL box on its way to the MRtrix3 box.
    arrow(ax, (1.42, 6.0), (6.6, 5.5), rad=-0.28)
    ax.text(3.9, 6.42, "COPY --from=stage1", fontsize=7.8, style="italic",
            color="#5A6673", ha="center")

    # Divider between build and run time
    ax.plot([0.15, 9.85], [4.32, 4.32], color="#C3CBD3", lw=1, ls=(0, (5, 4)),
            zorder=1)

    # ── Run time ─────────────────────────────────────────────────────────────
    ax.text(0.15, 4.08, "RUN TIME", fontsize=10, fontweight="bold",
            color="#5A6673")

    # Host
    box(ax, 0.15, 2.55, 2.35, 1.05,
        "Host machine\n\nBrowser\nlocalhost:8501", C_HOST, fontsize=9)
    ax.text(1.325, 2.33, "no neuroimaging software\nrequired on the host",
            ha="center", va="top", fontsize=7.6, style="italic",
            color="#5A6673")

    # Container
    box(ax, 3.15, 0.35, 6.7, 3.32, "", "#FAFBFC", radius=0.03, lw=1.4)
    ax.text(3.35, 3.5, "Container", fontsize=9.5, fontweight="bold",
            color="#1B252F", va="top")

    box(ax, 3.45, 2.55, 6.1, 0.78,
        "Streamlit application  (app/app.py)\n"
        "seven pipeline stages · three tabs per stage · Why? explanations",
        C_APP, fontsize=8.8)

    box(ax, 3.45, 1.72, 6.1, 0.52,
        "Python subprocess", "#FFFFFF", fontsize=8.8)

    # Three toolkits
    box(ax, 3.45, 0.62, 1.9, 0.78, "FSL 6.0.7\nbet · dtifit\neddy · TBSS",
        "#FFFFFF", fontsize=8.2, edgecolor=C_FSL, lw=1.8, textcolor=C_FSL)
    box(ax, 5.55, 0.62, 1.9, 0.78,
        "MRtrix3 3.0.4\ndwi2mask · dwi2fod\ntckgen", "#FFFFFF",
        fontsize=8.2, edgecolor=C_MRTRIX, lw=1.8, textcolor=C_MRTRIX)
    box(ax, 7.65, 0.62, 1.9, 0.78,
        "DIPY\nmedian_otsu\nTensorModel", "#FFFFFF",
        fontsize=8.2, edgecolor=C_DIPY, lw=1.8, textcolor=C_DIPY)

    # Wiring
    arrow(ax, (2.5, 3.0), (3.45, 2.94))
    ax.text(2.82, 3.06, "port 8501", fontsize=7.4, ha="center", va="bottom",
            color="#5A6673")
    arrow(ax, (6.5, 2.55), (6.5, 2.24))
    for cx, col in ((4.4, C_FSL), (6.5, C_MRTRIX), (8.6, C_DIPY)):
        arrow(ax, (6.5, 1.72), (cx, 1.4), color=col, rad=0.0)

    # Data volume
    box(ax, 0.15, 0.62, 2.35, 0.95,
        "Open sample data\n\nStanford HARDI\nSherbrooke 3-shell",
        C_HOST, fontsize=8.4)
    arrow(ax, (2.5, 1.1), (3.42, 1.04), ls=(0, (4, 3)))
    ax.text(2.82, 1.16, "mount", fontsize=7.4, ha="center", va="bottom",
            color="#5A6673")

    fig.tight_layout()
    for ext, dpi in (("png", 300), ("pdf", None)):
        out = FIG_DIR / f"fig1_architecture.{ext}"
        fig.savefig(str(out), dpi=dpi, bbox_inches="tight",
                    facecolor="white")
        print(f"  {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
