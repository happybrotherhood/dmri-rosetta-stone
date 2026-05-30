# dMRI Rosetta Stone

> **Translating diffusion MRI across FSL, MRtrix3, and DIPY — one pipeline at a time.**

---

## What Is This Book?

Diffusion MRI (dMRI) is a powerful technique for mapping white matter pathways in the living human brain. But starting out is hard: the field has three major toolboxes — **FSL**, **MRtrix3**, and **DIPY** — each with its own conventions, terminology, and strengths.

This book is your decoder ring. Like the Rosetta Stone that unlocked three scripts at once, this tutorial walks you through the **same pipeline steps** in all three tools side-by-side, so you understand not just *how* to run a command but *why* it works and *when* to prefer one tool over another.

---

## Who Is This For?

- **Graduate students** starting their first dMRI project
- **Clinicians** who want to understand what their neuroimaging collaborators are doing
- **Researchers from other modalities** (fMRI, EEG) transitioning to diffusion
- **Anyone** who has run a pipeline script without really understanding the steps

No previous dMRI experience is required, but basic familiarity with Python and neuroimaging concepts (MRI scanners, NIfTI files) is helpful.

---

## What You Will Learn

By the end of this book you will be able to:

1. **Explain** the physical basis of diffusion MRI and why it is sensitive to white matter structure
2. **Preprocess** raw dMRI data: denoising, Gibbs removal, eddy current correction, bias field correction
3. **Fit local models**: Diffusion Tensor Imaging (DTI) and Constrained Spherical Deconvolution (CSD)
4. **Generate tractograms** using deterministic and probabilistic algorithms
5. **Build connectivity matrices** for structural connectomics
6. **Critically evaluate** your results and understand common pitfalls

---

## The Three Tools

| Feature | FSL | MRtrix3 | DIPY |
|---|---|---|---|
| **Language** | C++/Python wrappers | C++/Python wrappers | Pure Python |
| **License** | Free for non-commercial | Open source (MPL) | Open source (BSD) |
| **Strength** | Eddy correction, bedpostX | Tractography, CSD, SIFT | Flexibility, transparency |
| **Best for** | Clinical pipelines, eddy | Research, whole-brain tractography | Custom algorithms, learning |
| **GUI** | FSLeyes | MRView | None (use matplotlib) |

---

## Data

This book uses data from the **Human Connectome Project (HCP)**, specifically subject `100307` from the minimally preprocessed dataset. See [Module 0 — Data Setup](notebooks/00_introduction/02_data_setup) for download instructions.

---

## How to Use This Book

- Each chapter has **concept** cells (explaining the theory) and **code** cells (running the analysis)
- Tool-specific sections are marked with badges: `[FSL]` `[MRtrix3]` `[DIPY]`
- Side-by-side comparisons highlight equivalent commands and their outputs
- The **Reproducibility module** (Module 5) teaches you to question every result

---

## Citation

If you use this material, please cite:

```bibtex
@misc{dmri_rosetta_stone_2025,
  title  = {dMRI Rosetta Stone: A Comparative Tutorial for FSL, MRtrix3, and DIPY},
  author = {Contributors},
  year   = {2025},
  url    = {https://github.com/happybrotherhood/dmri-rosetta-stone}
}
```

---

*Let's decode the white matter together.*
