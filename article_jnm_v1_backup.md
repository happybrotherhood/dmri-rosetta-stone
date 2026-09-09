# Do FSL, MRtrix3 and DIPY agree? A controlled benchmark of diffusion tensor metrics across two open datasets

**Busra Mutlu**¹\*

¹ Department of Neuroimaging, King's College London, London, United Kingdom

\* **Corresponding author.** Busra Mutlu, Department of Neuroimaging, King's College London, De Crespigny Park, London SE5 8AF, United Kingdom. E-mail: [KCL EMAIL]

## Abstract

**Background.** Diffusion MRI is analysed with three packages — FSL, MRtrix3 and DIPY — assumed to produce interchangeable tensor metrics. The assumption is rarely tested under controlled conditions.

**New method.** We benchmark the three on two independent open datasets, Stanford HARDI and Sherbrooke 3-shell, holding everything constant except the toolkit: the same volumes and gradient tables, one shared brain mask, one single-shell subset, and no preprocessing. Statistics use only physically admissible voxels. All three run in one container, so further datasets can be added in two commands.

**Results.** Agreement was asymmetric on both acquisitions. MRtrix3 and DIPY were near-identical in white matter (fractional anisotropy r = 0.9990 and 0.9966; mean diffusivity r = 0.9965 and 0.9991), whereas FSL diverged from both. The FSL discrepancy was not a fixed bias: mean diffusivity was lower by 5% on one dataset and 19% on the other, and the anisotropy offset reversed sign. Non-physical tensor fits reached 4.0% of white matter voxels in FSL and 2.0% in MRtrix3, but never occurred in DIPY.

**Comparison with existing methods.** Earlier work measures variability across whole pipelines, which cannot say which step is responsible. Holding every other input identical leaves the tensor fit as the only variable, so the difference is attributable to it.

**Conclusions.** MRtrix3 and DIPY are interchangeable for tensor metrics; FSL is not, and its offset cannot be corrected by a scaling factor because its sign depends on the acquisition. Leaving non-physical voxels in place drops an apparent diffusivity correlation from 0.997 to 0.118, a trap when computing agreement on raw tensor maps.

**Keywords:** diffusion MRI; tensor fitting; software comparison; reproducibility; benchmarking; FSL; MRtrix3

## Introduction

Diffusion magnetic resonance imaging (dMRI) is the principal non-invasive technique for probing white matter microstructure and structural connectivity in the living human brain (Basser et al., 1994; Jones, 2010). By encoding the directional displacement of water molecules, dMRI provides access to biophysical indices — including fibre orientation, axon density, and myelin integrity — that are invisible to conventional anatomical MRI (Beaulieu, 2002). Applications span fundamental neuroscientific questions about brain organisation and inter-individual variability, as well as clinical contexts including the characterisation of white matter alterations in neurodegenerative diseases, psychiatric conditions, and neurodevelopmental disorders (Catani and Thiebaut de Schotten, 2008; Jones, 2010).

The dMRI analysis ecosystem is dominated by three major software packages. FSL (FMRIB Software Library), developed at the University of Oxford, provides robust preprocessing, DTI fitting, and voxelwise group analysis via the Tract-Based Spatial Statistics (TBSS) pipeline (Smith et al., 2004; Jenkinson et al., 2012). MRtrix3, developed at The Florey Institute of Neuroscience and Mental Health, specialises in constrained spherical deconvolution (CSD) and high-fidelity fibre orientation modelling (Tournier et al., 2019). DIPY (Diffusion Imaging in Python) offers a flexible, Python-native implementation of the full dMRI pipeline and is widely used when algorithmic transparency or custom extensions are required (Garyfallidis et al., 2014).

Despite their complementary strengths, these toolkits present a significant practical barrier. Each employs distinct command-line syntax, file format conventions, and — in several cases — different terminology for the same operation. For example, brain extraction is called `bet` in FSL, `dwi2mask` in MRtrix3, and `median_otsu` in DIPY. Mean diffusivity is reported as `MD` in FSL, `ADC` in MRtrix3, and `md` in DIPY. These surface-level differences cause genuine confusion for researchers trained in one ecosystem who attempt to read, reproduce, or extend work conducted in another.

A more substantive concern is methodological reproducibility. Published dMRI studies rarely justify their choice of software, and it is not always clear whether reported group differences in white matter metrics reflect genuine biological effects or implementation-level differences between tools. Software-specific choices — brain masking algorithm, denoising method, tensor fitting algorithm — can introduce non-trivial variability in derived metrics such as fractional anisotropy (FA) and mean diffusivity (MD), and this has been demonstrated at the level of whole pipelines (Bhagwat et al., 2021; Richie-Halford et al., 2022).

Such studies leave a narrower question open: when the *only* thing that differs is the software performing the tensor fit, how much do the toolkits disagree? Answering that requires holding every other input fixed, which is laborious to arrange by hand across three toolkits with incompatible interfaces and file conventions.

We addressed this by building a containerised environment in which all three toolkits run on identical data, and then using it to run the controlled comparison. The instrument and the measurement are reported together here because neither is much use without the other: the comparison would be impractical to reproduce without the container, and the container would be an untested convenience without the comparison.

Three questions are addressed. First, how far do FSL, MRtrix3 and DIPY agree on fractional anisotropy and mean diffusivity when given byte-identical input? Second, does any disagreement behave like a fixed bias, which could be corrected, or does it vary with the acquisition? Third, how often does each toolkit return values that are physically impossible, and what does that do to the agreement statistics normally used to answer the first question?

We report the comparison on two open datasets acquired at different sites under different protocols, so that the findings are replicated rather than observed once. Both are distributed without credentials, and every reported value can be regenerated with four commands.

## Materials and Methods

### Data

All demonstrations use the Stanford HARDI dataset distributed by the DIPY project under an open-access licence (Rokem et al., 2015). The dataset comprises 160 volumes (10 b = 0, 150 DWI at b = 2000 s/mm²) with voxel size 2 × 2 × 2 mm and matrix 81 × 106 × 76. It is downloaded automatically on first launch via DIPY's `get_fnames("stanford_hardi")` utility without credentials. A brain mask is generated at download time using `median_otsu` and stored alongside the raw NIfTI data.

The quantitative benchmark reported below additionally uses the Sherbrooke 3-shell dataset, distributed openly as part of the DIPY sample data collection (Garyfallidis et al., 2014) and retrieved via `get_fnames("sherbrooke_3shell")`; like the Stanford data it requires no credentials. It comprises 193 volumes (1 b = 0; 64 directions at each of b = 1000, 2000, and 3500 s/mm²) with voxel size 2 × 2 × 2 mm and matrix 128 × 128 × 60. The dataset is distributed with DIPY rather than accompanied by a dedicated acquisition publication, and we use it here as an independent test acquisition rather than as a characterised reference sample. Because it differs from the Stanford data in site, protocol, angular sampling, b-value range, and — importantly for the results below — the number of b = 0 volumes, analysing both provides an independent replication of the inter-tool comparison rather than a second look at one acquisition.

The application also supports Human Connectome Project (HCP; Van Essen et al., 2013) multi-shell data (b = 1000/2000/3000 s/mm², 90 directions per shell) for users with HCP data access credentials, enabling demonstration of multi-tissue CSD which requires multiple non-zero b-value shells.

### Comparison design

Beyond the interactive pipeline, we conducted a systematic quantitative comparison of DTI scalar metrics and brain masks across all three toolkits, on both the Stanford HARDI and the Sherbrooke 3-shell datasets. This analysis serves two purposes: it validates that the platform produces outputs consistent with established diffusion MRI principles, and it constitutes a reproducible, openly available benchmark of inter-tool agreement under controlled conditions — identical input volumes, identical gradient tables, and a single shared brain mask.

The design is summarised in Figure 1. It comprises two comparisons that make opposite choices about the input, and the distinction between them matters for interpreting the results. For brain extraction, each tool is run on the input its algorithm expects, so the comparison reflects the difference a user would actually encounter. For tensor fitting, every tool is given byte-identical input, so the comparison isolates the fitting stage from every other source of variation.

**Brain mask agreement** was assessed using the Dice similarity coefficient (DSC) between each pair of binary masks produced by FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu`. Each tool was run in its own idiomatic configuration rather than forced onto a common input, because the input a tool is designed to consume is part of the algorithm being compared: `bet` operates on the mean b = 0 image, `dwi2mask` on the full DWI series, and `median_otsu` on the full series with the b = 0 volumes indexed. The DSC therefore quantifies the end-to-end difference between the three brain-extraction routines as a user would actually invoke them. DSC values are reported in Table 2.

Separately, and to keep brain extraction from confounding the metric comparison, a *single* shared brain mask generated by `median_otsu` was supplied to all three tensor fits. A white matter reference mask, defined as voxels where all three tools jointly yielded FA > 0.2, was used for all subsequent metric comparisons.

**DTI metric agreement** was assessed for FA and MD on both datasets. To isolate tensor-fitting differences from every other source of variability, all three tools were applied to the *identical* input: the same unprocessed volumes, the same bvals and bvecs, and the shared `median_otsu` brain mask described above. No denoising or eddy-current correction was applied before fitting. This omission is deliberate rather than a shortcut: any preprocessing step would itself be a toolkit-specific choice, and applying one tool's preprocessing to all three would confound the very comparison it is meant to enable. The consequence, which we state plainly, is that the reported agreement characterises the tensor-fitting stage alone and not a complete analysis pipeline.

For the multi-shell Sherbrooke data a further step was required. The single-tensor model assumes monoexponential signal decay, which does not hold across shells; FSL `dtifit` and MRtrix3 `dwi2tensor` silently fit every volume they are given, whereas DIPY requires the shell to be selected by the user. Left unaddressed, the three toolkits would have fitted different data and any difference between them would confound tensor fitting with shell selection. We therefore extracted the b = 0 and b = 1000 s/mm² volumes (65 of 193) once, and passed that identical subset to all three toolkits. The Stanford data is single-shell, so all 160 volumes were used.

Voxelwise Pearson correlation coefficients (r), Spearman rank correlations (ρ), and mean absolute error (MAE) were computed over white matter voxels, and Bland–Altman analysis was performed for each cross-tool pair to characterise the distribution of voxelwise differences and identify any systematic bias.

Statistics were restricted to voxels whose values are physically admissible in both tools of a given pair: FA within [0, 1], and MD positive and no greater than the diffusivity of free water at body temperature (3.0 × 10⁻³ mm²/s). This restriction is necessary rather than cosmetic. Unconstrained linear tensor fitting can return negative eigenvalues, which drive FA above unity and MD below zero; because Pearson correlation is dominated by extreme values, a few hundred such voxels are sufficient to depress the apparent MD agreement from r = 0.997 to r = 0.118 while changing the mean absolute error by less than 2%. The per-tool counts of these non-physical voxels are reported in the Results as a substantive inter-tool difference in their own right.

Results are reported in Tables 3 and 4 and in Figures 3 and 4, with the corresponding Sherbrooke figures provided as Supplementary Figures S1 and S2. All analyses were performed using the companion scripts `scripts/generate_fa_maps.py` and `scripts/compute_fa_comparison.py` distributed with the repository. Every value reported here is reproducible from openly available data with no credentials, by running:

```bash
python scripts/generate_fa_maps.py      --subject stanford
python scripts/compute_fa_comparison.py --subject stanford
python scripts/generate_fa_maps.py      --subject sherbrooke --shell 1000
python scripts/compute_fa_comparison.py --subject sherbrooke
```

### The execution environment

Running three toolkits on byte-identical input is the practical obstacle to a comparison of this kind, and the reason it is rarely done. We removed it by building a single container in which all three are installed and driven from one interface, so the same data can be pushed through each without reinstallation, format conversion, or hand-managed paths. The container is what makes the comparison reproducible by others, and is released with the paper.

#### Container build

dMRI Rosetta Stone is implemented as a Streamlit web application (version ≥ 1.40; Streamlit Inc., 2019) and containerised with Docker (Merkel, 2014). Streamlit converts Python scripts into interactive browser-based interfaces without requiring HTML, CSS, or JavaScript, making the codebase accessible to any researcher with Python familiarity.

The Dockerfile uses a two-stage build. Stage 1 copies MRtrix3 3.0.4 binaries from the official `mrtrix3/mrtrix3:latest` image. Stage 2 starts from `ubuntu:22.04`, installs FSL 6.0.7 via the official `fslinstaller.py` script, copies MRtrix3 from Stage 1, and installs the Python stack — Streamlit, DIPY ≥ 1.7, nibabel, numpy, scipy, matplotlib, pandas, scikit-image — via pip. This multi-stage approach avoids dependency conflicts between FSL and MRtrix3 that arise from single-stage installation. The container serves the Streamlit interface at `http://localhost:8501` via two commands:

```bash
docker build --platform linux/amd64 -t dmri-rosetta .
docker run --rm --platform linux/amd64 -p 8501:7860 dmri-rosetta
```

The first command builds the image (approximately 15 minutes, dominated by the FSL download); the second launches the container. No neuroimaging software is required on the host machine.

#### Pipeline coverage

The application covers seven pipeline stages, each as a dedicated page in the sidebar navigation (Table 1).

**Brain Extraction.** FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu` are demonstrated on the same b = 0 volume. Outputs are displayed as a red-tinted mask overlay on the b = 0 image (Figure 4).

**Denoising (MP-PCA).** Marchenko-Pastur PCA exploits diffusion signal redundancy to separate signal from thermal noise using random matrix theory (Veraart et al., 2016). MRtrix3 `dwidenoise` and DIPY `mppca` are demonstrated. FSL lacks a dedicated denoising tool; this asymmetry is made explicit with an explanation of when denoising is most beneficial.

**Eddy Current and Motion Correction.** FSL `eddy_cpu` (Andersson and Sotiropoulos, 2016), MRtrix3 `dwifslpreproc` (which wraps FSL eddy internally and prepends Gibbs-ringing removal via `mrdegibbs`), and DIPY `motion_correction` (rigid-body registration only, no eddy correction) are demonstrated. A demo subsample mode (5 b = 0 + 15 DWI volumes) reduces runtime from approximately 40 minutes to approximately 3 minutes for interactive use.

**DTI Fitting.** FSL `dtifit`, MRtrix3 `dwi2tensor` + `tensor2metric`, and DIPY `TensorModel.fit()` are applied to the same input data; FA, MD, AD, and RD maps are rendered for each toolkit (Figure 3).

**Constrained Spherical Deconvolution.** MRtrix3 `dwi2fod` (single-shell CSD, Tournier et al., 2007; multi-shell multi-tissue CSD, Jeurissen et al., 2014) and DIPY `ConstrainedSphericalDeconvModel` are demonstrated. FSL does not include CSD; its omission is discussed together with acquisition requirements for CSD (≥ 30 directions, high b-value).

**Tractography.** MRtrix3 `tckgen` with the iFOD2 probabilistic algorithm (Tournier et al., 2010) and streamline filtering via `tcksift2` (Smith et al., 2015), FSL `probtrackx2` (command display and conceptual overview), and DIPY `LocalTracking` (deterministic, DTI peaks) are demonstrated. Track density images (TDI) generated with `tckmap` provide voxelwise streamline density maps.

**TBSS Voxelwise Group Analysis.** The full TBSS pipeline (Smith et al., 2006) — `tbss_1_preproc`, `tbss_2_reg`, `tbss_3_postreg`, `tbss_4_prestats`, and `randomise` — is demonstrated. Because the platform operates on a single subject, a synthetic group is constructed by adding Gaussian noise realisations (σ = 0.03 FA units) to the real FA map. The absence of equivalent voxelwise pipelines in MRtrix3 and DIPY (fixel-based analysis in MRtrix3 is noted as the conceptual analogue) is made explicit.

#### Reference material

A dedicated Reference section provides: (1) a DTI metrics guide with the biological interpretation of FA, MD, AD, and RD and live map display; (2) a 16-term dMRI glossary; (3) a command cheat sheet covering all seven stages across all three toolkits; and (4) a decision framework for selecting the appropriate toolkit based on acquisition type, research question, and available compute resources.

#### Availability and requirements

| | |
|---|---|
| **Project name** | dMRI Rosetta Stone |
| **Project home page** | https://github.com/happybrotherhood/dmri-rosetta-stone |
| **Archived version** | v1.0.0, Zenodo, doi:10.5281/zenodo.22106455 (all versions: doi:10.5281/zenodo.22106454) |
| **Operating system** | Platform independent — Linux, macOS, and Windows, via Docker |
| **Programming language** | Python ≥ 3.9 |
| **Other requirements** | Docker ≥ 20.10. For local installation without Docker: FSL ≥ 6.0 and MRtrix3 ≥ 3.0.4 |
| **Bundled toolkits** | FSL 6.0.7, MRtrix3 3.0.4, DIPY ≥ 1.7 |
| **Licence** | MIT |
| **Restrictions for non-academic use** | None imposed by this project. Note, however, that the bundled FSL is distributed under the FSL Licence, which restricts commercial use; users intending commercial deployment must obtain a licence from Oxford University Innovation. MRtrix3 (MPL 2.0) and DIPY (BSD 3-clause) carry no such restriction. |

## Results

### Brain Mask Agreement

Brain masks produced by FSL `bet`, MRtrix3 `dwi2mask`, and DIPY `median_otsu`, each run on the input its algorithm is designed to consume, showed high pairwise overlap on both datasets (Table 2). Dice similarity coefficients ranged from 0.9009 to 0.9277 on Stanford and from 0.9058 to 0.9668 on Sherbrooke, with no pair falling below 0.90 in either acquisition.

Pairwise Dice, however, conceals how differently the three algorithms behave, and it conceals it in a way worth stating explicitly: for a large, compact object such as the brain, DSC stays high even when boundary decisions differ appreciably. On Stanford the mask volumes were 203,984 voxels (FSL), 187,948 (DIPY), and 167,950 (MRtrix3) — a spread of 21% between the largest and the smallest, despite every pairwise DSC exceeding 0.90. Nor is the ordering stable across acquisitions. On Sherbrooke the volumes were 199,249 (MRtrix3), 188,717 (FSL), and 186,450 (DIPY), a spread of only 7%, with MRtrix3 moving from the most conservative mask on one dataset to the most inclusive on the other. Which tool yields the largest brain mask is therefore a property of the tool *and* the acquisition together, not of the tool alone.

Disagreements were concentrated at the cortical boundary and, distinctively, at the lateral ventricles (Figure 4). DIPY `median_otsu` excluded ventricular CSF, whereas FSL `bet` and MRtrix3 `dwi2mask` retained it. This reflects both the different tissue models each algorithm employs — Otsu intensity thresholding after median filtering in DIPY, a deformable surface model in FSL `bet`, signal averaging over the DWI series in MRtrix3 `dwi2mask` — and the different inputs those models are designed to consume, which is part of what distinguishes them in practice. The consequence is practical rather than cosmetic: a mask that includes ventricles admits high-diffusivity, near-isotropic voxels into any subsequent group statistics. These differences are displayed in Figure 4 and annotated in the Stage 1 interface.

### Inter-Tool DTI Metric Agreement

**Table 2. Quantitative inter-tool agreement for brain masks and DTI scalar metrics, on two independent open datasets.** Brain mask agreement assessed by Dice similarity coefficient (DSC) between each pair of per-tool brain extractions. DTI metric agreement assessed over white matter voxels (FA > 0.2 in all three tools) by Pearson correlation coefficient (r), mean absolute error (MAE), Bland–Altman mean bias, and 95% limits of agreement (LoA). All three tensor fits used the same shared brain mask and the same volume subset, so metric differences reflect tensor fitting rather than masking or shell selection. MD in µm²/ms. Statistics are restricted to voxels physically admissible in both tools of the pair (FA ∈ [0, 1]; 0 < MD ≤ 3.0 × 10⁻³ mm²/s).

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

These per-tool means are computed over each tool's own physically admissible voxels, whereas the Bland–Altman bias in Table 2 is computed over voxels admissible in *both* tools of a pair. The two therefore need not agree exactly, and on Sherbrooke — where the number of excluded voxels differs substantially between toolkits — they do not: the FSL-minus-MRtrix3 difference in means is +0.0077 FA units against a paired bias of +0.0139. The paired statistic is the appropriate one for agreement, since it compares the same voxels in both tools.

The three toolkits do not, however, agree equally well with one another, and the pattern is the same on both datasets.

**MRtrix3 and DIPY are near-identical.** On Stanford, FA agreement reached r = 0.9990 (Spearman ρ = 0.9997, MAE = 0.0029, LoA [−0.0107, +0.0162]) and MD agreement r = 0.9965 (MAE = 0.0012 µm²/ms). On Sherbrooke the corresponding values were r = 0.9966 for FA and r = 0.9991 for MD. Differences of this magnitude are an order of magnitude below within-tract biological variability (FA SD ≈ 0.05–0.10) and are of no practical consequence in either acquisition.

**FSL is the outlier of the three, on both datasets.** Its agreement with the other two was consistently and substantially lower: FA r = 0.9652 and 0.9604 on Stanford, falling to 0.9157 and 0.8897 on Sherbrooke; MD r = 0.9402 and 0.9368 on Stanford, and 0.9020 and 0.9012 on Sherbrooke. Bland–Altman analysis (Figure 3c) showed systematic bias rather than symmetric scatter in every FSL pairing, and the limits of agreement against FSL — roughly ±0.08 FA units on Stanford and ±0.17 on Sherbrooke — reach or exceed the scale of within-tract biological variability.

**The direction of the offset, however, does not replicate for FA.** Mean diffusivity behaved consistently: FSL returned lower MD than both other toolkits on both datasets, by 0.033 µm²/ms on Stanford (approximately 5%) and by 0.127 µm²/ms on Sherbrooke (approximately 19%). Fractional anisotropy did not. On Stanford, FSL FA was *lower* than MRtrix3 and DIPY by 0.018 and 0.016 units; on Sherbrooke it was *higher*, by 0.014 and 0.015. The sign of the FA discrepancy reverses between acquisitions, and its magnitude changes by a factor of four for MD.

This matters more than a fixed offset would have. A constant bias can be measured once and then corrected, or absorbed into a covariate. A bias whose sign depends on the acquisition cannot, because there is no stable quantity to correct for, and an analyst comparing FA across studies processed with different software cannot predict even the direction of the discrepancy.

All three fits used identical input data, identical gradient tables, one shared brain mask, and one shared volume subset, so the effect must arise in the tensor fitting itself. All three were run with weighted linear least squares, but their weighting schemes, regularisation, and outlier handling differ, and those differences evidently interact with acquisition properties such as b-value, SNR, and the number of b = 0 volumes. We report this as an observation across two acquisitions. Identifying the mechanism would require a controlled comparison of the fitting routines, which is beyond the scope of this paper.

### Non-Physical Tensor Fits

The analysis also showed how often each toolkit returns values that are physically impossible — something no reading of the documentation would reveal. Fractional anisotropy is bounded to [0, 1] by definition and mean diffusivity must be positive; values outside these ranges mean the tensor fit returned negative eigenvalues, which unconstrained linear least squares allows.

**Table 3. Non-physical tensor fits within the white matter mask.** Counts of voxels violating the definition of each metric, with the percentage of the white matter mask in parentheses.

| Dataset | Metric | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|
| Stanford (n = 65,002) | FA > 1 | 261 (0.40%) | 178 (0.27%) | 0 (0%) |
| Stanford | MD ≤ 0 | 261 (0.40%) | 91 (0.14%) | 0 (0%) |
| Sherbrooke (n = 111,032) | FA > 1 | 4,404 (3.97%) | 2,252 (2.03%) | 0 (0%) |
| Sherbrooke | MD ≤ 0 | 3,016 (2.72%) | 603 (0.54%) | 0 (0%) |

The ordering is the same on both datasets: FSL produces the most non-physical fits, MRtrix3 roughly half as many, and DIPY none. DIPY's `TensorModel` did not return a single voxel with FA > 1 or MD ≤ 0 in either acquisition (20 and 3 voxels respectively exceeded the free-water diffusivity bound). What changes between datasets is the rate, not the ranking: Sherbrooke, which has one b = 0 volume against Stanford's ten, produced roughly ten times as many failed fits in both toolkits that allow them.

Their effect on correlation-based agreement is severe and easy to miss. Without the plausibility restriction, MRtrix3–DIPY MD agreement on the Stanford data appears to be r = 0.118 rather than r = 0.9965: Pearson correlation is dominated by extreme values, and a few hundred voxels carrying no shared signal are enough to swamp it. An analysis reporting r = 0.118 would conclude, wrongly, that two toolkits which agree to four significant figures are almost unrelated. Robust statistics are barely affected — excluding these voxels changes the MRtrix3–DIPY mean absolute error by less than 2%.

Two practical implications follow for anyone computing agreement statistics on tensor-derived maps. First, agreement statistics computed on raw tensor-derived maps without a physical plausibility check can be badly misleading, and the appropriate diagnostic is to count and inspect the inadmissible voxels rather than discard them silently. Second, the number of failed tensor fits is itself a usable quality indicator that differentiates toolkits, and it is sensitive to acquisition design — particularly to the number of b = 0 volumes.

### Shell Selection

A methodologically important asymmetry was identified in shell selection for DTI fitting. FSL `dtifit` and MRtrix3 `dwi2tensor` include all available b-value shells by default, whereas DIPY's `TensorModel` requires the user to explicitly select the shell used for fitting. For the Stanford HARDI single-shell dataset this has no practical consequence. For multi-shell data such as the HCP protocol (b = 1000/2000/3000 s/mm²), applying the single-tensor model to all shells simultaneously violates the monoexponential signal decay assumption; the resulting FA maps will differ from those obtained using only the b = 1000 shell. This is a non-trivial methodological difference that is rarely acknowledged in published methods sections and is highlighted explicitly in the dMRI Rosetta Stone Stage 4 interface.

### The environment in practice

Figure 2 shows the interface at the tensor-fitting stage. Each stage presents one tab per toolkit; the selected tab shows the exact command, runs it on the loaded dataset, streams the output, and renders the resulting maps. Commands are shown in full and with relative paths, so any of them can be copied and run outside the platform unchanged — the environment is a convenience, not a dependency, and nothing reported here requires it.

Runtimes are indicative rather than benchmarked, observed on one machine (macOS 14, Apple Silicon, 16 GB RAM; Docker Desktop with 8 GB allocated) on which the `linux/amd64` image runs under emulation; a native x86-64 host should be faster. Every stage of the comparison completes in a few minutes on the full 160-volume Stanford acquisition. The exception is eddy-current correction, which takes 35-45 minutes on a single core, but this falls outside the comparison reported here, which applies no preprocessing.

## Discussion

### Methodological Transparency and Reproducibility

dMRI Rosetta Stone contributes to methodological transparency at two levels. At the surface level, it makes implementation differences between toolkits visible and discussable: that FSL `eddy_cpu` corrects eddy current distortions, signal dropout, and outlier replacement in addition to head motion, whereas DIPY `motion_correction` performs rigid-body registration only, is a distinction that is rarely stated explicitly in published methods sections but is immediately apparent in the side-by-side interface. Similarly, the absence of CSD in FSL — a non-trivial limitation for acquisitions with crossing fibres — is not always apparent to an analyst working only in FSL.

At a deeper level, the agreement analysis tests something the field generally assumes but rarely checks: that FSL, MRtrix3, and DIPY produce interchangeable DTI scalar metrics when given the same data under controlled conditions. Our results support this only in part.

For MRtrix3 and DIPY the assumption holds comfortably, and it holds on both acquisitions. Agreement of r = 0.9990 and 0.9966 for FA, and r = 0.9965 and 0.9991 for MD, with limits of agreement an order of magnitude narrower than within-tract biological variability, means that a study analysed in one of these toolkits could have been analysed in the other with no material change to its tensor-derived results.

For FSL it does not hold in the form usually assumed, and using two datasets is what made this visible. Had we analysed Stanford alone, we would have reported an offset of roughly 4% in FA and 5% in MD and concluded that a fixed, correctable bias separates FSL from the other two. Sherbrooke contradicts that reading: the MD offset keeps its direction but quadruples in size, and the FA offset changes sign — FSL FA is lower than MRtrix3 and DIPY on one acquisition and higher on the other.

This is harder to deal with than a fixed bias. A constant offset can be measured once and then corrected or acknowledged. An offset whose sign depends on the acquisition cannot, and an analyst pooling FA across studies processed with different software cannot predict its direction, let alone its size, without re-running the comparison on their own data.

Two things keep this in proportion. Within a single study processed consistently, the offset moves every subject the same way, so it is unlikely to create a spurious group difference; the risk is in cross-study and multi-site work, normative reference ranges, and meta-analyses of absolute diffusivity. And toolkit choice at the fitting stage is a smaller source of variance than acquisition protocol or preprocessing. It is not, however, negligible, and an effect that changes sign between two ordinary open datasets is worth stating in a methods section.

The shell selection asymmetry is a second example of implementation differences that matter in practice: FSL and MRtrix3 fit all available shells by default, DIPY requires an explicit choice, and for multi-shell data this changes the resulting FA maps. Others have shown that pipeline-level choices introduce non-trivial variability in dMRI metrics (Bhagwat et al., 2021; Richie-Halford et al., 2022). What the platform adds is that such differences can be observed directly rather than only read about.

### Why existing platforms do not answer this question

Infrastructure for running dMRI analyses across toolkits already exists. Brainlife.io provides cloud execution with provenance tracking for applications drawn from several packages, including FSL and MRtrix3 (Avesani et al., 2019), and pipeline suites such as QSIPrep assemble multi-toolkit workflows into reproducible end-to-end analyses. Both are more capable than the environment used here for the work they were designed for.

Neither, however, is arranged for the comparison this paper reports. Their purpose is to process a dataset well, which means selecting one implementation per step and running it; ours is to hold every step but one fixed and vary the remaining one deliberately, which is the opposite arrangement. Running a controlled comparison on such a platform would mean working against its design rather than with it. That is the gap the environment described in Section 2.3 fills, and it is a narrow one: not a better way to analyse diffusion data, but a way to ask which implementation is responsible when two analyses of the same data disagree.

### Scalability

The platform and the benchmark scale differently, and it is worth separating them.

The interactive application is deliberately single-subject and single-machine. Each pipeline stage runs one command on one dataset in a container sized for a laptop, because its purpose is to isolate one operation at a time rather than to process a cohort. Within that scope it scales adequately. All stages except eddy correction complete in under three minutes on the full 160-volume Stanford acquisition on an Apple M2 with 8 GB allocated to Docker; eddy correction is the single bottleneck at 35–45 minutes on one CPU core, which the demo subsample mode reduces to 2–4 minutes for teaching purposes. Memory scales with volume count and matrix size, and the largest dataset used here (Sherbrooke, 193 volumes at 128 × 128 × 60) ran comfortably within the same allocation. The platform is explicitly not a cohort-processing pipeline, and users with that requirement should reach for a purpose-built workflow such as QSIPrep or a Nipype-based pipeline; nothing in this platform competes with those, and the Concepts and Reference module says so.

The benchmark scripts scale further, and were designed to. Adding a dataset requires one fetcher entry and two commands, which is how the Sherbrooke replication was produced; outputs are written per subject so that datasets accumulate rather than overwrite one another, and the `--shell` option makes multi-shell acquisitions tractable without hand-editing gradient tables. The cost per dataset is one tensor fit per toolkit, which is minutes rather than hours. This matters for the finding reported above: establishing how the FSL divergence depends on acquisition would require tens of datasets rather than two, and that is a matter of compute time and data access rather than of software redesign. We regard extending this benchmark as the most valuable use of the codebase beyond teaching.

The principal barrier to scale is not computational but distributional — the container is large, and the following section addresses that.

### Limitations

The platform currently supports single-subject analysis only; multi-subject group analysis beyond the synthetic TBSS demonstration requires real group data not included in the repository. The demo subsample mode for eddy correction is not suitable for quantitative analysis. The Docker image occupies approximately 17.6 GB uncompressed (approximately 5.6 GB as distributed layers) and requires approximately 15 minutes to build, which may be prohibitive in low-bandwidth settings; a pre-built image on a public container registry would mitigate this. GPU-accelerated MRtrix3 operations are not available in the current CPU-only Docker configuration.

The inter-tool benchmark reported here carries its own limitations, and they bound what may be concluded from the FSL divergence we describe. It rests on one subject from each of two datasets. Two acquisitions are enough to demonstrate that the FSL discrepancy is not a fixed, correctable bias — a single dataset would have suggested exactly the opposite — but they are not enough to characterise how it varies, to attribute it to specific acquisition properties such as b-value, SNR, or the number of b = 0 volumes, or to place a confidence interval around it. The benchmark isolates the tensor-fitting stage deliberately, applying no denoising or eddy-current correction, so the numbers characterise one pipeline step rather than an end-to-end analysis; whether the divergence persists, grows, or is absorbed after realistic preprocessing is untested. It compares only FA and MD under each toolkit's default weighted-least-squares configuration, and each toolkit exposes fitting options that were not explored. Establishing how the FSL divergence depends on acquisition, and identifying its algorithmic origin, would require a dedicated multi-subject study spanning several protocols — work that this platform is well suited to support but does not itself constitute.

Finally, the platform has not yet been evaluated in a formal user study; a structured assessment of learning outcomes in a workshop setting would strengthen the evidence base for its educational value.

### Future Directions

The most useful extension is more data. Two acquisitions establish that the FSL offset is not fixed but cannot describe how it varies, and the design makes adding a dataset cheap: one fetcher entry and two commands. Multi-subject collections on OpenNeuro would allow the offset to be characterised against acquisition parameters — b-value, angular sampling, SNR, and the number of b = 0 volumes, which our two datasets already suggest matters for fit failure rate.

Three further extensions follow from the design rather than from the results. The comparison currently covers the tensor fit; the same controlled arrangement could be applied to the preprocessing steps deliberately excluded here, one at a time, to attribute pipeline-level variability to its components. It could also be extended beyond the tensor to models with more parameters, such as constrained spherical deconvolution or NODDI, where implementations diverge more and the scope for disagreement is correspondingly larger. Finally, each toolkit exposes fitting options that were left at their defaults; whether the FSL divergence persists under non-default settings is an open and directly testable question.

## Conclusion

Given identical input volumes, identical gradient tables, one shared brain mask and no preprocessing, MRtrix3 and DIPY produce tensor metrics that are interchangeable in practice: agreement exceeded r = 0.996 for both fractional anisotropy and mean diffusivity on both acquisitions, with limits of agreement an order of magnitude narrower than within-tract biological variability. FSL diverged from both.

The FSL divergence does not behave as a fixed bias. Mean diffusivity was lower on both datasets, but by 5% on one and 19% on the other, and the anisotropy offset reversed sign between them. An offset whose sign depends on the acquisition cannot be removed by a scaling factor, because there is no stable quantity to correct for. Within a single study processed consistently this is unlikely to create a spurious group difference, since every subject moves the same way; the exposure is in cross-study and multi-site comparison, in normative reference ranges, and in meta-analyses of absolute diffusivity.

A second result is methodological rather than biological. Unconstrained linear fitting returns physically impossible values — fractional anisotropy above one, mean diffusivity below zero — in up to 4.0% of white matter voxels in FSL and 2.0% in MRtrix3, and in none in DIPY. These voxels barely move a robust statistic such as mean absolute error, but they dominate a correlation: left in place, they reduce an apparent mean diffusivity agreement from r = 0.997 to r = 0.118. Agreement computed on raw tensor maps without a plausibility check can therefore be wrong by an amount that changes the conclusion, and the count of inadmissible voxels is worth reporting in its own right as a quality indicator that distinguishes implementations.

These results rest on one subject per dataset and characterise the tensor-fitting stage alone. Two acquisitions are enough to show that the FSL offset is not fixed, which is the claim made here, but not enough to describe how it varies with acquisition parameters. Establishing that would require tens of datasets rather than two. The environment and analysis scripts released with this paper are intended to make that extension a matter of compute time rather than of software engineering.

## CRediT authorship contribution statement

**Busra Mutlu:** Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, Visualization, Writing - original draft, Writing - review and editing.

## Declaration of competing interest

The author declares that she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Funding

[TO COMPLETE: name the funder and grant number, or state that this research received no specific grant from funding agencies in the public, commercial, or not-for-profit sectors.]

## Declaration of generative AI and AI-assisted technologies in the writing process

[TO COMPLETE OR DELETE — see the note accompanying this manuscript. If generative AI was used to assist with drafting or editing, Elsevier requires a statement here naming the tool and describing its use, and confirming that the author reviewed and edited the output and takes full responsibility for the content of the publication.]

## Data availability

The complete source code, Dockerfile, and documentation are openly available at https://github.com/happybrotherhood/dmri-rosetta-stone under an MIT licence. The exact version reported here is archived on Zenodo as v1.0.0, doi:10.5281/zenodo.22106455; the concept DOI doi:10.5281/zenodo.22106454 always resolves to the most recent version. Both datasets analysed — Stanford HARDI and Sherbrooke 3-shell — are distributed openly by the DIPY project at https://dipy.org and are retrieved automatically by `scripts/fetch_sample_data.py`. No registration or credentials are required to reproduce any result presented here, and the four commands that regenerate every reported value are given at the end of the Materials and Methods.

## Acknowledgements

[TO COMPLETE OR DELETE: supervisors, colleagues, computing resources.]

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

Jeurissen B, Tournier JD, Dhollander T, Connelly A, and Sijbers J (2014) Multi-tissue constrained spherical deconvolution for improved analysis of multi-shell diffusion MRI data. *NeuroImage* 103, 411–426. doi: 10.1016/j.neuroimage.2014.07.061

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

**Table 2. Quantitative inter-tool agreement for brain masks and DTI scalar metrics, on two independent open datasets.** Brain mask agreement assessed by Dice similarity coefficient (DSC) between each pair of per-tool brain extractions. DTI metric agreement assessed over white matter voxels (FA > 0.2 in all three tools) by Pearson correlation coefficient (r), mean absolute error (MAE), Bland–Altman mean bias, and 95% limits of agreement (LoA). All three tensor fits used the same shared brain mask and the same volume subset, so metric differences reflect tensor fitting rather than masking or shell selection. MD in µm²/ms. Statistics are restricted to voxels physically admissible in both tools of the pair (FA ∈ [0, 1]; 0 < MD ≤ 3.0 × 10⁻³ mm²/s); per-tool counts of excluded voxels are reported in Table 3. All values generated by `scripts/compute_fa_comparison.py`.

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

**Table 3. Non-physical tensor fits within the white matter mask.** Counts of voxels violating the definition of each metric, with the percentage of the white matter mask in parentheses.

| Dataset | Metric | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|
| Stanford (n = 65,002) | FA > 1 | 261 (0.40%) | 178 (0.27%) | 0 (0%) |
| Stanford | MD ≤ 0 | 261 (0.40%) | 91 (0.14%) | 0 (0%) |
| Sherbrooke (n = 111,032) | FA > 1 | 4,404 (3.97%) | 2,252 (2.03%) | 0 (0%) |
| Sherbrooke | MD ≤ 0 | 3,016 (2.72%) | 603 (0.54%) | 0 (0%) |

## Figure Captions

**Figure 1.** Design of the inter-tool comparison. Both datasets are open and require no credentials. *Left:* brain extraction is compared with each tool run on the input its algorithm is designed to consume — `bet` on the mean b = 0 image, `dwi2mask` on the full DWI series, `median_otsu` on the full series with the b = 0 volumes indexed — so the Dice coefficients reflect the difference a user would encounter in practice. *Right:* tensor fitting is compared with every tool given identical input: one brain mask, one volume subset comprising b = 0 and a single non-zero shell, and no preprocessing. Holding these constant isolates the fitting stage, which is what the metric comparison is intended to measure. Statistics are then restricted to physically admissible voxels, without which a few hundred failed fits dominate the correlation. Toolkit colours are consistent across Figures 1, 3 and 4. The diagram is generated by `scripts/make_fig1_design.py`.

**Figure 2.** The Stage 4 (DTI Fitting) user interface, representative of all seven pipeline stages, shown on the Stanford HARDI dataset. The sidebar (left) reports the resolved dataset — detected shells and volume count — and lists the eight pipeline pages; a collapsible Tool status panel reports which toolkit binaries are present in the current environment. The main panel presents three tabs, one per toolkit (FSL `dtifit`, MRtrix3 `dwi2tensor`, DIPY `TensorModel`). The selected tab shows the exact executable command with syntax highlighting, the outputs that command will produce, a Run button that submits it via Python `subprocess` and streams stdout and stderr live, and the resulting metric maps rendered below (FSL FA and MD shown here). The collapsible Why? section, further down the page, provides biological and mathematical context and guidance on when to prefer the current toolkit.

**Figure 3.** Quantitative inter-tool DTI metric agreement, shown for the Stanford HARDI dataset (the equivalent panel for Sherbrooke 3-shell is provided as Supplementary Figure S1; both are generated by the same script). **(a)** FA maps (central axial slice) from FSL `dtifit`, MRtrix3 `tensor2metric`, and DIPY `TensorModel`, applied to identical input volumes with one shared brain mask. **(b)** Voxelwise FA scatter plots for each cross-tool pair over white matter voxels (FA > 0.2 in all three tools) with Pearson r, mean absolute error, and identity line. **(c)** Bland–Altman plots for each cross-tool pair showing the distribution of voxelwise FA differences against their mean; horizontal lines indicate the mean difference (bias) and ±1.96 SD limits of agreement. The MRtrix3–DIPY pair is tightly clustered about the identity line, whereas both FSL pairings show systematic bias and markedly wider scatter. Voxels with physically inadmissible values are excluded, as described in Methods.

**Figure 4.** Brain extraction comparison on the Stanford HARDI dataset (the Sherbrooke equivalent is provided as Supplementary Figure S2). The b = 0 mean image (greyscale) with brain mask overlaid in red, produced by FSL `bet` (left, 203,984 voxels), MRtrix3 `dwi2mask` (centre, 167,950 voxels), and DIPY `median_otsu` (right, 187,948 voxels) from the same input volume. Dice similarity coefficients for each pair are reported in Table 2. Two differences are visible: the extent of cortical boundary coverage, and the treatment of the lateral ventricles, which DIPY `median_otsu` excludes while FSL `bet` and MRtrix3 `dwi2mask` retain. These reflect the distinct tissue models employed by each algorithm.

**Supplementary Figure S1.** As Figure 3, for the Sherbrooke 3-shell dataset (b = 0 + b = 1000 s/mm² subset).

**Supplementary Figure S2.** As Figure 4, for the Sherbrooke 3-shell dataset.
