"""
dMRI Rosetta Stone — Streamlit Interface
Run: streamlit run app/app.py
"""

import streamlit as st
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import subprocess, shutil, sys
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="dMRI Rosetta Stone",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Project root (one level up from app/)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from utils import check_tool

# ── Helpers ───────────────────────────────────────────────────────────────────

def tool_badge(name: str) -> str:
    available = check_tool(name)
    colour    = "green" if available else "red"
    symbol    = "✓" if available else "✗"
    return f":{colour}[{symbol} `{name}`]"


def short(path) -> str:
    """Return a display-friendly path: relative to project root when possible."""
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def fmt_cmd(cmd: list) -> str:
    """Format a command list for display, shortening absolute paths.
    Handles both bare paths and --flag=/abs/path style tokens."""
    parts = []
    for token in cmd:
        s = str(token)
        # Handle --flag=value tokens
        if "=" in s and s.startswith("-"):
            flag, _, val = s.partition("=")
            try:
                rel = str(Path(val).relative_to(ROOT))
                parts.append(f"{flag}={rel}")
            except (ValueError, TypeError):
                parts.append(s)
        else:
            try:
                rel = str(Path(s).relative_to(ROOT))
                parts.append(rel)
            except (ValueError, TypeError):
                parts.append(s)
    return " ".join(parts)


def show_slice(img_path: str | Path, title: str = "",
               cmap: str = "gray", vmin=None, vmax=None, axis: int = 2):
    """Return a matplotlib figure of the central slice."""
    img  = nib.load(str(img_path))
    data = img.get_fdata()
    if data.ndim == 4:
        data = data[..., 0]
    idx = data.shape[axis] // 2
    sl  = np.take(data, idx, axis=axis)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(sl.T, cmap=cmap, origin="lower", vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=10)
    ax.axis("off")
    fig.tight_layout(pad=0.3)
    return fig


def show_mask_on_b0(b0_data: np.ndarray, mask,
                    title: str = "Brain mask", axis: int = 2):
    """Show brain mask as red overlay on b0 image.

    mask: bool/uint8 ndarray OR Path/str to a NIfTI file.
    """
    if not isinstance(mask, np.ndarray):
        mask = nib.load(str(mask)).get_fdata().astype(bool)
    else:
        mask = mask.astype(bool)
    z       = b0_data.shape[axis] // 2
    b0_sl   = np.take(b0_data, z, axis=axis)
    mask_sl = np.take(mask,    z, axis=axis)
    nonzero = b0_sl[b0_sl > 0]
    vmax    = float(np.percentile(nonzero, 98)) if nonzero.size else 1.0
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(b0_sl.T, cmap="gray", origin="lower", vmin=0, vmax=vmax)
    overlay = np.zeros((*mask_sl.shape, 4))
    overlay[mask_sl] = [1.0, 0.35, 0.35, 0.4]
    ax.imshow(overlay.transpose(1, 0, 2), origin="lower")
    ax.set_title(title, fontsize=10)
    ax.axis("off")
    fig.tight_layout(pad=0.3)
    return fig


def run_cmd(cmd: list[str], label: str) -> tuple[bool, str]:
    """Run a shell command; return (success, output)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    ok     = result.returncode == 0
    out    = result.stdout + ("\n" + result.stderr if not ok else "")
    return ok, out.strip()


def best_shell_sel(bvals: np.ndarray, preferred: int = 1000):
    """Return (boolean_selector, target_b) for b=0 + the shell closest to preferred.

    Works for single-shell (e.g. Stanford HARDI b=2000) and multi-shell (HCP b=1000/2000).
    """
    shells  = np.unique(np.round(bvals, -2).astype(int))
    nonzero = shells[shells > 100]
    if nonzero.size == 0:
        raise ValueError("No non-zero b-value shells found in dataset")
    target = int(nonzero[np.argmin(np.abs(nonzero - preferred))])
    tol    = max(100, int(target * 0.12))
    sel    = (bvals < 50) | ((bvals > target - tol) & (bvals < target + tol))
    return sel, target


@st.cache_resource
def ensure_demo_data(subject: str = "100307"):
    """Generate synthetic data on first run — needed for cloud deployment."""
    dd = ROOT / "data" / "hcp" / subject / "T1w" / "Diffusion"
    if not (dd / "data.nii.gz").exists():
        subprocess.run(
            [sys.executable,
             str(ROOT / "scripts" / "make_test_data.py"),
             "--subject", subject,
             "--outdir", str(ROOT / "data" / "hcp")],
            capture_output=True
        )


def data_dir() -> Path:
    return ROOT / "data" / "hcp" / st.session_state.get("subject", "100307") \
           / "T1w" / "Diffusion"


def prep_dir() -> Path:
    d = ROOT / "data" / "hcp" / st.session_state.get("subject", "100307") \
        / "preprocessed"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.title("🧠 dMRI Rosetta Stone")

        st.markdown("**Translating dMRI across FSL, MRtrix3, and DIPY**")
        st.divider()

        # Subject selector — at the top so it's always visible
        st.markdown("### Dataset")
        # Apply pending subject switch BEFORE the widget is instantiated
        pending = st.session_state.pop("_pending_subject", None)
        if pending:
            st.session_state["subject_id"] = pending
        if "subject_id" not in st.session_state:
            st.session_state["subject_id"] = "100307"
        subj = st.text_input("Subject ID", key="subject_id")
        st.session_state["subject"] = subj

        dd = data_dir()
        data_ready = (dd / "data.nii.gz").exists()
        if data_ready:
            st.success("Data found ✓")
            bvals = np.loadtxt(str(dd / "bvals"))
            shells = np.unique(np.round(bvals, -2)).astype(int)
            st.caption(f"Shells: {', '.join(map(str, shells))} s/mm²")
            st.caption(f"Volumes: {len(bvals)}")
        else:
            st.error("No data found")

        st.markdown("**Real brain data** (recommended):")
        if st.button("⬇ Download Stanford HARDI", help="Real brain dMRI — ~50 MB, no credentials needed"):
            with st.spinner("Downloading Stanford HARDI dataset (~50 MB)..."):
                r = subprocess.run(
                    [sys.executable,
                     str(ROOT / "scripts" / "fetch_sample_data.py"),
                     "--subject", "stanford",
                     "--outdir", str(ROOT / "data" / "hcp")],
                    capture_output=True, text=True
                )
            if r.returncode == 0:
                st.session_state["_pending_subject"] = "stanford"
                st.rerun()
            else:
                st.error(r.stderr or r.stdout)

        st.markdown("**Synthetic data** (instant, geometric phantom):")
        if st.button("⚙ Generate synthetic data"):
            with st.spinner("Generating..."):
                r = subprocess.run(
                    [sys.executable,
                     str(ROOT / "scripts" / "make_test_data.py"),
                     "--subject", subj,
                     "--outdir", str(ROOT / "data" / "hcp")],
                    capture_output=True, text=True
                )
            if r.returncode == 0:
                st.success("Done!")
                st.rerun()
            else:
                st.error(r.stderr)

        st.divider()

        # Tool availability — in expander so navigation is always visible
        with st.expander("🔧 Tool status"):
            fsl_tools = ["bet", "eddy", "dtifit", "randomise", "topup"]
            mrt_tools = ["dwidenoise", "mrdegibbs", "dwifslpreproc",
                         "dwi2response", "dwi2fod", "tckgen", "tcksift2"]
            col_f, col_m = st.columns(2)
            with col_f:
                st.caption("FSL")
                for t in fsl_tools:
                    st.markdown(tool_badge(t))
            with col_m:
                st.caption("MRtrix3")
                for t in mrt_tools:
                    st.markdown(tool_badge(t))
            # DIPY
            st.caption("DIPY")
            try:
                import dipy
                st.markdown(f":green[✓ `dipy` {dipy.__version__}]")
            except ImportError:
                st.markdown(":red[✗ `dipy` — pip install dipy]")

        st.divider()

        # Navigation
        st.markdown("### Pipeline steps")
        page = st.radio(
            "Go to",
            options=[
                "🏠 Introduction",
                "1️⃣  Brain Extraction",
                "2️⃣  Denoising",
                "3️⃣  Eddy Correction",
                "4️⃣  DTI Fitting",
                "5️⃣  CSD / FODs",
                "6️⃣  Tractography",
                "7️⃣  TBSS Group Analysis",
                "8️⃣  Concepts & Reference",
            ],
            label_visibility="collapsed",
        )
        return page


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_intro():
    st.title("🧠 dMRI Rosetta Stone")
    st.markdown("""
    > **Translating diffusion MRI across FSL, MRtrix3, and DIPY — one pipeline step at a time.**

    This app walks you through the complete dMRI pipeline, showing the **same operation
    in all three major tools side-by-side** so you understand not just *how* to run a
    command, but *why* it works and *when* to prefer one tool over another.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**FSL**\n\nStrong for: eddy correction, TBSS group studies, bedpostX\n\nLimitation: no CSD, closed-source eddy")
    with col2:
        st.success("**MRtrix3**\n\nStrong for: CSD, tractography (iFOD2), fixel-based analysis\n\nLimitation: steeper learning curve")
    with col3:
        st.warning("**DIPY**\n\nStrong for: flexibility, transparency, teaching\n\nLimitation: slower for large datasets")

    st.divider()
    st.markdown("### How to use this app")
    st.markdown("""
    1. **Select a pipeline step** from the sidebar
    2. Each step shows the command for all three tools in **side-by-side tabs**
    3. Click **Run** to execute the command (if the tool is installed)
    4. Compare the outputs visually
    5. Read the **Why?** section to understand the rationale

    👈 Start by selecting **Brain Extraction** in the sidebar.
    """)

    st.divider()
    st.markdown("### The full pipeline at a glance")
    pipeline_steps = {
        "Brain Extraction":   ("BET",              "dwi2mask",      "median_otsu"),
        "Denoising":          ("—",                "dwidenoise",    "mppca"),
        "Gibbs Removal":      ("—",                "mrdegibbs",     "gibbs_removal"),
        "Eddy Correction":    ("eddy",             "dwifslpreproc", "manual"),
        "Bias Correction":    ("fast",             "dwibiascorrect","—"),
        "DTI Fitting":        ("dtifit",           "dwi2tensor",    "TensorModel"),
        "CSD / FODs":         ("—",                "dwi2fod",       "CSDModel"),
        "Tractography":       ("probtrackx2",      "tckgen iFOD2",  "LocalTracking"),
        "Skeleton (SIFT2)":   ("—",                "tcksift2",      "—"),
        "TBSS":               ("tbss_1–4+randomise","—",            "—"),
        "Fixel Analysis":     ("—",                "fixelcfestats", "—"),
    }
    import pandas as pd
    df = pd.DataFrame(pipeline_steps, index=["FSL", "MRtrix3", "DIPY"]).T
    st.dataframe(df, use_container_width=True)


def page_brain_extraction():
    st.title("Step 1 — Brain Extraction")
    st.markdown("""
    Every downstream step needs a **brain mask** — a binary image marking which voxels
    are brain. Without it, fitting runs on skull/background, tractography seeds outside
    the brain, and registration is confused by non-brain tissue.
    """)

    dd = data_dir()
    pd_ = prep_dir()

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate synthetic data from the sidebar first.")
        return

    # Load b=0 mean
    img   = nib.load(str(dd / "data.nii.gz"))
    data  = img.get_fdata()
    bvals = np.loadtxt(str(dd / "bvals"))
    b0    = data[..., bvals < 50].mean(axis=-1).astype(np.float32)
    b0_path = pd_ / "b0_mean.nii.gz"
    nib.save(nib.Nifti1Image(b0, img.affine), str(b0_path))

    # Parameter controls
    st.markdown("### Parameters")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        f_thresh = st.slider("FSL BET -f (fractional threshold)",
                             0.1, 0.7, 0.25, 0.05,
                             help="Lower = keep more tissue. For dMRI b=0, 0.2–0.3 is typical.")
    with col_p2:
        robust = st.checkbox("FSL BET -R (robust centre estimation)", value=True)

    # Tabs: one per tool
    tab_fsl, tab_mrt, tab_dipy = st.tabs(["🔵 FSL BET", "🟢 MRtrix3 dwi2mask", "🟡 DIPY median_otsu"])

    with tab_fsl:
        cmd = ["bet", str(b0_path), str(pd_ / "bet_brain"),
               "-f", str(f_thresh), "-m"]
        if robust:
            cmd.append("-R")
        st.code(fmt_cmd(cmd), language="bash")
        st.caption("⚠️ Tip: If the mask looks over-stripped, lower `-f`. If skull leaks in, raise it.")

        if st.button("▶ Run FSL BET", key="run_bet"):
            if not check_tool("bet"):
                st.error("FSL not found on PATH")
            else:
                with st.spinner("Running BET..."):
                    ok, out = run_cmd(cmd, "BET")
                if ok:
                    st.success("Done!")
                    mask_path = pd_ / "bet_brain_mask.nii.gz"
                    if mask_path.exists():
                        fig = show_mask_on_b0(b0, mask_path, "FSL BET mask")
                        st.pyplot(fig)
                        plt.close(fig)
                else:
                    st.error(f"Failed:\n```\n{out}\n```")

        mask_path = pd_ / "bet_brain_mask.nii.gz"
        if mask_path.exists():
            fig = show_mask_on_b0(b0, mask_path, "FSL BET mask (existing)")
            st.pyplot(fig)
            plt.close(fig)

    with tab_mrt:
        mif_path = pd_ / "dwi_raw.mif"
        mrt_mask = pd_ / "mask_mrtrix.nii.gz"

        # Convert to mif if needed
        if not mif_path.exists():
            conv_cmd = ["mrconvert", str(dd / "data.nii.gz"), str(mif_path),
                        "-fslgrad", str(dd / "bvecs"), str(dd / "bvals"), "-force"]
            st.info("First, convert to MRtrix3 .mif format (embeds gradient table):")
            st.code(fmt_cmd(conv_cmd), language="bash")

        cmd_mrt = ["dwi2mask", str(mif_path), str(mrt_mask), "-force"]
        st.code(fmt_cmd(cmd_mrt), language="bash")
        st.caption("dwi2mask uses the full DWI signal — more robust than BET for b=0 contrast.")

        if st.button("▶ Run MRtrix3 dwi2mask", key="run_dwi2mask"):
            if not check_tool("mrconvert"):
                st.error("MRtrix3 not found on PATH")
            else:
                with st.spinner("Converting to .mif..."):
                    subprocess.run(conv_cmd if not mif_path.exists()
                                   else ["true"], capture_output=True)
                with st.spinner("Running dwi2mask..."):
                    ok, out = run_cmd(cmd_mrt, "dwi2mask")
                if ok:
                    st.success("Done!")
                    fig = show_mask_on_b0(b0, mrt_mask, "MRtrix3 mask")
                    st.pyplot(fig); plt.close(fig)
                else:
                    st.error(f"Failed:\n```\n{out}\n```")

    with tab_dipy:
        st.code("""from dipy.segment.mask import median_otsu

b0_indices = list(np.where(bvals < 50)[0])
_, brain_mask = median_otsu(
    data,
    vol_idx=b0_indices,
    median_radius=2,
    numpass=1,
    dilate=1,
)""", language="python")
        st.caption("Pure Python — no external tool required. Works on any platform.")

        if st.button("▶ Run DIPY median_otsu", key="run_otsu"):
            try:
                from dipy.segment.mask import median_otsu
                b0_idx = list(np.where(bvals < 50)[0])
                with st.spinner("Running median_otsu..."):
                    _, mask = median_otsu(data, vol_idx=b0_idx,
                                         median_radius=2, numpass=1, dilate=1)
                dipy_mask_path = pd_ / "mask_dipy.nii.gz"
                nib.save(nib.Nifti1Image(mask.astype(np.uint8), img.affine),
                         str(dipy_mask_path))
                st.success(f"Done! {mask.sum()} brain voxels")
                fig = show_mask_on_b0(b0, mask, "DIPY mask")
                st.pyplot(fig); plt.close(fig)
            except ImportError:
                st.error("DIPY not importable — check your environment")
            except Exception as e:
                st.error(str(e))

    # Comparison section
    st.divider()
    st.markdown("### 📊 Compare masks")
    masks = {}
    for label, path in [("FSL BET",  pd_ / "bet_brain_mask.nii.gz"),
                         ("MRtrix3",  pd_ / "mask_mrtrix.nii.gz"),
                         ("DIPY",     pd_ / "mask_dipy.nii.gz")]:
        if path.exists():
            masks[label] = nib.load(str(path)).get_fdata().astype(bool)

    if masks:
        cols = st.columns(len(masks))
        for col, (label, m) in zip(cols, masks.items()):
            with col:
                z = m.shape[2] // 2
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.imshow(b0[:, :, z].T, cmap="gray", origin="lower")
                overlay = np.zeros((*m[:, :, z].shape, 4))
                overlay[m[:, :, z]] = [1, 0.3, 0.3, 0.4]
                ax.imshow(overlay.transpose(1, 0, 2), origin="lower")
                ax.set_title(f"{label}\n({m.sum():,} voxels)", fontsize=9)
                ax.axis("off")
                st.pyplot(fig); plt.close(fig)

        if len(masks) >= 2:
            st.markdown("**Dice similarity** (1.0 = identical):")
            labels = list(masks.keys())
            for i in range(len(labels)):
                for j in range(i+1, len(labels)):
                    a, b2 = masks[labels[i]], masks[labels[j]]
                    dice  = 2*(a&b2).sum() / (a.sum()+b2.sum()+1e-10)
                    col_d = "green" if dice > 0.95 else "orange" if dice > 0.90 else "red"
                    st.markdown(f":{col_d}[{labels[i]} vs {labels[j]}: **{dice:.3f}**]")
    else:
        st.info("Run at least one tool above to see the comparison.")

    with st.expander("📖 Why does the mask matter so much?"):
        st.markdown("""
        - **Eddy correction**: without a mask, eddy fits a deformation to the skull too — corrupting the correction
        - **DTI fitting**: voxels outside the mask get FA=0, MD=0 — noise
        - **TBSS**: the skeleton is derived from within the mask — wrong mask → wrong skeleton
        - **Tractography**: seeds outside the brain produce spurious streamlines

        **Rule of thumb**: if in doubt, err on the side of *including* more tissue (lower `-f`).
        It's easier to erode a slightly too-large mask than to recover cut brain tissue.
        """)


def page_denoising():
    st.title("Step 2 — Denoising (MP-PCA)")
    st.markdown("""
    MP-PCA denoising exploits the redundancy across many dMRI volumes.
    Noise is random across volumes; true signal is structured.
    PCA separates them, and the Marchenko-Pastur distribution tells us how many
    components are pure noise.

    > **Rule**: always denoise **first** — before any interpolation, resampling, or correction.
    """)

    dd  = data_dir()
    pd_ = prep_dir()

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate synthetic data from the sidebar.")
        return

    tab_fsl, tab_mrt, tab_dipy = st.tabs(["🔵 FSL", "🟢 MRtrix3 dwidenoise", "🟡 DIPY mppca"])

    with tab_fsl:
        st.warning("**FSL has no MP-PCA denoising tool.** This step should use MRtrix3 or DIPY even in an FSL-based pipeline.")
        st.markdown("Recommended approach for FSL pipelines:")
        st.code("dwidenoise dwi_raw.mif dwi_denoised.mif -noise noise_map.mif", language="bash")
        st.caption("Run MRtrix3 dwidenoise first, then proceed with FSL eddy on the denoised data.")

    with tab_mrt:
        mif_in  = pd_ / "dwi_raw.mif"
        mif_out = pd_ / "dwi_denoised.mif"
        noise_m = pd_ / "noise_map.mif"

        cmd = ["dwidenoise", str(mif_in), str(mif_out),
               "-noise", str(noise_m), "-force"]
        st.code(fmt_cmd(cmd), language="bash")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Output**: denoised DWI")
        with col2:
            st.markdown("**Output**: noise map σ(x,y,z)")

        st.caption("The noise map should be spatially smooth. Any anatomical structure in it means the method removed real signal.")

        if st.button("▶ Run dwidenoise", key="run_denoise_mrt"):
            if not check_tool("dwidenoise"):
                st.error("MRtrix3 not found")
            elif not mif_in.exists():
                st.error(f"Input .mif not found: {mif_in}\nRun mrconvert first (see Brain Extraction step)")
            else:
                with st.spinner("Denoising..."):
                    ok, out = run_cmd(cmd, "dwidenoise")
                st.success("Done!") if ok else st.error(out)

    with tab_dipy:
        st.code("""from dipy.denoise.localpca import mppca

denoised, sigma = mppca(data, patch_radius=1, return_sigma=True)
# patch_radius=1 → 3×3×3 patches (fast demo; use 2 for production)
# sigma is the estimated noise level per voxel""", language="python")

        st.caption("⏱ Demo runs with patch_radius=1 (3×3×3, ~5 s). Production: patch_radius=2 (5×5×5, 5–15 min on HCP data).")
        if st.button("▶ Run DIPY mppca", key="run_denoise_dipy"):
            try:
                from dipy.denoise.localpca import mppca
                img  = nib.load(str(dd / "data.nii.gz"))
                data = img.get_fdata()
                with st.spinner("Running mppca — patch_radius=1 (3×3×3 patches, fast demo)..."):
                    denoised, sigma = mppca(data, patch_radius=1, return_sigma=True)
                out_path   = pd_ / "dwi_denoised_dipy.nii.gz"
                sigma_path = pd_ / "noise_map_dipy.nii.gz"
                nib.save(nib.Nifti1Image(denoised.astype(np.float32), img.affine), str(out_path))
                nib.save(nib.Nifti1Image(sigma.astype(np.float32), img.affine), str(sigma_path))
                st.success(f"Done! Mean σ = {sigma.mean():.2f}")

                col1, col2 = st.columns(2)
                with col1:
                    fig = show_slice(str(out_path), "Denoised (DIPY)", cmap="gray")
                    st.pyplot(fig); plt.close(fig)
                with col2:
                    fig = show_slice(str(sigma_path), "Noise map σ", cmap="hot")
                    st.pyplot(fig); plt.close(fig)
            except ImportError:
                st.error("DIPY not importable")
            except Exception as e:
                st.error(str(e))

    with st.expander("📖 How MP-PCA works"):
        st.markdown("""
        1. A small patch of voxels (e.g. 5×5×5) is extracted
        2. PCA is computed on the (voxels × volumes) matrix
        3. The **Marchenko-Pastur distribution** predicts how many PCA components are pure noise
        4. Noise components are zeroed; signal components are kept
        5. The denoised patch is written back

        **Why MRtrix3 > FSL here**: FSL simply does not implement this.
        **Why DIPY ≈ MRtrix3**: same algorithm — differences arise from boundary handling only.
        """)


def page_dti():
    st.title("Step 4 — DTI Fitting")
    st.markdown("""
    DTI models each voxel's diffusion as an **ellipsoid** — three eigenvalues describing
    how much diffusion occurs along each axis. From these we derive:
    **FA** (anisotropy), **MD** (mean diffusivity), **AD**, **RD**, and the principal eigenvector **V1**.
    """)

    dd  = data_dir()
    pd_ = prep_dir()
    dti_dir_ = ROOT / "data" / "hcp" / st.session_state.get("subject","100307") / "dti"
    dti_dir_.mkdir(parents=True, exist_ok=True)

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate synthetic data from the sidebar.")
        return

    mask_candidates = [
        pd_ / "bet_brain_mask.nii.gz",
        pd_ / "mask_dipy.nii.gz",
        dd  / "nodif_brain_mask.nii.gz",
    ]
    mask_path = next((p for p in mask_candidates if p.exists()), None)
    if not mask_path:
        st.warning("No brain mask found — run Brain Extraction first. Using whole-volume for now.")

    tab_fsl, tab_mrt, tab_dipy = st.tabs(["🔵 FSL dtifit", "🟢 MRtrix3 dwi2tensor", "🟡 DIPY TensorModel"])

    with tab_fsl:
        fsl_base = str(dti_dir_ / "fsl_dti")
        cmd = ["dtifit",
               "--data=" + str(dd / "data.nii.gz"),
               "--mask=" + str(mask_path or dd / "nodif_brain_mask.nii.gz"),
               "--bvecs=" + str(dd / "bvecs"),
               "--bvals=" + str(dd / "bvals"),
               "--out="   + fsl_base,
               "--wls",          # weighted least squares
               "--save_tensor",  # save full tensor
               ]
        st.code(fmt_cmd(cmd), language="bash")
        st.caption("Outputs: FA, MD, L1, L2, L3, V1, V2, V3, tensor, S0")

        if st.button("▶ Run FSL dtifit", key="run_dtifit"):
            if not check_tool("dtifit"):
                st.error("FSL not found")
            else:
                with st.spinner("Running dtifit..."):
                    ok, out = run_cmd(cmd, "dtifit")
                if ok:
                    st.success("Done!")
                else:
                    st.error(out)

        fa_path = dti_dir_ / "fsl_dti_FA.nii.gz"
        md_path = dti_dir_ / "fsl_dti_MD.nii.gz"
        if fa_path.exists():
            col1, col2 = st.columns(2)
            with col1:
                fig = show_slice(str(fa_path), "FSL FA", cmap="hot", vmin=0, vmax=1)
                st.pyplot(fig); plt.close(fig)
            with col2:
                fig = show_slice(str(md_path), "FSL MD", cmap="Blues")
                st.pyplot(fig); plt.close(fig)

    with tab_mrt:
        tensor_out = str(dti_dir_ / "mrt_tensor.mif")
        mif_path_dti = pd_ / "dwi_raw.mif"
        mask_arg = str(mask_path or dd / "nodif_brain_mask.nii.gz")

        if not mif_path_dti.exists():
            st.warning(
                "dwi_raw.mif not found — run **mrconvert** in the Brain Extraction step first. "
                "dwi2tensor requires a .mif file with an embedded gradient table."
            )

        mif_in = str(mif_path_dti) if mif_path_dti.exists() else str(mif_path_dti)

        cmd1 = ["dwi2tensor", mif_in, tensor_out, "-mask", mask_arg, "-force"]
        cmd2 = ["tensor2metric", tensor_out,
                "-fa",     str(dti_dir_ / "mrt_FA.nii.gz"),
                "-adc",    str(dti_dir_ / "mrt_MD.nii.gz"),
                "-vector", str(dti_dir_ / "mrt_V1.nii.gz"),
                "-mask",   mask_arg, "-force"]

        st.code(fmt_cmd(cmd1), language="bash")
        st.code(fmt_cmd(cmd2), language="bash")
        st.caption("Two commands: first fit tensor, then extract metrics. More explicit than dtifit.")

        if st.button("▶ Run MRtrix3 dwi2tensor", key="run_dwi2tensor"):
            if not check_tool("dwi2tensor"):
                st.error("MRtrix3 not found")
            else:
                with st.spinner("Fitting tensor..."):
                    ok1, out1 = run_cmd(cmd1, "dwi2tensor")
                if ok1:
                    with st.spinner("Extracting metrics..."):
                        ok2, out2 = run_cmd(cmd2, "tensor2metric")
                    st.success("Done!") if ok2 else st.error(out2)
                else:
                    st.error(out1)

    with tab_dipy:
        st.code("""from dipy.reconst.dti import TensorModel, fractional_anisotropy
from dipy.core.gradients import gradient_table

# Use lowest available non-zero shell (≤1500 ideal; works with b=2000 too)
shells  = np.unique(np.round(bvals, -2).astype(int))
target  = int(shells[shells > 100][np.argmin(np.abs(shells[shells > 100] - 1000))])
sel     = (bvals < 50) | (np.abs(bvals - target) < max(100, target * 0.12))
gtab    = gradient_table(bvals[sel], bvecs[sel])
model   = TensorModel(gtab, fit_method='WLS')
fit     = model.fit(data[..., sel], mask=brain_mask)

FA = fractional_anisotropy(fit.evals)   # shape (x, y, z)
MD = mean_diffusivity(fit.evals)
V1 = fit.evecs[..., 0]                  # principal eigenvector""", language="python")

        if st.button("▶ Run DIPY TensorModel", key="run_dipy_dti"):
            try:
                from dipy.reconst.dti import TensorModel, fractional_anisotropy, mean_diffusivity
                from dipy.io.gradients import read_bvals_bvecs
                from dipy.core.gradients import gradient_table

                bv, bvc = read_bvals_bvecs(str(dd/"bvals"), str(dd/"bvecs"))
                img_  = nib.load(str(dd/"data.nii.gz"))
                data_ = img_.get_fdata()
                msk   = nib.load(str(mask_path)).get_fdata().astype(bool) if mask_path else None

                sel, target_b = best_shell_sel(bv, preferred=1000)
                gtab  = gradient_table(bv[sel], bvc[sel])
                st.caption(f"Using b=0 + b={target_b} shell ({sel.sum()} volumes)")
                with st.spinner("Fitting tensor..."):
                    fit = TensorModel(gtab, fit_method='WLS').fit(data_[..., sel], mask=msk)
                FA  = fractional_anisotropy(fit.evals).astype(np.float32)
                MD  = mean_diffusivity(fit.evals).astype(np.float32)

                nib.save(nib.Nifti1Image(FA, img_.affine), str(dti_dir_/"dipy_FA.nii.gz"))
                nib.save(nib.Nifti1Image(MD, img_.affine), str(dti_dir_/"dipy_MD.nii.gz"))
                st.success(f"Done! FA mean (WM) = {FA[FA>0.2].mean():.3f}")

                col1, col2 = st.columns(2)
                with col1:
                    fig = show_slice(str(dti_dir_/"dipy_FA.nii.gz"), "DIPY FA", cmap="hot", vmin=0, vmax=1)
                    st.pyplot(fig); plt.close(fig)
                with col2:
                    fig = show_slice(str(dti_dir_/"dipy_MD.nii.gz"), "DIPY MD", cmap="Blues")
                    st.pyplot(fig); plt.close(fig)
            except ImportError:
                st.error("DIPY not importable")
            except Exception as e:
                st.error(str(e))

    # FA comparison
    st.divider()
    st.markdown("### 📊 FA map comparison")
    fa_maps = {}
    for label, path in [("FSL", dti_dir_/"fsl_dti_FA.nii.gz"),
                         ("MRtrix3", dti_dir_/"mrt_FA.nii.gz"),
                         ("DIPY", dti_dir_/"dipy_FA.nii.gz")]:
        if path.exists():
            fa_maps[label] = path

    if fa_maps:
        cols = st.columns(len(fa_maps))
        for col, (label, path) in zip(cols, fa_maps.items()):
            with col:
                fig = show_slice(str(path), f"{label} FA", cmap="hot", vmin=0, vmax=1)
                st.pyplot(fig); plt.close(fig)
                fa_vol = nib.load(str(path)).get_fdata()
                st.caption(f"Mean FA (>0.2): {fa_vol[fa_vol>0.2].mean():.3f}")
    else:
        st.info("Run at least one tool above to see FA maps.")

    with st.expander("📖 When to use which tool for DTI?"):
        st.markdown("""
        | | FSL dtifit | MRtrix3 dwi2tensor | DIPY |
        |---|---|---|---|
        | Speed | Fast | Fast | Moderate |
        | Multi-shell handling | Uses all shells (not ideal) | Uses all shells | You control shell selection |
        | **Recommendation** | ✓ Quick maps | ✓ MRtrix3 pipelines | ✓ Research / teaching |

        **Key insight**: For DTI, only use b≤1000 volumes. Higher b-values violate the
        monoexponential signal decay assumption that DTI is built on.
        DIPY makes this explicit — you select the shell. FSL and MRtrix3 use all shells by default.
        """)


def page_tbss():
    st.title("Step 7 — TBSS Group Analysis")
    st.markdown("""
    **Tract-Based Spatial Statistics (TBSS)** compares FA (or MD/RD/AD) across subjects
    on a **white matter skeleton** — robust to small registration errors.

    > FSL only. MRtrix3 equivalent = Fixel-Based Analysis. DIPY has no TBSS equivalent.
    > **TBSS requires ≥ 2 subjects.** Use the generator below to create a synthetic group.
    """)

    import pandas as pd

    subj     = st.session_state.get("subject", "100307")
    dti_dir_ = ROOT / "data" / "hcp" / subj / "dti"
    tbss_dir = ROOT / "data" / "group" / "tbss"

    fa_candidates = [dti_dir_ / "fsl_dti_FA.nii.gz",
                     dti_dir_ / "dipy_FA.nii.gz",
                     dti_dir_ / "mrt_FA.nii.gz"]
    fa_map = next((p for p in fa_candidates if p.exists()), None)

    # ── 0. Synthetic group setup ──────────────────────────────────────────────
    st.markdown("### 0. Setup — create a synthetic group for demo")
    st.info(
        "Real TBSS needs FA maps from multiple scanned subjects. "
        "For this demo, we perturb your single FA map with noise to simulate a group."
    )

    if fa_map:
        st.success(f"Source FA map: `{short(fa_map)}`")
    else:
        st.warning("No FA map found — run **DTI Fitting (Step 4)** first.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        n_sub = st.slider("Synthetic subjects", 4, 12, 6)
    with col_s2:
        noise_sd = st.slider("Noise SD (FA units)", 0.01, 0.08, 0.03, 0.01)

    if st.button("⚙ Generate synthetic group FA maps", disabled=fa_map is None):
        tbss_dir.mkdir(parents=True, exist_ok=True)
        img_ = nib.load(str(fa_map))
        FA_  = np.clip(img_.get_fdata(dtype=np.float32), 0, 1)
        rng  = np.random.default_rng(42)
        for i in range(n_sub):
            perturbed = np.clip(FA_ + rng.normal(0, noise_sd, FA_.shape).astype(np.float32), 0, 1)
            nib.save(nib.Nifti1Image(perturbed, img_.affine),
                     str(tbss_dir / f"sub{i+1:02d}_FA.nii.gz"))
        st.success(f"Created {n_sub} synthetic FA maps in `{short(tbss_dir)}/`")
        existing = list(tbss_dir.glob("sub*_FA.nii.gz"))
        st.caption(f"Files: {', '.join(p.name for p in sorted(existing))}")

    existing_fa = sorted(tbss_dir.glob("sub*_FA.nii.gz"))
    if existing_fa:
        st.caption(f"Group directory has {len(existing_fa)} FA maps ready.")
    else:
        st.caption("Group directory is empty — generate synthetic maps above first.")

    # ── 1. tbss_1_preproc ────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Step 1 — `tbss_1_preproc` — edge erosion & QC slices")
    st.code("cd data/group/tbss && tbss_1_preproc *.nii.gz", language="bash")
    st.caption("Erodes FA edges to reduce misregistration artifacts. Creates slicesdir/ for visual QC.")

    if st.button("▶ Run tbss_1_preproc", key="run_tbss1"):
        if not check_tool("tbss_1_preproc"):
            st.error("FSL not found on PATH")
        elif not existing_fa:
            st.error("No FA maps found — generate synthetic group first.")
        else:
            with st.spinner("Running tbss_1_preproc…"):
                r = subprocess.run("tbss_1_preproc *.nii.gz", shell=True,
                                   cwd=str(tbss_dir), capture_output=True, text=True)
            if r.returncode == 0:
                st.success("Done!")
                fa_subdir = tbss_dir / "FA"
                proc_maps = sorted(fa_subdir.glob("*_FA_mask.nii.gz")) if fa_subdir.exists() else []
                if proc_maps:
                    fig = show_slice(str(proc_maps[0]), f"Preprocessed FA — {proc_maps[0].name}", cmap="hot", vmin=0, vmax=1)
                    st.pyplot(fig); plt.close(fig)
            else:
                st.error(f"Failed:\n```\n{r.stderr}\n```")

    # ── 2. tbss_2_reg ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Step 2 — `tbss_2_reg` — register to FMRIB58 template")
    st.code("tbss_2_reg -t", language="bash")
    st.caption("`-t` = use FMRIB58_FA standard-space target. `-n` = use study-specific template (better for non-standard populations).")

    if st.button("▶ Run tbss_2_reg", key="run_tbss2"):
        if not check_tool("tbss_2_reg"):
            st.error("FSL not found on PATH")
        elif not (tbss_dir / "FA").exists():
            st.error("Run tbss_1_preproc first.")
        else:
            with st.spinner("Registering all FA maps to FMRIB58 template (FNIRT) — may take several minutes…"):
                r = subprocess.run("tbss_2_reg -t", shell=True,
                                   cwd=str(tbss_dir), capture_output=True, text=True)
            if r.returncode == 0:
                st.success("Done!")
                warped = sorted((tbss_dir / "FA").glob("*_FA_to_target.nii.gz"))
                if warped:
                    fig = show_slice(str(warped[0]), f"Registered FA — {warped[0].name}", cmap="hot", vmin=0, vmax=1)
                    st.pyplot(fig); plt.close(fig)
            else:
                st.error(f"Failed:\n```\n{r.stderr}\n```")

    # ── 3. tbss_3_postreg ────────────────────────────────────────────────────
    st.divider()
    st.markdown("### Step 3 — `tbss_3_postreg` — mean FA + skeleton")
    st.code("tbss_3_postreg -S", language="bash")
    st.caption("`-S` derives the skeleton from the study's own mean FA (recommended).")

    if st.button("▶ Run tbss_3_postreg", key="run_tbss3"):
        if not check_tool("tbss_3_postreg"):
            st.error("FSL not found on PATH")
        elif not sorted((tbss_dir / "FA").glob("*_FA_to_target.nii.gz") if (tbss_dir/"FA").exists() else []):
            st.error("Run tbss_2_reg first.")
        else:
            with st.spinner("Creating mean FA and skeleton…"):
                r = subprocess.run("tbss_3_postreg -S", shell=True,
                                   cwd=str(tbss_dir), capture_output=True, text=True)
            if r.returncode == 0:
                st.success("Done!")
                mean_fa  = tbss_dir / "stats" / "mean_FA.nii.gz"
                skeleton = tbss_dir / "stats" / "mean_FA_skeleton.nii.gz"
                if mean_fa.exists() and skeleton.exists():
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = show_slice(str(mean_fa), "Mean FA", cmap="hot", vmin=0, vmax=1)
                        st.pyplot(fig); plt.close(fig)
                    with col2:
                        fig = show_slice(str(skeleton), "WM Skeleton", cmap="hot", vmin=0, vmax=1)
                        st.pyplot(fig); plt.close(fig)
            else:
                st.error(f"Failed:\n```\n{r.stderr}\n```")

    # ── 4. tbss_4_prestats ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### Step 4 — `tbss_4_prestats` — project FA onto skeleton")
    fa_thresh = st.slider("FA threshold for skeleton", 0.10, 0.35, 0.20, 0.01,
                          help="Voxels with mean FA below this are excluded from the skeleton.")
    st.code(f"tbss_4_prestats {fa_thresh:.2f}", language="bash")
    st.caption("Projects every subject's FA onto the skeleton. Output: `all_FA_skeletonised.nii.gz` (4-D).")

    if st.button("▶ Run tbss_4_prestats", key="run_tbss4"):
        if not check_tool("tbss_4_prestats"):
            st.error("FSL not found on PATH")
        elif not (tbss_dir / "stats" / "mean_FA_skeleton.nii.gz").exists():
            st.error("Run tbss_3_postreg first.")
        else:
            with st.spinner("Projecting FA maps onto skeleton…"):
                r = subprocess.run(f"tbss_4_prestats {fa_thresh:.2f}", shell=True,
                                   cwd=str(tbss_dir), capture_output=True, text=True)
            if r.returncode == 0:
                st.success("Done!")
                skel_fa = tbss_dir / "stats" / "all_FA_skeletonised.nii.gz"
                if skel_fa.exists():
                    fig = show_slice(str(skel_fa), "Skeletonised FA (sub 1)", cmap="hot", vmin=0, vmax=1)
                    st.pyplot(fig); plt.close(fig)
            else:
                st.error(f"Failed:\n```\n{r.stderr}\n```")

    # ── 5. Design matrix + randomise ─────────────────────────────────────────
    st.divider()
    st.markdown("### Step 5 — Design matrix & `randomise`")

    col1, col2 = st.columns(2)
    with col1:
        n_group1 = st.number_input("Group 1 size", 1, 50, max(1, len(existing_fa)//2))
        label1   = st.text_input("Group 1 label", "Patients")
    with col2:
        n_group2 = st.number_input("Group 2 size", 1, 50, max(1, len(existing_fa) - len(existing_fa)//2))
        label2   = st.text_input("Group 2 label", "Controls")

    n_perm = st.number_input("Permutations", 100, 10000, 500,
                             help="5000 for publication; 500 for demo.")

    if st.button("Generate & download design files"):
        n1, n2 = int(n_group1), int(n_group2)
        design   = np.array([[1,0]]*n1 + [[0,1]]*n2)
        df       = pd.DataFrame(design, columns=[label1, label2])
        st.dataframe(df)
        mat_str = f"/NumWaves 2\n/NumPoints {n1+n2}\n/PPheights 1 1\n/Matrix\n"
        mat_str += "\n".join(" ".join(map(str, row)) for row in design)
        con_str = "/NumWaves 2\n/NumContrasts 2\n/PPheights 1 1\n/Matrix\n1 -1\n-1 1\n"
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button("⬇ design.mat", mat_str, "design.mat")
        with col_b:
            st.download_button("⬇ design.con", con_str, "design.con")

    stats_dir = tbss_dir / "stats"
    design_mat = stats_dir / "design.mat"
    design_con = stats_dir / "design.con"

    st.code(
        f"randomise -i stats/all_FA_skeletonised.nii.gz -o stats/tbss_FA "
        f"-m stats/mean_FA_skeleton_mask.nii.gz "
        f"-d stats/design.mat -t stats/design.con -n {int(n_perm)} --T2",
        language="bash")
    st.caption("`--T2` = Threshold-Free Cluster Enhancement (TFCE). Always use this — uncorrected p-values are invalid.")

    if st.button("▶ Run randomise", key="run_randomise"):
        if not check_tool("randomise"):
            st.error("FSL not found on PATH")
        elif not (stats_dir / "all_FA_skeletonised.nii.gz").exists():
            st.error("Run tbss_4_prestats first.")
        elif not design_mat.exists() or not design_con.exists():
            st.error("Place design.mat and design.con in stats/ and re-run.")
        else:
            cmd_rand = [
                "randomise",
                "-i", str(stats_dir / "all_FA_skeletonised.nii.gz"),
                "-o", str(stats_dir / "tbss_FA"),
                "-m", str(stats_dir / "mean_FA_skeleton_mask.nii.gz"),
                "-d", str(design_mat),
                "-t", str(design_con),
                "-n", str(int(n_perm)),
                "--T2",
            ]
            with st.spinner(f"Running randomise ({int(n_perm)} permutations)…"):
                ok, out = run_cmd(cmd_rand, "randomise")
            if ok:
                st.success("Done!")
                pmap = stats_dir / "tbss_FA_tfce_corrp_tstat1.nii.gz"
                if pmap.exists():
                    fig = show_slice(str(pmap), "TFCE corrected p-map (1−p, contrast 1)",
                                     cmap="hot", vmin=0.95, vmax=1.0)
                    st.pyplot(fig); plt.close(fig)
                    st.caption("Voxels with 1−p > 0.95 are significant at p < 0.05 (corrected).")
            else:
                st.error(f"Failed:\n```\n{out}\n```")

    with st.expander("📖 Common TBSS mistakes"):
        st.markdown("""
| Mistake | Sign | Fix |
|---|---|---|
| Using uncorrected p | Too many significant voxels | Always use `--T2` (TFCE) |
| Wrong FA threshold | Skeleton too sparse or dense | Try 0.15–0.25 |
| Bad registration | Results in CSF/ventricles | Use `-n` (study-specific template) |
| Mixing bvec conventions | Asymmetric FA maps | Check FSL vs MRtrix3 sign |
| Not QC-checking | Outlier subjects corrupt results | Always check slicesdir/ |
| Using edited FA for TBSS | Biased skeleton projection | Use raw dtifit FA output |
""")


def page_reference():
    st.title("8️⃣  dMRI Concepts & Quick Reference")
    st.markdown(
        "A beginner's guide to the key ideas, metrics, and decisions in diffusion MRI. "
        "No steps need to be completed first — this is pure reference material."
    )

    tab_metrics, tab_glossary, tab_cheatsheet, tab_decide = st.tabs([
        "📊 DTI Metrics", "📖 Glossary", "📋 Command Cheat Sheet", "🤔 Which Tool?"
    ])

    # ── Tab 1: DTI Metrics ────────────────────────────────────────────────────
    with tab_metrics:
        st.markdown("### What do FA, MD, RD, AD actually mean?")

        metrics = {
            "FA — Fractional Anisotropy": {
                "range": "0 (isotropic) → 1 (perfectly anisotropic)",
                "healthy_wm": "0.40 – 0.65",
                "biology": "How directional the diffusion is. High FA = tightly packed, coherently oriented axons. "
                           "Low FA = crossing fibres, damage, oedema, or grey matter.",
                "sensitive_to": "Axonal loss, demyelination, fibre coherence",
                "watch_out": "FA drops at fibre crossings even in healthy tissue — DTI cannot separate crossing from damage.",
                "color": "hot",
            },
            "MD — Mean Diffusivity": {
                "range": "~0.6–1.2 × 10⁻³ mm²/s in WM",
                "healthy_wm": "0.7 – 0.9 × 10⁻³ mm²/s",
                "biology": "Overall magnitude of diffusion (average of the three eigenvalues). "
                           "High MD = oedema, tissue loss, or decreased cellularity. "
                           "Low MD = hypercellularity (e.g. tumour), cytotoxic oedema.",
                "sensitive_to": "Oedema, tissue loss, tumour",
                "watch_out": "MD increases are non-specific — many pathologies elevate it.",
                "color": "Blues",
            },
            "AD — Axial Diffusivity (λ₁)": {
                "range": "~1.0–1.5 × 10⁻³ mm²/s",
                "healthy_wm": "1.1 – 1.4 × 10⁻³ mm²/s",
                "biology": "Diffusion along the primary fibre direction (largest eigenvalue). "
                           "Sensitive to axonal integrity.",
                "sensitive_to": "Axonal injury, Wallerian degeneration",
                "watch_out": "Affected by fibre orientation relative to MRI axes.",
                "color": "Greens",
            },
            "RD — Radial Diffusivity (λ₂+λ₃)/2": {
                "range": "~0.3–0.7 × 10⁻³ mm²/s",
                "healthy_wm": "0.3 – 0.5 × 10⁻³ mm²/s",
                "biology": "Diffusion perpendicular to axons. Increases with demyelination "
                           "(myelin sheath acts as a barrier; removing it increases RD).",
                "sensitive_to": "Myelin damage, demyelinating diseases (MS, leukodystrophies)",
                "watch_out": "Also affected by fibre crossings — less reliable in complex WM.",
                "color": "Oranges",
            },
        }

        subj    = st.session_state.get("subject", "100307")
        dti_dir_ = ROOT / "data" / "hcp" / subj / "dti"
        pd_     = prep_dir()
        mask_p  = next((p for p in [pd_ / "bet_brain_mask.nii.gz",
                                     data_dir() / "nodif_brain_mask.nii.gz"] if p.exists()), None)

        for name, info in metrics.items():
            with st.expander(f"**{name}**", expanded=(name.startswith("FA"))):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown(f"**Range:** {info['range']}")
                    st.markdown(f"**Healthy WM:** {info['healthy_wm']}")
                    st.markdown(f"**Biology:** {info['biology']}")
                    st.markdown(f"**Sensitive to:** {info['sensitive_to']}")
                    st.caption(f"Watch out: {info['watch_out']}")
                with col_b:
                    short_key = name.split("—")[0].strip().split()[0]
                    candidates = {
                        "FA":  ["fsl_dti_FA.nii.gz", "dipy_FA.nii.gz", "mrt_FA.nii.gz"],
                        "MD":  ["fsl_dti_MD.nii.gz", "dipy_MD.nii.gz", "mrt_MD.nii.gz"],
                        "AD":  ["fsl_dti_L1.nii.gz"],
                        "RD":  [],
                    }
                    found = next((dti_dir_ / f for f in candidates.get(short_key, [])
                                  if (dti_dir_ / f).exists()), None)
                    if found:
                        fig = show_slice(str(found), short_key, cmap=info["color"], vmin=0)
                        st.pyplot(fig); plt.close(fig)
                    else:
                        st.caption(f"Run DTI Fitting (Step 4) to see the {short_key} map here.")

        # All-metrics comparison if FA exists
        fa_path = next((dti_dir_ / f for f in ["fsl_dti_FA.nii.gz", "dipy_FA.nii.gz"]
                        if (dti_dir_ / f).exists()), None)
        if fa_path and mask_p:
            st.divider()
            st.markdown("### FA distribution in your data")
            FA_   = nib.load(str(fa_path)).get_fdata()
            maskd = nib.load(str(mask_p)).get_fdata().astype(bool)
            wm    = FA_[maskd & (FA_ > 0.2)]
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.hist(wm, bins=50, color="steelblue", edgecolor="none")
            ax.axvline(wm.mean(), color="red",    lw=2, label=f"Your mean = {wm.mean():.3f}")
            ax.axvspan(0.40, 0.65, alpha=0.12, color="green", label="Healthy WM range (0.40–0.65)")
            ax.set_xlabel("FA"); ax.legend(fontsize=9)
            ax.set_title("FA distribution — WM voxels (FA > 0.2)")
            st.pyplot(fig); plt.close(fig)

    # ── Tab 2: Glossary ───────────────────────────────────────────────────────
    with tab_glossary:
        st.markdown("### Key dMRI terms")
        glossary = {
            "b-value (s/mm²)": "Controls diffusion weighting strength. b=0: no diffusion weighting (T2 image). "
                                "b=1000: standard clinical. b=2000–3000: research, CSD. Higher b → more diffusion contrast, lower SNR.",
            "b-vector (bvec)": "Unit vector pointing in the gradient direction for each volume. "
                                "Each DWI volume is sensitised to diffusion along one direction. "
                                "Typically 30–300 directions uniformly distributed on a sphere.",
            "Gradient table": "The combination of b-values and b-vectors that fully describes the diffusion encoding. "
                               "DIPY stores this as a `GradientTable` object.",
            "b=0 image": "A DWI volume acquired with no diffusion weighting. "
                          "Looks like a T2 image. Used as reference for registration and SNR estimation.",
            "Multi-shell": "Acquisition with multiple non-zero b-values (e.g. b=1000 + b=2000). "
                            "Required for MSMT-CSD. Provides more microstructural information than single-shell.",
            "DTI (Diffusion Tensor Imaging)": "Models diffusion as an ellipsoid (3×3 tensor) per voxel. "
                                               "Simple, fast, works on single-shell data. "
                                               "Cannot resolve crossing fibres (>1 fibre population per voxel).",
            "CSD (Constrained Spherical Deconvolution)": "Estimates a Fibre Orientation Distribution (FOD) per voxel. "
                                                          "Can resolve crossing fibres. Requires b≥1000, preferably b=2000–3000.",
            "FOD (Fibre Orientation Distribution)": "A function on the sphere describing the probability of fibre orientations "
                                                     "in each voxel. The peak(s) of the FOD give the fibre direction(s).",
            "Spherical harmonics (SH)": "Mathematical basis functions used to represent FODs compactly. "
                                         "lmax=8 gives 45 coefficients per voxel — enough for most WM.",
            "Tractography": "Algorithm that traces streamlines through the brain by following FOD peaks or DTI eigenvectors. "
                             "Probabilistic (iFOD2): samples from FOD uncertainty. Deterministic: follows single direction.",
            "SIFT2": "Post-tractography streamline reweighting. Each streamline gets a weight so the "
                     "tractogram density matches the FOD integrals. Improves quantitative accuracy.",
            "TBSS (Tract-Based Spatial Statistics)": "FSL group analysis method. Registers all subjects' FA to a template, "
                                                      "extracts a WM skeleton, and runs permutation tests on the skeleton.",
            "Eddy currents": "Magnetic field distortions caused by rapidly switching gradient coils. "
                              "They cause geometric distortions that vary per gradient direction. Corrected by FSL eddy.",
            "Phase encoding direction": "The axis along which susceptibility distortions occur (usually AP or PA). "
                                         "Required by FSL eddy in acqparams.txt.",
            "Phase encoding direction": "The axis along which susceptibility distortions occur (usually AP or PA). "
                                         "Required by FSL eddy in acqparams.txt.",
            "Readout time": "Time to acquire one EPI volume. Used to model susceptibility distortions. "
                             "Typical value: 0.05–0.1 s. Goes in acqparams.txt.",
            "MP-PCA denoising": "Marchenko-Pastur PCA denoising. Exploits redundancy across many DWI volumes "
                                 "to separate signal from noise. Always apply before any interpolation or resampling.",
            "Gibbs ringing": "Truncation artefact appearing as ringing bands near sharp edges (e.g. skull). "
                              "Removed by MRtrix3 `mrdegibbs` before eddy correction.",
        }
        for term, definition in glossary.items():
            with st.expander(f"**{term}**"):
                st.markdown(definition)

    # ── Tab 3: Command Cheat Sheet ────────────────────────────────────────────
    with tab_cheatsheet:
        st.markdown("### Complete pipeline — all commands in one place")
        st.caption("Copy any block and adapt paths to your data.")

        sections = {
            "1. Brain Extraction": {
                "FSL": "bet b0_mean.nii.gz bet_brain -f 0.25 -m -R",
                "MRtrix3": "mrconvert data.nii.gz dwi.mif -fslgrad bvecs bvals\ndwi2mask dwi.mif mask.nii.gz",
                "DIPY": "from dipy.segment.mask import median_otsu\n_, mask = median_otsu(data, vol_idx=b0_idx, median_radius=2, numpass=1, dilate=1)",
            },
            "2. Denoising": {
                "FSL": "# FSL has no MP-PCA denoising — use MRtrix3 or DIPY",
                "MRtrix3": "dwidenoise dwi.mif dwi_denoised.mif -noise noise_map.mif",
                "DIPY": "from dipy.denoise.localpca import mppca\ndenoised, sigma = mppca(data, patch_radius=2)",
            },
            "3. Eddy Correction": {
                "FSL": "eddy_cpu --imain=data.nii.gz --mask=mask.nii.gz \\\n  --index=index.txt --acqp=acqparams.txt \\\n  --bvecs=bvecs --bvals=bvals --out=eddy_corrected --repol",
                "MRtrix3": "dwifslpreproc dwi.mif dwi_preproc.mif -pe_dir AP -rpe_none \\\n  -eddy_options \" --repol\"",
                "DIPY": "from dipy.align.motion import motion_correction\ncorrected, _ = motion_correction(img, gtab, affine)",
            },
            "4. DTI Fitting": {
                "FSL": "dtifit --data=data.nii.gz --mask=mask.nii.gz \\\n  --bvecs=bvecs --bvals=bvals --out=dti --wls",
                "MRtrix3": "dwi2tensor dwi.mif tensor.mif -mask mask.nii.gz\ntensor2metric tensor.mif -fa FA.nii.gz -adc MD.nii.gz -vector V1.nii.gz",
                "DIPY": "from dipy.reconst.dti import TensorModel, fractional_anisotropy\nfit = TensorModel(gtab).fit(data, mask=mask)\nFA = fractional_anisotropy(fit.evals)",
            },
            "5. CSD / FODs": {
                "FSL": "# FSL does not implement CSD",
                "MRtrix3": "dwi2response dhollander dwi.mif wm.txt gm.txt csf.txt\ndwi2fod msmt_csd dwi.mif wm.txt wm_fod.mif gm.txt gm_fod.mif csf.txt csf_fod.mif",
                "DIPY": "from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel, auto_response_ssst\nresponse, _ = auto_response_ssst(gtab, data, roi_radii=10, fa_thr=0.7)\ncsd_fit = ConstrainedSphericalDeconvModel(gtab, response).fit(data)",
            },
            "6. Tractography": {
                "FSL": "# bedpostX (6–24 h) required before probtrackx2\nbedpostx subject/T1w/Diffusion/\nprobtrackx2 -s merged -m mask.nii.gz -x seed.nii.gz --dir=output",
                "MRtrix3": "tckgen wm_fod.mif tracks.tck -algorithm iFOD2 -select 1000000 \\\n  -seed_image mask.nii.gz -mask mask.nii.gz\ntcksift2 tracks.tck wm_fod.mif sift2_weights.txt",
                "DIPY": "from dipy.tracking.local_tracking import LocalTracking\nfrom dipy.tracking.stopping_criterion import ThresholdStoppingCriterion\nstopping = ThresholdStoppingCriterion(FA, 0.2)\nstreamlines = LocalTracking(peaks, stopping, seeds, affine, step_size=0.5)",
            },
            "7. TBSS (group)": {
                "FSL": "tbss_1_preproc *.nii.gz\ntbss_2_reg -t\ntbss_3_postreg -S\ntbss_4_prestats 0.2\nrandomise -i all_FA_skeletonised.nii.gz -o tbss_FA \\\n  -m mean_FA_skeleton_mask.nii.gz -d design.mat -t design.con -n 5000 --T2",
                "MRtrix3": "# Fixel-Based Analysis (FBA) is the MRtrix3 equivalent of TBSS",
                "DIPY": "# No TBSS equivalent in DIPY",
            },
        }

        for step, tools in sections.items():
            st.markdown(f"#### {step}")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.caption("🔵 FSL")
                st.code(tools["FSL"], language="bash")
            with c2:
                st.caption("🟢 MRtrix3")
                st.code(tools["MRtrix3"], language="bash")
            with c3:
                st.caption("🟡 DIPY")
                st.code(tools["DIPY"], language="python")

    # ── Tab 4: Decision Guide ─────────────────────────────────────────────────
    with tab_decide:
        st.markdown("### Which tool should I use?")

        st.markdown("#### By task")
        st.markdown("""
| Task | Best tool | Why |
|---|---|---|
| Brain mask | DIPY `median_otsu` | No installation, works anywhere |
| Denoising | MRtrix3 `dwidenoise` | Fastest, well-validated |
| Eddy correction | FSL `eddy` | Only production-grade eddy correction |
| Bias correction | MRtrix3 `dwibiascorrect` | Simple wrapper for ANTs/FSL |
| DTI fitting | FSL `dtifit` | Fast, standard output format |
| CSD / FODs | MRtrix3 `dwi2fod` | Gold standard for research |
| Whole-brain tractography | MRtrix3 `tckgen iFOD2` | Best algorithm (iFOD2 + SIFT2) |
| ROI tractography | FSL `probtrackx2` | Best for specific pathway connectivity |
| Group statistics | FSL `TBSS + randomise` | Standard for VBA studies |
| Fixel-based analysis | MRtrix3 `fixelcfestats` | More sensitive than TBSS for WM |
| Teaching / flexibility | DIPY | Full control, transparent code |
""")

        st.markdown("#### By dataset type")
        st.markdown("""
| Dataset | Recommended pipeline |
|---|---|
| Single-shell b=1000, clinical | FSL: BET → eddy → dtifit → TBSS |
| Single-shell b=2000, research | MRtrix3: dwidenoise → dwifslpreproc → dwi2fod (SS-CSD) → tckgen |
| Multi-shell b=1000+2000, HCP-style | MRtrix3: full MSMT-CSD pipeline |
| Teaching / exploration | DIPY: full pipeline, modify any parameter |
""")

        st.markdown("#### Common beginner mistakes")
        st.markdown("""
| Mistake | Why it's wrong | Fix |
|---|---|---|
| Running DTI on all shells | DTI assumes mono-exponential decay, breaks at b>1000 | Select b=1000 only for DTI |
| Skipping denoising | Noise amplified by all downstream steps | Always denoise first |
| Not checking the mask | Wrong mask → wrong FA/tractography | Visually inspect every mask |
| Using eddy on already-resampled data | Double interpolation degrades data | Eddy must run on raw k-space data |
| Reporting uncorrected p-values | Massive false positive rate | Always use TFCE (`--T2`) in randomise |
| Comparing FA across scanners without harmonisation | Scanner differences look like disease effects | Use ComBat or similar harmonisation |
""")


# ── Stub pages for steps not yet fully implemented ────────────────────────────

def page_eddy():
    st.title("Step 3 — Eddy Current & Motion Correction")
    st.markdown("""
    Eddy currents and subject motion distort dMRI volumes. This step corrects
    both simultaneously by registering each volume to a model prediction.
    """)

    dd  = data_dir()
    pd_ = prep_dir()

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate synthetic data from the sidebar first.")
        return

    # Auto-generate required eddy input files from the existing data
    bvals_arr = np.loadtxt(str(dd / "bvals"))
    n_vols    = len(bvals_arr)
    index_path = dd / "index.txt"
    acqp_path  = dd / "acqparams.txt"
    if not index_path.exists():
        np.savetxt(str(index_path), np.ones(n_vols, dtype=int), fmt="%d")
    if not acqp_path.exists():
        with open(str(acqp_path), "w") as f:
            f.write("0 1 0 0.05\n")

    mask_candidates = [pd_ / "bet_brain_mask.nii.gz", dd / "nodif_brain_mask.nii.gz"]
    mask_path = next((p for p in mask_candidates if p.exists()), None)
    if not mask_path:
        st.warning("No brain mask found — run Brain Extraction first.")

    eddy_out = pd_ / "eddy_corrected"

    st.warning(
        "⏱ **Runtime warning** — `eddy_cpu` runs on a single CPU core and is inherently slow:  \n"
        "- Synthetic data (30³ vox, 70 vols): ~2 min  \n"
        "- Stanford HARDI (81×106×76, 160 vols): **20–60 min**  \n"
        "- Real HCP data (145×174×145, 288 vols): **2–4 hours**  \n\n"
        "**You can skip this step for the demo** — DTI Fitting (Step 4) and CSD (Step 5) "
        "work directly on the raw data without eddy correction."
    )

    tab_fsl, tab_mrt, tab_dipy = st.tabs(
        ["🔵 FSL eddy", "🟢 MRtrix3 dwifslpreproc", "🟡 DIPY motion correction"])

    with tab_fsl:
        demo_mode = st.checkbox(
            "⚡ Demo mode — subsample to 20 volumes (~3 min instead of 20–60 min)",
            value=True, key="eddy_demo_mode"
        )

        cmd_eddy = [
            "eddy_cpu",
            "--imain="  + str(dd / "data.nii.gz"),
            "--mask="   + str(mask_path or dd / "nodif_brain_mask.nii.gz"),
            "--index="  + str(index_path),
            "--acqp="   + str(acqp_path),
            "--bvecs="  + str(dd / "bvecs"),
            "--bvals="  + str(dd / "bvals"),
            "--out="    + str(eddy_out),
            "--repol",
        ]
        st.code(fmt_cmd(cmd_eddy), language="bash")
        st.caption("`--repol` replaces outlier slices — always recommended.")

        if st.button("▶ Run FSL eddy", key="run_eddy_fsl"):
            if not check_tool("eddy_cpu") and not check_tool("eddy"):
                st.error("FSL eddy not found on PATH")
            elif not mask_path:
                st.error("Brain mask required — run Brain Extraction first.")
            else:
                run_data   = str(dd / "data.nii.gz")
                run_bvals  = str(dd / "bvals")
                run_bvecs  = str(dd / "bvecs")
                run_index  = str(index_path)

                if demo_mode:
                    bv_all = np.loadtxt(str(dd / "bvals"))
                    b0_idx  = np.where(bv_all < 50)[0][:5]
                    dwi_idx = np.where(bv_all >= 50)[0][:15]
                    sel     = np.sort(np.concatenate([b0_idx, dwi_idx]))
                    img_sub = nib.load(run_data)
                    sub_data = img_sub.get_fdata(dtype=np.float32)[..., sel]
                    sub_path = pd_ / "data_sub20.nii.gz"
                    nib.save(nib.Nifti1Image(sub_data, img_sub.affine), str(sub_path))
                    sub_bvals = pd_ / "bvals_sub20"
                    sub_bvecs = pd_ / "bvecs_sub20"
                    bvc_all   = np.loadtxt(str(dd / "bvecs"))
                    np.savetxt(str(sub_bvals), bv_all[sel].reshape(1, -1), fmt="%g")
                    np.savetxt(str(sub_bvecs), bvc_all[:, sel], fmt="%g")
                    sub_index = pd_ / "index_sub20.txt"
                    np.savetxt(str(sub_index), np.ones(len(sel), dtype=int), fmt="%d")
                    run_data  = str(sub_path)
                    run_bvals = str(sub_bvals)
                    run_bvecs = str(sub_bvecs)
                    run_index = str(sub_index)
                    st.info(f"Demo mode: running eddy on {len(sel)} volumes (5 b0 + 15 DWI)")

                tool = "eddy_cpu" if check_tool("eddy_cpu") else "eddy"
                cmd_run = [
                    tool,
                    "--imain="  + run_data,
                    "--mask="   + str(mask_path or dd / "nodif_brain_mask.nii.gz"),
                    "--index="  + run_index,
                    "--acqp="   + str(acqp_path),
                    "--bvecs="  + run_bvecs,
                    "--bvals="  + run_bvals,
                    "--out="    + str(eddy_out),
                    "--repol",
                ]
                est = "~3 min" if demo_mode else "20–60 min for real data"
                with st.spinner(f"Running {tool} ({est})…"):
                    ok, out = run_cmd(cmd_run, "eddy")
                if ok:
                    st.success("Done! Eddy-corrected data saved.")
                    corrected = str(eddy_out) + ".nii.gz"
                    if Path(corrected).exists():
                        fig = show_slice(corrected, "Eddy corrected (b=0)", cmap="gray")
                        st.pyplot(fig); plt.close(fig)
                else:
                    st.error(f"Failed:\n```\n{out}\n```")

    with tab_mrt:
        mif_in = pd_ / "dwi_raw.mif"
        if not mif_in.exists():
            st.warning("dwi_raw.mif not found — run mrconvert in Brain Extraction first.")
        cmd_mrt = [
            "dwifslpreproc", str(mif_in), str(pd_ / "dwi_preproc.mif"),
            "-pe_dir", "AP", "-rpe_none",
            "-eddy_options", " --repol", "-force",
        ]
        st.code(fmt_cmd(cmd_mrt), language="bash")
        st.caption("Wraps FSL eddy internally — same algorithm, simpler syntax. Same runtime caveat applies.")

        if st.button("▶ Run MRtrix3 dwifslpreproc", key="run_dwifslpreproc"):
            if not check_tool("dwifslpreproc"):
                st.error("MRtrix3 not found on PATH")
            elif not mif_in.exists():
                st.error("dwi_raw.mif not found — run mrconvert in Brain Extraction first.")
            else:
                with st.spinner("Running dwifslpreproc — 20–60 min on real data…"):
                    ok, out = run_cmd(cmd_mrt, "dwifslpreproc")
                st.success("Done!") if ok else st.error(f"Failed:\n```\n{out}\n```")

    with tab_dipy:
        st.info(
            "**DIPY does not implement eddy current correction.** "
            "Eddy currents require a physics-based distortion model (FSL eddy's approach). "
            "DIPY instead provides **volume-to-volume motion correction** via affine registration — "
            "this corrects head motion between volumes but does NOT remove eddy-current-induced "
            "geometric distortions."
        )
        st.code("""from dipy.align.motion import motion_correction
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table

bvals, bvecs = read_bvals_bvecs('bvals', 'bvecs')
gtab = gradient_table(bvals, bvecs)
img  = nib.load('data.nii.gz')

# Pipeline: align each volume to the mean b=0
corrected_img, reg_affines = motion_correction(
    img, gtab, img.affine,
    pipeline=['center_of_mass', 'translation', 'rigid']
)
nib.save(corrected_img, 'motion_corrected.nii.gz')""", language="python")

        st.markdown("**What this corrects vs FSL eddy:**")
        st.markdown("""
| Artefact | FSL eddy | DIPY motion_correction |
|---|---|---|
| Head motion between volumes | ✓ | ✓ |
| Eddy current distortions | ✓ | ✗ |
| Outlier slice replacement (`--repol`) | ✓ | ✗ |
| Susceptibility distortions (topup) | ✓ (with fieldmap) | ✗ |

**When to use DIPY's approach**: datasets where eddy currents are negligible
(short readout times, low b-values, or when you only need motion correction).
For clinical/research dMRI, prefer FSL eddy.
""")

        if st.button("▶ Run DIPY motion correction", key="run_mc_dipy"):
            try:
                from dipy.align.motion import motion_correction as dipy_mc
                from dipy.io.gradients import read_bvals_bvecs
                from dipy.core.gradients import gradient_table

                bv, bvc = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
                gtab    = gradient_table(bv, bvc)
                img_    = nib.load(str(dd / "data.nii.gz"))

                with st.spinner("Running DIPY motion correction — ~5 min on Stanford HARDI…"):
                    corrected_img, _ = dipy_mc(
                        img_, gtab, img_.affine,
                        pipeline=["center_of_mass", "translation", "rigid"]
                    )
                out_path = pd_ / "motion_corrected_dipy.nii.gz"
                nib.save(corrected_img, str(out_path))
                st.success("Done!")
                fig = show_slice(str(out_path), "DIPY motion corrected (b=0)", cmap="gray")
                st.pyplot(fig); plt.close(fig)
            except ImportError as e:
                st.error(f"Import error: {e}")
            except Exception as e:
                st.error(f"Failed: {e}")

    with st.expander("📖 What eddy correction does"):
        st.markdown("""
        | Problem | Effect on data | Fix |
        |---|---|---|
        | Eddy currents | Geometric distortion per gradient direction | Model + warp correction |
        | Subject motion | Volume misalignment | Rigid registration to prediction |
        | Outlier slices | Signal dropouts | `--repol` replacement |

        **Order matters**: denoise → Gibbs removal → eddy → bias correction.
        **index.txt**: one line per volume, each value = row number in acqparams.txt (here: all `1`).
        **acqparams.txt**: phase-encode direction (AP = `0 1 0`) and readout time (0.05 s).
        """)


def page_csd():
    st.title("Step 5 — CSD / Fibre Orientation Distributions")
    st.markdown("""
    Constrained Spherical Deconvolution (CSD) estimates a Fibre Orientation
    Distribution (FOD) in each voxel — resolving crossing fibres that DTI cannot.
    """)

    dd  = data_dir()
    pd_ = prep_dir()
    csd_dir = ROOT / "data" / "hcp" / st.session_state.get("subject", "100307") / "csd"
    csd_dir.mkdir(parents=True, exist_ok=True)

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate synthetic data from the sidebar first.")
        return

    st.info(
        "**FSL does not implement CSD.** FSL's diffusion model is DTI only. "
        "For FOD-based tractography in an FSL pipeline, run CSD here (MRtrix3 or DIPY) "
        "and pass the result to tckgen in Step 6."
    )

    tab_mrt, tab_dipy = st.tabs(["🟢 MRtrix3 dwi2fod", "🟡 DIPY CSDModel"])

    with tab_mrt:
        mif_in = pd_ / "dwi_preproc.mif"
        if not mif_in.exists():
            mif_in = pd_ / "dwi_raw.mif"
        st.info("MRtrix3 CSD requires the .mif file from Brain Extraction / Eddy Correction steps.")
        st.code("""# Step 1: estimate response function (tissue-specific)
dwi2response dhollander dwi_preproc.mif \\
  wm_response.txt gm_response.txt csf_response.txt

# Step 2: multi-shell multi-tissue CSD
dwi2fod msmt_csd dwi_preproc.mif \\
  wm_response.txt  wm_fod.mif \\
  gm_response.txt  gm_fod.mif \\
  csf_response.txt csf_fod.mif \\
  -mask nodif_brain_mask.nii.gz""", language="bash")
        st.caption("dhollander algorithm automatically selects WM/GM/CSF voxels.")

        if st.button("▶ Run MRtrix3 CSD", key="run_csd_mrt"):
            if not check_tool("dwi2response"):
                st.error("MRtrix3 not found on PATH")
            elif not mif_in.exists():
                st.error("No .mif file found — run mrconvert in Brain Extraction first.")
            else:
                resp_wm  = str(csd_dir / "wm_response.txt")
                resp_gm  = str(csd_dir / "gm_response.txt")
                resp_csf = str(csd_dir / "csf_response.txt")
                cmd_resp = ["dwi2response", "dhollander", str(mif_in),
                            resp_wm, resp_gm, resp_csf, "-force"]
                with st.spinner("Estimating response functions..."):
                    ok, out = run_cmd(cmd_resp, "dwi2response")
                if not ok:
                    st.error(f"dwi2response failed:\n```\n{out}\n```")
                else:
                    mask_path = next((p for p in [
                        pd_ / "bet_brain_mask.nii.gz",
                        dd  / "nodif_brain_mask.nii.gz"] if p.exists()), None)
                    cmd_fod = ["dwi2fod", "msmt_csd", str(mif_in),
                               resp_wm, str(csd_dir / "wm_fod.mif"),
                               resp_gm, str(csd_dir / "gm_fod.mif"),
                               resp_csf, str(csd_dir / "csf_fod.mif"), "-force"]
                    if mask_path:
                        cmd_fod += ["-mask", str(mask_path)]
                    with st.spinner("Running CSD (dwi2fod)..."):
                        ok2, out2 = run_cmd(cmd_fod, "dwi2fod")
                    st.success("FODs computed — saved to csd/") if ok2 else st.error(out2)

    with tab_dipy:
        st.code("""from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel, auto_response_ssst
from dipy.core.gradients import gradient_table

gtab          = gradient_table(bvals, bvecs)
response, ratio = auto_response_ssst(gtab, data, roi_radii=10, fa_thr=0.7)
csd_model     = ConstrainedSphericalDeconvModel(gtab, response)
csd_fit       = csd_model.fit(data)
fodf          = csd_fit.shm_coeff    # spherical harmonic coefficients""", language="python")

        if st.button("▶ Run DIPY CSD", key="run_csd_dipy"):
            try:
                from dipy.reconst.csdeconv import (ConstrainedSphericalDeconvModel,
                                                    auto_response_ssst)
                from dipy.core.gradients import gradient_table
                from dipy.io.gradients import read_bvals_bvecs

                bv, bvc = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
                img_    = nib.load(str(dd / "data.nii.gz"))
                data_   = img_.get_fdata()

                sel, target_b = best_shell_sel(bv, preferred=1000)
                gtab  = gradient_table(bv[sel], bvc[sel])
                data_sel = data_[..., sel]
                st.caption(f"Using b=0 + b={target_b} shell ({sel.sum()} volumes) for single-shell CSD")

                with st.spinner("Estimating WM response function..."):
                    response, ratio = auto_response_ssst(
                        gtab, data_sel, roi_radii=5, fa_thr=0.5)
                st.write(f"Response function ratio: **{ratio:.3f}** (>0.1 = good WM signal)")

                with st.spinner("Fitting CSD model (this takes ~30 s on synthetic data)..."):
                    csd_model = ConstrainedSphericalDeconvModel(gtab, response)
                    csd_fit   = csd_model.fit(data_sel)
                    shm       = csd_fit.shm_coeff.astype(np.float32)

                shm_path = csd_dir / "dipy_fodf_shm.nii.gz"
                nib.save(nib.Nifti1Image(shm, img_.affine), str(shm_path))
                st.success(f"Done! SH coefficients saved ({shm.shape[-1]} coefficients per voxel)")

                # Show max FOD amplitude per voxel as a summary image
                max_fod = np.abs(shm).max(axis=-1)
                max_path = csd_dir / "dipy_max_fod.nii.gz"
                nib.save(nib.Nifti1Image(max_fod, img_.affine), str(max_path))
                fig = show_slice(str(max_path), "Max FOD amplitude (DIPY CSD)", cmap="hot")
                st.pyplot(fig); plt.close(fig)
                st.caption("Bright voxels = high FOD amplitude = high directional coherence.")
            except ImportError as e:
                st.error(f"DIPY import error: {e}")
            except Exception as e:
                st.error(f"CSD failed: {e}")

    with st.expander("📖 CSD vs DTI — when to use each"):
        st.markdown("""
        | | DTI | CSD |
        |---|---|---|
        | Single fibre voxels | ✓ Accurate FA/MD | ✓ |
        | Crossing fibre voxels | ✗ Underestimates FA | ✓ Resolves crossings |
        | Clinical datasets (single-shell) | ✓ | ✓ (SS-CSD) |
        | Multi-shell HCP data | Sub-optimal | ✓ (MSMT-CSD preferred) |

        **Rule**: use DTI for scalar metrics (FA, MD), use CSD for tractography.
        """)


def page_tractography():
    st.title("Step 6 — Tractography")
    st.markdown("""
    Tractography reconstructs white matter pathways by propagating streamlines
    through voxel-wise fibre orientation information. **Probabilistic tractography**
    (iFOD2) is preferred for whole-brain studies — it samples from the FOD uncertainty
    rather than following a single direction.
    """)

    dd      = data_dir()
    pd_     = prep_dir()
    subj    = st.session_state.get("subject", "100307")
    csd_dir = ROOT / "data" / "hcp" / subj / "csd"
    dti_dir = ROOT / "data" / "hcp" / subj / "dti"
    tck_dir = ROOT / "data" / "hcp" / subj / "tractography"
    tck_dir.mkdir(parents=True, exist_ok=True)

    if not (dd / "data.nii.gz").exists():
        st.error("No data found. Generate data from the sidebar first.")
        return

    mask_path = next((p for p in [pd_ / "bet_brain_mask.nii.gz",
                                   dd  / "nodif_brain_mask.nii.gz"] if p.exists()), None)
    if not mask_path:
        st.warning("No brain mask found — run Brain Extraction first.")

    tab_mrt, tab_fsl, tab_dipy = st.tabs(
        ["🟢 MRtrix3 tckgen (iFOD2)", "🔵 FSL probtrackx2", "🟡 DIPY LocalTracking"])

    # ── MRtrix3 ──────────────────────────────────────────────────────────────
    with tab_mrt:
        wm_fod  = csd_dir / "wm_fod.mif"
        tck_out = tck_dir / "whole_brain.tck"
        tdi_out = tck_dir / "tdi.nii.gz"

        if not wm_fod.exists():
            st.warning("wm_fod.mif not found — run **CSD (Step 5)** first to compute FODs.")

        n_sel = st.number_input(
            "Number of streamlines", 1000, 1_000_000, 10_000, 1_000,
            help="10 K for demo (~30 s). 1 M for publication (~5 min).")

        cmd_tck = [
            "tckgen", str(wm_fod), str(tck_out),
            "-algorithm", "iFOD2",
            "-select", str(int(n_sel)),
            "-seed_image", str(mask_path or dd / "nodif_brain_mask.nii.gz"),
            "-mask",        str(mask_path or dd / "nodif_brain_mask.nii.gz"),
            "-force",
        ]
        st.code(fmt_cmd(cmd_tck), language="bash")
        st.caption("iFOD2 samples from the FOD amplitude at each step — naturally avoids noise peaks.")

        if st.button("▶ Run tckgen", key="run_tckgen"):
            if not check_tool("tckgen"):
                st.error("MRtrix3 not found on PATH")
            elif not wm_fod.exists():
                st.error("wm_fod.mif not found — run CSD first.")
            elif not mask_path:
                st.error("Brain mask required — run Brain Extraction first.")
            else:
                with st.spinner(f"Generating {int(n_sel):,} streamlines (iFOD2)…"):
                    ok, out = run_cmd(cmd_tck, "tckgen")
                if ok:
                    st.success(f"Done! {int(n_sel):,} streamlines saved.")
                    cmd_tdi = ["tckmap", str(tck_out), str(tdi_out),
                               "-template", str(mask_path), "-force"]
                    ok2, _ = run_cmd(cmd_tdi, "tckmap")
                    if ok2:
                        fig = show_slice(str(tdi_out), "Track Density Image (TDI)", cmap="hot")
                        st.pyplot(fig); plt.close(fig)
                        st.caption("TDI: voxel intensity = number of streamlines passing through.")
                else:
                    st.error(f"tckgen failed:\n```\n{out}\n```")

        st.divider()
        st.markdown("#### SIFT2 — streamline reweighting")
        sift_weights = tck_dir / "sift2_weights.txt"
        cmd_sift = ["tcksift2", str(tck_out), str(wm_fod), str(sift_weights), "-force"]
        st.code(fmt_cmd(cmd_sift), language="bash")
        st.caption("SIFT2 assigns a weight to each streamline so the tractogram density matches the FOD integrals.")

        if st.button("▶ Run SIFT2", key="run_sift2"):
            if not check_tool("tcksift2"):
                st.error("MRtrix3 not found")
            elif not tck_out.exists():
                st.error("Run tckgen first.")
            elif not wm_fod.exists():
                st.error("wm_fod.mif not found.")
            else:
                with st.spinner("Running SIFT2…"):
                    ok, out = run_cmd(cmd_sift, "tcksift2")
                st.success(f"Done! Weights saved to {short(sift_weights)}") if ok else st.error(out)

    # ── FSL ──────────────────────────────────────────────────────────────────
    with tab_fsl:
        st.error(
            "**FSL probtrackx2 requires bedpostX first** — a Bayesian fibre orientation "
            "estimation that takes **6–24 hours** per subject even on a GPU. "
            "It cannot be run interactively in this demo app."
        )
        st.markdown("#### Reference commands (intended for a cluster):")
        st.code("""# Step 1 — Bayesian fibre orientation estimation (6–24 h on CPU)
bedpostx /path/to/subject/T1w/Diffusion/

# Step 2 — Seed-based probabilistic tractography
probtrackx2 \\
  -s subject.bedpostX/merged \\
  -m nodif_brain_mask.nii.gz \\
  -x seed_mask.nii.gz \\
  --dir=tractography_output \\
  --opd --os2t --forcedir""", language="bash")

        st.markdown("""
| | MRtrix3 tckgen | FSL probtrackx2 |
|---|---|---|
| Input model | CSD FODs | bedpostX distributions |
| Tractography type | Whole-brain | Seed-based (ROI → ROI) |
| Setup time | Minutes (after CSD) | 6–24 h (bedpostX) |
| Best for | Whole-brain tractography, fixel analysis | Specific pathway connectivity |
""")

    # ── DIPY ─────────────────────────────────────────────────────────────────
    with tab_dipy:
        st.code("""from dipy.data import get_sphere
from dipy.direction import peaks_from_model
from dipy.reconst.dti import TensorModel, fractional_anisotropy
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
from dipy.tracking import utils
from dipy.io.stateful_tractogram import Space, StatefulTractogram
from dipy.io.streamline import save_tractogram

# Fit DTI to get fibre directions
sphere  = get_sphere('repulsion724')
tenfit  = TensorModel(gtab).fit(data, mask=brain_mask)
FA      = fractional_anisotropy(tenfit.evals)
peaks   = peaks_from_model(TensorModel(gtab), data, sphere,
                            relative_peak_threshold=0.5,
                            min_separation_angle=25, mask=brain_mask)

# Tractography
stopping    = ThresholdStoppingCriterion(FA, threshold=0.2)
seeds       = utils.seeds_from_mask(brain_mask, affine, density=1)
streamlines = LocalTracking(peaks, stopping, seeds, affine, step_size=0.5)

sft = StatefulTractogram(streamlines, img, Space.RASMM)
save_tractogram(sft, 'tractogram_dipy.trk', bbox_valid_check=False)""", language="python")

        st.caption("Uses DTI peaks — no CSD required. CSD-based tracking is more accurate for crossing fibres.")

        if st.button("▶ Run DIPY LocalTracking", key="run_dipy_tract"):
            try:
                from dipy.data import get_sphere
                from dipy.direction import peaks_from_model
                from dipy.reconst.dti import TensorModel, fractional_anisotropy
                from dipy.tracking.local_tracking import LocalTracking
                from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
                from dipy.tracking import utils as dutils
                from dipy.io.gradients import read_bvals_bvecs
                from dipy.core.gradients import gradient_table
                from dipy.io.stateful_tractogram import Space, StatefulTractogram
                from dipy.io.streamline import save_tractogram

                bv, bvc  = read_bvals_bvecs(str(dd / "bvals"), str(dd / "bvecs"))
                sel, _   = best_shell_sel(bv, preferred=1000)
                gtab     = gradient_table(bv[sel], bvc[sel])
                img_     = nib.load(str(dd / "data.nii.gz"))
                data_    = img_.get_fdata(dtype=np.float32)[..., sel]
                msk      = nib.load(str(mask_path)).get_fdata().astype(bool) if mask_path else None

                sphere = get_sphere("repulsion724")
                with st.spinner("Fitting DTI and computing peaks…"):
                    tenmodel = TensorModel(gtab)
                    tenfit   = tenmodel.fit(data_, mask=msk)
                    FA       = fractional_anisotropy(tenfit.evals).astype(np.float32)
                    peaks    = peaks_from_model(
                        tenmodel, data_, sphere,
                        relative_peak_threshold=0.5,
                        min_separation_angle=25,
                        mask=msk,
                    )

                stopping = ThresholdStoppingCriterion(FA, 0.2)
                seeds    = dutils.seeds_from_mask(
                    msk if msk is not None else np.ones(data_.shape[:3], bool),
                    img_.affine, density=1)

                with st.spinner("Running LocalTracking…"):
                    streamlines = list(LocalTracking(
                        peaks, stopping, seeds, img_.affine, step_size=0.5))

                trk_path = tck_dir / "tractogram_dipy.trk"
                sft = StatefulTractogram(streamlines, img_, Space.RASMM)
                save_tractogram(sft, str(trk_path), bbox_valid_check=False)

                n_sl = len(streamlines)
                st.success(f"Done! {n_sl:,} streamlines saved to {short(trk_path)}")

                # 2-D density map for visualisation
                from dipy.tracking.utils import density_map
                dm   = density_map(streamlines, img_.affine, data_.shape[:3]).astype(np.float32)
                dm_path = tck_dir / "density_dipy.nii.gz"
                nib.save(nib.Nifti1Image(dm, img_.affine), str(dm_path))
                fig = show_slice(str(dm_path), "DIPY streamline density", cmap="hot")
                st.pyplot(fig); plt.close(fig)
                st.caption("Bright voxels = many streamlines passing through.")

            except ImportError as e:
                st.error(f"Import error: {e}")
            except Exception as e:
                st.error(f"Tractography failed: {e}")

    with st.expander("📖 Probabilistic vs deterministic tractography"):
        st.markdown("""
| | Deterministic (DTI peaks) | Probabilistic (iFOD2) |
|---|---|---|
| Direction choice | Single best direction | Samples from FOD distribution |
| Crossing fibres | ✗ Follows dominant fibre only | ✓ Resolves crossings |
| False negatives | Higher (misses connections) | Lower |
| False positives | Lower | Higher — SIFT2 corrects this |
| Speed | Fast | Moderate |
| Recommended for | Quick QC, single-fibre tracts | Publication-quality whole-brain |
""")


# ── Main router ───────────────────────────────────────────────────────────────

def main():
    ensure_demo_data()   # auto-generate synthetic data on cloud / first run
    page = sidebar()

    if page == "🏠 Introduction":
        page_intro()
    elif "Brain Extraction" in page:
        page_brain_extraction()
    elif "Denoising" in page:
        page_denoising()
    elif "Eddy" in page:
        page_eddy()
    elif "DTI" in page:
        page_dti()
    elif "CSD" in page:
        page_csd()
    elif "Tractography" in page:
        page_tractography()
    elif "TBSS" in page:
        page_tbss()
    elif "Concepts" in page:
        page_reference()
    else:
        st.title(page)
        st.info("This step is coming soon. Check the Jupyter notebooks in the meantime.")

if __name__ == "__main__":
    main()
