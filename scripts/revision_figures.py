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
import re
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
    fig.suptitle(f"FA agreement with the estimator matched, {DATASET_TITLES.get(subj, subj)}\n"
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
    fig.suptitle(f"Where the two admissibility rules fail, {DATASET_TITLES.get(subj, subj)}: "
                 "negative eigenvalues (red) and eigenvalues above free water (blue)", fontsize=12, y=1.0)
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


# ----------------------------------------------------------------------------
# Figures 3 and 4 of the revised manuscript
ARM_STYLE = {   # colour follows the toolkit (Figure 2); the matched pair shares one line
    "fsl_ols":  dict(color=COLORS["FSL"], marker="o", mfc="white", mec=COLORS["FSL"], mew=1.4, ls="--", label="FSL default (OLS)"),
    "fsl_wls":  dict(color=COLORS["FSL"], marker="o", mec="white", mew=0.6, label="FSL --wls = MRtrix3 -iter 0 (measured-signal weights)"),
    "mrt_iwls": dict(color=COLORS["MRtrix3"], marker="s", mec="white", mew=0.6, label="MRtrix3 default (IWLS)"),
    "dipy_wls": dict(color=COLORS["DIPY"], marker="^", mec="white", mew=0.6, label="DIPY WLS (default)"),
}
SCANNER_STYLE = {   # Okabe-Ito hues, fixed order, plus marker shape as a second encoding
    "1A": dict(color="#0072B2", marker="o", label="site 1, scanner A (Philips)"),
    "1B": dict(color="#E69F00", marker="s", label="site 1, scanner B (Philips)"),
    "2":  dict(color="#009E73", marker="^", label="site 2 (GE)"),
    "3":  dict(color="#CC79A7", marker="D", label="site 3 (Siemens)"),
}


def read_tsv(path):
    rows = [l.split("\t") for l in Path(path).read_text().splitlines()]
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:]]


def test_retest_figure():
    raw = read_tsv(ROOT / "test_retest_scans_b1000.tsv")
    pre = read_tsv(ROOT / "test_retest_scans_b1000_prequal.tsv")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1, 1, 1.35]})
    for ax, rows, title in ((axes[0], raw, "Unprocessed"), (axes[1], pre, "After PreQual preprocessing")):
        for sc, st in SCANNER_STYLE.items():
            pts = [(float(r["snr_b0"]), float(r["fsl_wls_MD"]) - float(r["dipy_wls_MD"]))
                   for r in rows if r["scanner"] == sc and r["snr_b0"] != "nan"]
            if pts:
                ax.plot(*zip(*pts), linestyle="none", markersize=7, mec="white", mew=0.6, **st)
        ax.axhline(0, color="0.6", lw=0.8)
        ax.set_xlabel("b = 0 SNR of the scan (white matter)")
        ax.set_ylabel("MD offset between weighting schemes (µm²/ms)")
        ax.set_title(title, fontsize=11)
        ax.set_ylim(-0.11, 0.01)
        ax.grid(axis="y", color="0.9", lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False, loc="lower right")
    # panel C: MD of each arm per scan, scans grouped by scanner (unprocessed)
    ax = axes[2]
    order = ["1A", "1B", "2", "3"]
    rows = sorted(raw, key=lambda r: (order.index(r["scanner"]), r["sub"], r["ses"], r["run"]))
    x = np.arange(len(rows))
    for arm, st in ARM_STYLE.items():
        ax.plot(x, [float(r[f"{arm}_MD"]) for r in rows], **{**st, "ls": "none", "markersize": 5})
    bounds = [i for i in range(1, len(rows)) if rows[i]["scanner"] != rows[i - 1]["scanner"]]
    for b in bounds:
        ax.axvline(b - 0.5, color="0.8", lw=0.8)
    starts = [0] + bounds + [len(rows)]
    for s0, s1 in zip(starts[:-1], starts[1:]):
        ax.text((s0 + s1 - 1) / 2, 0.505, SCANNER_STYLE[rows[s0]["scanner"]]["label"].replace(" (", "\n("),
                ha="center", va="bottom", fontsize=8, color="0.3")
    ax.set_xlabel("scan (38 scans, grouped by scanner)")
    ax.set_ylabel("white matter mean MD (µm²/ms)")
    ax.set_title("MD of each estimator, unprocessed scans", fontsize=11)
    ax.set_xticks([])
    ax.set_ylim(0.50, 0.82)
    ax.grid(axis="y", color="0.9", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.98))
    ax.set_ylim(0.50, 0.86)
    for ax, lab in zip(axes, "ABC"):
        ax.text(-0.08, 1.04, lab, transform=ax.transAxes, fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig3_test_retest")


def parse_table7(path):
    """The 'Table 7 values' blocks of sherbrooke_fa_diagnosis.txt, per dataset."""
    txt = Path(path).read_text().splitlines()
    out, subj = {}, None
    for i, line in enumerate(txt):
        m = re.match(r"(stanford|sherbrooke):", line)
        if m:
            subj = m.group(1)
        if line.startswith("Table 7 values") and subj:
            rows = []
            for l in txt[i + 2:i + 9]:
                parts = l.split()
                if not parts or parts[0] == "all":
                    continue
                vals = [float(v.split("±")[0]) for v in parts[2:]]
                rows.append((parts[0], vals))      # FA obs, FA 1.00, FA 1.27, MD obs, MD 1.00, MD 1.27
            out[subj] = rows
    return out


def bias_figure():
    import re as _re
    globals()["re"] = _re
    snr = [30, 20, 10]
    phantom = {   # Table 6, MD bias (um^2/ms) in the single-fibre region
        "fsl_wls": [-0.0065, -0.0147, -0.0542], "dipy_wls": [0.0001, -0.0001, -0.0022],
        "mrt_iwls": [0.0004, 0.0007, 0.0006], "fsl_ols": [0.0004, 0.0007, 0.0011]}
    t7 = parse_table7(ROOT / "sherbrooke_fa_diagnosis.txt")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    for arm, st in ARM_STYLE.items():
        ax.plot(snr, phantom[arm], **{**st, "lw": 2, "markersize": 7})
    ax.axhline(0, color="0.6", lw=0.8)
    ax.invert_xaxis()
    ax.set_xticks(snr)
    ax.set_xlabel("b = 0 SNR of the phantom (noise increases to the right)")
    ax.set_ylabel("MD bias, estimate minus truth (µm²/ms)")
    ax.set_title("Phantom with known eigenvalues", fontsize=11)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    for ax, subj, title in ((axes[1], "stanford", "Stanford HARDI (b = 2000)"), (axes[2], "sherbrooke", "Sherbrooke (b = 1000)")):
        rows = t7[subj]
        x = np.arange(len(rows))
        obs = [v[3] for _, v in rows]; s100 = [v[4] for _, v in rows]; s127 = [v[5] for _, v in rows]
        ax.plot(x, obs, color="0.15", marker="o", lw=2, markersize=7, mec="white", label="observed, real data")
        ax.plot(x, s127, color=COLORS["DIPY"], marker="^", lw=2, markersize=7, mec="white", label="noise on the real tensors, 1.27σ")
        ax.plot(x, s100, color=COLORS["DIPY"], marker="^", mfc="white", lw=1.5, ls="--", markersize=7, label="noise on the real tensors, 1.00σ")
        ax.set_xticks(x)
        ax.set_xticklabels([b for b, _ in rows])
        ax.set_xlabel("FA bin (DIPY fit)")
        ax.set_ylabel("MD offset between weighting schemes (µm²/ms)")
        ax.set_title(title, fontsize=11)
        ax.legend(fontsize=8, frameon=False, loc="lower left")
    for ax in axes:
        ax.grid(axis="y", color="0.9", lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax, lab in zip(axes, "ABC"):
        ax.text(-0.08, 1.04, lab, transform=ax.transAxes, fontsize=13, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig4_bias_and_noise")


if __name__ == "__main__" and "--new" in sys.argv:
    test_retest_figure()
    bias_figure()
