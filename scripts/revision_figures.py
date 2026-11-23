"""
revision_figures.py
-------------------
Figures of the revised manuscript that depend on the new voxel set and
admissibility rule (arms.py).

    fig2_agreement_<subject>      Figure 2 (Stanford) and Supplementary Figure S4
                                  (Sherbrooke): FA maps of FSL --wls, MRtrix3
                                  -iter 0 and DIPY WLS; voxelwise FA for each pair;
                                  Bland-Altman plots. FAST white matter, admissible
                                  in both arms of each pair.
    figS_inadmissible_<subject>   where inadmissible fits lie (Reviewer 1, S3):
                                  axial slices of the mean b = 0 image with the
                                  voxels whose tensor has a negative eigenvalue or
                                  a largest eigenvalue above 3.0 um^2/ms, for the
                                  arms of Table 2, and the FAST white matter outline.

Each figure is written as PNG and PDF to figures/revision/, and as a 300-dpi
TIFF 2126 px wide (the width of the submitted figures).

Usage:
    python scripts/revision_figures.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import gridspec  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.stats import pearsonr  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from arms import ROOT, admissible, arm_dir, brain_mask, load, load_arm, wm_mask  # noqa: E402
from compute_fa_comparison import COLORS, DATASET_TITLES, bland_altman  # noqa: E402

OUT = ROOT / "figures" / "revision"
TIFF_WIDTH = 2126
ARMS = [("FSL", "fsl_wls", "dtifit --wls"), ("MRtrix3", "mrt_wls", "dwi2tensor -iter 0"),
        ("DIPY", "dipy_wls", "TensorModel WLS")]
TABLE2 = [("FSL dtifit --wls", "fsl_wls"), ("MRtrix3 dwi2tensor (default)", "mrt_iwls"),
          ("DIPY TensorModel WLS (default)", "dipy_wls")]


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(str(OUT / f"{name}.{ext}"), dpi=300 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)
    im = Image.open(OUT / f"{name}.png").convert("RGB")
    im = im.resize((TIFF_WIDTH, round(im.height * TIFF_WIDTH / im.width)), Image.LANCZOS)
    im.save(OUT / f"{name}.tif", dpi=(300, 300), compression="tiff_lzw")
    print(f"  {OUT / name}.png/.pdf/.tif")


def agreement_figure(subj):
    wm = wm_mask(subj)
    A = {tool: load_arm(subj, arm) for tool, arm, _ in ARMS}
    ok = {tool: wm & admissible(A[tool]["ev"]) for tool in A}
    z = int(np.argmax(wm.sum((0, 1))))      # the axial slice with most white matter
    fig = plt.figure(figsize=(12, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)
    for col, (tool, _, cmd) in enumerate(ARMS):
        ax = fig.add_subplot(gs[0, col])
        im = ax.imshow((A[tool]["FA"] * brain_mask(subj))[:, :, z].T, cmap="hot", origin="lower",
                       vmin=0, vmax=1)
        ax.set_title(f"{tool} FA\n{cmd}", fontsize=10, color=COLORS[tool], fontweight="bold")
        ax.axis("off")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    for col, (ta, tb) in enumerate((("FSL", "MRtrix3"), ("FSL", "DIPY"), ("MRtrix3", "DIPY"))):
        sel = ok[ta] & ok[tb]
        a, b = A[ta]["FA"][sel], A[tb]["FA"][sel]
        ax = fig.add_subplot(gs[1, col])
        ax.scatter(a, b, s=1, alpha=0.15, color="grey", rasterized=True)
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Identity")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel(f"{ta} FA", fontsize=9)
        ax.set_ylabel(f"{tb} FA", fontsize=9)
        ax.set_title(f"r = {pearsonr(a, b)[0]:.4f}\nMAE = {np.abs(a - b).mean():.4f}   "
                     f"n = {int(sel.sum()):,}", fontsize=9)
        ax.set_aspect("equal")
        ax.legend(fontsize=7)
        bland_altman(fig.add_subplot(gs[2, col]), a, b, ta, tb, unit="FA")
    fig.suptitle(f"FA agreement with the estimator matched — {DATASET_TITLES.get(subj, subj)}\n"
                 f"FAST white matter, tensors admissible in both arms",
                 fontsize=13, fontweight="bold", y=1.02)
    save(fig, f"fig2_agreement_{subj}")


def inadmissible_figure(subj):
    brain, wm = brain_mask(subj), wm_mask(subj)
    b0 = load(arm_dir(subj) / "b0_brain.nii.gz")
    codes = {arm: load(arm_dir(subj) / f"inadmissible_{arm}.nii.gz").astype(int) for _, arm in TABLE2}
    nz = brain.shape[2]
    slices = [int(round(f * nz)) for f in (0.25, 0.4, 0.55, 0.7)]
    cmap = ListedColormap([(0, 0, 0, 0), (0.85, 0.1, 0.1, 1), (0.1, 0.4, 0.95, 1)])
    fig, axes = plt.subplots(len(TABLE2), len(slices), figsize=(3.2 * len(slices), 3.4 * len(TABLE2)))
    for r, (label, arm) in enumerate(TABLE2):
        c = codes[arm]
        n_neg, n_big = int((c == 1).sum()), int((c == 2).sum())
        for k, z in enumerate(slices):
            ax = axes[r, k]
            ax.imshow(b0[:, :, z].T, cmap="gray", origin="lower", vmax=np.percentile(b0[brain], 99))
            ax.contour(wm[:, :, z].T, levels=[0.5], colors="gold", linewidths=0.4, origin="lower")
            ax.imshow(c[:, :, z].T, cmap=cmap, origin="lower", vmin=0, vmax=2, interpolation="nearest")
            ax.set_xticks([])
            ax.set_yticks([])
            if k == 0:
                ax.set_ylabel(f"{label}\nnegative eigenvalue {n_neg:,}\nlargest > 3.0 µm²/ms {n_big:,}",
                              fontsize=8)
            if r == 0:
                ax.set_title(f"slice {z}", fontsize=9)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    handles = [Patch(facecolor=(0.85, 0.1, 0.1), label="an eigenvalue below zero"),
               Patch(facecolor=(0.1, 0.4, 0.95), label="largest eigenvalue above 3.0 µm²/ms"),
               Line2D([0], [0], color="gold", lw=1.5, label="FAST white matter (outline)")]
    fig.suptitle(f"Inadmissible tensor fits, {DATASET_TITLES.get(subj, subj)}", fontsize=12, y=1.0)
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=10, frameon=False,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    save(fig, f"figS_inadmissible_{subj}")


def main():
    for subj in ("stanford", "sherbrooke"):
        print(subj)
        agreement_figure(subj)
        inadmissible_figure(subj)


if __name__ == "__main__":
    main()
