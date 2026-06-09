# dMRI Rosetta Stone — Project Overview

## Why "Rosetta Stone"?

The Rosetta Stone was a 196 BCE decree inscribed in three scripts — Ancient Egyptian hieroglyphs, Demotic, and Ancient Greek — allowing scholars to finally decode a language that had been unreadable for centuries. The key insight was that **the same content was expressed three different ways**, and having all three side by side made translation possible.

This project borrows that metaphor directly. Diffusion MRI has three major software ecosystems — **FSL**, **MRtrix3**, and **DIPY** — each with its own command syntax, terminology, and conventions. A researcher trained in one tool often cannot read or reproduce work done in another, even when the underlying operation is identical. The dMRI Rosetta Stone solves this by showing **the same pipeline step, in all three tools, side by side** — so you can translate your knowledge from one ecosystem to another and understand not just *how* to run a command, but *why* it works.

---

## What Is the Project?

**dMRI Rosetta Stone** is an interactive, browser-based educational app that walks users through the complete diffusion MRI preprocessing and analysis pipeline. At every step, it presents the FSL, MRtrix3, and DIPY implementations in parallel tabs, runs them on real brain data, and displays the outputs for direct visual comparison.

It is aimed at:
- PhD students and researchers new to dMRI who need to learn all three toolkits
- Experienced users who know one tool and want to understand the equivalents in the others
- Educators who want a self-contained, reproducible teaching environment
- Anyone who has ever asked "what is the MRtrix3 equivalent of `dtifit`?"

---

## The Pipeline Covered

The app covers the canonical dMRI preprocessing and analysis workflow in 8 interactive sections:

| Step | FSL | MRtrix3 | DIPY |
|------|-----|---------|------|
| 1. Brain Extraction | `BET` | `dwi2mask` | `median_otsu` |
| 2. Denoising (MP-PCA) | — | `dwidenoise` | `mppca` |
| 3. Eddy & Motion Correction | `eddy_cpu` | `dwifslpreproc` | `motion_correction` |
| 4. DTI Fitting | `dtifit` | `dwi2tensor` / `tensor2metric` | `TensorModel` |
| 5. CSD / Fibre ODFs | — (DTI only) | `dwi2fod (msmt_csd)` | `ConstrainedSphericalDeconvModel` |
| 6. Tractography | `probtrackx2` | `tckgen iFOD2` + `tcksift2` | `LocalTracking` |
| 7. TBSS Group Analysis | `tbss_1–4` + `randomise` | — | — |
| 8. Concepts & Reference | DTI metrics, glossary, command cheat sheet, tool comparison |

Each step includes:
- Side-by-side tabbed command display with the exact shell command executed
- A **Run** button that executes the command on real data and shows the output
- Visual result display (NIfTI slice viewer, metric maps, tract density images)
- A **Why?** explanation of what the step does biologically and mathematically

---

## The Data

The app ships with the **Stanford HARDI dataset** — a real, open-access human brain scan provided by the DIPY project, requiring no credentials or registration. It is automatically downloaded and cached on first use via DIPY's `get_fnames("stanford_hardi")`.

- Dimensions: 81 × 106 × 76 × 160 volumes
- Acquisition: single-shell, b = 2000 s/mm², 10 b0 + 150 DWI directions
- Brain mask: generated with `median_otsu` at download time
- Stored at: `data/hcp/stanford/T1w/Diffusion/`

The subject ID field in the sidebar supports switching between datasets. The app also has infrastructure to load HCP subjects (via `scripts/download_hcp.py`) when AWS credentials are available.

---

## Technology Stack

### Streamlit
Streamlit is a Python framework for building data applications with pure Python — no HTML, CSS, or JavaScript needed. It converts Python scripts into interactive web apps by treating function calls like `st.button()`, `st.tabs()`, and `st.pyplot()` as UI components.

In this project, Streamlit provides:
- The sidebar navigation between pipeline steps
- Tabbed layouts for FSL / MRtrix3 / DIPY side-by-side views
- Run buttons that trigger subprocess calls to the actual tools
- Matplotlib figure display for NIfTI slice visualisation
- Session state management (e.g. remembering which subject is loaded)

The app is configured via `.streamlit/config.toml` — notably with `magicEnabled = false` (prevents bare Python expressions from accidentally being rendered as UI elements) and `headless = true` (required for running inside Docker without a display).

### Docker
Docker packages the entire application — operating system, FSL, MRtrix3, Python, DIPY, and the app code — into a single portable container image. This solves the notoriously painful installation problem that dMRI software presents: FSL alone requires a multi-gigabyte installer that only runs on Linux; MRtrix3 has its own build dependencies; DIPY depends on specific NumPy versions.

The Dockerfile uses a **multi-stage build**:
1. **Stage 1** pulls MRtrix3 binaries from the official `mrtrix3/mrtrix3:latest` image
2. **Stage 2** starts from `ubuntu:22.04`, installs FSL via its official `fslinstaller.py` script, copies MRtrix3 from Stage 1, then installs the Python stack via `pip`

Key environment variables set in the image:
- `FSLDIR`, `FSLOUTPUTTYPE`, `PATH` — FSL configuration
- `PATH` extended with `/opt/mrtrix3/bin` — MRtrix3 availability
- `STREAMLIT_SERVER_HEADLESS=true`, `STREAMLIT_SERVER_ADDRESS=0.0.0.0` — headless server mode

The container exposes port **7860** (mapped to **8501** on the host) and serves the Streamlit app at `http://localhost:8501`.

### FSL (FMRIB Software Library)
Open-source neuroimaging toolkit from the University of Oxford. Used in this project for brain extraction (`bet`), eddy current and motion correction (`eddy_cpu`), DTI fitting (`dtifit`), and voxelwise group analysis (`tbss_*`, `randomise`).

### MRtrix3
Open-source toolkit specialising in white matter tractography and fibre orientation modelling. Used for brain masking (`dwi2mask`), denoising (`dwidenoise`), Gibbs ringing removal (`mrdegibbs`), DTI fitting (`dwi2tensor`, `tensor2metric`), constrained spherical deconvolution (`dwi2fod`), probabilistic tractography (`tckgen iFOD2`), and streamline filtering (`tcksift2`).

### DIPY (Diffusion Imaging in Python)
Python library for diffusion MRI analysis. Used for brain masking (`median_otsu`), MP-PCA denoising (`mppca`), motion correction, DTI fitting (`TensorModel`), CSD (`ConstrainedSphericalDeconvModel`), deterministic tractography (`LocalTracking`), and as the source of the open-access Stanford HARDI sample dataset.

### Supporting Python Libraries
- **nibabel** — reading and writing NIfTI and other neuroimaging file formats
- **numpy** — array operations on imaging data
- **scipy** — signal processing and statistical functions
- **matplotlib** — slice visualisation and metric map rendering
- **pandas** — tabular comparison tables in the reference section
- **scikit-image** — image processing utilities

---

## Project Structure

```
dmri-rosetta-stone/
├── app/
│   └── app.py                  # All Streamlit pages (~1900 lines)
├── scripts/
│   ├── utils.py                # Tool availability checks
│   ├── make_test_data.py       # Synthetic phantom generator (for CI)
│   ├── fetch_sample_data.py    # Stanford HARDI downloader
│   └── download_hcp.py        # HCP S3 downloader (requires credentials)
├── data/
│   └── hcp/
│       └── stanford/
│           └── T1w/Diffusion/  # data.nii.gz, bvals, bvecs, mask
├── .streamlit/
│   └── config.toml             # Theme and server settings
├── Dockerfile
└── PROJECT_OVERVIEW.md
```

---

## How to Build and Run

**Build the Docker image** (first time, ~10–15 min due to FSL download):
```bash
docker build --platform linux/amd64 -t dmri-rosetta .
```

**Run the container:**
```bash
docker run --rm --platform linux/amd64 -p 8501:7860 dmri-rosetta
```

**Open the app:**
```
http://localhost:8501
```

**Run locally** (requires FSL, MRtrix3, and Python dependencies installed):
```bash
pip install streamlit nibabel numpy scipy matplotlib pandas dipy scikit-image
streamlit run app/app.py
```

---

## Design Decisions

**Why show all three tools at every step rather than picking the "best" one?**
Because "best" depends on your data, your question, and your existing pipeline. A researcher who already uses FSL for everything should not need to relearn from scratch just to run a CSD model. Showing all three makes the translation explicit.

**Why real brain data instead of a synthetic phantom?**
Synthetic phantoms produce unrealistically clean outputs that do not prepare users for what real data looks like — the noise, artefacts, and masking errors that motivate each preprocessing step. The Stanford HARDI dataset is freely available, well-characterised, and small enough to run in a reasonable time.

**Why Docker?**
Installing FSL, MRtrix3, and DIPY together on a local machine is a weekend-long exercise that regularly fails due to conflicting dependencies or OS incompatibilities. Docker removes this barrier entirely: the user runs two commands and has a working environment.

**Why Streamlit and not a Jupyter notebook?**
Jupyter notebooks require the user to execute cells in order, understand Python, and manage kernel state. Streamlit gives a point-and-click interface that any researcher can use regardless of programming background — while the underlying code is still fully visible and auditable.
