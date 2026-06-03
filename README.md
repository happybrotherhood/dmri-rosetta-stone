---
title: dMRI Rosetta Stone
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# dMRI Rosetta Stone

> **Translating diffusion MRI across FSL, MRtrix3, and DIPY — one pipeline step at a time.**

An interactive educational app for learning dMRI analysis. Every step shows the same operation in all three major tools side-by-side, so you understand not just *how* to run a command but *why* it works and *when* to prefer one tool over another.

## Tools included

| Tool | Version | How installed |
|---|---|---|
| FSL | 6.0.7+ | conda (fsl conda channel) |
| MRtrix3 | 3.0.4+ | conda (mrtrix3 channel) |
| DIPY | latest | pip |

## Pipeline covered

1. Brain Extraction (BET / dwi2mask / median_otsu)
2. Denoising — MP-PCA
3. Eddy Current & Motion Correction
4. DTI Fitting (FA, MD, AD, RD)
5. CSD / Fibre Orientation Distributions
6. Tractography (deterministic + probabilistic)
7. TBSS Group Analysis
8. Reproducibility & QC

## Run locally

```bash
git clone https://github.com/happybrotherhood/dmri-rosetta-stone
cd dmri-rosetta-stone
conda create -n dmri python=3.10 -y && conda activate dmri
pip install -r requirements.txt
python scripts/make_test_data.py   # generate synthetic demo data
streamlit run app/app.py
```

Or with Docker:

```bash
docker build -t dmri-rosetta-stone .
docker run -p 8501:8501 dmri-rosetta-stone
# open http://localhost:8501
```

## Data

Uses synthetic phantom data by default (runs without any download).  
For real analysis, download HCP subject 100307:

```bash
python scripts/download_hcp.py --subject 100307 --outdir data/hcp
```

Requires HCP account: https://db.humanconnectome.org/

## Citation

```bibtex
@misc{dmri_rosetta_stone_2025,
  title  = {dMRI Rosetta Stone: A Comparative Tutorial for FSL, MRtrix3, and DIPY},
  author = {Contributors},
  year   = {2025},
  url    = {https://github.com/happybrotherhood/dmri-rosetta-stone}
}
```
