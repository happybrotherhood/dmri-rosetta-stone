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


def run_cmd(cmd: list[str], label: str) -> tuple[bool, str]:
    """Run a shell command; return (success, output)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    ok     = result.returncode == 0
    out    = result.stdout + ("\n" + result.stderr if not ok else "")
    return ok, out.strip()


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
        st.image("https://raw.githubusercontent.com/happybrotherhood/"
                 "dmri-rosetta-stone/main/assets/logo.png",
                 use_column_width=True) if False else st.title("🧠 dMRI Rosetta Stone")

        st.markdown("**Translating dMRI across FSL, MRtrix3, and DIPY**")
        st.divider()

        # Subject selector — at the top so it's always visible
        st.markdown("### Dataset")
        subj = st.text_input("Subject ID", value="100307")
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
            if st.button("Generate synthetic data"):
                with st.spinner("Generating..."):
                    r = subprocess.run(
                        [sys.executable,
                         str(ROOT / "scripts" / "make_test_data.py"),
                         "--subject", subj,
                         "--outdir", str(ROOT / "data" / "hcp")],
                        capture_output=True, text=True
                    )
                if r.returncode == 0:
                    st.success("Done! Refresh the page.")
                else:
                    st.error(r.stderr)

        st.divider()

        # Tool availability — in expander so navigation is always visible
        with st.expander("🔧 Tool status"):
            fsl_tools = ["bet", "eddy_openmp", "dtifit", "randomise", "topup"]
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
                "8️⃣  Reproducibility QC",
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
                        fig = show_slice(str(mask_path), "FSL BET mask", cmap="hot")
                        st.pyplot(fig)
                        plt.close(fig)
                else:
                    st.error(f"Failed:\n```\n{out}\n```")

        mask_path = pd_ / "bet_brain_mask.nii.gz"
        if mask_path.exists():
            fig = show_slice(str(mask_path), "FSL BET mask (existing)", cmap="hot")
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

        cmd_mrt = ["dwi2mask", "legacy", str(mif_path), str(mrt_mask), "-force"]
        st.code(" ".join(cmd_mrt), language="bash")
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
                    fig = show_slice(str(mrt_mask), "MRtrix3 mask", cmap="hot")
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
                fig = show_slice(str(dipy_mask_path), "DIPY mask", cmap="hot")
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
                    a, b_ = masks[labels[i]], masks[labels[j]]
                    dice  = 2*(a&b_).sum() / (a.sum()+b_.sum()+1e-10)
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

denoised, sigma = mppca(data, patch_radius=2, return_sigma=True)
# sigma is the estimated noise level per voxel
# patch_radius=2 → 5×5×5 patches (same as MRtrix3 default)""", language="python")

        if st.button("▶ Run DIPY mppca", key="run_denoise_dipy"):
            try:
                from dipy.denoise.localpca import mppca
                img  = nib.load(str(dd / "data.nii.gz"))
                data = img.get_fdata()
                with st.spinner("Running mppca (this may take a few minutes)..."):
                    denoised, sigma = mppca(data, patch_radius=2, return_sigma=True)
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
        mif_in = str(pd_ / "dwi_raw.mif") if (pd_ / "dwi_raw.mif").exists() \
                 else str(dd / "data.nii.gz")

        cmd1 = ["dwi2tensor", mif_in, tensor_out,
                "-mask", str(mask_path or dd / "nodif_brain_mask.nii.gz"), "-force"]
        cmd2 = ["tensor2metric", tensor_out,
                "-fa",     str(dti_dir_ / "mrt_FA.nii.gz"),
                "-md",     str(dti_dir_ / "mrt_MD.nii.gz"),
                "-vector", str(dti_dir_ / "mrt_V1.nii.gz"),
                "-mask",   str(mask_path or dd / "nodif_brain_mask.nii.gz"),
                "-force"]

        st.code(" ".join(cmd1), language="bash")
        st.code(" ".join(cmd2), language="bash")
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

# Use only b=1000 for DTI (mono-exponential model breaks at higher b)
sel   = (bvals < 50) | ((bvals > 900) & (bvals < 1100))
gtab  = gradient_table(bvals[sel], bvecs[sel])
model = TensorModel(gtab, fit_method='WLS')
fit   = model.fit(data[..., sel], mask=brain_mask)

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

                sel   = (bv < 50) | ((bv > 900) & (bv < 1100))
                gtab  = gradient_table(bv[sel], bvc[sel])
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
    **Tract-Based Spatial Statistics (TBSS)** is how most DTI group studies are done.
    It compares FA (or MD/RD/AD) across subjects on a **white matter skeleton** —
    a thin 1-voxel-wide representation of tract centres that is robust to small registration errors.

    > **This step requires FSL. MRtrix3 and DIPY do not implement TBSS.**
    > MRtrix3's equivalent is Fixel-Based Analysis (see next step).
    """)

    st.markdown("### The full TBSS pipeline")

    steps = {
        "tbss_1_preproc": {
            "cmd": "cd /path/to/FA_dir && tbss_1_preproc *.nii.gz",
            "what": "Erodes edges of all FA images, creates QC slices",
            "output": "FA/ directory + slicesdir/ for visual QC",
        },
        "tbss_2_reg": {
            "cmd": "tbss_2_reg -t",
            "what": "Registers each FA to FMRIB58_FA standard template (FNIRT)",
            "output": "FA/*_FA_to_target.nii.gz warp fields",
        },
        "tbss_3_postreg": {
            "cmd": "tbss_3_postreg -S",
            "what": "Creates mean FA across all subjects, derives skeleton",
            "output": "mean_FA.nii.gz  +  mean_FA_skeleton.nii.gz",
        },
        "tbss_4_prestats": {
            "cmd": "tbss_4_prestats 0.2",
            "what": "Projects each subject's FA onto the skeleton at threshold 0.2",
            "output": "all_FA_skeletonised.nii.gz  (4D: one volume per subject)",
        },
        "randomise": {
            "cmd": "randomise -i all_FA_skeletonised.nii.gz -o tbss_FA -m mean_FA_skeleton_mask.nii.gz -d design.mat -t design.con -n 5000 --T2",
            "what": "Permutation testing with TFCE — the actual statistics",
            "output": "tbss_FA_tfce_corrp_tstat1.nii.gz  (1-p corrected map)",
        },
    }

    for step, info in steps.items():
        with st.expander(f"**{step}** — {info['what']}", expanded=step=="tbss_1_preproc"):
            st.code(info["cmd"], language="bash")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Output**: {info['output']}")
            with col2:
                if step == "tbss_1_preproc":
                    if st.button("▶ Run (demo)", key="run_tbss1"):
                        if check_tool("tbss_1_preproc"):
                            tbss_dir = ROOT / "data" / "group" / "tbss"
                            if list(tbss_dir.glob("*_FA.nii.gz")):
                                with st.spinner("Running tbss_1_preproc..."):
                                    r = subprocess.run("tbss_1_preproc *.nii.gz",
                                                      shell=True, cwd=str(tbss_dir),
                                                      capture_output=True, text=True)
                                st.success("Done!") if r.returncode == 0 else st.error(r.stderr)
                            else:
                                st.error("No *_FA.nii.gz files found in group/tbss/")
                        else:
                            st.error("FSL not found on PATH")

    st.divider()
    st.markdown("### Design matrix builder")
    st.markdown("Define your group comparison:")

    col1, col2 = st.columns(2)
    with col1:
        n_group1 = st.number_input("Group 1 (e.g. patients)", 1, 100, 10)
        label1   = st.text_input("Group 1 label", "Patients")
    with col2:
        n_group2 = st.number_input("Group 2 (e.g. controls)", 1, 100, 10)
        label2   = st.text_input("Group 2 label", "Controls")

    if st.button("Generate design matrix"):
        import pandas as pd
        design   = np.array([[1,0]]*int(n_group1) + [[0,1]]*int(n_group2))
        contrast = np.array([[1,-1],[-1,1]])
        df       = pd.DataFrame(design, columns=[label1, label2])
        st.dataframe(df)
        st.caption(f"Contrast 1: {label1} > {label2}  |  Contrast 2: {label2} > {label1}")

        mat_str  = f"/NumWaves 2\n/NumPoints {int(n_group1+n_group2)}\n/Matrix\n"
        mat_str += "\n".join(" ".join(map(str, row)) for row in design)
        con_str  = "/NumWaves 2\n/NumContrasts 2\n/Matrix\n1 -1\n-1 1\n"

        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button("Download design.mat", mat_str, "design.mat")
        with col_b:
            st.download_button("Download design.con", con_str, "design.con")

    with st.expander("📖 Common TBSS mistakes"):
        st.markdown("""
        | Mistake | Sign | Fix |
        |---|---|---|
        | Using uncorrected p | Too many significant voxels | Always use `--T2` (TFCE) |
        | Wrong FA threshold | Skeleton too sparse or too dense | Try 0.15–0.25 |
        | Bad registration | Results in CSF / ventricles | Use study-specific template (`-n`) |
        | Mixing bvec conventions | Asymmetric FA maps | Check FSL vs MRtrix3 bvec sign |
        | Not checking QC | Outlier subjects corrupt results | Always inspect slicesdir/ |
        """)


def page_qc():
    st.title("Step 8 — Reproducibility & QC")
    st.markdown("""
    Quality control is not optional — it's the difference between a publishable result
    and a silent failure. This page runs automated QC checks on your pipeline outputs.
    """)

    dd  = data_dir()
    pd_ = prep_dir()
    dti_dir_ = ROOT/"data"/"hcp"/st.session_state.get("subject","100307")/"dti"

    if not (dd/"data.nii.gz").exists():
        st.error("No data found.")
        return

    img   = nib.load(str(dd/"data.nii.gz"))
    data  = img.get_fdata()
    bvals = np.loadtxt(str(dd/"bvals"))
    maskd = nib.load(str(dd/"nodif_brain_mask.nii.gz")).get_fdata().astype(bool)

    st.markdown("### 1. Per-volume SNR")
    snr_per_vol = []
    for v in range(data.shape[3]):
        brain = data[..., v][maskd].mean()
        bg    = data[..., v][~maskd].std() + 1e-10
        snr_per_vol.append(brain / bg)
    snr_arr = np.array(snr_per_vol)
    mean_snr = snr_arr.mean()
    low_snr  = np.where(snr_arr < mean_snr - 2*snr_arr.std())[0]

    fig, ax = plt.subplots(figsize=(10, 3))
    colors = ['red' if i in low_snr else
              ('navy' if bvals[i]<50 else
               ('royalblue' if bvals[i]<1100 else 'tomato'))
              for i in range(len(snr_arr))]
    ax.bar(range(len(snr_arr)), snr_arr, color=colors)
    ax.axhline(mean_snr - 2*snr_arr.std(), color='red', linestyle='--', label='Outlier threshold')
    ax.set_xlabel("Volume"); ax.set_ylabel("SNR"); ax.legend()
    ax.set_title("Per-volume SNR — red bars = outliers | dark=b0 | blue=b1000 | orange=b2000")
    st.pyplot(fig); plt.close(fig)

    col1, col2, col3 = st.columns(3)
    col1.metric("Mean SNR", f"{mean_snr:.1f}")
    col2.metric("Outlier volumes", len(low_snr))
    col3.metric("Total volumes", len(bvals))

    if mean_snr < 10:
        st.error("⚠️  SNR < 10 — very noisy data. Check scanner settings or acquisition parameters.")
    elif mean_snr < 20:
        st.warning("⚠️  SNR < 20 — consider denoising before model fitting.")
    else:
        st.success(f"✓  SNR = {mean_snr:.1f} — acceptable range (>20 is good for dMRI)")

    # DTI metrics distribution
    fa_path = dti_dir_ / "fsl_dti_FA.nii.gz"
    if not fa_path.exists():
        fa_path = dti_dir_ / "dipy_FA.nii.gz"

    if fa_path.exists():
        st.markdown("### 2. FA distribution (sanity check)")
        FA   = nib.load(str(fa_path)).get_fdata()
        wm   = FA[maskd & (FA > 0.2)]

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.hist(wm, bins=40, color='steelblue', edgecolor='none')
        ax.axvline(wm.mean(), color='red', label=f"Mean = {wm.mean():.3f}")
        ax.axvline(0.40, color='orange', linestyle='--', label='Expected min (healthy WM)')
        ax.axvline(0.55, color='green',  linestyle='--', label='Expected max (healthy WM)')
        ax.set_xlabel("FA"); ax.legend(fontsize=8)
        ax.set_title("FA distribution (WM voxels, FA > 0.2)")
        st.pyplot(fig); plt.close(fig)

        fa_ok = 0.35 < wm.mean() < 0.60
        if fa_ok:
            st.success(f"✓  FA mean = {wm.mean():.3f} — within expected range (0.35–0.60 for WM)")
        else:
            st.warning(f"⚠️  FA mean = {wm.mean():.3f} — outside expected range. Check preprocessing.")

    # QC checklist
    st.markdown("### 3. QC checklist")
    checks = {
        "b=0 SNR > 20":           mean_snr > 20,
        "Outlier volumes < 5%":   len(low_snr) < 0.05 * len(bvals),
        "Brain mask exists":      (pd_/"bet_brain_mask.nii.gz").exists() or (dd/"nodif_brain_mask.nii.gz").exists(),
        "Denoised image exists":  (pd_/"dwi_denoised.mif").exists() or (pd_/"dwi_denoised_dipy.nii.gz").exists(),
        "FA map exists":          fa_path.exists(),
    }
    for check, passed in checks.items():
        icon = "✅" if passed else "❌"
        st.markdown(f"{icon} {check}")


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
    elif "DTI" in page:
        page_dti()
    elif "TBSS" in page:
        page_tbss()
    elif "Reproducibility" in page:
        page_qc()
    else:
        st.title(page)
        st.info("This step is coming soon. Check the Jupyter notebooks in the meantime.")

if __name__ == "__main__":
    main()
