# What actually differs between diffusion MRI toolkits: the estimator, not the software

**Busra Mutlu**¹\*

¹ Department of Neuroimaging, King's College London, London, United Kingdom

\* **Corresponding author.** Busra Mutlu, Department of Neuroimaging, King's College London, De Crespigny Park, London SE5 8AF, United Kingdom. E-mail: [KCL EMAIL]

## Abstract

**Background.** Differences between diffusion MRI toolkits are commonly attributed to the software, without asking which component is responsible.

**New method.** We compared tensor fits from FSL, MRtrix3 and DIPY on two open datasets with every input held constant, then varied the estimator rather than the toolkit, and validated each arm against a phantom with known eigenvalues.

**Results.** At each toolkit's default the three appeared to disagree — an artefact of unmatched estimators, since MRtrix3 iterates its reweighting twice and FSL performs ordinary least squares unless asked otherwise. Matched to plain weighted least squares, FSL and MRtrix3 agree exactly (r = 1.0000, mean absolute error 0.0000). DIPY differs because it weights by a predicted rather than a measured signal; supplying measured-signal weights cuts its disagreement with FSL from 0.0222 to 0.0003 FA units and 0.0468 to 0.0035. Switching FSL between its own default and `--wls` changed FA by more than replacing FSL with another toolkit, by 0.12 to 0.26 standard deviations of white matter FA. Five estimators across three toolkits sat apart from the measured-signal weighted fit. Against phantom ground truth every arm recovered FA to within 0.003, so none is inaccurate.

**Comparison with existing methods.** Earlier work measures variability across pipelines and reports it as software-dependent. Isolating the fit and manipulating the estimator shows the dependence is on the weighting scheme and defaults, not the implementation.

**Conclusions.** Implementations of the same estimator agree to numerical precision. What differs is the estimator each applies by default, which the command a user runs does not reveal. Reporting the toolkit is insufficient; the estimator and its settings should be reported.

**Keywords:** diffusion MRI; tensor fitting; weighted least squares; reproducibility; benchmarking; software defaults

## Introduction

Diffusion magnetic resonance imaging (dMRI) is the principal non-invasive technique for probing white matter microstructure and structural connectivity in the living human brain (Basser et al., 1994; Jones, 2010). By encoding the directional displacement of water molecules, dMRI provides access to biophysical indices — including fibre orientation, axon density, and myelin integrity — that are invisible to conventional anatomical MRI (Beaulieu, 2002). Applications span fundamental neuroscientific questions about brain organisation and inter-individual variability, as well as clinical contexts including the characterisation of white matter alterations in neurodegenerative diseases, psychiatric conditions, and neurodevelopmental disorders (Catani and Thiebaut de Schotten, 2008; Jones, 2010).

The dMRI analysis ecosystem is dominated by three major software packages. FSL (FMRIB Software Library), developed at the University of Oxford, provides robust preprocessing, DTI fitting, and voxelwise group analysis via the Tract-Based Spatial Statistics (TBSS) pipeline (Smith et al., 2004; Jenkinson et al., 2012). MRtrix3, developed at The Florey Institute of Neuroscience and Mental Health, specialises in constrained spherical deconvolution (CSD) and high-fidelity fibre orientation modelling (Tournier et al., 2019). DIPY (Diffusion Imaging in Python) offers a flexible, Python-native implementation of the full dMRI pipeline and is widely used when algorithmic transparency or custom extensions are required (Garyfallidis et al., 2014).

Despite their complementary strengths, these toolkits present a significant practical barrier. Each employs distinct command-line syntax, file format conventions, and — in several cases — different terminology for the same operation. For example, brain extraction is called `bet` in FSL, `dwi2mask` in MRtrix3, and `median_otsu` in DIPY. Mean diffusivity is reported as `MD` in FSL, `ADC` in MRtrix3, and `md` in DIPY. These surface-level differences cause genuine confusion for researchers trained in one ecosystem who attempt to read, reproduce, or extend work conducted in another.

A more substantive concern is methodological reproducibility. Published dMRI studies rarely justify their choice of software, and it is not always clear whether reported group differences in white matter metrics reflect genuine biological effects or implementation-level differences between tools. Software-specific choices — brain masking algorithm, denoising method, tensor fitting algorithm — can introduce non-trivial variability in derived metrics such as fractional anisotropy (FA) and mean diffusivity (MD), and this has been demonstrated at the level of whole pipelines (Bhagwat et al., 2021; Richie-Halford et al., 2022).

Such studies leave a narrower question open: when the *only* thing that differs is the software performing the tensor fit, how much do the toolkits disagree, and what inside the software is responsible? Answering the first part requires holding every other input fixed. Answering the second requires going further, and manipulating the candidate cause directly.

We built a containerised environment in which all three toolkits run on byte-identical data, used it to run the controlled comparison, and then followed the difference to its source. The instrument and the measurement are reported together because neither is much use alone.

Four questions are addressed. First, how far do FSL, MRtrix3 and DIPY agree on fractional anisotropy and mean diffusivity given identical input? Second, are the toolkits in fact running the same estimator, or does each apply a different one by default? Third, if the estimator is matched, does the disagreement persist? Fourth, when the toolkits disagree, is any of them wrong — a question that requires a ground truth the real data cannot supply.

Each of the estimator choices we identify is documented by the project that made it. MRtrix3 states that `dwi2tensor` iterates its reweighting twice; DIPY cites Chung et al. (2006) for its weighting; FSL's `--wls` flag is described in its own help text. What is not documented anywhere is the consequence: that these choices, rather than the implementations, account for the differences the field attributes to software; that they can be removed by a single argument; and that none of the estimators involved is inaccurate. Reading three manuals establishes that the components differ. It does not establish which difference matters, by how much, or whether any of them is wrong — and those are the questions a researcher choosing a toolkit actually faces.

We report the comparison on two open datasets acquired at different sites under different protocols, on a synthetic phantom whose generating eigenvalues are known, and under a direct manipulation of the weighting scheme. Every value can be regenerated from openly available data.

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

### Matching the estimator

The comparison above compares toolkits at their usual settings, which is what a user encounters, but it does not guarantee that the same estimator is being applied. MRtrix3 `dwi2tensor` performs weighted least squares followed by two iterations of reweighting by default. To place all three on plain WLS we repeated the comparison with `dwi2tensor -iter 0`, which stops after the first weighted fit, alongside FSL `dtifit --wls` and DIPY `fit_method="WLS"`. Both configurations are reported: the default arms because they describe practice, the matched arms because they isolate the estimator.

### Manipulating the weighting scheme

MRtrix3 documents its first stage as weighting by the empirical signal intensities; DIPY documents its weights as the squared signal predicted by an initial ordinary least-squares fit, following Chung et al. (2006). To test whether this accounts for the residual difference we used DIPY's facility for user-supplied weights, running the same DIPY code twice on the same data — once with its default predicted-signal weights, once with the measured signal — and compared each against the FSL fit. Signals were floored at unity before both fits so that the weighted design matrix stays non-singular where a voxel reads zero; both arms received identical clipped data.

### Accuracy against a known ground truth

Agreement between toolkits cannot say whether any of them is accurate. We therefore fitted a synthetic phantom whose generating eigenvalues are known: an isotropic region with eigenvalues 0.9, 0.9, 0.9 × 10⁻³ mm²/s (FA = 0, MD = 0.90 µm²/ms) and a single-fibre region with 1.4, 0.35, 0.35 × 10⁻³ mm²/s (FA = 0.7071, MD = 0.70 µm²/ms), at an SNR of approximately 30. A crossing-fibre region is present in the phantom but excluded from scoring, since no single tensor is correct there by construction. Voxels within two of a region boundary were also excluded, as they mix tissue types. Bias and root-mean-square error against truth are reported for each arm.

### Sensitivity to preprocessing

The comparison applies no denoising or eddy-current correction, so that the fit is examined at a defined starting point rather than after an arbitrary preprocessing choice. To test whether the findings survive realistic preprocessing, we repeated the whole comparison on MP-PCA denoised data. Denoising was performed once, with MRtrix3 `dwidenoise`, on the full series before shell selection, and the denoised data given to all three toolkits. Denoising is thereby held constant and the estimator remains the only variable.

Giving each toolkit its own denoiser would not be a more faithful alternative. FSL provides none, so it would fit noisier data than the other two and any difference could no longer be attributed to the fit. Eddy-current correction was not tested; it corrects geometric distortion, whereas the finding under examination concerns eigenvalue estimation, which is driven by noise.

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

### The apparent difference between toolkits

Run as a user would normally run them — FSL `dtifit --wls`, MRtrix3 `dwi2tensor` at its default, DIPY `fit_method="WLS"` — the three toolkits do not agree equally well with one another (Table 2). MRtrix3 and DIPY were close on both datasets (FA r = 0.9990 and 0.9966), while FSL sat apart from both (FA r = 0.9604-0.9652 on Stanford, 0.8897-0.9157 on Sherbrooke). Read at face value this says FSL is the odd one out.

Bland-Altman analysis (Figure 3c) showed systematic offset rather than symmetric scatter in every FSL pairing. The offset did not behave consistently: FSL mean diffusivity was lower on both datasets, by 0.033 µm²/ms on Stanford and 0.127 on Sherbrooke, while the fractional anisotropy offset changed sign between them, FSL being lower on Stanford by 0.018 and higher on Sherbrooke by 0.014.

An offset that reverses sign between two ordinary acquisitions is difficult to explain as an implementation difference, and that inconsistency prompted the checks reported next.

### The toolkits were not running the same estimator

MRtrix3's `dwi2tensor` does not perform plain weighted least squares by default. Its documentation states that it fits in two stages: weighted least squares using weights taken from the empirical signal intensities, followed by iteratively reweighted least squares in which the weights come from the signal predicted by the previous iteration, with two such iterations by default. FSL `--wls` and DIPY `fit_method="WLS"` perform a single weighted fit. The comparison above therefore contrasted two IWLS iterations against plain WLS, and attributed the result to the toolkit.

Repeating the comparison with MRtrix3 constrained to plain WLS (`-iter 0`) reverses the grouping entirely (Table 3). FSL and MRtrix3 then agree exactly: r = 1.0000 for both FA and MD on both datasets, with mean absolute error 0.0000 and a mean voxelwise difference of 1.1 × 10⁻⁴ FA units, which is numerical precision rather than agreement in the usual sense. MRtrix3 simultaneously moves away from DIPY, to r = 0.9602 on Stanford and 0.8895 on Sherbrooke — the same distance that had previously separated DIPY from FSL.

Two implementations of weighted least squares, written independently in different languages by different groups, return the same tensor. The apparent toolkit effect was an estimator effect.

### What separates DIPY is the source of the weights

DIPY remains apart from the other two even with MRtrix3 matched, and its documentation identifies why. Where MRtrix3's first stage weights the fit by the *measured* signal, DIPY follows the two-pass scheme of Chung et al. (2006): an ordinary least-squares fit is performed first, and the signal it *predicts* supplies the weights for the weighted fit. FSL's `--wls` agrees with MRtrix3 to numerical precision, so it uses measured-signal weights as well.

This divides the four arms into two families by weighting scheme rather than by software:

| Weights derived from | Arms |
|---|---|
| Measured signal | FSL `dtifit --wls`; MRtrix3 `dwi2tensor -iter 0` |
| Predicted signal | DIPY `fit_method="WLS"`; MRtrix3 `dwi2tensor` default (iterated twice) |

The grouping predicts every correlation observed: within the measured-signal family r = 1.0000, within the predicted-signal family r = 0.9990, and between families r ≈ 0.96.

We tested this directly rather than resting on the correspondence. DIPY accepts user-supplied weights, so the same DIPY code was run twice on the same data, once with its default predicted-signal weights and once with measured-signal weights, and each compared against the FSL fit (Table 4). Supplying measured-signal weights reduced the FA disagreement with FSL from 0.0222 to 0.0003 mean absolute error on Stanford and from 0.0468 to 0.0035 on Sherbrooke; for MD the reduction was from 0.0320 to 0.0001 and from 0.1224 to 0.0022 µm²/ms. The bias fell to within 0.0023 FA units of zero in both datasets.

Changing one argument inside a single toolkit removes almost all of the difference previously attributed to the choice between toolkits.

### The same toolkit disagrees with itself more than with another

FSL `dtifit` performs ordinary least squares unless `--wls` is passed. The comparison so far used `--wls`, to match the estimator the other toolkits apply; the default is what most users run. Fitting the same data both ways places the size of the between-toolkit differences in context (Table 7).

Within FSL, switching between its default and `--wls` changed FA by a mean absolute 0.0176 on Stanford and 0.0505 on Sherbrooke. Between FSL `--wls` and MRtrix3 `-iter 0` — different software, different language, different developers — the mean absolute difference was 0.0000 on both.

One flag inside one program therefore produced a larger difference than replacing the program entirely. The same holds against DIPY: FSL's default sits 0.0191 and 0.0182 FA units from DIPY's WLS on the two datasets, comparable to the between-scheme gap already reported, but reached without changing toolkit at all.

On the phantom FSL's default recovers the truth about as well as the other arms, with FA bias +0.0028 against +0.0014 to +0.0022 for the weighted fits and a slightly higher RMSE of 0.0235 against 0.0209 to 0.0212 (Table 8). Ordinary least squares is a defensible estimator and is not being called incorrect here; the point is that it is a different one, selected by default, and that the choice is not recorded anywhere a reader of the methods section would see it.

### The effect is not confined to weighted least squares

Weighted least squares is one of several estimators the toolkits provide, and confining the comparison to it would leave open whether the pattern is an artefact of that choice. We therefore added DIPY's non-linear fit, which works on the signal rather than its logarithm, and RESTORE, which downweights outliers, and compared every arm against the reference established above — FSL `--wls`, which is numerically identical to MRtrix3 `-iter 0` (Table 7).

No estimator recovers the reference. On Stanford, mean absolute FA differences from it were 0.0219 (DIPY WLS), 0.0180 (NLLS), 0.0188 (RESTORE), 0.0244 (MRtrix3's default IWLS) and 0.0173 (FSL's default OLS); on Sherbrooke, 0.0465, 0.0376, 0.0392, 0.0451 and 0.0496. The spread across five distinct estimators, spanning three toolkits and both linear and non-linear fitting, is narrower than the gap between any of them and the measured-signal weighted fit.

This locates the effect more precisely than the initial contrast did. It is not that DIPY's implementation is unusual; it is that one specific estimator — weighted least squares with weights taken from the measured signal — sits apart from every other option we tested, and two toolkits reach it only when explicitly asked.

### How large is the effect

Absolute differences in fractional anisotropy are hard to weigh without a scale. Expressed against the standard deviation of FA across white matter voxels in the same data, the differences reported above run from 0.12 to 0.25 standard deviations (Table 7).

The within-FSL comparison is the clearest case: changing one flag moved FA by 0.12 standard deviations on Stanford and 0.26 on Sherbrooke. A shift of a quarter of a standard deviation, produced by a command-line argument that is not recorded in any methods section we are aware of, is of the same order as effects that dMRI studies are designed to detect between groups.

### Neither weighting is wrong

That two estimators disagree does not establish that either is inaccurate. On the synthetic phantom, where the eigenvalues generating the signal are known exactly, all four arms recover them closely (Table 7). In the single-fibre region, against a true FA of 0.7071 and true MD of 0.7000 µm²/ms, the measured-signal arms returned FA biased by −0.0021 and MD by −0.0050, and the predicted-signal arms FA by +0.0014 to +0.0022 and MD by +0.0017 to +0.0020. Root-mean-square errors were 0.021 for FA and 0.018 for MD in every arm.

The two families therefore bracket the truth, one slightly low and one slightly high, and the gap between them on clean data is about 0.004 FA units. On real data the same two families differ by 0.015 to 0.020 FA units, four to five times more. The estimators are not inaccurate; they respond differently to what real data contains and the phantom does not.

In the isotropic region, where the true FA is zero, every arm returned approximately 0.086. This is the familiar noise floor of anisotropy estimates and is not a toolkit property; it appeared identically in all four.

### Sensitivity to denoising

If the difference between weighting schemes is driven by noise, denoising should reduce it. MP-PCA denoising was applied once with MRtrix3 `dwidenoise` and the denoised series given to all three toolkits, leaving the estimator as the only variable (Table 8).

The differences shrink substantially but do not close. The FSL-to-MRtrix3-default MD offset fell from 0.033 to 0.019 µm²/ms on Stanford and from 0.127 to 0.049 on Sherbrooke, reductions of 44% and 61%. The FA offset fell correspondingly, and its sign still reversed between the two datasets, from −0.013 on Stanford to +0.003 on Sherbrooke. Agreement within the predicted-signal family was unaffected (MRtrix3 default against DIPY, r = 0.9990 before and after).

Roughly half of the between-family difference on real data is therefore attributable to noise, consistent with the phantom result that the two schemes differ little when noise is well behaved.

### Non-physical tensor fits

Unconstrained linear fitting can return negative eigenvalues, which produce fractional anisotropy above one and mean diffusivity below zero. Counts differ markedly between arms (Table 9). DIPY returned no such voxel in any run — two datasets, with and without denoising. FSL and MRtrix3 both returned them: on unprocessed data, 0.40% and 0.27% of white matter voxels on Stanford, and 3.97% and 2.03% on Sherbrooke.

Which of the two produces more is not stable. On unprocessed data FSL produced more than MRtrix3 in both datasets, but after denoising the order reversed on Stanford, MRtrix3 rising slightly to 0.29% while FSL fell to 0.23%. The robust statement is the one that held throughout: DIPY produced none, and the other two produced them at a rate that depends on both the acquisition and the preprocessing.

The rate tracks acquisition quality. Sherbrooke, with a single b = 0 volume against Stanford's ten, produced roughly ten times as many failed fits in every arm that admits them.

These voxels barely move a robust statistic — excluding them changes mean absolute error by under 2% — but they dominate a correlation. Computed without a plausibility restriction, MRtrix3-DIPY MD agreement on Stanford appears to be r = 0.118 rather than 0.9965. Agreement statistics computed on raw tensor maps can therefore be wrong by an amount that changes the conclusion.

### Brain extraction

Brain masks produced by FSL `bet`, MRtrix3 `dwi2mask` and DIPY `median_otsu`, each run on the input its algorithm expects, overlapped at Dice coefficients of 0.9009 to 0.9277 on Stanford and 0.9058 to 0.9668 on Sherbrooke (Table 2), with no pair below 0.90.

Pairwise Dice conceals how differently the algorithms behave. On Stanford the mask volumes were 203,984 voxels (FSL), 187,948 (DIPY) and 167,950 (MRtrix3), a spread of 21% between largest and smallest despite every pairwise coefficient exceeding 0.90. The ordering is not stable either: on Sherbrooke the volumes were 199,249 (MRtrix3), 188,717 (FSL) and 186,450 (DIPY), a spread of 7%, with MRtrix3 moving from the most conservative mask on one dataset to the most inclusive on the other.

Disagreements concentrate at the cortical boundary and, distinctively, at the lateral ventricles (Figure 4), which DIPY `median_otsu` excludes and the other two retain. A mask that includes ventricles admits high-diffusivity, near-isotropic voxels into any subsequent group statistics.

## Discussion

### What the toolkit label does and does not tell you

The result that organises the others is that FSL and MRtrix3, given the same estimator, return the same tensor to numerical precision. Two independent implementations — different languages, different groups, different decades — agree at r = 1.0000 with a mean voxelwise difference of about 10⁻⁴ FA units. Implementation quality is not the variable.

What varies is which estimator each toolkit applies when the user does not specify one. MRtrix3 ships two iterations of reweighted least squares; FSL performs ordinary least squares unless `--wls` is passed; DIPY performs a single weighted fit but derives the weights from a preliminary OLS prediction rather than from the measured signal. None of this appears in the command a user types. `dwi2tensor dwi.mif tensor.mif` and `dtifit -k data -o out ...` look like the same operation described in two dialects, which is how the field generally treats them, and they are not.

The comparison within FSL makes the size of this plain. Changing one flag in one program moved FA by 0.0176 and 0.0505 mean absolute units on the two datasets, while replacing that program with MRtrix3 at a matched estimator moved it by 0.0000. Whatever "software-related variability" denotes, it is not a property of the software.

Expressed on a scale that can be weighed, those shifts are 0.12 and 0.26 standard deviations of white matter FA. That is not a rounding difference. It is the same order as the group effects dMRI studies are powered to detect, produced by an argument that appears in no methods section we have read. Widening the comparison to five estimators across three toolkits, linear and non-linear, does not change the picture: every one of them sits apart from the measured-signal weighted fit, and the spread among them is smaller than their common distance from it.

This reframes what "software-related variability" means in dMRI. Reported differences between toolkits are real, and our first analysis reproduced them, but they are not differences between codebases. They are differences between statistical estimators that happen to be bundled as defaults. The distinction matters because the two have different remedies: a codebase difference would require the developers to act, whereas an estimator difference can be removed by the analyst, in our case with a single command-line argument.

### Neither scheme is wrong, and that is the useful part

The phantom shows that both weighting schemes recover known eigenvalues, one marginally low and one marginally high, with the gap between them about 0.004 FA units on clean data. Neither can be called incorrect, and we do not recommend one over the other.

That makes the finding more awkward for practice rather than less. If one scheme were wrong it could be deprecated. Because both are defensible, both will persist, and studies analysed in different toolkits will continue to differ by an amount that is small within a study and not small across studies. On real data the gap grows to 0.015-0.020 FA units, four to five times the phantom value, and denoising removes only about half of it. The remainder reflects properties of real data — noise structure, artefacts, partial volume — that the two schemes weight differently.

For a single study processed consistently the practical exposure is limited: every subject is displaced in the same direction. The exposure is in pooling. Normative reference ranges, multi-site studies, and meta-analyses of absolute diffusivity all combine values whose estimator is usually unstated and, in our reading of methods sections, usually unknown to the authors.

### The reporting problem

Methods sections routinely record the toolkit and version. On the evidence here that is the wrong level of description. Two studies both reporting "MRtrix3 3.0.4" may have used different estimators if one passed `-iter 0`; two studies reporting different toolkits may have used the same one. The toolkit name is neither necessary nor sufficient to reconstruct what was computed.

What would suffice is short: the estimator, the weighting scheme, and any non-default fitting arguments. We would encourage journals and reporting checklists to ask for it, and we note that our own first analysis — which compared IWLS against WLS and concluded that one toolkit was aberrant — is an example of what happens when this information is absent.

### Non-physical fits as a quality indicator

DIPY returned no physically impossible tensor in any configuration tested, while FSL and MRtrix3 returned them at rates between 0.14% and 3.97% depending on acquisition and preprocessing. We report this without proposing a mechanism, and note that which of the two produces more is not stable: denoising reversed their order on one dataset.

The practical value lies less in ranking toolkits than in the diagnostic. The count of inadmissible voxels responds to acquisition quality — Sherbrooke's single b = 0 volume produced roughly ten times the rate of Stanford's ten — and is cheap to compute. It is also a trap: left in place these voxels reduced an apparent MD correlation from 0.997 to 0.118 while moving the mean absolute error by under 2%. Agreement statistics on tensor-derived maps should be computed only over voxels whose values are physically admissible, and the excluded count reported.

### Limitations

The real-data component rests on one subject from each of two datasets. This is sufficient for the central claim, which concerns whether two implementations of one estimator agree — a question that does not require a sample, since the answer was exact agreement. It is not sufficient to characterise how the between-scheme difference varies with acquisition, and we do not attempt to.

The comparison covers the tensor fit under default and matched settings, on unprocessed and denoised data. Eddy-current and motion correction were not applied, so the numbers describe two operating points rather than a complete pipeline. Only FA and MD were examined; the analysis does not extend to models with more parameters, where the scope for divergence is larger.

The phantom is a deliberately simple test: Gaussian noise, no artefacts, no partial volume, no motion. It establishes that neither weighting scheme is systematically inaccurate under favourable conditions. It cannot establish which behaves better under unfavourable ones, which is the question the real-data gap raises and which we leave open.

### Extensions

Adding datasets is cheap by design — one fetcher entry and two commands — and multi-subject collections would allow the between-scheme difference to be characterised against acquisition parameters rather than merely observed at two points. The same controlled arrangement applies to the preprocessing steps excluded here, taken one at a time, and to models beyond the tensor, where implementations diverge more. Each toolkit also exposes fitting options left at their defaults here; whether the between-scheme gap persists across them is directly testable.

## Conclusion

Given identical input, FSL and MRtrix3 constrained to the same estimator return the same diffusion tensor to numerical precision. The differences reported between diffusion MRI toolkits are not differences between implementations. They are differences between statistical estimators, distributed as defaults that the user's command does not reveal: MRtrix3 iterates its reweighting twice, DIPY derives its weights from a predicted rather than a measured signal, and FSL performs ordinary least squares unless asked otherwise.

Neither weighting scheme is wrong. Both recover known eigenvalues on a phantom to within 0.002 FA units, bracketing the truth from either side. On real data they diverge by four to five times that amount, about half of which denoising removes, and the residual difference is small within a study but not across studies.

The practical consequence is a reporting one. Recording the toolkit and version does not describe what was computed; recording the estimator and its settings does, and costs one line. Our own first pass through this comparison concluded that one toolkit was aberrant, on evidence that turned out to reflect an unmatched default — which is the clearest argument we can offer for making that line standard.

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

**Table 1. Tensor-fitting configurations compared.** The first three rows are each toolkit as a user would normally invoke it; the fourth places MRtrix3 on the same estimator as the other two. Weighting scheme as documented by each project.

| Arm | Command | Estimator | Weights derived from | Is it the default? |
|---|---|---|---|---|
| FSL, default | `dtifit` | OLS | unweighted | yes |
| FSL, weighted | `dtifit --wls` | WLS | measured signal | no |
| MRtrix3, default | `dwi2tensor` | WLS + 2 IWLS | predicted signal | yes |
| MRtrix3, matched | `dwi2tensor -iter 0` | WLS | measured signal | no |
| DIPY | `TensorModel(fit_method="WLS")` | WLS | predicted signal, from an initial OLS fit | yes |

**Table 2. Toolkits at their default settings.** Agreement over white matter voxels (FA > 0.2 in all three), with every input held identical. Pearson r, mean absolute error (MAE) and Bland-Altman mean bias. MD in µm²/ms. Statistics use only physically admissible voxels (FA in [0, 1]; 0 < MD ≤ 3.0 × 10⁻³ mm²/s). Mask DSC compares each pair of brain extractions, each tool run on the input its algorithm expects.

*Stanford HARDI (n = 65,002 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | MD r | MD MAE | MD bias |
|---|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 0.9024 | 0.9652 | 0.0247 | -0.0181 | 0.9402 | 0.0333 | -0.0330 |
| FSL vs. DIPY | 0.9277 | 0.9604 | 0.0228 | -0.0158 | 0.9368 | 0.0325 | -0.0322 |
| MRtrix3 vs. DIPY | 0.9009 | 0.9990 | 0.0029 | +0.0027 | 0.9965 | 0.0012 | +0.0009 |

*Sherbrooke 3-shell (n = 111,032 white matter voxels)*

| Comparison | Mask DSC | FA r | FA MAE | FA bias | MD r | MD MAE | MD bias |
|---|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 0.9058 | 0.9157 | 0.0460 | +0.0139 | 0.9020 | 0.1271 | -0.1271 |
| FSL vs. DIPY | 0.9668 | 0.8897 | 0.0504 | +0.0148 | 0.9012 | 0.1272 | -0.1272 |
| MRtrix3 vs. DIPY | 0.9163 | 0.9966 | 0.0059 | +0.0053 | 0.9991 | 0.0029 | -0.0009 |

**Table 3. The same comparison with the estimator matched.** MRtrix3 constrained to plain weighted least squares (`dwi2tensor -iter 0`), alongside FSL `dtifit --wls` and DIPY `fit_method="WLS"`. Compare with Table 2, where MRtrix3 ran its default of two reweighting iterations.

*Stanford HARDI*

| Comparison | FA r | FA MAE | FA bias | MD r | MD MAE | MD bias |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 1.0000 | 0.0000 | +0.0000 | 1.0000 | 0.0000 | +0.0000 |
| FSL vs. DIPY | 0.9601 | 0.0228 | -0.0158 | 0.9367 | 0.0325 | -0.0322 |
| MRtrix3 vs. DIPY | 0.9602 | 0.0228 | -0.0158 | 0.9366 | 0.0325 | -0.0322 |

*Sherbrooke 3-shell*

| Comparison | FA r | FA MAE | FA bias | MD r | MD MAE | MD bias |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 1.0000 | 0.0000 | +0.0000 | 1.0000 | 0.0000 | +0.0000 |
| FSL vs. DIPY | 0.8895 | 0.0505 | +0.0149 | 0.9013 | 0.1274 | -0.1274 |
| MRtrix3 vs. DIPY | 0.8895 | 0.0505 | +0.0149 | 0.9012 | 0.1274 | -0.1274 |

**Table 4. Manipulating the weighting scheme inside one toolkit.** The same DIPY code run twice on the same data, once with its default weights (squared signal predicted by an initial OLS fit) and once with measured-signal weights, each compared against the FSL `dtifit --wls` fit. MD in µm²/ms.

| Dataset | DIPY weights | FA r | FA MAE | FA bias | MD r | MD MAE | MD bias |
|---|---|---|---|---|---|---|---|
| Stanford | predicted (default) | 0.9662 | 0.0222 | +0.0152 | 0.9579 | 0.0320 | +0.0317 |
|  | measured (as FSL) | 0.9989 | 0.0003 | -0.0001 | 0.9982 | 0.0001 | +0.0001 |
| Sherbrooke | predicted (default) | 0.9173 | 0.0468 | -0.0201 | 0.9136 | 0.1224 | +0.1224 |
|  | measured (as FSL) | 0.9949 | 0.0035 | -0.0023 | 0.9962 | 0.0022 | +0.0022 |

**Table 5. The same toolkit against itself.** FSL `dtifit` at its default (ordinary least squares) compared with FSL `--wls`, and with the matched-estimator fits from the other toolkits. White matter voxels admissible in every arm.

| Dataset | Comparison | FA r | FA MAE | FA bias |
|---|---|---|---|---|
| Stanford | FSL `--wls` vs. FSL default (OLS) | 0.9649 | 0.0176 | +0.0016 |
|  | FSL `--wls` vs. MRtrix3 `-iter 0` | 1.0000 | 0.0000 | −0.0000 |
|  | FSL default (OLS) vs. DIPY WLS | 0.9921 | 0.0191 | −0.0171 |
| Sherbrooke | FSL `--wls` vs. FSL default (OLS) | 0.9069 | 0.0505 | +0.0166 |
|  | FSL `--wls` vs. MRtrix3 `-iter 0` | 1.0000 | 0.0000 | +0.0000 |
|  | FSL default (OLS) vs. DIPY WLS | 0.9884 | 0.0182 | +0.0013 |

**Table 6. Every estimator against the measured-signal weighted fit.** The reference is FSL `dtifit --wls`, which is numerically identical to MRtrix3 `dwi2tensor -iter 0`. MAE/SD expresses the mean absolute difference as a fraction of the standard deviation of FA across white matter voxels in the same data, so that the size of each difference can be weighed. Arms marked (default) are what the toolkit does without options.

| Dataset | Arm | FA r | FA MAE | FA bias | MAE / SD |
|---|---|---|---|---|---|
| Stanford | FSL default, OLS (default) | 0.9676 | 0.0173 | +0.0015 | 0.12 |
|  | MRtrix3, IWLS ×2 (default) | 0.9683 | 0.0244 | -0.0184 | 0.17 |
|  | DIPY WLS (default) | 0.9686 | 0.0219 | -0.0156 | 0.15 |
|  | DIPY NLLS | 0.9781 | 0.0180 | -0.0125 | 0.12 |
|  | DIPY RESTORE | 0.9730 | 0.0188 | -0.0128 | 0.13 |
| Sherbrooke | FSL default, OLS (default) | 0.9126 | 0.0496 | +0.0171 | 0.25 |
|  | MRtrix3, IWLS ×2 (default) | 0.9213 | 0.0451 | +0.0142 | 0.23 |
|  | DIPY WLS (default) | 0.9176 | 0.0465 | +0.0186 | 0.24 |
|  | DIPY NLLS | 0.9386 | 0.0376 | +0.0178 | 0.19 |
|  | DIPY RESTORE | 0.9344 | 0.0392 | +0.0165 | 0.20 |

**Table 7. Accuracy against a known ground truth.** Synthetic phantom, SNR approximately 30. FSL `--wls`, MRtrix3 `-iter 0` and DIPY WLS are the same estimator; MRtrix3's default and FSL's default are listed separately. Crossing-fibre region excluded. MD in µm²/ms.

*Isotropic region — true FA = 0.0000, true MD = 0.9000*

| Arm | FA mean | FA bias | FA RMSE | MD mean | MD bias | MD RMSE |
|---|---|---|---|---|---|---|
| FSL dtifit --wls | 0.0858 | +0.0858 | 0.0900 | 0.8909 | -0.0091 | 0.0248 |
| MRtrix3 -iter 0 (WLS) | 0.0858 | +0.0858 | 0.0900 | 0.8909 | -0.0091 | 0.0248 |
| DIPY WLS | 0.0862 | +0.0862 | 0.0905 | 0.9046 | +0.0046 | 0.0238 |
| MRtrix3 default (IWLS) | 0.0865 | +0.0865 | 0.0908 | 0.9046 | +0.0046 | 0.0238 |
| FSL default (OLS) | 0.0865 | +0.0865 | 0.0908 | 0.9046 | +0.0046 | 0.0238 |

*Single Fibre region — true FA = 0.7071, true MD = 0.7000*

| Arm | FA mean | FA bias | FA RMSE | MD mean | MD bias | MD RMSE |
|---|---|---|---|---|---|---|
| FSL dtifit --wls | 0.7050 | -0.0021 | 0.0212 | 0.6950 | -0.0050 | 0.0180 |
| MRtrix3 -iter 0 (WLS) | 0.7050 | -0.0021 | 0.0212 | 0.6950 | -0.0050 | 0.0180 |
| DIPY WLS | 0.7085 | +0.0014 | 0.0209 | 0.7017 | +0.0017 | 0.0174 |
| MRtrix3 default (IWLS) | 0.7093 | +0.0022 | 0.0209 | 0.7020 | +0.0020 | 0.0175 |
| FSL default (OLS) | 0.7099 | +0.0028 | 0.0235 | 0.7021 | +0.0021 | 0.0176 |

**Table 8. Sensitivity to denoising.** The same comparison after MP-PCA denoising applied once and given to all three toolkits. Toolkits at their default settings, as in Table 2. MD in µm²/ms.

| Dataset | Comparison | FA bias raw | FA bias denoised | MD bias raw | MD bias denoised |
|---|---|---|---|---|---|
| Stanford | FSL vs. MRtrix3 | -0.0181 | -0.0134 | -0.0330 | -0.0186 |
|  | FSL vs. DIPY | -0.0158 | -0.0110 | -0.0322 | -0.0178 |
|  | MRtrix3 vs. DIPY | +0.0027 | +0.0026 | +0.0009 | +0.0009 |
| Sherbrooke | FSL vs. MRtrix3 | +0.0139 | +0.0034 | -0.1271 | -0.0494 |
|  | FSL vs. DIPY | +0.0148 | +0.0048 | -0.1272 | -0.0502 |
|  | MRtrix3 vs. DIPY | +0.0053 | +0.0031 | -0.0009 | -0.0011 |

**Table 9. Non-physical tensor fits within the white matter mask.** Voxels violating the definition of each metric, with percentage of the mask in parentheses, before and after denoising.

| Dataset | Metric | Preprocessing | FSL | MRtrix3 | DIPY |
|---|---|---|---|---|---|
| Stanford | FA > 1 | none | 261 (0.40%) | 178 (0.27%) | 0 (0.00%) |
| Stanford | MD ≤ 0 | none | 261 (0.40%) | 91 (0.14%) | 0 (0.00%) |
| Stanford | FA > 1 | MP-PCA | 154 (0.23%) | 193 (0.29%) | 0 (0.00%) |
| Stanford | MD ≤ 0 | MP-PCA | 105 (0.16%) | 101 (0.15%) | 0 (0.00%) |
| Sherbrooke | FA > 1 | none | 4,404 (3.97%) | 2,252 (2.03%) | 0 (0.00%) |
| Sherbrooke | MD ≤ 0 | none | 3,016 (2.72%) | 603 (0.54%) | 0 (0.00%) |
| Sherbrooke | FA > 1 | MP-PCA | 2,675 (2.56%) | 2,092 (2.00%) | 0 (0.00%) |
| Sherbrooke | MD ≤ 0 | MP-PCA | 1,330 (1.27%) | 641 (0.61%) | 0 (0.00%) |

## Figure Captions

**Figure 1.** Design of the comparison. Both datasets are open and need no credentials. *Left:* brain extraction is compared with each tool run on the input its algorithm expects, so the Dice coefficients reflect the difference a user would meet in practice. *Right:* tensor fitting is compared with every arm given identical input — one brain mask, one volume subset of b = 0 plus a single non-zero shell, no preprocessing — and the estimator varied deliberately instead. Arms are labelled by the source of their weights: FSL `--wls` and MRtrix3 `-iter 0` weight by the measured signal, while DIPY and MRtrix3's default weight by a predicted signal. Statistics are then restricted to physically admissible voxels, without which a few hundred failed fits dominate the correlation, and every arm is checked against a phantom with known eigenvalues. Toolkit colours are consistent across Figures 1, 3 and 4. Generated by `scripts/make_fig1_design.py`.

**Figure 2.** The environment at the tensor-fitting stage, on the Stanford HARDI dataset. The sidebar reports the resolved dataset — detected shells and volume count — and lists the pipeline pages; a collapsible panel reports which toolkit binaries are present. The main panel presents one tab per toolkit, and the selected tab shows the exact command, the outputs it will produce, a Run button that submits it via Python `subprocess` and streams output live, and the resulting maps. Commands are shown in full and with relative paths, so any of them can be copied and run outside the environment unchanged.

**Figure 3.** Agreement between toolkits at their default settings, on the Stanford HARDI dataset; the Sherbrooke equivalent is Supplementary Figure S1. **(a)** FA maps from FSL `dtifit`, MRtrix3 `tensor2metric` and DIPY `TensorModel`, applied to identical input with one shared brain mask. **(b)** Voxelwise FA scatter for each pair over white matter voxels (FA > 0.2 in all three), with Pearson r, mean absolute error and identity line. **(c)** Bland–Altman plots showing voxelwise FA differences against their mean; horizontal lines mark the mean difference and ±1.96 SD. The MRtrix3–DIPY pair clusters tightly about the identity line while both FSL pairings show systematic offset — a pattern that Table 3 shows to follow the estimator rather than the toolkit. Voxels with physically inadmissible values are excluded.

**Figure 4.** Brain extraction on the Stanford HARDI dataset; the Sherbrooke equivalent is Supplementary Figure S2. The b = 0 mean image in greyscale with the brain mask overlaid in red, from FSL `bet` (left, 203,984 voxels), MRtrix3 `dwi2mask` (centre, 167,950) and DIPY `median_otsu` (right, 187,948). Dice coefficients are in Table 2. Two differences are visible: the extent of cortical boundary coverage, and the treatment of the lateral ventricles, which `median_otsu` excludes and the other two retain.

**Supplementary Figure S1.** As Figure 3, for the Sherbrooke 3-shell dataset (b = 0 + b = 1000 s/mm² subset).

**Supplementary Figure S2.** As Figure 4, for the Sherbrooke 3-shell dataset.
