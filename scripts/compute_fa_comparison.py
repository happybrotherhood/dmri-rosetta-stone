"""
compute_fa_comparison.py
------------------------
Quantitative inter-tool agreement analysis for the dMRI Rosetta Stone paper.

Computes, across whichever of FSL / MRtrix3 / DIPY are available:

  1. Brain-mask agreement  — Dice similarity coefficient between each pair of
     per-tool brain masks (FSL bet, MRtrix3 dwi2mask, DIPY median_otsu).
  2. DTI scalar agreement  — voxelwise Pearson r, mean absolute error (MAE),
     Bland-Altman bias and 95% limits of agreement (LoA) for FA and MD, over
     white-matter voxels (FA > 0.2 in every available tool).

All tensor fits are driven from ONE shared brain mask, so the FA/MD numbers
isolate tensor-fitting differences from brain-extraction differences. The mask
comparison in (1) is what quantifies the brain-extraction differences.

Run AFTER `generate_fa_maps.py`, which produces the required inputs:
    data/hcp/<subject>/dti/{fsl_dti,mrt,dipy}_{FA,MD}.nii.gz
    data/hcp/<subject>/dti/mask_{fsl,mrtrix,dipy}.nii.gz

Usage:
    python scripts/generate_fa_maps.py     --subject stanford
    python scripts/compute_fa_comparison.py --subject stanford

Outputs:
    figures/fig3_fa_comparison.png / .pdf   paper Figure 3 (FA maps, scatter, BA)
    figures/fig4_brain_masks.png   / .pdf   paper Figure 4 (mask overlays)
    fa_comparison_stats.txt                 human-readable full results
    table3.md                               paper-ready Table 3 (paste into MS)
"""

from __future__ import annotations

import argparse
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).parent.parent

TOOLS = ["FSL", "MRtrix3", "DIPY"]
COLORS = {"FSL": "#2166AC", "MRtrix3": "#1A9850", "DIPY": "#D6604D"}

# Metric maps written by generate_fa_maps.py, per tool.
METRIC_FILES = {
    "FSL":     {"FA": "fsl_dti_FA.nii.gz", "MD": "fsl_dti_MD.nii.gz"},
    "MRtrix3": {"FA": "mrt_FA.nii.gz",     "MD": "mrt_MD.nii.gz"},
    "DIPY":    {"FA": "dipy_FA.nii.gz",    "MD": "dipy_MD.nii.gz"},
}
MASK_FILES = {
    "FSL":     "mask_fsl.nii.gz",
    "MRtrix3": "mask_mrtrix.nii.gz",
    "DIPY":    "mask_dipy.nii.gz",
}

# DTI mean diffusivity is produced in mm^2/s by all three toolkits; the paper
# reports the conventional micrometre^2/ms (= 1e-3 mm^2/s) for readability.
MD_SCALE = 1e3
MD_UNIT = "um^2/ms"

WM_FA_THRESHOLD = 0.2

# Unconstrained linear tensor fitting can return negative eigenvalues, which
# yield non-physical diffusion metrics. MRtrix3 `dwi2tensor` permits this by
# default; DIPY's WLS fit does not. On the Stanford HARDI data this affects a
# few hundred white-matter voxels, which barely move the MAE but severely
# distort Pearson r, since correlation is dominated by outliers carrying no
# shared signal. Raw MD agreement appears to be r ~ 0.12 for this reason alone.
#
# Statistics are therefore restricted to voxels whose values are physically
# admissible in BOTH tools of a pair:
#   FA must lie in [0, 1]      -- the definition of fractional anisotropy;
#   MD must lie in (0, 3.0e-3] -- positive, and no faster than free water
#                                 at body temperature (mm^2/s).
# The number of voxels this excludes is reported per tool, because it is
# itself a meaningful inter-tool difference rather than a nuisance.
MD_MAX_MM2_S = 3.0e-3
FA_MAX = 1.0


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subject", default="stanford")
    p.add_argument("--fa-threshold", type=float, default=WM_FA_THRESHOLD,
                   help="FA threshold defining the white-matter mask")
    p.add_argument("--md-max", type=float, default=MD_MAX_MM2_S,
                   help="upper bound (mm^2/s) for a physiologically plausible MD; "
                        "voxels outside (0, md-max] are excluded from MD statistics")
    return p.parse_args()


# ── Loading ───────────────────────────────────────────────────────────────────

def load_volume(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    return nib.load(str(path)).get_fdata(dtype=np.float32)


def load_metrics(dti_dir: Path) -> dict[str, dict[str, np.ndarray]]:
    """Return {tool: {"FA": arr, "MD": arr}} for tools with at least an FA map."""
    out: dict[str, dict[str, np.ndarray]] = {}
    for tool in TOOLS:
        fa = load_volume(dti_dir / METRIC_FILES[tool]["FA"])
        if fa is None:
            print(f"  {tool:<8} FA map absent — tool excluded from metric comparison")
            continue
        md = load_volume(dti_dir / METRIC_FILES[tool]["MD"])
        if md is None:
            print(f"  {tool:<8} FA present, MD absent — MD columns will be blank")
        out[tool] = {"FA": np.nan_to_num(fa),
                     "MD": None if md is None else np.nan_to_num(md)}
        print(f"  {tool:<8} loaded (FA{'' if md is None else ' + MD'})")
    return out


def load_masks(dti_dir: Path) -> dict[str, np.ndarray]:
    out = {}
    for tool in TOOLS:
        arr = load_volume(dti_dir / MASK_FILES[tool])
        if arr is None:
            print(f"  {tool:<8} brain mask absent — excluded from Dice comparison")
            continue
        out[tool] = arr > 0.5
        print(f"  {tool:<8} mask loaded ({int(out[tool].sum()):,} voxels)")
    return out


def check_shapes(arrays: dict[str, np.ndarray], what: str) -> None:
    shapes = {k: v.shape for k, v in arrays.items()}
    if len(set(shapes.values())) > 1:
        raise RuntimeError(f"{what} have mismatched shapes: {shapes}")


# ── Statistics ────────────────────────────────────────────────────────────────

def dice(a: np.ndarray, b: np.ndarray) -> float:
    """Dice similarity coefficient between two binary masks."""
    denom = a.sum() + b.sum()
    if denom == 0:
        return float("nan")
    return float(2.0 * np.logical_and(a, b).sum() / denom)


def agreement(a: np.ndarray, b: np.ndarray) -> dict:
    """Pearson r, Spearman rho, MAE, Bland-Altman bias and 95% LoA."""
    diff = a - b
    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1))
    r, p = pearsonr(a, b)
    rho, _ = spearmanr(a, b)
    return {
        "n": int(a.size),
        "r": float(r),
        "p": float(p),
        "rho": float(rho),
        "MAE": float(np.mean(np.abs(diff))),
        "bias": bias,
        "sd": sd,
        "loa_lo": bias - 1.96 * sd,
        "loa_hi": bias + 1.96 * sd,
    }


def plausible(arr: np.ndarray, metric: str, md_max: float) -> np.ndarray:
    """Voxelwise mask of physically admissible values for FA or MD."""
    if metric == "FA":
        return np.isfinite(arr) & (arr >= 0) & (arr <= FA_MAX)
    return np.isfinite(arr) & (arr > 0) & (arr <= md_max)


def exclusion_report(metrics, wm_mask, md_max) -> dict[str, dict]:
    """Per-tool count of non-physical FA/MD voxels inside the WM mask."""
    out = {}
    for tool, m in metrics.items():
        rec = {
            "FA_above_1": int(np.sum(wm_mask & (m["FA"] > FA_MAX))),
            "FA_below_0": int(np.sum(wm_mask & (m["FA"] < 0))),
        }
        if m["MD"] is not None:
            rec["MD_nonpositive"] = int(np.sum(wm_mask & ~(m["MD"] > 0)))
            rec["MD_above_max"] = int(np.sum(wm_mask & (m["MD"] > md_max)))
        out[tool] = rec
    return out


def fmt_p(p: float) -> str:
    return "< 1e-300" if p == 0.0 else f"{p:.2e}"


# ── Figures ───────────────────────────────────────────────────────────────────

def bland_altman(ax, a, b, label_a, label_b, unit_scale=1.0, unit=""):
    a, b = a * unit_scale, b * unit_scale
    mean_val = (a + b) / 2
    diff = a - b
    md = np.mean(diff)
    sd = np.std(diff, ddof=1)
    ax.scatter(mean_val, diff, s=1, alpha=0.2, color="steelblue", rasterized=True)
    ax.axhline(md, color="black", lw=1.2, label=f"Bias = {md:.4f}")
    ax.axhline(md + 1.96 * sd, color="red", lw=1, ls="--",
               label=f"+1.96 SD = {md + 1.96 * sd:.4f}")
    ax.axhline(md - 1.96 * sd, color="red", lw=1, ls="--",
               label=f"-1.96 SD = {md - 1.96 * sd:.4f}")
    suffix = f" ({unit})" if unit else ""
    ax.set_xlabel(f"Mean{suffix}", fontsize=9)
    ax.set_ylabel(f"{label_a} - {label_b}{suffix}", fontsize=9)
    ax.legend(fontsize=7)
    ax.set_title(f"Bland-Altman: {label_a} vs {label_b}", fontsize=9)


def make_figure3(metrics, wm_mask, pairs, z_idx, fig_dir, subj):
    """Row 1: FA maps per tool. Row 2: FA scatter per pair. Row 3: BA per pair."""
    available = list(metrics.keys())
    n_cols = max(len(available), len(pairs))
    fig = plt.figure(figsize=(4 * n_cols, 12))
    gs = gridspec.GridSpec(3, n_cols, figure=fig, hspace=0.45, wspace=0.35)

    for col, tool in enumerate(available):
        ax = fig.add_subplot(gs[0, col])
        im = ax.imshow(metrics[tool]["FA"][:, :, z_idx].T, cmap="hot",
                       origin="lower", vmin=0, vmax=1)
        ax.set_title(f"{tool} FA", fontsize=11, color=COLORS[tool], fontweight="bold")
        ax.axis("off")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    for col, (ta, tb, st) in enumerate(pairs):
        ax = fig.add_subplot(gs[1, col])
        valid = st["FA"]["valid_mask"]
        a = metrics[ta]["FA"][valid]
        b = metrics[tb]["FA"][valid]
        ax.scatter(a, b, s=1, alpha=0.15, color="grey", rasterized=True)
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Identity")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel(f"{ta} FA", fontsize=9)
        ax.set_ylabel(f"{tb} FA", fontsize=9)
        ax.set_title(f"r = {st['FA']['r']:.4f}\nMAE = {st['FA']['MAE']:.4f}", fontsize=9)
        ax.set_aspect("equal")
        ax.legend(fontsize=7)

        ax_ba = fig.add_subplot(gs[2, col])
        bland_altman(ax_ba, a, b, ta, tb, unit="FA")

    fig.suptitle(f"FA agreement across FSL / MRtrix3 / DIPY - {subj}",
                 fontsize=13, fontweight="bold", y=1.01)
    for ext in ("png", "pdf"):
        out = fig_dir / f"fig3_fa_comparison_{subj}.{ext}"
        fig.savefig(str(out), dpi=300 if ext == "png" else None, bbox_inches="tight")
        print(f"  {out}")
    plt.close(fig)


def make_figure4(masks, b0, z_idx, fig_dir, subj):
    """b=0 image in greyscale with each tool's brain mask overlaid in red."""
    if not masks or b0 is None:
        print("  (skipped Figure 4 — need b0_mean.nii.gz and at least one mask)")
        return
    tools = list(masks.keys())
    fig, axes = plt.subplots(1, len(tools), figsize=(4.2 * len(tools), 4.6))
    axes = np.atleast_1d(axes)
    overlay_cmap = plt.matplotlib.colors.ListedColormap(["none", "red"])

    for ax, tool in zip(axes, tools):
        ax.imshow(b0[:, :, z_idx].T, cmap="gray", origin="lower")
        ax.imshow(masks[tool][:, :, z_idx].T.astype(float), cmap=overlay_cmap,
                  origin="lower", alpha=0.35, vmin=0, vmax=1)
        ax.set_title(f"{tool}\n{int(masks[tool].sum()):,} voxels",
                     fontsize=11, color=COLORS[tool], fontweight="bold")
        ax.axis("off")

    fig.suptitle(f"Brain extraction comparison - {subj}",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        out = fig_dir / f"fig4_brain_masks_{subj}.{ext}"
        fig.savefig(str(out), dpi=300 if ext == "png" else None, bbox_inches="tight")
        print(f"  {out}")
    plt.close(fig)


# ── Report writers ────────────────────────────────────────────────────────────

def write_stats(path, subj, wm_mask, fa_thr, md_max, metrics, masks, dices,
                pairs, excl, z_idx):
    n_wm = 0 if wm_mask is None else int(wm_mask.sum())
    with open(path, "w") as f:
        w = f.write
        w("dMRI Rosetta Stone - Inter-tool agreement statistics\n")
        w("=" * 62 + "\n")
        w(f"Subject: {subj}\n")
        w(f"Tools with tensor fits: {', '.join(metrics) or 'none'}\n")
        w(f"Tools with brain masks: {', '.join(masks) or 'none'}\n")
        w(f"White-matter definition: FA > {fa_thr} in all available tools\n")
        w(f"White-matter voxels: {n_wm:,}\n")
        w(f"Axial slice shown in figures: z index {z_idx}\n\n")

        w("1. BRAIN MASK AGREEMENT (Dice similarity coefficient)\n")
        w("-" * 62 + "\n")
        if dices:
            for (ta, tb), d in dices.items():
                w(f"  {ta} vs {tb}: DSC = {d:.4f}\n")
        else:
            w("  Not computed - fewer than two per-tool masks available.\n")
        w("\n  Mask sizes (voxels):\n")
        for t, m in masks.items():
            w(f"    {t}: {int(m.sum()):,}\n")

        w("\n2. DTI SCALAR AGREEMENT (white-matter voxels)\n")
        w("-" * 62 + "\n")
        if not pairs:
            w("  Not computed - fewer than two tensor fits available.\n")
        for ta, tb, st in pairs:
            w(f"\n  {ta} vs {tb}\n")
            for metric in ("FA", "MD"):
                s = st.get(metric)
                if s is None:
                    w(f"    {metric}: not available\n")
                    continue
                unit = f" {MD_UNIT}" if metric == "MD" else ""
                w(f"    {metric} (n = {s['n']:,} voxels)\n")
                w(f"        Pearson  r   = {s['r']:.4f} (p = {fmt_p(s['p'])})\n")
                w(f"        Spearman rho = {s['rho']:.4f}\n")
                w(f"        MAE          = {s['MAE']:.4f}{unit}\n")
                w(f"        bias         = {s['bias']:+.4f}{unit}  "
                  f"95% LoA [{s['loa_lo']:+.4f}, {s['loa_hi']:+.4f}]\n")
                w(f"        excluded     = {s['n_excluded']:,} non-physical "
                  f"voxels of {n_wm:,}\n")

        w("\n2b. NON-PHYSICAL VOXELS PER TOOL (inside white-matter mask)\n")
        w("-" * 62 + "\n")
        w(f"  Admissible: FA in [0, {FA_MAX}]; 0 < MD <= {md_max:.1e} mm^2/s\n")
        w("  (free-water diffusivity at body temperature).\n")
        w("  Unconstrained linear tensor fitting can yield negative eigenvalues,\n"
          "  which push FA above 1 and MD below 0. Such voxels are excluded from\n"
          "  the statistics above, and the counts themselves are a genuine\n"
          "  inter-tool difference.\n\n")
        if not excl:
            w("  Not computed.\n")
        for tool, c in excl.items():
            w(f"    {tool}: FA > 1 = {c['FA_above_1']:,}, "
              f"FA < 0 = {c['FA_below_0']:,}, "
              f"MD <= 0 = {c.get('MD_nonpositive', 0):,}, "
              f"MD > bound = {c.get('MD_above_max', 0):,}\n")

        w("\n3. MEAN METRIC VALUES PER TOOL (white-matter voxels)\n")
        w("-" * 62 + "\n")
        w("  Computed over that tool's own physically admissible voxels, so the\n"
          "  summary statistics are not distorted by failed tensor fits.\n\n")
        if wm_mask is None:
            w("  Not computed - no white-matter mask.\n")
        for t, m in (metrics.items() if wm_mask is not None else []):
            valid = wm_mask & plausible(m["FA"], "FA", md_max)
            fa = m["FA"][valid]
            w(f"  {t}:\n    FA = {fa.mean():.4f} +/- {fa.std(ddof=1):.4f} "
              f"(n = {fa.size:,})\n")
            if m["MD"] is not None:
                valid_md = wm_mask & plausible(m["MD"], "MD", md_max)
                md = m["MD"][valid_md] * MD_SCALE
                w(f"    MD = {md.mean():.4f} +/- {md.std(ddof=1):.4f} {MD_UNIT} "
                  f"(n = {md.size:,})\n")
    print(f"  {path}")


def write_table3(path, metrics, dices, pairs):
    """Paper-ready Table 3, columns matching article_frontiers.md."""
    def cell(value, fmt="{:.4f}"):
        return "n/a" if value is None else fmt.format(value)

    with open(path, "w") as f:
        w = f.write
        w("**Table 3. Quantitative inter-tool agreement for brain masks and DTI "
          "scalar metrics on the Stanford HARDI dataset.** Brain mask agreement "
          "assessed by Dice similarity coefficient (DSC) between each pair of "
          "per-tool brain extractions. DTI metric agreement assessed over "
          f"white-matter voxels (FA > {WM_FA_THRESHOLD} in all tools) by Pearson "
          "correlation coefficient (r), mean absolute error (MAE), Bland-Altman "
          "mean bias, and 95% limits of agreement (LoA). All three tensor fits "
          "used the same shared brain mask, so metric differences reflect "
          f"tensor-fitting rather than masking. MD in {MD_UNIT}. Statistics are "
          "restricted to voxels whose values are physically admissible in both "
          f"tools of the pair (FA in [0, {FA_MAX}]; 0 < MD <= "
          f"{MD_MAX_MM2_S:.1e} mm^2/s), because unconstrained linear tensor "
          "fitting can return negative eigenvalues; per-tool counts of excluded "
          "voxels are reported in the text. Values generated by "
          "`scripts/compute_fa_comparison.py`.\n\n")
        w("| Comparison | Mask DSC | FA r | FA MAE | FA bias | FA 95% LoA | MD r | MD MAE |\n")
        w("|---|---|---|---|---|---|---|---|\n")

        rows = [("FSL", "DIPY"), ("FSL", "MRtrix3"), ("MRtrix3", "DIPY")]
        pair_lookup = {(ta, tb): st for ta, tb, st in pairs}
        for ta, tb in rows:
            st = pair_lookup.get((ta, tb)) or pair_lookup.get((tb, ta))
            dsc = dices.get((ta, tb)) or dices.get((tb, ta))
            if st is None:
                w(f"| {ta} vs. {tb} | {cell(dsc)} | n/a | n/a | n/a | n/a | n/a | n/a |\n")
                continue
            fa, md = st.get("FA"), st.get("MD")
            loa = ("n/a" if fa is None
                   else f"[{fa['loa_lo']:+.4f}, {fa['loa_hi']:+.4f}]")
            w(f"| {ta} vs. {tb} "
              f"| {cell(dsc)} "
              f"| {cell(fa and fa['r'])} "
              f"| {cell(fa and fa['MAE'])} "
              f"| {'n/a' if fa is None else format(fa['bias'], '+.4f')} "
              f"| {loa} "
              f"| {cell(md and md['r'])} "
              f"| {cell(md and md['MAE'])} |\n")

        missing = [t for t in TOOLS if t not in metrics]
        if missing:
            w(f"\n> INCOMPLETE: no tensor fit for {', '.join(missing)}. "
              "Re-run inside the project Docker image to fill the remaining rows.\n")
    print(f"  {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    subj = args.subject
    dti_dir = ROOT / "data" / "hcp" / subj / "dti"
    fig_dir = ROOT / "figures"
    fig_dir.mkdir(exist_ok=True)

    if not dti_dir.exists():
        raise SystemExit(f"No DTI outputs at {dti_dir}. "
                         f"Run: python scripts/generate_fa_maps.py --subject {subj}")

    print(f"Subject: {subj}\nInputs:  {dti_dir}\n")
    print("Loading brain masks:")
    masks = load_masks(dti_dir)
    print("\nLoading DTI metric maps:")
    metrics = load_metrics(dti_dir)

    # ── Dice between per-tool brain masks ────────────────────────────────────
    dices = {}
    if len(masks) >= 2:
        check_shapes(masks, "brain masks")
        for i, ta in enumerate(TOOLS):
            for tb in TOOLS[i + 1:]:
                if ta in masks and tb in masks:
                    dices[(ta, tb)] = dice(masks[ta], masks[tb])
    print("\nBrain mask agreement:")
    for (ta, tb), d in dices.items():
        print(f"  {ta} vs {tb}: DSC = {d:.4f}")
    if not dices:
        print("  fewer than two masks available - skipped")

    # ── White-matter mask and metric agreement ───────────────────────────────
    pairs = []
    wm_mask = None
    excl = {}
    n_wm = 0
    z_idx = 0
    if len(metrics) >= 2:
        check_shapes({t: m["FA"] for t, m in metrics.items()}, "FA maps")
        wm_mask = np.ones(next(iter(metrics.values()))["FA"].shape, dtype=bool)
        for m in metrics.values():
            wm_mask &= m["FA"] > args.fa_threshold
        n_wm = int(wm_mask.sum())
        z_idx = wm_mask.shape[2] // 2
        print(f"\nWhite-matter voxels (FA > {args.fa_threshold} in all tools): {n_wm:,}")
        if n_wm < 1000:
            print("  WARNING: very few white-matter voxels - check masks and fits.")

        available = list(metrics.keys())
        print("\nDTI scalar agreement:")
        for i, ta in enumerate(available):
            for tb in available[i + 1:]:
                st = {}
                # Restrict each metric to voxels physically admissible in
                # BOTH tools of the pair, so that a handful of failed tensor
                # fits cannot dominate the correlation.
                for metric, scale in (("FA", 1.0), ("MD", MD_SCALE)):
                    a, b = metrics[ta][metric], metrics[tb][metric]
                    if a is None or b is None:
                        st[metric] = None
                        continue
                    valid = (wm_mask
                             & plausible(a, metric, args.md_max)
                             & plausible(b, metric, args.md_max))
                    st[metric] = agreement(a[valid] * scale, b[valid] * scale)
                    st[metric]["n_excluded"] = n_wm - int(valid.sum())
                    # kept so the figures plot exactly the voxels summarised here
                    st[metric]["valid_mask"] = valid

                pairs.append((ta, tb, st))
                for metric in ("FA", "MD"):
                    s = st[metric]
                    if s is None:
                        print(f"  {ta} vs {tb}: {metric} n/a")
                        continue
                    print(f"  {ta} vs {tb}: {metric} r = {s['r']:.4f}, "
                          f"MAE = {s['MAE']:.4f}, bias = {s['bias']:+.4f}, "
                          f"LoA [{s['loa_lo']:+.4f}, {s['loa_hi']:+.4f}] "
                          f"({s['n_excluded']:,} excluded)")

        excl = exclusion_report(metrics, wm_mask, args.md_max)
        if excl:
            print("\nNon-physical voxels inside the white-matter mask "
                  f"(FA outside [0, {FA_MAX}]; MD outside 0 < MD <= "
                  f"{args.md_max:.1e} mm^2/s):")
            for tool, c in excl.items():
                print(f"  {tool:<8} FA>1: {c['FA_above_1']:>5,} | "
                      f"FA<0: {c['FA_below_0']:>5,} | "
                      f"MD<=0: {c.get('MD_nonpositive', 0):>5,} | "
                      f"MD>max: {c.get('MD_above_max', 0):>5,}")
    else:
        print("\nFewer than two tensor fits available - metric comparison skipped.")

    # ── Figures ──────────────────────────────────────────────────────────────
    print("\nWriting figures:")
    if pairs:
        make_figure3(metrics, wm_mask, pairs, z_idx, fig_dir, subj)
    else:
        print("  (skipped Figure 3 - needs at least two tensor fits)")
    b0 = load_volume(dti_dir / "b0_mean.nii.gz")
    make_figure4(masks, b0, (b0.shape[2] // 2) if b0 is not None else 0,
                 fig_dir, subj)

    # ── Reports ──────────────────────────────────────────────────────────────
    # Outputs are per-subject so that running a second dataset does not
    # silently overwrite the first one's figures and tables.
    print("\nWriting reports:")
    write_stats(ROOT / f"fa_comparison_stats_{subj}.txt", subj, wm_mask,
                args.fa_threshold, args.md_max, metrics, masks, dices, pairs,
                excl, z_idx)
    write_table3(ROOT / f"table3_{subj}.md", metrics, dices, pairs)

    missing = [t for t in TOOLS if t not in metrics]
    if missing:
        print(f"\nINCOMPLETE: no tensor fit for {', '.join(missing)}. "
              "Table 3 rows for these tools remain 'n/a'.")


if __name__ == "__main__":
    main()
