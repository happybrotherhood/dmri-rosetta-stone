ARTICLE TYPE: Technology and Code
JOURNAL: Frontiers in Neuroinformatics
SPECIALTY SECTION: Methods in Neuroimaging

---

# dMRI Rosetta Stone: An Open-Source Interactive Platform for Cross-Tool Diffusion MRI Education and Reproducibility

**Busra Mutlu**¹\*

¹ Department of Neuroimaging, King's College London, London, United Kingdom

\* **Correspondence:** Busra Mutlu, [email address], Department of Neuroimaging, King's College London, De Crespigny Park, London SE5 8AF, United Kingdom

**Running title:** dMRI Rosetta Stone: Cross-Tool dMRI Education Platform

---

## Abstract

Diffusion magnetic resonance imaging (dMRI) is the principal non-invasive technique for characterising white matter microstructure in the living human brain, and its analysis ecosystem is dominated by three major software packages: FSL, MRtrix3, and DIPY. Despite their complementary strengths, these toolkits employ divergent command-line interfaces, terminology conventions, and algorithmic implementations that create a substantial barrier for students and early-career researchers seeking to learn, reproduce, or cross-validate dMRI analyses. No existing resource enables concurrent, executable, side-by-side comparison of all three toolkits on the same real human brain dataset within a single browser-based interface. Here we present dMRI Rosetta Stone, an open-source interactive platform built with Streamlit and containerised with Docker, which guides users through seven canonical dMRI pipeline stages: brain extraction, Marchenko-Pastur PCA denoising, eddy current and motion correction, diffusion tensor imaging (DTI) fitting, constrained spherical deconvolution (CSD), probabilistic and deterministic tractography, and voxelwise group analysis (TBSS). For each stage, the platform simultaneously displays the exact executable command for all three toolkits, runs it on the openly available Stanford HARDI dataset, and renders the outputs for direct visual comparison. Alongside the platform we report a reproducible benchmark of inter-tool agreement on two independent open datasets — Stanford HARDI and Sherbrooke 3-shell — with identical input volumes, gradient tables, and a single shared brain mask, so that the comparison isolates the tensor-fitting stage. Brain masks from the three toolkits overlapped at Dice coefficients of 0.90–0.97 despite a spread of up to 21% in mask volume. DTI scalar agreement was strongly asymmetric and the asymmetry replicated across both acquisitions: MRtrix3 and DIPY were near-identical in white matter (FA r = 0.9990 and 0.9966; MD r = 0.9965 and 0.9991), whereas FSL diverged from both (FA r = 0.890–0.965). Critically, the FSL discrepancy was not a fixed bias — mean diffusivity was consistently lower but by 5% on one dataset and 19% on the other, and the fractional anisotropy offset reversed sign between acquisitions — so it cannot be corrected by a single scaling factor. We further show that non-physical tensor fits (FA > 1 or MD ≤ 0, arising from unconstrained least squares) occurred in 0.4–4.0% of white matter voxels in FSL and 0.3–2.0% in MRtrix3 but never in DIPY, and that ignoring them is sufficient to depress an apparent MD correlation from 0.997 to 0.118 — a methodological trap for anyone computing agreement statistics on raw diffusion maps. Key implementation asymmetries — the absence of dedicated denoising and CSD in FSL, the conceptually distinct tractography models across toolkits — are made immediately visible and discussable. A built-in Concepts and Reference module provides a 16-term glossary, DTI metric guide, command cheat sheet, and a decision framework for tool selection. The containerised deployment requires no local installation of neuroimaging software and runs on Linux, macOS, and Windows. dMRI Rosetta Stone is freely available at https://github.com/happybrotherhood/dmri-rosetta-stone under an MIT licence.

**Keywords:** diffusion MRI; FSL; MRtrix3; DIPY; educational software; neuroinformatics; reproducibility; open science

---

## Introduction

Diffusion magnetic resonance imaging (dMRI) is the principal non-invasive technique for probing white matter microstructure and structural connectivity in the living human brain (Basser et al., 1994; Jones, 2010). By encoding the directional displacement of water molecules, dMRI provides access to biophysical indices — including fibre orientation, axon density, and myelin integrity — that are invisible to conventional anatomical MRI (Beaulieu, 2002). Applications span fundamental neuroscientific questions about brain organisation and inter-individual variability, as well as clinical contexts including the characterisation of white matter alterations in neurodegenerative diseases, psychiatric conditions, and neurodevelopmental disorders (Catani and Thiebaut de Schotten, 2008; Jones, 2010).

The dMRI analysis ecosystem is dominated by three major software packages. FSL (FMRIB Software Library), developed at the University of Oxford, provides robust preprocessing, DTI fitting, and voxelwise group analysis via the Tract-Based Spatial Statistics (TBSS) pipeline (Smith et al., 2004; Jenkinson et al., 2012). MRtrix3, developed at The Florey Institute of Neuroscience and Mental Health, specialises in constrained spherical deconvolution (CSD) and high-fidelity fibre orientation modelling (Tournier et al., 2019). DIPY (Diffusion Imaging in Python) offers a flexible, Python-native implementation of the full dMRI pipeline and is widely used when algorithmic transparency or custom extensions are required (Garyfallidis et al., 2014).

Despite their complementary strengths, these toolkits present a significant practical barrier. Each employs distinct command-line syntax, file format conventions, and — in several cases — different terminology for the same operation. For example, brain extraction is called `bet` in FSL, `dwi2mask` in MRtrix3, and `median_otsu` in DIPY. Mean diffusivity is reported as `MD` in FSL, `ADC` in MRtrix3, and `md` in DIPY. These surface-level differences cause genuine confusion for researchers trained in one ecosystem who attempt to read, reproduce, or extend work conducted in another.

A more substantive concern is methodological reproducibility. Published dMRI studies rarely justify their choice of software, and it is not always clear whether reported group differences in white matter metrics reflect genuine biological effects or implementation-level differences between tools (Bhagwat et al., 2021; Richie-Halford et al., 2022). Software-specific choices — brain masking algorithm, denoising method, tensor fitting algorithm — can introduce non-trivial variability in derived metrics such as fractional anisotropy (FA) and mean diffusivity (MD).

Existing educational resources address individual toolkits in depth. FSL is covered through the annual FSL Course and its wiki; MRtrix3 provides extensive documentation at docs.mrtrix.org; DIPY provides executable Jupyter notebook tutorials at dipy.org; Andy's Brain Book (Jahn, 2020) covers FSL comprehensively and touches on MRtrix3. However, no existing resource places all three toolkits side by side on the same data, in the same interface, with executable commands and live visual outputs. The specific combination of cross-tool coverage, real human brain data, browser-based executability, and zero neuroimaging software installation has not been offered by any prior platform (Table 2). This is the gap that dMRI Rosetta Stone addresses.

The name is drawn from the original Rosetta Stone (196 BCE), a priestly decree inscribed in three scripts — Ancient Egyptian hieroglyphs, Demotic, and Ancient Greek — whose parallel presentation enabled decipherment of a language unreadable for over a millennium. Here, FSL, MRtrix3, and DIPY are three parallel "languages" for dMRI analysis, and juxtaposing them enables translation between ecosystems.

---

## Design Principles

Four principles guided development. First, **parallel transparency**: every pipeline stage must show the complete, executable command in all three toolkits simultaneously, without requiring the user to navigate between separate documents or websites. Second, **real human data**: the platform must operate on real brain acquisitions, not synthetic phantoms, because the noise, artefacts, and masking ambiguities that motivate each preprocessing step are only apparent on real data. Third, **zero installation barrier**: a researcher with no prior Linux or FSL experience should be able to run the full pipeline within minutes; this mandates containerisation of FSL, MRtrix3, and DIPY into a single portable image. Fourth, **conceptual scaffolding**: every stage must include a biological and mathematical explanation of what the operation does, why it is necessary, and when one toolkit should be preferred over another.

---

## Materials and Methods

### Software Architecture

dMRI Rosetta Stone is implemented as a Streamlit web application (version ≥ 1.40; Streamlit Inc., 2019) and containerised with Docker (Merkel, 2014). Streamlit converts Python scripts into interactive browser-based interfaces without requiring HTML, CSS, or JavaScript, making the codebase accessible to any researcher with Python familiarity.

The Dockerfile uses a two-stage build (Figure 1). Stage 1 copies MRtrix3 3.0.4 binaries from the official `mrtrix3/mrtrix3:latest` image. Stage 2 starts from `ubuntu:22.04`, installs FSL 6.0.7 via the official `fslinstaller.py` script, copies MRtrix3 from Stage 1, and installs the Python stack — Streamlit, DIPY ≥ 1.7, nibabel, numpy, scipy, matplotlib, pandas, scikit-image — via pip. This multi-stage approach avoids dependency conflicts between FSL and MRtrix3 that arise from single-stage installation. The container serves the Streamlit interface at `http://localhost:8501` via two commands:

```bash
docker build --platform linux/amd64 -t dmri-rosetta .
docker run --rm --platform linux/amd64 -p 8501:7860 dmri-rosetta
```

The first command builds the image (approximately 15 minutes, dominated by the FSL download); the second launches the container. No neuroimaging software is required on the host machine.

### Data

All demonstrations use the Stanford HARDI dataset distributed by the DIPY project under an open-access licence (Rokem et al., 2015). The dataset comprises 160 volumes (10 b = 0, 150 DWI at b = 2000 s/mm²) with voxel size 2 × 2 × 2 mm and matrix 81 × 106 × 76. It is downloaded automatically on first launch via DIPY's `get_fnames("stanford_hardi")` utility without credentials. A brain mask is generated at download time using `median_otsu` and stored alongside the raw NIfTI data.

The quantitative benchmark reported below additionally uses the Sherbrooke 3-shell dataset, also distributed openly by DIPY via `get_fnames("sherbrooke_3shell")`. It comprises 193 volumes (1 b = 0; 64 directions at each of b = 1000, 2000, and 3500 s/mm²) with voxel size 2 × 2 × 2 mm and matrix 128 × 128 × 60. Because it originates from a different site and protocol than the Stanford data, analysing both provides an independent replication of the inter-tool comparison rather than a second look at one acquisition.

The application also supports Human Connectome Project (HCP; Van Essen et al., 2013) multi-shell data (b = 1000/2000/3000 s/mm², 90 directions per shell) for users with HCP data access credentials, enabling demonstration of multi-tissue CSD which requires multiple non-zero b-value shells.

### Pipeline Coverage

The application covers seven pipeline stages, each as a dedicated page in the sidebar navigation (Table 1).

**Brain Extraction.** FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu` are demonstrated on the same b = 0 volume. Outputs are displayed as a red-tinted mask overlay on the b = 0 image (Figure 4).

**Denoising (MP-PCA).** Marchenko-Pastur PCA exploits diffusion signal redundancy to separate signal from thermal noise using random matrix theory (Veraart et al., 2016). MRtrix3 `dwidenoise` and DIPY `mppca` are demonstrated. FSL lacks a dedicated denoising tool; this asymmetry is made explicit with an explanation of when denoising is most beneficial.

**Eddy Current and Motion Correction.** FSL `eddy_cpu` (Andersson and Sotiropoulos, 2016), MRtrix3 `dwifslpreproc` (which wraps FSL eddy internally and prepends Gibbs-ringing removal via `mrdegibbs`), and DIPY `motion_correction` (rigid-body registration only, no eddy correction) are demonstrated. A demo subsample mode (5 b = 0 + 15 DWI volumes) reduces runtime from approximately 40 minutes to approximately 3 minutes for interactive use.

**DTI Fitting.** FSL `dtifit`, MRtrix3 `dwi2tensor` + `tensor2metric`, and DIPY `TensorModel.fit()` are applied to the same input data; FA, MD, AD, and RD maps are rendered for each toolkit (Figure 3).

**Constrained Spherical Deconvolution.** MRtrix3 `dwi2fod` (multi-shell multi-tissue CSD; Tournier et al., 2007) and DIPY `ConstrainedSphericalDeconvModel` are demonstrated. FSL does not include CSD; its omission is discussed together with acquisition requirements for CSD (≥ 30 directions, high b-value).

**Tractography.** MRtrix3 `tckgen` with the iFOD2 probabilistic algorithm (Tournier et al., 2010) and streamline filtering via `tcksift2` (Smith et al., 2015), FSL `probtrackx2` (command display and conceptual overview), and DIPY `LocalTracking` (deterministic, DTI peaks) are demonstrated. Track density images (TDI) generated with `tckmap` provide voxelwise streamline density maps.

**TBSS Voxelwise Group Analysis.** The full TBSS pipeline (Smith et al., 2006) — `tbss_1_preproc`, `tbss_2_reg`, `tbss_3_postreg`, `tbss_4_prestats`, and `randomise` — is demonstrated. Because the platform operates on a single subject, a synthetic group is constructed by adding Gaussian noise realisations (σ = 0.03 FA units) to the real FA map. The absence of equivalent voxelwise pipelines in MRtrix3 and DIPY (fixel-based analysis in MRtrix3 is noted as the conceptual analogue) is made explicit.

### Concepts and Reference Module

A dedicated Reference section provides: (1) a DTI metrics guide with the biological interpretation of FA, MD, AD, and RD and live map display; (2) a 16-term dMRI glossary; (3) a command cheat sheet covering all seven stages across all three toolkits; and (4) a decision framework for selecting the appropriate toolkit based on acquisition type, research question, and available compute resources.

### Quantitative Inter-Tool Agreement Analysis

Beyond the interactive pipeline, we conducted a systematic quantitative comparison of DTI scalar metrics and brain masks across all three toolkits on the Stanford HARDI dataset. This analysis serves two purposes: it validates that the platform produces outputs consistent with established diffusion MRI principles, and it constitutes a reproducible, openly available benchmark of inter-tool agreement under controlled conditions — identical data, identical preprocessing, identical brain mask.

**Brain mask agreement** was assessed using the Dice similarity coefficient (DSC) between each pair of binary masks produced by FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu`. DSC values are reported in Table 3. A white matter reference mask, defined as voxels where all three tools jointly yielded FA > 0.2, was used for all subsequent metric comparisons.

**DTI metric agreement** was assessed for FA and MD on both datasets. To isolate tensor-fitting differences from every other source of variability, all three tools were applied to the *identical* input: the same unprocessed volumes, the same bvals and bvecs, and one shared brain mask generated by `median_otsu`. No denoising or eddy-current correction was applied before fitting.

For the multi-shell Sherbrooke data this required an explicit step. The single-tensor model assumes monoexponential signal decay, which does not hold across shells; FSL `dtifit` and MRtrix3 `dwi2tensor` silently fit every volume they are given, whereas DIPY requires the shell to be selected by the user. Left unaddressed, the three toolkits would have fitted different data and any difference between them would confound tensor fitting with shell selection. We therefore extracted the b = 0 and b = 1000 s/mm² volumes (65 of 193) once, and passed that identical subset to all three toolkits. The Stanford data is single-shell, so all 160 volumes were used. This is deliberate: any preprocessing step would itself be a toolkit-specific choice, and applying one tool's preprocessing to all three would confound the comparison it is meant to measure. The consequence is that the reported agreement characterises the tensor-fitting stage alone, not a complete analysis pipeline.

Voxelwise Pearson correlation coefficients (r), Spearman rank correlations (ρ), and mean absolute error (MAE) were computed over white matter voxels, and Bland–Altman analysis was performed for each cross-tool pair to characterise the distribution of voxelwise differences and identify any systematic bias.

Statistics were restricted to voxels whose values are physically admissible in both tools of a given pair: FA within [0, 1], and MD positive and no greater than the diffusivity of free water at body temperature (3.0 × 10⁻³ mm²/s). This restriction is necessary rather than cosmetic. Unconstrained linear tensor fitting can return negative eigenvalues, which drive FA above unity and MD below zero; because Pearson correlation is dominated by extreme values, a few hundred such voxels are sufficient to depress the apparent MD agreement from r = 0.997 to r = 0.118 while changing the mean absolute error by less than 2%. The per-tool counts of these non-physical voxels are reported in the Results as a substantive inter-tool difference in their own right.

Results are reported in Table 3 and Figures 3 and 4. All analyses were performed using the companion script `scripts/compute_fa_comparison.py` distributed with the repository; all values reported here are fully reproducible from the openly available Stanford HARDI dataset with no credentials required.

---

## Results

### Brain Mask Agreement

Brain masks generated by FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu` on the same b = 0 mean volume showed high pairwise overlap, with Dice similarity coefficients of:

- FSL vs. DIPY: DSC = 0.9277
- FSL vs. MRtrix3: DSC = 0.9024
- MRtrix3 vs. DIPY: DSC = 0.9009

The three algorithms nonetheless differ substantially in how much tissue they retain: FSL `bet` produced the most inclusive mask (203,984 voxels), MRtrix3 `dwi2mask` the most conservative (167,950 voxels), and DIPY `median_otsu` an intermediate one (187,948 voxels) — a spread of 21% between the largest and smallest mask despite pairwise Dice values above 0.90. This illustrates a general property of the Dice coefficient that is worth making explicit to learners: for a large, compact object such as the brain, DSC remains high even when boundary decisions differ appreciably.

Disagreements were concentrated at the cortical boundary and, distinctively, at the lateral ventricles (Figure 4). DIPY `median_otsu` excluded ventricular CSF, whereas FSL `bet` and MRtrix3 `dwi2mask` retained it. This reflects the different tissue models each algorithm employs — Otsu intensity thresholding after median filtering in DIPY, a deformable surface model in FSL `bet`, and full-DWI-signal averaging in MRtrix3 `dwi2mask`. The consequence is practical rather than cosmetic: a mask that includes ventricles admits high-diffusivity, near-isotropic voxels into any subsequent group statistics. These differences are displayed in Figure 4 and annotated in the Stage 1 interface.

### Inter-Tool DTI Metric Agreement

**Table 3. Quantitative inter-tool agreement for brain masks and DTI scalar metrics, on two independent open datasets.** Brain mask agreement assessed by Dice similarity coefficient (DSC) between each pair of per-tool brain extractions. DTI metric agreement assessed over white matter voxels (FA > 0.2 in all three tools) by Pearson correlation coefficient (r), mean absolute error (MAE), Bland–Altman mean bias, and 95% limits of agreement (LoA). All three tensor fits used the same shared brain mask and the same volume subset, so metric differences reflect tensor fitting rather than masking or shell selection. MD in µm²/ms. Statistics are restricted to voxels physically admissible in both tools of the pair (FA ∈ [0, 1]; 0 < MD ≤ 3.0 × 10⁻³ mm²/s).

*Stanford HARDI (single shell, b = 2000 s/mm², 160 volumes; n = 65,002 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | FA 95% LoA | MD r | MD MAE |
|---|---|---|---|---|---|---|---|
| FSL vs. DIPY | 0.9277 | 0.9604 | 0.0228 | −0.0158 | [−0.0992, +0.0676] | 0.9368 | 0.0325 |
| FSL vs. MRtrix3 | 0.9024 | 0.9652 | 0.0247 | −0.0181 | [−0.0964, +0.0602] | 0.9402 | 0.0333 |
| MRtrix3 vs. DIPY | 0.9009 | 0.9990 | 0.0029 | +0.0027 | [−0.0107, +0.0162] | 0.9965 | 0.0012 |

*Sherbrooke 3-shell (b = 0 + b = 1000 s/mm² subset, 65 volumes; n = 111,032 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | FA 95% LoA | MD r | MD MAE |
|---|---|---|---|---|---|---|---|
| FSL vs. DIPY | 0.9668 | 0.8897 | 0.0504 | +0.0148 | [−0.1640, +0.1937] | 0.9012 | 0.1272 |
| FSL vs. MRtrix3 | 0.9058 | 0.9157 | 0.0460 | +0.0139 | [−0.1419, +0.1696] | 0.9020 | 0.1271 |
| MRtrix3 vs. DIPY | 0.9163 | 0.9966 | 0.0059 | +0.0053 | [−0.0260, +0.0366] | 0.9991 | 0.0029 |

All three tools produced visually consistent FA maps (Figure 3a), with the canonical high-FA signature (FA > 0.6) in compact white matter tracts — corpus callosum, corticospinal tract, superior longitudinal fasciculus — and low FA values (FA < 0.2) in grey matter and CSF. On the Stanford data, mean white matter FA was 0.4000 ± 0.1479 (FSL), 0.4182 ± 0.1532 (MRtrix3), and 0.4168 ± 0.1537 (DIPY), with mean MD of 0.6034 ± 0.1295, 0.6350 ± 0.1442, and 0.6334 ± 0.1460 µm²/ms respectively. On the Sherbrooke data the corresponding values were FA 0.4775 ± 0.1977, 0.4698 ± 0.1914, and 0.4741 ± 0.1978, and MD 0.5224 ± 0.2249, 0.6410 ± 0.2820, and 0.6388 ± 0.2814 µm²/ms. All lie within the range conventionally reported for healthy white matter.

The comparison does not, however, partition symmetrically across the three toolkits, and the asymmetry takes the same form on both datasets.

**MRtrix3 and DIPY are near-identical.** On Stanford, FA agreement reached r = 0.9990 (Spearman ρ = 0.9997, MAE = 0.0029, LoA [−0.0107, +0.0162]) and MD agreement r = 0.9965 (MAE = 0.0012 µm²/ms). On Sherbrooke the corresponding values were r = 0.9966 for FA and r = 0.9991 for MD. Differences of this magnitude are an order of magnitude below within-tract biological variability (FA SD ≈ 0.05–0.10) and are of no practical consequence in either acquisition.

**FSL is the outlier of the three, on both datasets.** Its agreement with the other two was consistently and substantially lower: FA r = 0.9652 and 0.9604 on Stanford, falling to 0.9157 and 0.8897 on Sherbrooke; MD r = 0.9402 and 0.9368 on Stanford, and 0.9020 and 0.9012 on Sherbrooke. Bland–Altman analysis (Figure 3c) showed systematic bias rather than symmetric scatter in every FSL pairing, and the limits of agreement against FSL — roughly ±0.08 FA units on Stanford and ±0.17 on Sherbrooke — reach or exceed the scale of within-tract biological variability.

**The direction of the offset, however, does not replicate for FA.** Mean diffusivity behaved consistently: FSL returned lower MD than both other toolkits on both datasets, by 0.033 µm²/ms on Stanford (approximately 5%) and by 0.127 µm²/ms on Sherbrooke (approximately 19%). Fractional anisotropy did not. On Stanford, FSL FA was *lower* than MRtrix3 and DIPY by 0.018 and 0.016 units; on Sherbrooke it was *higher*, by 0.014 and 0.015. The sign of the FA discrepancy reverses between acquisitions, and its magnitude changes by a factor of four for MD.

This is a more consequential finding than a fixed offset would have been. A constant bias, once characterised, can in principle be corrected or absorbed into a covariate. A bias whose sign depends on the acquisition cannot: there is no single correction factor to apply, and an analyst comparing FA values across studies processed with different software has no way to anticipate even the direction of the discrepancy. Because all three fits were driven from identical input data, identical gradient tables, one shared brain mask, and one shared volume subset, the effect must originate in the tensor-fitting stage itself. All three toolkits were run with weighted linear least squares, but their weighting schemes, regularisation, and outlier handling differ in implementation, and the interaction between those choices and acquisition properties such as b-value, SNR, and the number of b = 0 volumes is evidently not negligible. We report this as an empirical observation across two acquisitions; identifying the precise algorithmic mechanism would require a controlled comparison of the fitting routines themselves, which lies beyond the scope of this platform paper.

### Non-Physical Tensor Fits

A finding that emerged directly from the quantitative analysis, and that is invisible in any side-by-side reading of documentation, concerns the frequency with which each toolkit returns physically impossible values. Fractional anisotropy is bounded to [0, 1] by definition and mean diffusivity must be positive; values outside these ranges indicate that the tensor fit returned negative eigenvalues, which unconstrained linear least squares permits.

**Table 4. Non-physical tensor fits within the white matter mask.** Counts of voxels violating the definition of each metric, with the percentage of the white matter mask in parentheses.

| Dataset | Metric | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|
| Stanford (n = 65,002) | FA > 1 | 261 (0.40%) | 178 (0.27%) | 0 (0%) |
| Stanford | MD ≤ 0 | 261 (0.40%) | 91 (0.14%) | 0 (0%) |
| Sherbrooke (n = 111,032) | FA > 1 | 4,404 (3.97%) | 2,252 (2.03%) | 0 (0%) |
| Sherbrooke | MD ≤ 0 | 3,016 (2.72%) | 603 (0.54%) | 0 (0%) |

The ordering is identical on both datasets and admits no ambiguity: FSL produces the most non-physical fits, MRtrix3 roughly half as many, and DIPY none at all. DIPY's `TensorModel` did not return a single voxel with FA > 1 or MD ≤ 0 in either acquisition (a small number of voxels, 20 and 3 respectively, exceeded the free-water diffusivity bound). What varies between datasets is the rate, not the ranking: the Sherbrooke acquisition, which supplies only one b = 0 volume against Stanford's ten, produced roughly ten times as many failed fits in every toolkit that admits them.

Their effect on correlation-based agreement metrics is severe and easy to overlook. Computed without a plausibility restriction, MRtrix3–DIPY MD agreement on the Stanford data appears to be r = 0.118 rather than r = 0.9965, because Pearson correlation is dominated by extreme values and a few hundred wild outliers carry no shared signal. An analysis reporting the former would conclude, incorrectly, that two toolkits which in fact agree to four significant figures are nearly unrelated. The effect on robust summary statistics is by contrast negligible: excluding these voxels changes the MRtrix3–DIPY mean absolute error by less than 2%.

Two practical implications follow, and the platform makes both concrete for learners. First, agreement statistics computed on raw tensor-derived maps without a physical plausibility check can be badly misleading, and the appropriate diagnostic is to count and inspect the inadmissible voxels rather than discard them silently. Second, the number of failed tensor fits is itself a usable quality indicator that differentiates toolkits, and it is sensitive to acquisition design — particularly to the number of b = 0 volumes.

### Shell Selection

A methodologically important asymmetry was identified in shell selection for DTI fitting. FSL `dtifit` and MRtrix3 `dwi2tensor` include all available b-value shells by default, whereas DIPY's `TensorModel` requires the user to explicitly select the shell used for fitting. For the Stanford HARDI single-shell dataset this has no practical consequence. For multi-shell data such as the HCP protocol (b = 1000/2000/3000 s/mm²), applying the single-tensor model to all shells simultaneously violates the monoexponential signal decay assumption; the resulting FA maps will differ from those obtained using only the b = 1000 shell. This is a non-trivial methodological difference that is rarely acknowledged in published methods sections and is highlighted explicitly in the dMRI Rosetta Stone Stage 4 interface.

### User Interface and Interaction Design

Figure 2 illustrates the Stage 4 (DTI Fitting) interface, representative of all seven pipeline stages. Each stage page presents three tabs labelled FSL, MRtrix3, and DIPY. Within each tab, the user sees: (1) the exact shell command formatted with relative file paths; (2) a green or red status badge confirming whether the required binary is available in the current environment; (3) a Run button that submits the command via Python's `subprocess` module and streams stdout and stderr in real time; and (4) the output visualised as a NIfTI slice or metric map. A collapsible **Why?** section below the tabs provides a biological and mathematical explanation of the operation and guidance on when to prefer the current toolkit.

Session state — subject identifier, data availability, detected b-value shells — is maintained in the sidebar and persists across page navigation, allowing users to switch datasets without restarting the application.

### Runtime Performance

On standard laptop hardware (macOS 14, Apple M2, 16 GB RAM; Docker Desktop, 8 GB memory allocation), all pipeline stages except eddy correction complete in under 3 minutes on the full 160-volume Stanford HARDI dataset. Eddy correction with FSL `eddy_cpu` on the full dataset requires approximately 35–45 minutes on a single CPU core. The demo subsample mode (20 volumes) reduces this to approximately 2–4 minutes while preserving the educational content of the stage.

---

## Discussion

### Educational Contribution

dMRI Rosetta Stone fills a specific gap in the neuroimaging training landscape that the comparison in Table 2 makes concrete. The closest existing analogue — Andy's Brain Book (Jahn, 2020) — covers FSL comprehensively and touches on MRtrix3, but is a read-only web resource with no code execution. DIPY tutorials are executable via Jupyter notebooks but cover DIPY exclusively. No existing resource places all three toolkits side by side on the same data in an executable format.

The Rosetta Stone metaphor is pedagogically productive. Learners with expertise in one toolkit can rapidly orient themselves in the syntax of another by reading the parallel tabs. Critically, the platform makes the *asymmetries* as visible as the equivalences: the absence of CSD in FSL, the fact that `dwifslpreproc` delegates eddy correction to FSL `eddy` rather than implementing it independently, and the conceptually distinct tractography models (iFOD2 probabilistic in MRtrix3, deterministic DTI-peaks in DIPY, ROI-seeded probabilistic in FSL `probtrackx2`) are each highlighted explicitly with a contextual explanation.

Containerised deployment is especially valuable in workshop contexts. Organisers can distribute the Docker image to participants in advance, eliminating the dependency installation bottlenecks that typically consume significant hands-on session time. The application runs on standard laptop hardware without GPU acceleration and has been tested on Linux (Ubuntu 22.04), macOS 13–14, and Windows 11 via Docker Desktop.

### Methodological Transparency and Reproducibility

dMRI Rosetta Stone contributes to methodological transparency at two levels. At the surface level, it makes implementation differences between toolkits visible and discussable: that FSL `eddy_cpu` corrects eddy current distortions, signal dropout, and outlier replacement in addition to head motion, whereas DIPY `motion_correction` performs rigid-body registration only, is a distinction that is rarely stated explicitly in published methods sections but is immediately apparent in the side-by-side interface. Similarly, the absence of CSD in FSL — a non-trivial limitation for acquisitions with crossing fibres — is not always communicated to students trained exclusively in FSL.

At a deeper level, the quantitative inter-tool agreement analysis presented here tests a proposition that is widely assumed but rarely demonstrated: that FSL, MRtrix3, and DIPY produce effectively interchangeable DTI scalar metrics when applied to the same data under controlled conditions. Our results support that proposition only in part, and the qualification is the more interesting half of the finding.

For MRtrix3 and DIPY the assumption holds comfortably, and it holds on both acquisitions. Agreement of r = 0.9990 and 0.9966 for FA, and r = 0.9965 and 0.9991 for MD, with limits of agreement an order of magnitude narrower than within-tract biological variability, means that a study analysed in one of these toolkits could have been analysed in the other with no material change to its tensor-derived results.

For FSL the assumption does not hold in the form usually assumed, and our two-dataset design is what makes this visible. Had we analysed the Stanford data alone, we would have reported a systematic offset of approximately 4% in FA and 5% in MD and concluded that a fixed, characterisable bias separates FSL from the other two. The Sherbrooke replication refutes that reading. The MD offset persists in direction but quadruples in magnitude, and the FA offset reverses sign entirely — FSL FA is lower than MRtrix3 and DIPY on one acquisition and higher on the other.

The practical consequence is worse than a fixed bias would be. A constant offset is a nuisance parameter: once measured, it can be corrected, or absorbed into a covariate, or simply acknowledged. An offset whose sign depends on the acquisition is not correctable in that way, because there is nothing stable to correct for. An analyst pooling FA values across studies processed with different software cannot anticipate even the direction of the discrepancy, let alone its size, without re-running the comparison on their own data — which is precisely what this platform makes cheap to do.

Two qualifications keep this in proportion. Within a single study processed consistently, the offset displaces every subject in the same direction and is therefore unlikely to manufacture a spurious group difference; the risk lies in cross-study and multi-site comparison, in normative reference ranges, and in meta-analyses of absolute diffusivity. And toolkit choice at the tensor-fitting stage remains a smaller source of variance than acquisition protocol or preprocessing. But "smaller" is not "negligible", and an effect that changes sign between two ordinary open datasets is not one that a methods section can responsibly leave unstated. The asymmetry we observe — two toolkits agreeing almost exactly while the third diverges unpredictably from both — is exactly the kind of implementation-level behaviour that side-by-side execution exposes and that reading three sets of documentation does not.

However, the shell selection asymmetry identified in Stage 4 — FSL and MRtrix3 including all shells by default while DIPY is explicit — serves as a concrete example of where implementation differences *do* matter for multi-shell data. This asymmetry is not captured by any existing documentation comparison but is immediately apparent in the dMRI Rosetta Stone interface. Several studies have demonstrated that such pipeline-level choices introduce non-trivial variability in dMRI-derived metrics (Bhagwat et al., 2021; Richie-Halford et al., 2022); the present platform makes this variability directly observable and educationally exploitable rather than merely reported.

### Comparison with Existing Resources

**Table 2. Comparison of dMRI Rosetta Stone with existing dMRI educational resources.**

| Resource | Toolkits | Executable | Real human data | Cross-tool, side-by-side | No local install |
|---|---|---|---|---|---|
| FSL Course / wiki | FSL | Local FSL required | Yes | No | No |
| MRtrix3 documentation | MRtrix3 | Local MRtrix3 required | Example data | No | No |
| DIPY tutorials | DIPY | Yes (Jupyter) | Yes | No | No (Python) |
| Andy's Brain Book (Jahn, 2020) | FSL, some MRtrix3 | No (read-only) | Screenshots | Partial, manual | No |
| NeuroHackademy recordings | Multiple | No (video) | Screenshots | No | No |
| Brainlife.io | Multiple | Yes (cloud) | Yes | No | No (account) |
| **dMRI Rosetta Stone** | **FSL + MRtrix3 + DIPY** | **Yes (Docker)** | **Yes** | **Yes** | **Docker only** |

The only dimension on which dMRI Rosetta Stone is not strictly superior to all alternatives is that it requires Docker Desktop (~4 GB) rather than a fully browser-native solution. Docker is currently necessary to bundle FSL and MRtrix3, which do not support WebAssembly compilation. Future work may remove this barrier.

Brainlife.io warrants a specific note. It is a cloud-based provenance-tracking and pipeline-execution platform that supports multiple neuroimaging tools, including FSL and MRtrix3 applications (Avesani et al., 2019). Its purpose is fundamentally different from dMRI Rosetta Stone: users upload their own research data, select a pre-packaged application, and run it on cloud infrastructure to obtain results with full provenance records. Brainlife.io does not provide tutorial scaffolding, side-by-side command comparison, or the conceptual explanation layer that learners need to understand what each operation does and why. It is designed for reproducible research execution, not for cross-tool education.

### Limitations

The platform currently supports single-subject analysis only; multi-subject group analysis beyond the synthetic TBSS demonstration requires real group data not included in the repository. The demo subsample mode for eddy correction is not suitable for quantitative analysis. The Docker image occupies approximately 17.6 GB uncompressed (approximately 5.6 GB as distributed layers) and requires approximately 15 minutes to build, which may be prohibitive in low-bandwidth settings; a pre-built image on a public container registry would mitigate this. GPU-accelerated MRtrix3 operations are not available in the current CPU-only Docker configuration.

The inter-tool benchmark reported here carries its own limitations, and they bound what may be concluded from the FSL divergence we describe. It rests on one subject from each of two datasets. Two acquisitions are enough to demonstrate that the FSL discrepancy is not a fixed, correctable bias — a single dataset would have suggested exactly the opposite — but they are not enough to characterise how it varies, to attribute it to specific acquisition properties such as b-value, SNR, or the number of b = 0 volumes, or to place a confidence interval around it. The benchmark isolates the tensor-fitting stage deliberately, applying no denoising or eddy-current correction, so the numbers characterise one pipeline step rather than an end-to-end analysis; whether the divergence persists, grows, or is absorbed after realistic preprocessing is untested. It compares only FA and MD under each toolkit's default weighted-least-squares configuration, and each toolkit exposes fitting options that were not explored. Establishing how the FSL divergence depends on acquisition, and identifying its algorithmic origin, would require a dedicated multi-subject study spanning several protocols — work that this platform is well suited to support but does not itself constitute.

Finally, the platform has not yet been evaluated in a formal user study; a structured assessment of learning outcomes in a workshop setting would strengthen the evidence base for its educational value.

### Future Directions

Planned developments include: (i) cloud deployment (e.g., Binder or Google Colab) to support GPU-accelerated tractography without local Docker installation; (ii) extension to advanced modules including fixel-based analysis, NODDI modelling, and automated tract segmentation; (iii) support for real multi-subject datasets from OpenNeuro; and (iv) a structured workshop pilot with pre/post knowledge assessment.

---

## Conclusion

dMRI Rosetta Stone is an open-source, containerised, interactive platform that enables side-by-side comparison, execution, and visual inspection of the complete dMRI preprocessing and analysis pipeline across FSL, MRtrix3, and DIPY. By running real human brain data through all three toolkits in a unified browser interface, the platform makes cross-tool translation immediately accessible to students and researchers at all levels of experience. The application addresses a genuine and previously unmet gap in the neuroimaging training landscape, and is designed to accelerate dMRI education while promoting the methodological transparency that reproducible neuroimaging science requires.

---

## Data Availability Statement

The complete source code, Dockerfile, and documentation are openly available at https://github.com/happybrotherhood/dmri-rosetta-stone under an MIT licence. The Stanford HARDI demonstration dataset is freely available through the DIPY project at https://dipy.org and is downloaded automatically by the application. No registration or credentials are required to reproduce all results presented here.

---

## Author Contributions

BM: Conceptualization, Data curation, Formal analysis, Methodology, Software, Validation, Visualization, Writing – original draft, Writing – review and editing.

---

## Funding

[*Complete before submission: include grant numbers and funding bodies.*]

---

## Conflict of Interest Statement

The author declares that the research was conducted in the absence of any commercial or financial relationships that could be construed as a potential conflict of interest.

---

## Acknowledgements

[*Complete before submission: supervisors, HPC resources, collaborators.*]

---

## References

Avesani P, McPherson B, Hayashi S, Caiafa CF, Henschel R, Garyfallidis E, et al. (2019) The open diffusion data derivatives, brain data upcycling via integrated collection and reuse. *Scientific Data* 6, 69. doi: 10.1038/s41597-019-0073-y

Andersson JLR and Sotiropoulos SN (2016) An integrated approach to correction for off-resonance effects and subject movement in diffusion MR imaging. *NeuroImage* 125, 1063–1078. doi: 10.1016/j.neuroimage.2015.10.019

Basser PJ, Mattiello J, and LeBihan D (1994) MR diffusion tensor spectroscopy and imaging. *Biophysical Journal* 66, 259–267. doi: 10.1016/S0006-3495(94)80775-1

Beaulieu C (2002) The basis of anisotropic water diffusion in the nervous system – a technical review. *NMR in Biomedicine* 15, 435–455. doi: 10.1002/nbm.782

Bhagwat N, Barry A, Dickie EW, Brown ST, Devenyi GA, Hatano K, et al. (2021) Understanding the impact of preprocessing pipelines on neuroimaging cortical surface analyses. *GigaScience* 10, giaa155. doi: 10.1093/gigascience/giaa155

Catani M and Thiebaut de Schotten M (2008) A diffusion tensor imaging tractography atlas for virtual in vivo dissections. *Cortex* 44, 1105–1132. doi: 10.1016/j.cortex.2008.05.004

Garyfallidis E, Brett M, Amirbekian B, Rokem A, Van Der Walt S, Descoteaux M, et al. (2014) Dipy, a library for the analysis of diffusion MRI data. *Frontiers in Neuroinformatics* 8, 8. doi: 10.3389/fninf.2014.00008

Glasser MF, Sotiropoulos SN, Wilson JA, Coalson TS, Fischl B, Andersson JL, et al. (2013) The minimal preprocessing pipelines for the Human Connectome Project. *NeuroImage* 80, 105–124. doi: 10.1016/j.neuroimage.2013.04.127

Jahn A (2020) *Andy's Brain Book: An Introduction to Neuroimaging Analysis*. Available at: https://andysbrainbook.readthedocs.io (Accessed June 2026).

Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, and Smith SM (2012) FSL. *NeuroImage* 62, 782–790. doi: 10.1016/j.neuroimage.2011.09.015

Jones DK (ed.) (2010) *Diffusion MRI: Theory, Methods, and Applications*. Oxford: Oxford University Press.

Merkel D (2014) Docker: Lightweight Linux containers for consistent development and deployment. *Linux Journal* 2014, 2.

Richie-Halford A, Cieslak M, Ai L, Caffarra S, Covitz S, Franco AR, et al. (2022) An analysis-ready and quality controlled resource for pediatric brain white-matter research. *Scientific Data* 9, 616. doi: 10.1038/s41597-022-01695-7

Rokem A, Yeatman JD, Pestilli F, Kay KN, Mezer A, van der Walt S, et al. (2015) Evaluating the accuracy of diffusion MRI models in white matter. *PLOS ONE* 10, e0123272. doi: 10.1371/journal.pone.0123272

Smith RE, Tournier JD, Calamante F, and Connelly A (2015) SIFT2: Enabling dense quantitative assessment of brain white matter connectivity using streamlines tractography. *NeuroImage* 119, 338–351. doi: 10.1016/j.neuroimage.2015.06.092

Smith SM, Jenkinson M, Woolrich MW, Beckmann CF, Behrens TEJ, Johansen-Berg H, et al. (2004) Advances in functional and structural MR image analysis and implementation as FSL. *NeuroImage* 23 (Suppl 1), S208–S219. doi: 10.1016/j.neuroimage.2004.07.051

Smith SM, Jenkinson M, Johansen-Berg H, Rueckert D, Nichols TE, Mackay CE, et al. (2006) Tract-based spatial statistics: Voxelwise analysis of multi-subject diffusion data. *NeuroImage* 31, 1487–1505. doi: 10.1016/j.neuroimage.2006.02.024

Streamlit Inc (2019) *Streamlit: The fastest way to build and share data apps* [Computer software]. Available at: https://streamlit.io

Tournier JD, Calamante F, and Connelly A (2007) Robust determination of the fibre orientation distribution in diffusion MRI: Non-negativity constrained super-resolved spherical deconvolution. *NeuroImage* 35, 1459–1472. doi: 10.1016/j.neuroimage.2007.02.016

Tournier JD, Calamante F, and Connelly A (2010) Improved probabilistic streamlines tractography by 2nd order integration over fibre orientation distributions. *Proceedings of the International Society for Magnetic Resonance in Medicine* 18, 1670.

Tournier JD, Smith RE, Raffelt D, Tabbara R, Dhollander T, Pietsch M, et al. (2019) MRtrix3: A fast, flexible and open software framework for medical image processing and visualisation. *NeuroImage* 202, 116137. doi: 10.1016/j.neuroimage.2019.116137

Van Essen DC, Smith SM, Barch DM, Behrens TEJ, Yacoub E, Ugurbil K, et al. (2013) The WU-Minn Human Connectome Project: An overview. *NeuroImage* 80, 62–79. doi: 10.1016/j.neuroimage.2013.05.041

Veraart J, Novikov DS, Christiaens D, Ades-aron B, Sijbers J, and Fieremans E (2016) Denoising of diffusion MRI using random matrix theory. *NeuroImage* 142, 394–406. doi: 10.1016/j.neuroimage.2016.08.016

---

## Tables

**Table 1. Pipeline stage coverage across FSL, MRtrix3, and DIPY in dMRI Rosetta Stone.** Dashes indicate the toolkit does not provide a dedicated implementation for that operation.

| Stage | Operation | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|
| 1 | Brain extraction | `bet` | `dwi2mask` | `median_otsu` |
| 2 | Denoising (MP-PCA) | — | `dwidenoise` | `mppca` |
| 3 | Eddy and motion correction | `eddy_cpu` | `dwifslpreproc` | `motion_correction` |
| 4 | DTI fitting | `dtifit` | `dwi2tensor` + `tensor2metric` | `TensorModel` |
| 5 | CSD / fibre orientation distributions | — | `dwi2fod` (msmt-CSD) | `ConstrainedSphericalDeconvModel` |
| 6 | Tractography | `probtrackx2` | `tckgen` (iFOD2) + `tcksift2` | `LocalTracking` |
| 7 | Voxelwise group analysis | `tbss_1–4` + `randomise` | — | — |

**Table 3. Quantitative inter-tool agreement for brain masks and DTI scalar metrics, on two independent open datasets.** Brain mask agreement assessed by Dice similarity coefficient (DSC) between each pair of per-tool brain extractions. DTI metric agreement assessed over white matter voxels (FA > 0.2 in all three tools) by Pearson correlation coefficient (r), mean absolute error (MAE), Bland–Altman mean bias, and 95% limits of agreement (LoA). All three tensor fits used the same shared brain mask and the same volume subset, so metric differences reflect tensor fitting rather than masking or shell selection. MD in µm²/ms. Statistics are restricted to voxels physically admissible in both tools of the pair (FA ∈ [0, 1]; 0 < MD ≤ 3.0 × 10⁻³ mm²/s); per-tool counts of excluded voxels are reported in Table 4. All values generated by `scripts/compute_fa_comparison.py`.

*Stanford HARDI (single shell, b = 2000 s/mm², 160 volumes; n = 65,002 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | FA 95% LoA | MD r | MD MAE |
|---|---|---|---|---|---|---|---|
| FSL vs. DIPY | 0.9277 | 0.9604 | 0.0228 | −0.0158 | [−0.0992, +0.0676] | 0.9368 | 0.0325 |
| FSL vs. MRtrix3 | 0.9024 | 0.9652 | 0.0247 | −0.0181 | [−0.0964, +0.0602] | 0.9402 | 0.0333 |
| MRtrix3 vs. DIPY | 0.9009 | 0.9990 | 0.0029 | +0.0027 | [−0.0107, +0.0162] | 0.9965 | 0.0012 |

*Sherbrooke 3-shell (b = 0 + b = 1000 s/mm² subset, 65 volumes; n = 111,032 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | FA 95% LoA | MD r | MD MAE |
|---|---|---|---|---|---|---|---|
| FSL vs. DIPY | 0.9668 | 0.8897 | 0.0504 | +0.0148 | [−0.1640, +0.1937] | 0.9012 | 0.1272 |
| FSL vs. MRtrix3 | 0.9058 | 0.9157 | 0.0460 | +0.0139 | [−0.1419, +0.1696] | 0.9020 | 0.1271 |
| MRtrix3 vs. DIPY | 0.9163 | 0.9966 | 0.0059 | +0.0053 | [−0.0260, +0.0366] | 0.9991 | 0.0029 |

**Table 4. Non-physical tensor fits within the white matter mask.** Counts of voxels violating the definition of each metric, with the percentage of the white matter mask in parentheses.

| Dataset | Metric | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|
| Stanford (n = 65,002) | FA > 1 | 261 (0.40%) | 178 (0.27%) | 0 (0%) |
| Stanford | MD ≤ 0 | 261 (0.40%) | 91 (0.14%) | 0 (0%) |
| Sherbrooke (n = 111,032) | FA > 1 | 4,404 (3.97%) | 2,252 (2.03%) | 0 (0%) |
| Sherbrooke | MD ≤ 0 | 3,016 (2.72%) | 603 (0.54%) | 0 (0%) |

---

## Figure Captions

**Figure 1.** Software architecture of the dMRI Rosetta Stone Docker container. A two-stage build copies MRtrix3 3.0.4 binaries from the official MRtrix3 image and installs FSL 6.0.7 and the Python stack (DIPY, Streamlit, nibabel, numpy, scipy, matplotlib) on Ubuntu 22.04. The Streamlit server runs on port 8501 and executes pipeline commands via Python `subprocess` within the container environment.

**Figure 2.** The Stage 4 (DTI Fitting) user interface, representative of all seven pipeline stages. Three tabs (FSL, MRtrix3, DIPY) each show the exact executable command, a tool-availability status badge, a Run button that streams live output, and a rendered output metric map. The collapsible Why? section (not shown) provides biological and mathematical context.

**Figure 3.** Quantitative inter-tool DTI metric agreement, shown for the Stanford HARDI dataset (the equivalent panel for Sherbrooke 3-shell is provided as Supplementary Figure S1; both are generated by the same script). **(a)** FA maps (central axial slice) from FSL `dtifit`, MRtrix3 `tensor2metric`, and DIPY `TensorModel`, applied to identical input volumes with one shared brain mask. **(b)** Voxelwise FA scatter plots for each cross-tool pair over white matter voxels (FA > 0.2 in all three tools) with Pearson r, mean absolute error, and identity line. **(c)** Bland–Altman plots for each cross-tool pair showing the distribution of voxelwise FA differences against their mean; horizontal lines indicate the mean difference (bias) and ±1.96 SD limits of agreement. The MRtrix3–DIPY pair is tightly clustered about the identity line, whereas both FSL pairings show systematic bias and markedly wider scatter. Voxels with physically inadmissible values are excluded, as described in Methods.

**Figure 4.** Brain extraction comparison on the Stanford HARDI dataset (the Sherbrooke equivalent is provided as Supplementary Figure S2). The b = 0 mean image (greyscale) with brain mask overlaid in red, produced by FSL `bet` (left, 203,984 voxels), MRtrix3 `dwi2mask` (centre, 167,950 voxels), and DIPY `median_otsu` (right, 187,948 voxels) from the same input volume. Dice similarity coefficients for each pair are reported in Table 3. Two differences are visible: the extent of cortical boundary coverage, and the treatment of the lateral ventricles, which DIPY `median_otsu` excludes while FSL `bet` and MRtrix3 `dwi2mask` retain. These reflect the distinct tissue models employed by each algorithm.

**Supplementary Figure S1.** As Figure 3, for the Sherbrooke 3-shell dataset (b = 0 + b = 1000 s/mm² subset).

**Supplementary Figure S2.** As Figure 4, for the Sherbrooke 3-shell dataset.
