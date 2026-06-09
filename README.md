# 🧠 dMRI Rosetta Stone

> **Translating diffusion MRI across FSL, MRtrix3, and DIPY — one pipeline step at a time.**

An interactive, browser-based educational app for diffusion MRI analysis. Every pipeline step shows the **same operation in all three major tools side by side** — so you learn not just *how* to run a command, but *why* it works and *when* to prefer one tool over another.

---

## Why "Rosetta Stone"?

The original Rosetta Stone (196 BCE) carried the same royal decree in three scripts, allowing scholars to decode Ancient Egyptian for the first time. This project applies the same idea to dMRI: **FSL**, **MRtrix3**, and **DIPY** are three different "languages" for the same underlying science. Seeing all three side by side makes translation possible.

---

## Pipeline Covered

| Step | FSL | MRtrix3 | DIPY |
|------|-----|---------|------|
| 1. Brain Extraction | `bet` | `dwi2mask` | `median_otsu` |
| 2. Denoising (MP-PCA) | — | `dwidenoise` | `mppca` |
| 3. Eddy & Motion Correction | `eddy_cpu` | `dwifslpreproc` | `motion_correction` |
| 4. DTI Fitting | `dtifit` | `dwi2tensor` + `tensor2metric` | `TensorModel` |
| 5. CSD / Fibre ODFs | — (DTI only) | `dwi2fod msmt_csd` | `ConstrainedSphericalDeconvModel` |
| 6. Tractography | `probtrackx2` | `tckgen iFOD2` + `tcksift2` | `LocalTracking` |
| 7. TBSS Group Analysis | `tbss_1–4` + `randomise` | — | — |
| 8. Concepts & Reference | DTI metrics glossary, command cheat sheet, tool comparison guide | | |

---

## Quick Start

### Option A — Docker (recommended, no installation required)

```bash
git clone https://github.com/YOUR_USERNAME/dmri-rosetta-stone.git
cd dmri-rosetta-stone

# Build — first time takes ~15 min (downloads FSL + MRtrix3)
docker build --platform linux/amd64 -t dmri-rosetta .

# Run
docker run --rm --platform linux/amd64 -p 8501:7860 dmri-rosetta
```

Open **http://localhost:8501** in your browser.

> The container bundles FSL 6.0.7, MRtrix3 3.0.4, and DIPY. No separate installation needed.

### Option B — Local (requires FSL + MRtrix3 already installed)

```bash
git clone https://github.com/YOUR_USERNAME/dmri-rosetta-stone.git
cd dmri-rosetta-stone

pip install -r requirements.txt

# Download sample data (Stanford HARDI, ~50 MB, free — no credentials needed)
python scripts/fetch_sample_data.py --subject stanford --outdir data/hcp

streamlit run app/app.py
```

---

## Sample Data

The app uses the **Stanford HARDI dataset** — a real, open-access human brain scan provided by the DIPY project. No account or credentials required.

```bash
python scripts/fetch_sample_data.py --subject stanford --outdir data/hcp
```

For real HCP data (requires an HCP account and AWS credentials):

```bash
python scripts/download_hcp.py --subject 100307 --outdir data/hcp
```

HCP account: https://db.humanconnectome.org/

---

## Project Structure

```
dmri-rosetta-stone/
├── app/
│   └── app.py                   # All Streamlit pages (~1900 lines)
├── scripts/
│   ├── utils.py                 # Tool availability checks
│   ├── make_test_data.py        # Synthetic phantom generator (used in Docker build)
│   ├── fetch_sample_data.py     # Stanford HARDI downloader
│   └── download_hcp.py         # HCP S3 downloader (requires credentials)
├── data/
│   └── hcp/
│       └── stanford/
│           └── T1w/Diffusion/   # bvals + bvecs committed; NIfTI excluded (too large)
├── notebooks/                   # Companion Jupyter notebooks
├── .streamlit/
│   └── config.toml              # Theme + server settings
├── Dockerfile
├── requirements.txt
├── environment.yml
└── PROJECT_OVERVIEW.md          # Full project description and design rationale
```

---

## Requirements

### Python packages
```
streamlit>=1.40
nibabel>=5.0
numpy>=1.24,<2.0
scipy>=1.10
matplotlib>=3.7
pandas>=2.0
networkx>=3.0
dipy>=1.7
scikit-image>=0.20
```

Install with: `pip install -r requirements.txt`

### Neuroimaging tools (only needed for local Option B — not required with Docker)
- **FSL** ≥ 6.0 — https://fsl.fmrib.ox.ac.uk/fsl/docs/#/install/index
- **MRtrix3** ≥ 3.0.4 — https://www.mrtrix.org/download/

---

## How the App Works

1. Select a **pipeline step** from the sidebar
2. Each step shows the command for all three tools in **tabbed panels**
3. Click **Run** to execute the command on real brain data
4. Compare the outputs visually — NIfTI slices, FA/MD maps, tractograms
5. Read the **Why?** section for the biological and mathematical rationale

---

## Documentation

See [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) for a detailed description of:
- The Rosetta Stone metaphor explained in full
- Why each technology was chosen (Streamlit, Docker, FSL, MRtrix3, DIPY)
- Design decisions — real data vs phantom, Docker vs local, Streamlit vs Jupyter notebook

---

## Citation

If you use this tool in teaching or research, please cite:

```bibtex
@misc{dmri_rosetta_stone_2026,
  title  = {dMRI Rosetta Stone: A Comparative Tutorial for FSL, MRtrix3, and DIPY},
  author = {Mutlu, Busra},
  year   = {2026},
  url    = {https://github.com/YOUR_USERNAME/dmri-rosetta-stone}
}
```

---

## License

MIT — see [LICENSE](LICENSE)
