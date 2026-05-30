"""
Shared utilities for the dMRI Rosetta Stone notebooks.

Thin wrappers around FSL and MRtrix3 CLI calls so every notebook can use
the same interface without repeating boilerplate subprocess code.
"""

import subprocess
import shutil
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------

def check_tool(name: str) -> bool:
    """Return True if *name* is on PATH."""
    return shutil.which(name) is not None


def require_tool(name: str):
    if not check_tool(name):
        raise EnvironmentError(
            f"'{name}' not found on PATH. "
            f"Install the relevant package (FSL / MRtrix3 / DIPY) and re-run."
        )


def check_all_tools():
    tools = {
        "FSL":     ["fslinfo", "dtifit", "eddy", "bedpostx", "probtrackx2"],
        "MRtrix3": ["mrinfo", "dwidenoise", "mrdegibbs", "dwifslpreproc",
                    "dwi2response", "dwi2fod", "tckgen", "tcksift2",
                    "tck2connectome"],
        "DIPY":    [],   # checked via importlib
    }

    print("=== Tool availability ===")
    for suite, cmds in tools.items():
        if suite == "DIPY":
            try:
                import dipy  # noqa: F401
                print(f"  DIPY          ✓  (v{dipy.__version__})")
            except ImportError:
                print("  DIPY          ✗  (pip install dipy)")
        else:
            statuses = []
            for cmd in cmds:
                mark = "✓" if check_tool(cmd) else "✗"
                statuses.append(f"{cmd}:{mark}")
            overall = "✓" if all(check_tool(c) for c in cmds) else "partial"
            print(f"  {suite:<12}  {overall}  [{', '.join(statuses)}]")


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str], *, cwd: str | Path | None = None, check: bool = True,
        verbose: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command, print it, and return the result."""
    cmd_str = " ".join(str(c) for c in cmd)
    if verbose:
        print(f"\n$ {cmd_str}")
    result = subprocess.run(
        cmd, capture_output=not verbose, text=True, cwd=cwd
    )
    if verbose and result.stdout:
        print(result.stdout)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd_str, result.stdout, result.stderr
        )
    return result


# ---------------------------------------------------------------------------
# FSL wrappers
# ---------------------------------------------------------------------------

def fsl_dtifit(dwi: str, mask: str, bvec: str, bval: str,
               out_base: str) -> None:
    """Fit the diffusion tensor using FSL dtifit."""
    require_tool("dtifit")
    run(["dtifit",
         "--data=" + dwi,
         "--mask=" + mask,
         "--bvecs=" + bvec,
         "--bvals=" + bval,
         "--out=" + out_base])


def fsl_eddy(dwi: str, mask: str, index: str, acqp: str,
             bvec: str, bval: str, out: str,
             topup_base: str | None = None) -> None:
    """Run FSL eddy for motion and eddy current correction."""
    require_tool("eddy")
    cmd = ["eddy",
           "--imain=" + dwi,
           "--mask=" + mask,
           "--index=" + index,
           "--acqp=" + acqp,
           "--bvecs=" + bvec,
           "--bvals=" + bval,
           "--out=" + out,
           "--repol"]          # --repol replaces outlier slices
    if topup_base:
        cmd += ["--topup=" + topup_base]
    run(cmd)


def fsl_topup(imain: str, datain: str, config: str, out_base: str) -> None:
    """Estimate susceptibility-induced distortions with FSL topup."""
    require_tool("topup")
    run(["topup",
         "--imain=" + imain,
         "--datain=" + datain,
         "--config=" + config,
         "--out=" + out_base,
         "--iout=" + out_base + "_iout",
         "--fout=" + out_base + "_fout"])


def fsl_bedpostx(data_dir: str) -> None:
    """Run FSL bedpostX (GPU version preferred if available)."""
    tool = "bedpostx_gpu" if check_tool("bedpostx_gpu") else "bedpostx"
    require_tool(tool)
    run([tool, data_dir])


def fsl_probtrackx2(samples: str, mask: str, seed: str,
                    out_dir: str, **kwargs) -> None:
    """Run FSL probtrackx2 probabilistic tractography."""
    require_tool("probtrackx2")
    cmd = ["probtrackx2",
           "-s", samples,
           "-m", mask,
           "-x", seed,
           "--dir=" + out_dir,
           "--opd",            # output path distribution
           "--os2t"]           # output seeds to targets
    for k, v in kwargs.items():
        cmd += [f"--{k}={v}"]
    run(cmd)


# ---------------------------------------------------------------------------
# MRtrix3 wrappers
# ---------------------------------------------------------------------------

def mrtrix_dwidenoise(dwi_in: str, dwi_out: str,
                      noise_map: str | None = None) -> None:
    """MP-PCA denoising with MRtrix3 dwidenoise."""
    require_tool("dwidenoise")
    cmd = ["dwidenoise", dwi_in, dwi_out]
    if noise_map:
        cmd += ["-noise", noise_map]
    run(cmd)


def mrtrix_mrdegibbs(dwi_in: str, dwi_out: str) -> None:
    """Gibbs ringing removal with MRtrix3 mrdegibbs."""
    require_tool("mrdegibbs")
    run(["mrdegibbs", dwi_in, dwi_out])


def mrtrix_dwifslpreproc(dwi_in: str, dwi_out: str,
                         pe_dir: str, rpe_header: bool = True,
                         bvec: str | None = None,
                         bval: str | None = None) -> None:
    """
    Combined eddy + topup preprocessing via MRtrix3 dwifslpreproc.
    Expects gradient info embedded in the .mif file when bvec/bval are None.
    """
    require_tool("dwifslpreproc")
    cmd = ["dwifslpreproc", dwi_in, dwi_out,
           "-pe_dir", pe_dir]
    if rpe_header:
        cmd += ["-rpe_header"]
    if bvec:
        cmd += ["-fslgrad", bvec, bval]
    run(cmd)


def mrtrix_dwi2response(dwi: str, wm_out: str, gm_out: str, csf_out: str,
                        algorithm: str = "dhollander") -> None:
    """Estimate the response function for multi-shell CSD."""
    require_tool("dwi2response")
    run(["dwi2response", algorithm, dwi,
         wm_out, gm_out, csf_out,
         "-voxels", wm_out.replace(".txt", "_voxels.mif")])


def mrtrix_dwi2fod(dwi: str, algo: str, response_wm: str, wm_fod: str,
                   response_gm: str = None, gm_fod: str = None,
                   response_csf: str = None, csf_fod: str = None,
                   mask: str = None) -> None:
    """Compute fibre orientation distributions (FODs)."""
    require_tool("dwi2fod")
    cmd = ["dwi2fod", algo, dwi, response_wm, wm_fod]
    if response_gm and gm_fod:
        cmd += [response_gm, gm_fod]
    if response_csf and csf_fod:
        cmd += [response_csf, csf_fod]
    if mask:
        cmd += ["-mask", mask]
    run(cmd)


def mrtrix_tckgen(fod: str, out_tck: str, algorithm: str = "iFOD2",
                  ntracks: int = 1_000_000, mask: str | None = None,
                  seed_image: str | None = None) -> None:
    """Generate streamlines with MRtrix3 tckgen."""
    require_tool("tckgen")
    cmd = ["tckgen", fod, out_tck,
           "-algorithm", algorithm,
           "-select", str(ntracks)]
    if mask:
        cmd += ["-mask", mask]
    if seed_image:
        cmd += ["-seed_image", seed_image]
    run(cmd)


def mrtrix_tcksift2(tck: str, fod: str, out_weights: str,
                    out_csv: str | None = None) -> None:
    """Weight streamlines with SIFT2 to match FOD integrals."""
    require_tool("tcksift2")
    cmd = ["tcksift2", tck, fod, out_weights]
    if out_csv:
        cmd += ["-csv", out_csv]
    run(cmd)


def mrtrix_tck2connectome(tck: str, parcellation: str,
                          out_csv: str, weights: str | None = None) -> None:
    """Build a connectivity matrix from streamlines."""
    require_tool("tck2connectome")
    cmd = ["tck2connectome", tck, parcellation, out_csv,
           "-symmetric", "-zero_diagonal"]
    if weights:
        cmd += ["-tck_weights_in", weights]
    run(cmd)


# ---------------------------------------------------------------------------
# Plotting helpers (used across notebooks)
# ---------------------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib


def show_slices(img_path: str, title: str = "", cmap: str = "gray",
                vmin=None, vmax=None):
    """Display axial/coronal/sagittal centre slices of a 3-D NIfTI volume."""
    img = nib.load(img_path)
    data = img.get_fdata()
    if data.ndim == 4:
        data = data[..., 0]

    cx, cy, cz = [s // 2 for s in data.shape]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (sl, label) in zip(axes, [
        (data[cx, :, :], "Sagittal"),
        (data[:, cy, :], "Coronal"),
        (data[:, :, cz], "Axial"),
    ]):
        ax.imshow(sl.T, cmap=cmap, origin="lower", vmin=vmin, vmax=vmax)
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


def compare_images(paths: list[str], labels: list[str],
                   slice_axis: int = 2, cmap: str = "gray"):
    """
    Show the same central slice from several images side-by-side.
    Useful for before/after or FSL vs MRtrix3 comparisons.
    """
    fig, axes = plt.subplots(1, len(paths), figsize=(5 * len(paths), 4))
    if len(paths) == 1:
        axes = [axes]
    for ax, path, label in zip(axes, paths, labels):
        data = nib.load(path).get_fdata()
        if data.ndim == 4:
            data = data[..., 0]
        idx = data.shape[slice_axis] // 2
        sl = np.take(data, idx, axis=slice_axis)
        ax.imshow(sl.T, cmap=cmap, origin="lower")
        ax.set_title(label)
        ax.axis("off")
    plt.tight_layout()
    return fig


def plot_metric_map(fa_path: str, md_path: str):
    """Quick FA / MD side-by-side for DTI output."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, path, label, cmap, vmax in zip(
        axes,
        [fa_path, md_path],
        ["FA (Fractional Anisotropy)", "MD (Mean Diffusivity)"],
        ["hot", "Blues"],
        [1.0, 3e-3]
    ):
        data = nib.load(path).get_fdata()
        cz = data.shape[2] // 2
        ax.imshow(data[:, :, cz].T, cmap=cmap, origin="lower",
                  vmin=0, vmax=vmax)
        ax.set_title(label)
        ax.axis("off")
    plt.tight_layout()
    return fig
