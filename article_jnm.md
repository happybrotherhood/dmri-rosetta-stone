# Estimator choice, not implementation, accounts for most of the difference in diffusion tensor fitting between FSL, MRtrix3 and DIPY

**Busra Mutlu Ipek**¹\*

¹ Department of Neuroimaging, King's College London, London, United Kingdom

\* **Corresponding author.** Busra Mutlu Ipek, Department of Neuroimaging, King's College London, De Crespigny Park, London SE5 8AF, United Kingdom. E-mail: busra.mutlu_ipek@kcl.ac.uk

## Abstract

**Background.** Weighting a linear tensor fit by the measured signal biases it; weights from a predicted signal do not (Salvador et al., 2005; Veraart et al., 2013). Which toolkit configurations apply each scheme, and whether it matters next to test-retest variability, is unknown.

**New method.** We fitted tensors with FSL, MRtrix3 and DIPY on identical input from two open datasets and 38 test-retest scans, so only the estimator varied. Agreement was measured on white matter defined without any tensor fit, keeping only fits with admissible eigenvalues. The schemes were scored against phantoms and against simulations with crossing fibres and partial volume.

**Results.** FSL `dtifit --wls` and MRtrix3 `dwi2tensor -iter 0` implement the same estimator and returned the same tensor in every white matter voxel. MRtrix3 and DIPY weight by a predicted signal by default; FSL fits ordinary least squares, and its `--wls` option weights by the measured signal. That option gave MD 0.02 to 0.09 µm²/ms lower than every other estimator, with a bias that grew as SNR fell, and raised between-scanner MD variability 1.6 to 1.9 times. The three defaults differed by less than test-retest variability.

**Comparison with existing methods.** Previous studies have documented variability between whole pipelines. In this study, the variability from the tensor fit is traced to one estimator, selected by a command-line option.

**Conclusions.** For these toolkits and versions, the estimator, not the implementation, determines the result. The toolkit name does not identify the estimator; the estimator and the source of its weights do. Measured-signal weighting adds between-scanner variance that grows as SNR falls.

**Keywords:** diffusion MRI; tensor fitting; weighted least squares; estimator bias; signal-to-noise ratio; test-retest variability; reproducibility

## 1. Introduction

Diffusion MRI (dMRI) sensitises the magnetic resonance signal to the microscopic motion of water molecules, and because this motion is constrained by the oriented structure of axon bundles, it provides the only non-invasive means of probing white matter microstructure in the living brain (Basser et al., 1994; Jones, 2010). The diffusion tensor was the first model to summarise this information in each voxel, and the two scalar measures derived from it, fractional anisotropy (FA) and mean diffusivity (MD), remain the most widely reported quantities in the field. They serve as markers of white matter integrity in studies of development, ageing and disease, and they are routinely compared between individuals, between groups and between imaging sites (Beaulieu, 2002; Jones, 2010). The reliability of these comparisons therefore depends on the step that turns raw measurements into a tensor: the tensor fit.

In practice, that step is performed by one of three open-source packages: FSL (Smith et al., 2004; Jenkinson et al., 2012), MRtrix3 (Tournier et al., 2019) or DIPY (Garyfallidis et al., 2014). Each fits the tensor to the same data, and a methods section that names one of them is generally taken to have specified the computation. Whether this assumption holds is a question of reproducibility. Studies of the reproducibility of dMRI have shown that analyses of the same data diverge when the processing pipeline, the analysing group or the scanner changes (Maier-Hein et al., 2017; Tax et al., 2019; Schilling et al., 2021), and the fitting procedure itself is a recognised pitfall of tensor analysis (Jones and Cercignani, 2010). These studies, however, vary many choices at once, so the contribution of the tensor fit alone cannot be separated from that of the other steps. Two narrower questions consequently remain open. When only the software performing the tensor fit differs, how far do the toolkits disagree, and what within the software is responsible for the disagreement? And is that disagreement large or small when set against the variability that arises when the same person is scanned again?

The theory of tensor estimation indicates where the answer is likely to lie. The tensor is usually fitted by linear least squares to the logarithm of the signal, because the logarithm turns the exponential signal model into a linear one. The transformation, however, also changes the noise: the error in the log-signal is inversely proportional to the signal-to-noise ratio (SNR) of each measurement, so that measurements with low signal become far less reliable than those with high signal (Salvador et al., 2005; Koay et al., 2006). A weighted fit is therefore required, with weights proportional to the squared signal. The source of that signal is the decisive choice. Salvador et al. (2005) characterised the errors of the linearised model and showed that the weights should be derived from the signal predicted by a preliminary fit, with the option of refining them by iteration; this has been the standard recommendation since. Taking the weights from the measured signal instead introduces a bias, because the weights then share the noise of the measurements they weight, and Veraart et al. (2013) quantified this cost and described the resulting loss of accuracy as surprisingly high. Weights from a predicted signal performed better, in some cases better than non-linear least squares.

Whether the three toolkits follow this recommendation has not been examined. Each relevant choice is documented in isolation: MRtrix3 states that `dwi2tensor` reweights its fit twice, DIPY cites Chung et al. (2006) for its weights, and FSL lists `--wls` in the help text of `dtifit`. The documentation thus shows that the components differ, but it does not show whether two implementations of one estimator agree, which distributed configurations carry the documented bias, how large that bias is at the SNR of real acquisitions, or how it compares with test-retest variability. The last point matters most for practice. A bias that depends on SNR will differ between scanners, coils, protocols and participants, and will therefore appear as a difference in microstructure wherever groups differ in image quality.

This study addresses these questions with a controlled comparison in which the input data, the brain mask and the gradient table are held fixed and only the estimator varies. It makes three contributions. First, as a control, it establishes that FSL and MRtrix3 return the same tensor when given the same estimator, so that differences between the toolkits can be attributed to the estimator rather than to the code. Second, it maps which distributed configuration implements which weighting scheme, and finds that the only weighted option of FSL implements the scheme the literature advises against. Third, it measures the size of the resulting differences against test-retest variability on repeated scans from four scanners, and tests whether the conclusions hold with crossing fibres, partial volume, multi-shell input, non-Rician noise and errors in the b-matrix. All analyses use open data, and every value can be regenerated from the accompanying code.

## 2. Materials and methods

### 2.1. Data

Two open datasets distributed by the DIPY project were analysed. Neither requires registration. The Stanford HARDI dataset (Rokem et al., 2015) was acquired on a 3 T GE Discovery MR750 with a 32-channel head coil and a twice-refocused spin-echo sequence. It has 10 b = 0 volumes and 150 directions at b = 2000 s/mm² (TE 93.6 ms), with 2 mm isotropic voxels and a matrix of 81 × 106 × 76. The Sherbrooke 3-shell dataset (Garyfallidis et al., 2014) has one b = 0 volume and 64 directions at each of b = 1000, 2000 and 3500 s/mm², with 2 mm isotropic voxels and a matrix of 128 × 128 × 60. It has no acquisition paper. Its distribution records no acquisition parameters; the only documented fact is that it was acquired on a 1.5 T Siemens scanner (M. Descoteaux, DIPY mailing list, July 2015). We used it as an independent acquisition rather than a characterised reference. For neither dataset are the parallel-imaging factor, the partial-Fourier factor or the reconstruction documented. Supplementary Table S8 lists what is known. The two datasets differ in site, protocol, b-value, angular sampling and number of b = 0 volumes, but not in voxel size.

The main analysis used the b = 1000 s/mm² shell of the Sherbrooke data, extracted once together with the b = 0 volume (65 of 193 volumes) and given to every arm. Its b = 2000 s/mm² shell, and the two shells together, were analysed separately (Section 2.9). The Stanford data are single-shell and were used whole.

### 2.2. Test-retest data

To set the differences between estimators against how much a measure varies when the same person is scanned again, we used the MASiVar dataset (Cai et al., 2021a), distributed on OpenNeuro (ds003416) under a CC0 licence. Two of its cohorts were used. Cohort I is one adult scanned in three sessions on consecutive days on a 3 T Philips Achieva, with three or four scans per session (11 scans). Cohort II is five adults, each scanned on three or four scanners at three sites within one year, with one or two sessions per scanner (27 scans). The scanners are two Philips Achieva at site 1 (1A and 1B), a GE Discovery MR750 at site 2 and a Siemens Skyra at site 3. From each scan we took the 96-direction acquisition at b = 1000 s/mm², which contains its own b = 0 volume, so that each scan is a complete single-shell acquisition. Voxels are 2.5 mm isotropic, except on scanner 1A for Cohort II (1.9 × 1.9 × 2.2 mm) and at site 2, whose images are stored at 0.94 × 0.94 × 2.5 mm. The site 2 and site 3 scans contain ten and two b = 0 volumes. Unprocessed data were used, as for the two main datasets. The analysis was then repeated on the same scans as preprocessed by the dataset's own pipeline, PreQual (Cai et al., 2021b), which applies MP-PCA denoising, susceptibility, eddy-current and motion correction, and intensity normalisation. Using the dataset's preprocessing, rather than one chosen here, keeps the preprocessing outside the comparison.

### 2.3. Signal-to-noise ratio and noise level

SNR was measured rather than inferred from the protocol. The noise standard deviation σ was the median, over white matter, of the noise map from MRtrix3 `dwidenoise` (Marchenko–Pastur PCA, MP-PCA; Veraart et al., 2016), computed from each dataset's full series before shell selection. SNR is the mean signal of one b = 0 volume, or of the fitted shell, divided by σ. White matter is defined in the next section. The SNR of a single b = 0 volume was 35.8 for Stanford and 11.1 for Sherbrooke. The SNR of the fitted shell was 10.0 for Stanford (b = 2000 s/mm²) and 6.3 for Sherbrooke (b = 1000 s/mm²).

The MP-PCA value was checked in three ways. On Stanford, which has ten b = 0 volumes, the SD across those volumes was divided by σ in each white matter voxel. The median ratio, corrected for the small-sample bias of the SD (dividing by 0.963), was 1.27, with a 95% bootstrap confidence interval over voxels of 1.26 to 1.27. The interval is narrow, but the ratio itself varies from voxel to voxel (interquartile range 1.04 to 1.53), because the SD across volumes also contains motion and physiological fluctuation. DIPY's PIESNO estimator (Koay et al., 2009) gave σ = 17.4 on Stanford, against 18.0 from MP-PCA. On Sherbrooke, PIESNO (15.1) and the magnitude of the background far from the head (15.9, after Rician correction) were both below the MP-PCA value in white matter (22.3), which is consistent with noise that varies across the image, as parallel imaging produces. The Sherbrooke background is also narrower than a Rayleigh distribution; its quantile ratios lie between those of one and two complex channels (Supplementary Table S9). The Stanford background cannot be examined, because 39% of its voxels outside the brain are exactly zero and the rest carry ghosting. The noise level and its distribution are therefore uncertain, and the simulations below are run at more than one noise level and with more than one noise model. Because σ varies across the image, the simulation on each voxel's own tensor adds noise at that voxel's own σ from the MP-PCA map rather than at one value for the whole image.

### 2.4. Comparison design

Figure 1 summarises the design. Each fitting configuration is called an arm. Every arm received identical input: the same unprocessed volumes, the same gradient table and one shared brain mask from DIPY `median_otsu`. No preprocessing was applied, because any preprocessing step is itself a toolkit-specific choice. Denoising was tested separately. The results describe the fitting stage, not a complete pipeline.

Statistics were computed on white matter defined without any tensor fit, so that the voxel set is the same for every arm and cannot favour one of them. The mean b = 0 and the mean diffusion-weighted image were segmented into three classes with FSL FAST, using both images as channels. White matter was taken as the class with the lowest b = 0 signal, at a partial-volume estimate of at least 0.5 inside the shared brain mask: 96,773 voxels on Stanford and 100,005 on Sherbrooke. A threshold of 0.9 gave the same conclusions (Supplementary Table S10).

A tensor fit was admissible if all three eigenvalues were non-negative and the largest did not exceed 3.0 µm²/ms (3.0 × 10⁻³ mm²/s), the diffusivity of free water at body temperature. The rule is applied to the eigenvalues because a rule on FA and MD does not exclude every non-physical tensor: eigenvalues of 1.0, 1.0 and −0.1 µm²/ms give FA = 0.78 and MD = 0.63 µm²/ms. Each pair of arms was compared on the white matter voxels admissible in both, and every table states how many voxels each arm loses to the rule. Table 5 uses one voxel set, admissible in all seven arms. A small number of inadmissible voxels can change a correlation: on Sherbrooke, the 3.2% of white matter voxels inadmissible in MRtrix3's default fit lower its MD correlation with DIPY from 0.9999 to 0.9989 when kept. The arms differ in how often they return inadmissible fits, and this is reported as a result in its own right.

For each pair of arms, we computed three statistics: the voxelwise Pearson correlation (r), the mean absolute error (MAE) and the Bland–Altman mean difference with 95% limits of agreement. MD is reported in µm²/ms.

### 2.5. Estimators compared

Table 1 lists the arms. At their defaults, the three toolkits use three different estimators:

- FSL `dtifit` performs ordinary least squares (OLS).
- MRtrix3 `dwi2tensor` performs weighted least squares (WLS) with measured-signal weights. It then runs two iterations of reweighted least squares (IWLS), with weights from the predicted signal.
- DIPY performs one WLS fit. Its weights come from the signal predicted by a preliminary OLS fit (Chung et al., 2006), the scheme of Salvador et al. (2005).

Four non-default arms were added. FSL `dtifit --wls` is FSL's weighted option. MRtrix3 `dwi2tensor -iter 0` stops after the first, measured-signal step, so MRtrix3 and FSL can be compared on one estimator. DIPY's non-linear least squares (NLLS) and RESTORE (Chang et al., 2005) test whether a pattern is specific to weighted linear fits. Both used DIPY's defaults; for RESTORE, the noise level is estimated from the residuals. MRtrix3's final weights come from a predicted signal, so its default is grouped with the predicted-signal schemes. For every arm the three eigenvalues and the six tensor components were kept, so that admissibility could be judged on the eigenvalues and the implementations compared component by component. Supplementary Table S11 records the signal floor, the treatment of non-positive measurements, the tensor frame, the numerical precision and the eigenvalue handling of each toolkit.

### 2.6. Manipulating the weighting scheme

This test asks whether the source of the weights, rather than the software, explains why DIPY differs. DIPY's WLS fit was run twice on the same data. The first run used its default predicted-signal weights. The second used the squared measured signal as weights. Each run was compared with FSL `dtifit --wls`. Signals were floored at 1 before both fits, so that a zero-valued voxel cannot make the weighted design matrix singular.

### 2.7. Accuracy against a known ground truth

Agreement between toolkits does not show which one is accurate. We therefore built synthetic phantoms with known eigenvalues at SNR 30, 20 and 10. This range extends from slightly below the single-b = 0 SNR of the Stanford data to about that of the Sherbrooke data. Each 30 × 30 × 30-voxel phantom has three regions:

- an isotropic region (eigenvalues 0.9, 0.9 and 0.9 µm²/ms; FA = 0, MD = 0.90 µm²/ms);
- a single-fibre region (1.4, 0.35 and 0.35 µm²/ms; FA = 0.7071, MD = 0.70 µm²/ms), oriented left–right in one half and superior–inferior in the other;
- a crossing-fibre region, excluded from scoring because no single tensor is correct there; crossing fibres are treated in the simulations below.

The fitted scheme had 10 b = 0 volumes and 30 directions at b = 1000 s/mm². Noise was Rician, as in magnitude images from one channel (Gudbjartsson and Patz, 1995). Gaussian noise with standard deviation 1000/SNR was added to the real and imaginary channels, and the magnitude was taken. S₀ was 1000 in the fibre regions, so SNR is as stated there. The isotropic region had S₀ = 800, so its SNR was 24, 16 and 8. Two voxels were trimmed from each in-plane edge of the volume, and one slice from each end of every region. This left 5,408 scored voxels per region. The five linear-fit arms were scored: FSL default and `--wls`, MRtrix3 default and `-iter 0`, and DIPY WLS. For each, we report bias (estimate minus truth), its standard error across voxels, and root-mean-square error (RMSE). This phantom reproduces the test of Veraart et al. (2013) for the configurations the toolkits distribute.

### 2.8. Simulations on the real acquisition protocols

The phantom has one tensor shape and one gradient scheme. The remaining simulations used the exact gradient tables given to the toolkits: 10 b = 0 volumes and 150 directions at b = 2000 s/mm² for Stanford, and one b = 0 volume and 64 directions at b = 1000 s/mm² for Sherbrooke. All used the toolkits' linear estimators reimplemented in NumPy, so that noise, voxels and single measurements could be controlled. The reimplementations include each toolkit's signal floor, MRtrix3's two reweightings and, for the DIPY arm only, DIPY's eigenvalue clipping. On the real data they matched the published maps of FSL `--wls`, MRtrix3's default and DIPY WLS to a mean absolute FA difference below 0.00001 in white matter on both datasets. FSL applies a further floor at 1% of the S₀ estimated by an initial fit (Supplementary Table S11); it binds only where the signal is very low, in 218 white matter voxels on Stanford, and the simulations below do not reach it. Each cell of every simulation had 10,000 voxels, random fibre orientations and its own random seed.

*Idealised tensors.* Tensors were axially symmetric, with MD = 0.70 µm²/ms, FA from 0.25 to 0.80 and random orientation. S₀ and σ were the same in every voxel. Rician noise was added at SNR 10, 20, 30 and 50, and at each dataset's measured SNR. All four linear estimators were fitted to the same noisy voxels. For each, we report bias with its Monte Carlo standard error, and RMSE.

*Each voxel's own tensor.* The second simulation kept the properties of the real data. It used the white matter voxels with FA above 0.2 in the DIPY WLS fit, binned by that FA. In each voxel, the DIPY tensor and S₀ defined a noise-free signal, with negative eigenvalues clipped at zero. Rician noise was added at the voxel's own MP-PCA σ and at 1.27 times that σ, the ratio measured on the Stanford b = 0 volumes. Both weighting schemes were then refitted. Each noise level was simulated five times with independent noise; we report the mean, and standard errors were at most 0.0002. Voxels and bins were not defined from the measured-signal fit, because that fit is the one whose offset is being measured. Inadmissible fits were treated identically in observed and simulated data. The main rule excluded a voxel when either fit was inadmissible. As sensitivity analyses, FA was instead clipped to [0, 1] and MD to [0, 3] µm²/ms, or all values were kept as fitted. As an upper bound on the noise, we found the σ at which the simulated residuals were as widely spread as the real ones, measured by a robust SD. Real residuals also contain model misfit, so this bound overstates the noise. On the real data, we computed the same difference, FSL `--wls` minus DIPY WLS, over the same voxels and bins. Four further analyses addressed possible artefacts. Each Sherbrooke volume was matched by content to its source volume. The real data were refitted without measurements more than 3σ below the predicted signal, and without any measurement beyond ±3σ. Each voxel's residuals were shuffled across gradient directions and added back to the fitted signal. The idealisations of the first simulation were imposed one at a time on the real tensors.

*Crossing fibres and partial volume.* Where no single tensor is correct, each estimator was scored against its own fit to the noise-free signal, so that the effect of noise is separated from the effect of the mismatch. Nine scenarios were simulated at SNR 10, 20 and 30: one fibre (eigenvalues 1.4, 0.35 and 0.35 µm²/ms); two equal fibres crossing at 30°, 60° and 90°; the fibre with 10%, 30% and 50% free water (isotropic, 3.0 µm²/ms); and the fibre with 30% and 50% grey matter (isotropic, 0.8 µm²/ms).

*Noise model.* Because the reconstruction of the real data is not documented, the single-fibre simulation (true FA 0.45 and 0.71) was repeated with non-central χ noise from 4 and 8 complex channels at the same per-channel σ, which raises the noise floor, at SNR 10, 20 and 30.

*Errors in the b-matrix.* Gradient non-linearity and other spatial systematic errors make the effective b-matrix of a voxel differ from the nominal one (Krzyżak et al., 2024, 2025). Neither dataset provides the gradient-field information needed to correct this, and none was applied. To test whether such errors alter the comparison between estimators, the signal was generated with a per-voxel b-matrix that differed from the nominal one and fitted with the nominal one: b-value scale errors uniform within ±2% or ±5% across voxels, systematic scale errors of +5% and −5%, and gradient directions tilted by a random angle with SD 1° or 3°. Each was run without noise and at SNR 20, and the bias with both noise and error was compared with the sum of the two biases alone.

### 2.9. Multi-shell input

FSL `dtifit`, MRtrix3 `dwi2tensor` and DIPY's `TensorModel` all fit every volume they receive. The main analysis gave them one shell, because the single-tensor model does not describe the signal decay across shells at these b-values, and the choice of shell is then separated from the choice of estimator. To test how the estimators behave when the model is strained, all seven arms were also fitted to the Sherbrooke b = 2000 s/mm² shell alone, which is the b-value of the Stanford data, and to the b = 1000 and 2000 s/mm² shells together (129 volumes).

### 2.10. Sensitivity to denoising

We repeated the comparison of Table 2 on denoised data. MRtrix3 `dwidenoise` (MP-PCA; Veraart et al., 2016) was applied once to the full series, before shell selection. The denoised data were given to every arm, so the estimator remained the only variable. Giving each toolkit its own denoiser would not have been fairer: FSL has none, so it would have fitted noisier data. Eddy-current and motion correction were not tested on these two datasets; their effect is covered by the preprocessed test-retest data.

### 2.11. Test-retest analysis

Each of the 38 MASiVar scans was fitted by the five linear arms with one shared `median_otsu` brain mask, and each arm's FA and MD were averaged over the scan's white matter: voxels with FA above 0.2 and an admissible tensor in all five arms. For a fixed estimator, variability was measured as a coefficient of variation (CoV, SD divided by the mean): within session and between sessions in Cohort I; between repeat sessions on the same scanner, between scanners within a subject, and between subjects on the same scanner in Cohort II. The difference between estimators was measured on the same scans as the mean difference of one arm from another, as a percentage of the mean. Because a constant offset would cancel in any study that uses one estimator, the offset was also examined as it varied: its spread across scans, its mean on each scanner, and the change it made to between-scanner variability. The SNR of each scan was the mean b = 0 signal over white matter divided by the median MP-PCA σ, and was left undefined for the four site 2 scans stored at an interpolated resolution, where MP-PCA returns no noise estimate.

### 2.12. Execution environment

All three toolkits ran in one Docker container (Merkel, 2014) that pins FSL 6.0.7, MRtrix3 3.0.8 and DIPY 1.12.1 with Python 3.12. The container fixes the versions, which matters because defaults can change between releases, and lets every result be regenerated with the commands listed in Supplementary Section S8. Every results table is produced by a script in the repository.

## 3. Results

### 3.1. As usually configured, the weighted fits set FSL apart from the other two toolkits

We first compared the weighted fits as they are usually configured (Table 2). FSL was run with `--wls`, its weighted option. MRtrix3 and DIPY were run at their defaults, which both weight. MRtrix3 and DIPY agreed closely (FA r = 0.9999 on both datasets; MD within 0.0006 µm²/ms). FSL differed from both (FA r = 0.9973 to 0.9975 on Stanford and 0.9724 to 0.9727 on Sherbrooke). On this comparison alone, FSL appears to differ from the other two toolkits.

The offsets did not behave like an implementation difference. FSL's MD was lower on both datasets, by 0.024 µm²/ms on Stanford and 0.086 µm²/ms on Sherbrooke. Its FA offset, however, changed sign: FSL was 0.015 lower than MRtrix3 on Stanford and 0.002 higher on Sherbrooke. This inconsistency motivated the analyses that follow.

### 3.2. Given the same estimator, FSL and MRtrix3 return the same tensor

MRtrix3's default is not a single weighted fit. It is WLS followed by two IWLS iterations. The comparison above set reweighting against a single weighted fit, and attributed the result to the toolkit.

Constraining MRtrix3 to one weighted fit (`-iter 0`) reversed the grouping (Table 3; Figure 2). In white matter, FSL and MRtrix3 then agreed to the precision of their output files. The median absolute difference in FA, MD and each of the six tensor components, once both tensors were brought into one frame, was below 10⁻⁷; the largest FA difference in any white matter voxel was 1.1 × 10⁻⁴ on Stanford and 5.4 × 10⁻⁵ on Sherbrooke; and 1 − r was about 10⁻¹¹ (Supplementary Table S12). The same held for the b = 2000 s/mm² shell, for both shells together, for denoised data and for all 38 test-retest scans. Under the same constraint, MRtrix3 diverged from DIPY, to FA r = 0.9975 and 0.9724. This was the distance that had separated FSL from DIPY.

The agreement is not exact in every voxel of the brain, and the exception has a known cause. On Stanford, 3.6% of voxels inside the brain mask differed by more than 0.001 in FA, with a largest difference of 0.20. These voxels lie outside white matter and 78% of them contain a measurement below half the noise SD. The two programs floor the signal differently before taking its logarithm: MRtrix3 at 10⁻⁶ of the voxel's maximum, FSL at 1% of the S₀ estimated by an initial fit (Supplementary Table S11). Every one of the 6,687 differing voxels is a voxel in which FSL's floor binds, and a reimplementation with FSL's rule reproduces its values there to a mean absolute FA difference of 0.00002. On Sherbrooke, ten brain voxels differed by more than 0.001. Two separately developed implementations of the same closed-form estimator therefore return the same tensor wherever the signal exceeds 1% of S₀, and where it does not, the difference is a documented choice of floor, not an error.

### 3.3. What separates DIPY is the source of its weights

DIPY differs from both even when MRtrix3 is matched to FSL. MRtrix3 documents its first step as weighted by the measured signal. FSL `--wls` reproduces that step, so it also uses measured-signal weights. DIPY, in contrast, takes its weights from a signal predicted by a preliminary OLS fit.

The arms therefore group by the source of their weights, not by software (Tables 2 and 3):

- within the measured-signal group (FSL `--wls`, MRtrix3 `-iter 0`), FA r = 1.0000;
- within the predicted-signal group (DIPY, MRtrix3 default), FA r = 0.9999 on both datasets;
- between the groups, FA r = 0.9975 on Stanford and 0.9724 on Sherbrooke.

We tested this grouping directly by changing the weights inside DIPY (Table 4). With measured-signal weights, DIPY's FA difference from FSL fell from an MAE of 0.0140 to 0.0000 on Stanford and from 0.0332 to 0.0000 on Sherbrooke, and its MD difference fell from 0.0237 and 0.0858 µm²/ms to 0.0000. Once inadmissible fits are excluded, DIPY with measured-signal weights reproduces FSL `--wls` exactly. The small residual reported in the first version of this analysis came from DIPY's clipping of negative eigenvalues, which the admissibility rule now removes from both arms. Changing one argument inside one toolkit removed the whole of the difference attributed to the choice of toolkit.

### 3.4. In MD, measured-signal weighting differs from every other estimator

Table 5 compares every arm with the measured-signal fit, on one voxel set per dataset.

In MD, the pattern was consistent. OLS, IWLS, predicted-signal WLS, NLLS and RESTORE all differed from the measured-signal fit, which was always the lower one, by 0.018 to 0.024 µm²/ms on Stanford and 0.062 to 0.086 µm²/ms on Sherbrooke. The three toolkit defaults agreed with one another within 0.0022 µm²/ms on Stanford and 0.0005 µm²/ms on Sherbrooke.

In FA, the differences were smaller. The other estimators differed from the measured-signal fit by an MAE of 0.011 to 0.016 on Stanford (0.06 to 0.09 SD of white matter FA) and 0.025 to 0.037 on Sherbrooke (0.13 to 0.19 SD). On Sherbrooke the defaults differed from one another by at most 0.014, and on Stanford FSL's OLS default was about as far from the two predicted-signal defaults (0.013 to 0.014) as from the measured-signal fit (0.011).

The comparison within FSL shows the practical size of this effect. Switching `dtifit` from its default to `--wls` changed MD by 0.022 µm²/ms on Stanford and 0.086 µm²/ms on Sherbrooke. Replacing FSL `--wls` with MRtrix3 at the same estimator changed nothing. A single option within one toolkit changes the result more than a change of toolkit at a fixed estimator.

### 3.5. Against ground truth, measured-signal weighting is the most biased scheme

The phantoms showed which estimator is accurate (Table 6; Figure 4A).

At SNR 30, in the single-fibre region, the measured-signal arms underestimated FA by 0.0039 and MD by 0.0065 µm²/ms. Standard errors were 0.0003 or less. Every other arm was within 0.0005 of truth in both metrics.

As SNR fell, the measured-signal bias grew. At SNR 20 it was −0.0081 in FA and −0.0147 µm²/ms in MD. At SNR 10 it was −0.0257 and −0.0542 µm²/ms. The other arms stayed within 0.0013 of truth at SNR 20 and within 0.007 at SNR 10. At SNR 10, FSL's OLS default (+0.0068) and MRtrix3's default (+0.0046) showed small but detectable positive FA biases. In the isotropic region, noise raised FA in every arm, least in the measured-signal arms. Only the measured-signal arms underestimated MD by a substantial amount (Supplementary Table S2).

The MD bias grew as theory predicts. Relative to SNR 30, it was 2.3 times larger at SNR 20 and 8.3 times larger at SNR 10. A bias caused by the correlation between weights and noise should scale with 1/SNR², which gives factors of 2.25 and 9. The FA bias grew more slowly, by 2.1 and 6.6 times.

Measured-signal weighting also had a higher RMSE than predicted-signal weighting at every SNR, in both FA and MD, and the gap widened as SNR fell: in FA, 0.0703 against 0.0614 at SNR 10 (Table 6). FSL's OLS default was close to unbiased, but it had the highest FA RMSE at SNR 30 and 20. These results reproduce the finding of Veraart et al. (2013) for the configurations the toolkits distribute.

The phantom has ten b = 0 volumes, so we repeated the comparison in simulations on the two real gradient tables (Supplementary Table S3). There, measured-signal weighting had the largest MD bias and the largest MD RMSE of the four linear estimators in every condition. In FA, the result depended on the protocol. On the Stanford table, it had the largest FA bias in every condition. On the Sherbrooke table, with one b = 0 volume and b = 1000 s/mm², noise raised FA in most conditions, especially at low FA, and the negative bias of measured-signal weighting partly offset this rise, so its absolute FA bias was smaller than that of predicted-signal weighting in 21 of 30 conditions.

### 3.6. The conclusion holds with crossing fibres and partial volume

Where no single tensor is correct, each estimator was scored against its own fit to the noise-free signal (Supplementary Table S13). In all nine scenarios, at every SNR and on both protocols, measured-signal weighting had the largest MD bias and the largest MD RMSE. On the Stanford table at SNR 20, its MD bias was −0.054 µm²/ms for one fibre, −0.027 for two fibres crossing at 90° and −0.149 for the fibre with 50% free water; the predicted-signal arm's bias in the same cases was −0.004, −0.0003 and −0.031. The offset between the two weighting schemes grew with the free-water fraction, from −0.050 to −0.118 µm²/ms, because free water lowers the diffusion-weighted signal and with it the effective SNR. In FA, measured-signal weighting had the largest bias in every scenario at SNR 20 and 30. Crossing fibres and partial volume change the value every estimator converges to, but not the ranking of the estimators.

### 3.7. Noise on the real tensors reproduces most of the offsets

The single-b = 0 SNR of the two datasets, 35.8 and 11.1, spans the phantom range. The MD offset between the weighting groups was about three times larger on Sherbrooke (−0.089 against −0.026 µm²/ms over the voxels of this analysis). We tested whether noise explains the offsets (Table 7; Figure 4B and C).

The simulation with idealised tensors did not reproduce them (Supplementary Table S4). On Stanford it matched the observed FA offset within 0.003 below FA 0.5 but fell short above it, and on Sherbrooke it predicted a small negative FA offset where the data showed a small positive one. For MD it reproduced the sign on both datasets but only 35 to 62% of the size.

Noise added to each voxel's own tensor reproduced the offsets much better, and the share it reproduced depended on the noise level assumed (Table 7). At the MP-PCA σ it accounted for 56 to 62% of the Stanford offsets and 61% of the Sherbrooke MD offset. At 1.27σ, the noise level measured on the Stanford b = 0 volumes, it reproduced 93% of the Stanford FA offset, 86% of its MD offset and 93% of the Sherbrooke MD offset. At the upper bound set by the residuals, 1.39σ on Stanford and 1.31σ on Sherbrooke, the shares were 108% and 100% on Stanford and 98% for Sherbrooke MD. By bin, the simulated FA offset at 1.27σ was within 0.003 of the observed offset in every Stanford bin, including the most anisotropic one (−0.0267 against −0.0288).

The Sherbrooke FA offset itself was small, +0.0034, and the measured-signal fit was inadmissible in 5.9% of the voxels of this analysis. The treatment of those fits therefore decided the share (Supplementary Table S6): 75% under the exclusion rule, and more than 100% when FA was clipped or kept as fitted, because the observed and simulated offsets then both grew. Which idealisation of the simpler simulation reverses the sign is shown in Supplementary Table S5: setting MD to 0.70 µm²/ms, against a real white matter median of 0.58, moved the simulated offset furthest, and imposing all four idealisations reproduced the simpler simulation. Because the observed offset is of the same size as these effects, we do not draw conclusions from its sign.

Checks of the real residuals found no pipeline error and no signal dropout (Supplementary Table S7). All 65 Sherbrooke volumes matched their source volumes and gradient entries, and no volume had more than three times the median rate of measurements below −3σ. Residuals beyond ±3σ were 1.4 to 2.3 times as common as in noise-only data at 1.27σ, and removing them changed the MD offset by 17% on Stanford against 10% in noise-only data. In Stanford voxels with FA of 0.6 or more, the median residual was +0.93σ along the fibre against +0.31σ in noise-only data, a pattern consistent with a single tensor failing to fit the angular profile of the signal at b = 2000 s/mm². On Sherbrooke, at b = 1000 s/mm², the pattern was weak (+0.31σ against +0.20σ).

Denoising reduced the real-data offsets but did not remove them (Table 8). The MD offset between FSL `--wls` and MRtrix3's default fell by 42% on Stanford and by 58% on Sherbrooke. The FA offset shrank on both datasets, and the small difference between MRtrix3 and DIPY changed little.

### 3.8. The noise floor affects every estimator

The simulations above assume Rician noise, that is, magnitude images from one channel. Reconstructions that combine several channels raise the noise floor, and the Sherbrooke background suggests such a reconstruction (Materials and methods). With non-central χ noise from 4 and 8 channels at the same per-channel σ, every estimator underestimated MD, and this shared bias exceeded the difference between weighting schemes (Supplementary Table S14). On the Stanford table at SNR 20 and true FA 0.45, the MD bias of the predicted-signal arm went from −0.001 µm²/ms with one channel to −0.064 with four and −0.122 with eight, while the offset between measured- and predicted-signal weighting shrank from −0.041 to −0.026 and −0.017 and kept its sign. The Sherbrooke table behaved the same way. At low SNR, the choice of estimator does not compensate for the noise floor, and no linear estimator is accurate.

### 3.9. Errors in the b-matrix do not change the comparison

With the signal generated under a b-matrix that differed from the nominal one and fitted with the nominal one, scale errors that vary from voxel to voxel (uniform within ±2% or ±5%) and gradient tilts with SD 1° or 3° changed no arm's bias by more than 0.001 (Supplementary Table S15). A systematic scale error of ±5% shifted the MD of every arm by ±0.035 µm²/ms, that is, by 5% of MD, and shifted FA by less than 0.002. The interaction between this error and the weighting bias was 0.005 to 0.009 µm²/ms at SNR 20, so the two effects are not exactly additive, but the ranking of the estimators and the sign of their differences were unchanged in every case.

### 3.10. The estimator offset exceeds test-retest variability and varies with the scanner

On the 38 MASiVar scans fitted without preprocessing (Table 10; Figure 3), FSL `--wls` and MRtrix3 `-iter 0` again returned the same tensor in every scan. The MD of the measured-signal fit was 8.5 to 9.0% lower than that of the other three linear arms, with a range of 3.1 to 15.0% across scans. The three toolkit defaults differed from one another by 0.05 to 0.44% in MD. For a fixed estimator, MD varied by 0.9 to 1.4% within a session, by 0.6 to 1.5% between sessions and by 1.2 to 1.5% between subjects on one scanner. The difference between estimators was therefore six to fifteen times the between-session variability, and the difference between defaults was below it. In FA the estimator offset was 1.1 to 1.3%, larger than the between-session variability (0.2 to 0.4%) but smaller than the between-scanner (2.8 to 3.3%) and between-subject (2.6 to 2.7%) variability.

The offset was not constant. Across scans its SD was 0.025 µm²/ms (3.2% of MD), and its mean differed between scanners: −0.074 µm²/ms on scanner 1A, −0.051 on 1B, −0.025 at site 2 and −0.031 at site 3, a spread of 6.4% of MD, five times the between-subject variability. Across the 34 scans with a defined SNR, the offset followed the b = 0 SNR (Spearman ρ = 0.95; Figure 3A), and it did so within a single scanner as well (ρ = 0.81 on scanner 1A, 20 scans). As a result, measured-signal weighting raised the between-scanner CoV of MD from 2.9 to 3.1% with the three defaults to 5.7%, a factor of 1.9.

On the same scans after the dataset's own preprocessing, the offset fell to 2.8 to 2.9% of MD (range 0.3 to 6.6%), the defaults differed by 0.03 to 0.10%, and the between-scanner CoV of MD was 4.8% with measured-signal weighting against 3.0 to 3.1% with the defaults, a factor of 1.6 (Table 10). The per-scanner offsets were −0.035, −0.016, −0.009 and −0.006 µm²/ms, a spread of 4.0% of MD, and the correlation with SNR remained (ρ = 0.65). In FA, preprocessing reduced the offset to 0.4 to 0.6%, below the within-session variability, and the between-scanner CoV was unchanged by the estimator.

### 3.11. Multi-shell input also separates the defaults

At b = 2000 s/mm², where the Sherbrooke diffusion-weighted SNR is 3.4, the measured-signal fit gave MD 0.120 to 0.123 µm²/ms lower than the OLS, IWLS and predicted-signal arms, and 0.083 lower than NLLS (Supplementary Table S16). The defaults agreed within 0.003 µm²/ms in MD, as at b = 1000 s/mm², but differed by up to 0.014 in FA.

With the two shells together, the single-tensor model no longer describes the decay, and the weighting also decides how the two shells are balanced. The measured-signal fit stayed 0.126 to 0.138 µm²/ms below the other linear arms, and the three defaults, which agreed within 0.0005 µm²/ms on one shell, now differed by up to 0.012 µm²/ms in MD: MRtrix3's default exceeded DIPY's by 0.012 and FSL's OLS default exceeded DIPY's by 0.010. FSL `--wls` and MRtrix3 `-iter 0` agreed on every input.

### 3.12. Inadmissible tensor fits

The arms differed in how often they returned inadmissible fits (Table 9). On Stanford, almost no white matter voxel was inadmissible in any arm; the inadmissible fits lay at the edge of the brain mask (91 to 99% within two voxels of it) in 0.2 to 0.8% of brain voxels. On Sherbrooke, the measured-signal fit returned a negative eigenvalue in 5.2% of white matter voxels, MRtrix3's default in 3.2% and FSL's OLS default in 3.2%; most of these voxels lie in clusters of ten or more, half of them in or next to cerebrospinal fluid, and half contain a measurement below half the noise SD (Supplementary Figure S5). Denoising reduced the rate of the measured-signal fit to 3.8%.

DIPY's WLS fit returned no negative eigenvalue in any run, because it replaces them with a small positive value before computing FA and MD. Before that step, the same fit has a negative eigenvalue in 3.1% of Sherbrooke white matter voxels, the rate of FSL's OLS default (Supplementary Table S12). DIPY's zero count reflects an implementation choice rather than a better fit, and it is the one implementation difference between the toolkits that changes values in white matter. The rate of inadmissible fits tracked acquisition quality: over the whole brain mask it was 9 to 15 times higher on Sherbrooke than on Stanford for the two arms that report negative eigenvalues.

## 4. Discussion

### 4.1. What the toolkit label does and does not specify

The central result is that FSL and MRtrix3 return the same tensor when given the same estimator. In white matter, two separately developed implementations agree in FA, MD and every tensor component to the precision of their output files, on two datasets, three shell selections, denoised data and 38 test-retest scans. For these two toolkits and versions, implementation is not what separates them.

What separates them is the estimator each toolkit applies by default, and the command does not show it. `dwi2tensor dwi.mif tensor.mif` and `dtifit -k data -o out ...` appear to be the same operation expressed in two syntaxes, whereas one performs iteratively reweighted least squares and the other ordinary least squares.

On one shell, the defaults agree with one another in MD within 0.002 µm²/ms. Measured-signal weighting, which FSL users reach through `--wls`, differs from each default by 0.02 to 0.09 µm²/ms. In FA the pattern is less clear: on Sherbrooke the measured-signal fit is 0.13 to 0.19 SD of white matter FA from the other estimators, but on Stanford FSL's OLS default differs from the two predicted-signal defaults about as much as from the measured-signal fit.

This result changes the meaning of "software-related variability" for the tensor fit. The differences in our first analysis were real, but they were not differences between codebases. They were differences between estimators, bundled as defaults or options. The two require different remedies: a difference between codebases must be corrected by the developers, whereas a difference between estimators can be removed by the analyst with one command-line argument.

The title refers to most of the difference rather than all of it, for two reasons. DIPY replaces negative eigenvalues with a small positive value before computing FA and MD, and FSL and MRtrix3 do not. This is an implementation choice, and on Sherbrooke it changes values in 3% of white matter voxels. And in voxels with very low signal outside white matter, FSL and MRtrix3 differ because they floor the signal differently, FSL at 1% of S₀ and MRtrix3 at 10⁻⁶ of the voxel maximum (Supplementary Table S11). Neither affects the comparison in white matter once inadmissible fits are excluded, but both are implementation differences, and the title and conclusions are phrased accordingly.

### 4.2. Agreement is not accuracy

Agreement between implementations shows that they compute the same quantity. It does not show that the quantity is right. Accuracy was assessed only against synthetic ground truth: the phantom, the simulations on the real gradient tables, and the crossing-fibre and partial-volume scenarios. On real data we report agreement and difference, not error, because the true tensor is unknown and the measurement is limited by noise, by the single-tensor model and by spatial systematic errors in the b-matrix that neither dataset allows us to characterise (Krzyżak et al., 2024, 2025). The phantom and simulations show which weighting scheme is closer to truth under their assumptions. The real data show how large the resulting differences are and how they behave. The two kinds of evidence are kept apart throughout.

### 4.3. Alternative explanations tested

Nine alternative explanations could undermine these conclusions. Each was tested directly.

- **The toolkits are implemented differently.** With the estimator matched, FSL and MRtrix3 agreed in every tensor component (Table 3; Supplementary Table S12).
- **The software, not the weights, causes the difference.** Swapping the weights inside DIPY removed all of it (Table 4).
- **The pattern is specific to weighted linear fits.** In MD, OLS, IWLS, NLLS and RESTORE all differed from the measured-signal fit, in the same direction (Table 5).
- **All schemes are equally accurate.** Against known eigenvalues with Rician noise, measured-signal weighting was the most biased in the single-fibre region, and more so at lower SNR (Table 6). In simulations of both real protocols, it had the largest MD bias and error in every condition (Supplementary Table S3).
- **The ranking depends on the single-tensor model holding.** With crossing fibres and partial volume, scored against each estimator's own noise-free fit, the ranking was the same in every scenario (Supplementary Table S13).
- **The voxel set favours one arm.** Voxels were selected by a tissue segmentation of the mean images, without any tensor fit, and fits were excluded on their eigenvalues; the grouping of the arms was the same at a stricter tissue threshold (Supplementary Table S10).
- **A small number of inadmissible fits distort the statistics.** They would do so if retained; all statistics therefore use admissible voxels only, every table states how many were excluded, and the main comparisons are also given over every voxel with robust summaries (Supplementary Table S12).
- **Noise alone explains the real-data differences.** This holds to a large extent. Noise added to each voxel's own tensor at the measured noise level reproduced 93% of the Stanford FA offset and 86 to 93% of the MD offsets (Table 7). No gradient-table error or signal dropout was found. Denoising reduced the MD offset by 42 to 58% (Table 8).
- **The noise model or the b-matrix is wrong.** With non-central χ noise, every arm acquired the same floor bias and the offset between schemes shrank but kept its sign (Supplementary Table S14). With errors in the b-matrix, no bias changed by more than 0.001 unless the error was systematic, and then every arm shifted together (Supplementary Table S15).

### 4.4. The recommended weighting scheme, and which defaults follow it

Salvador et al. (2005) showed that the weights of a linear tensor fit should come from the signal predicted by a preliminary fit, and Veraart et al. (2013) measured the cost of taking them from the measured signal instead. Our phantoms reproduce that cost for the configurations the toolkits distribute: in the single-fibre region, measured-signal weighting was the only scheme with a substantial MD bias, and its bias grew as SNR fell. On simulated versions of the two real protocols, its MD bias and error were the largest in every condition. Its FA bias was the largest in every condition on the Stanford protocol, but in only 8 of 30 on the Sherbrooke protocol, where it partly offset the upward FA bias that noise causes at low FA.

MRtrix3 and DIPY use predicted-signal weights by default, so both follow the recommendation. FSL's OLS default was close to unbiased in the phantom, though with the highest FA RMSE. The exception is FSL's weighted option. `--wls` implements the single-step measured-signal weighting that this literature advises against. A user may reasonably regard `--wls` as the more principled choice; it is the scheme the literature advises against, and the interface does not indicate this.

We do not propose a new estimator or contradict the existing recommendation. We show which configurations of widely used toolkits carry the documented bias, that the command does not reveal it, and how large it is at realistic SNR.

### 4.5. Why a systematic offset matters

A constant bias would cancel if every participant were processed the same way. The test-retest data show that this bias is not constant. On 38 scans from four scanners, the MD offset of measured-signal weighting averaged 9% of MD before preprocessing and 3% after it, but it ranged from 0.3 to 15% between scans and followed each scan's SNR, within a scanner as well as between scanners. Its mean on one scanner was three times its mean on another. The consequence is that measured-signal weighting raised the between-scanner variability of MD by a factor of 1.9 on unprocessed data and 1.6 on preprocessed data, while leaving within-session and between-subject variability unchanged. An estimator that converts differences in SNR into differences in MD adds variance between scanners, which is the component that multi-site studies most need to control.

The same data place the two kinds of difference on one scale. The difference between implementations at a matched estimator was zero to the precision of the output. The difference between the toolkit defaults was 0.03 to 0.4% of MD, below the within-session variability of 0.8 to 1.4%. The difference between weighting schemes was 3 to 9% of MD, six to fifteen times the between-session variability. In FA, the weighting offset of 1% on unprocessed data fell to 0.5% after preprocessing, below the within-session variability, so for FA the choice of estimator has little practical effect at b = 1000 s/mm².

The simulations say why the MD offset follows SNR: the bias scales with 1/SNR², and SNR differs between scanners, coils, protocols and participants. Groups that differ in SNR will differ in MD if they are fitted with measured-signal weights. This matters most for multi-site pooling, normative reference values and comparisons between cohorts acquired differently.

### 4.6. Multi-shell input

The main analysis gave every toolkit one shell. With both Sherbrooke shells, the three defaults, which agree within 0.0005 µm²/ms on one shell, differed by up to 0.012 µm²/ms in MD, and the measured-signal fit sat 0.13 µm²/ms below them. When the model does not describe the decay across shells, the weighting also decides how the shells are balanced, and the toolkits balance them differently. The grouping of the arms by weighting scheme survived, but the agreement between defaults did not. Studies that fit a single tensor to multi-shell data should expect larger toolkit differences than on one shell, from the same cause.

### 4.7. The reporting problem

Methods sections usually record the toolkit and its version. On this evidence, that level of description is insufficient. Two studies reporting "MRtrix3 3.0.8" may have used different estimators if one passed `-iter 0`. Two studies reporting different toolkits may have used the same one. The toolkit name alone does not tell a reader what was computed.

Three items suffice: the estimator, the source of its weights, and any non-default fitting argument. Our own first analysis illustrates the consequence of omitting them: it compared IWLS with WLS and attributed the difference to the toolkit.

### 4.8. Inadmissible fits as a quality indicator

DIPY's WLS fit returned no negative eigenvalue in any run. FSL and MRtrix3 returned them in up to 5% of Sherbrooke white matter voxels. DIPY's zero count follows from its clipping of negative eigenvalues; before that step its fit has the same rate as FSL's default. The count therefore says nothing about which toolkit fits better, but it says something about the data. It was an order of magnitude higher on Sherbrooke than on Stanford, it fell with denoising, and the voxels concerned cluster where the signal is lowest. A rule on FA and MD alone would have missed most of them, because a tensor with one negative eigenvalue can still have FA below one and MD above zero. Agreement statistics on tensor maps should therefore exclude fits on their eigenvalues, and should report how many were excluded.

### 4.9. Limitations

The real-data analysis uses one subject from each of two datasets, and one adult for the within-session test-retest. This is enough for the central claim, that two implementations of one estimator agree, because that is a property of the software rather than the sample, and the test-retest cohort adds five adults on four scanners. It is not enough to describe how the difference between schemes varies across populations or acquisitions.

The noise level and its distribution are uncertain. The MP-PCA σ was checked against the b = 0 volumes, PIESNO, the residuals and the image background, which agreed on Stanford but not on Sherbrooke, where the background suggests spatially varying, non-Rician noise from a multi-channel reconstruction. The share of each offset that noise reproduces is reported at several noise levels rather than as one number, and the simulations were repeated under non-central χ noise. The simulated ground truth is the DIPY fit of the noisy data, which is a self-consistency check rather than an independent truth. No correction of the magnitude noise floor was applied before fitting; such a correction is expected to reduce the floor bias that every estimator shares, and its effect on the difference between weighting schemes was not tested.

Part of the real-data offsets remains unexplained. At the measured noise level, 7 to 14% of the offsets are not reproduced by noise on the real tensors. The residuals of Stanford's most anisotropic voxels show the angular pattern expected of single-tensor misfit at b = 2000 s/mm², but this was not tested directly on the real data. The Sherbrooke FA offset is small enough that its sign is not interpreted.

Spatial systematic errors in the b-matrix were not characterised, because neither dataset provides gradient-field information or a phantom measurement. The simulations show that such errors shift every estimator together and do not change the comparison between them, but absolute FA and MD values on real data remain limited by them, and at high SNR they may be the dominant source of error.

Eddy-current and motion correction were tested only through the dataset's own preprocessing of the test-retest scans. The test-retest analysis uses the white matter mean of each scan; regional variability is larger and was not examined. Only FA and MD from the single tensor were examined. Finally, defaults can change between releases; our results refer to FSL 6.0.7, MRtrix3 3.0.8 and DIPY 1.12.1.

## 5. Conclusion

Given identical input and the same estimator, FSL and MRtrix3 return the same diffusion tensor. Differences between these toolkits at the fitting stage are therefore mostly differences between estimators, not implementations. The estimators are set by defaults and options, and the command line does not name them. MRtrix3 reweights its fit twice. DIPY takes its weights from a predicted signal. FSL performs ordinary least squares unless `--wls` is passed.

Which weighting scheme is more accurate in MD was established by Salvador et al. (2005) and Veraart et al. (2013), and our phantoms and simulations confirm it for the distributed configurations, with crossing fibres and partial volume included. MRtrix3 and DIPY follow the recommendation by default. FSL's weighted option does not, and the interface does not indicate this. On repeated scans from four scanners, the difference it makes to MD exceeds test-retest variability and grows with falling SNR, so it adds variance between scanners rather than a constant shift.

The practical consequence concerns reporting. The toolkit and version do not describe what was computed. The estimator and the source of its weights do, and reporting them requires one sentence.

## CRediT authorship contribution statement

**Busra Mutlu Ipek:** Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft, Writing – review and editing.

## Declaration of competing interest

The author declares that she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Funding

This work was carried out during a doctoral scholarship funded by the Republic of Türkiye Ministry of National Education (YLSY programme). The funder had no role in study design; in the collection, analysis or interpretation of data; in the writing of the report; or in the decision to submit the article for publication.

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used Claude (Anthropic) to assist with drafting and editing the manuscript and with writing analysis code. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## Data availability

The source code, Dockerfile and analysis scripts are openly available at https://github.com/happybrotherhood/dmri-rosetta-stone under the MIT licence. The version reported here is archived on Zenodo as release v1.2.0, under the concept DOI 10.5281/zenodo.22106454. This DOI always resolves to the latest version and lists every archived release. The Stanford HARDI and Sherbrooke 3-shell datasets are distributed openly by the DIPY project at https://dipy.org and are retrieved by `scripts/fetch_sample_data.py`. The MASiVar scans are distributed on OpenNeuro as dataset ds003416 under a CC0 licence and are retrieved by `scripts/fetch_masivar.py`. No registration or credentials are needed to reproduce any result. Supplementary Section S8 lists the commands that regenerate every table.

## Acknowledgements

The author thanks the DIPY project for distributing the Stanford HARDI and Sherbrooke 3-shell datasets openly, the MASiVar investigators for distributing their test-retest data openly, and the two reviewers, whose comments led to the test-retest comparison, the eigenvalue-based admissibility rule and the additional simulations.

## References

Basser PJ, Mattiello J, and LeBihan D (1994) MR diffusion tensor spectroscopy and imaging. *Biophysical Journal* 66, 259–267. doi: 10.1016/S0006-3495(94)80775-1

Beaulieu C (2002) The basis of anisotropic water diffusion in the nervous system – a technical review. *NMR in Biomedicine* 15, 435–455. doi: 10.1002/nbm.782

Cai LY, Yang Q, Hansen CB, Nath V, Ramadass K, Johnson GW, et al. (2021b) PreQual: An automated pipeline for integrated preprocessing and quality assurance of diffusion weighted MRI images. *Magnetic Resonance in Medicine* 86, 456–470. doi: 10.1002/mrm.28678

Cai LY, Yang Q, Kanakaraj P, Nath V, Newton AT, Edmonson HA, et al. (2021a) MASiVar: Multisite, multiscanner, and multisubject acquisitions for studying variability in diffusion weighted MRI. *Magnetic Resonance in Medicine* 86, 3304–3320. doi: 10.1002/mrm.28926

Chang LC, Jones DK, and Pierpaoli C (2005) RESTORE: Robust estimation of tensors by outlier rejection. *Magnetic Resonance in Medicine* 53, 1088–1095. doi: 10.1002/mrm.20426

Chung S, Lu Y, and Henry RG (2006) Comparison of bootstrap approaches for estimation of uncertainties of DTI parameters. *NeuroImage* 33, 531–541. doi: 10.1016/j.neuroimage.2006.07.001

Garyfallidis E, Brett M, Amirbekian B, Rokem A, Van Der Walt S, Descoteaux M, et al. (2014) Dipy, a library for the analysis of diffusion MRI data. *Frontiers in Neuroinformatics* 8, 8. doi: 10.3389/fninf.2014.00008

Gudbjartsson H and Patz S (1995) The Rician distribution of noisy MRI data. *Magnetic Resonance in Medicine* 34, 910–914. doi: 10.1002/mrm.1910340618

Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, and Smith SM (2012) FSL. *NeuroImage* 62, 782–790. doi: 10.1016/j.neuroimage.2011.09.015

Jones DK (ed.) (2010) *Diffusion MRI: Theory, Methods, and Applications*. Oxford: Oxford University Press.

Jones DK and Cercignani M (2010) Twenty-five pitfalls in the analysis of diffusion MRI data. *NMR in Biomedicine* 23, 803–820. doi: 10.1002/nbm.1543

Koay CG, Özarslan E, and Pierpaoli C (2009) Probabilistic Identification and Estimation of Noise (PIESNO): A self-consistent approach and its applications in MRI. *Journal of Magnetic Resonance* 199, 94–103. doi: 10.1016/j.jmr.2009.03.005

Koay CG, Chang LC, Carew JD, Pierpaoli C, and Basser PJ (2006) A unifying theoretical and algorithmic framework for least squares methods of estimation in diffusion tensor imaging. *Journal of Magnetic Resonance* 182, 115–125. doi: 10.1016/j.jmr.2006.06.020

Krzyżak AT, Lasek J, Schneider Z, Wnuk M, Bryll A, Popiela T, and Słowik A (2024) Diffusion tensor imaging metrics as natural markers of multiple sclerosis-induced brain disorders with a low Expanded Disability Status Scale score. *NeuroImage* 290, 120567. doi: 10.1016/j.neuroimage.2024.120567

Krzyżak AT, Lasek J, and Słowik A (2025) Diagnostic performance of a multi-shell DTI protocol and its subsets with B-matrix spatial distribution correction in differentiating early multiple sclerosis patients from healthy controls. *Frontiers in Neurology* 16, 1618582. doi: 10.3389/fneur.2025.1618582

Maier-Hein KH, Neher PF, Houde JC, Côté MA, Garyfallidis E, Zhong J, et al. (2017) The challenge of mapping the human connectome based on diffusion tractography. *Nature Communications* 8, 1349. doi: 10.1038/s41467-017-01285-x

Merkel D (2014) Docker: Lightweight Linux containers for consistent development and deployment. *Linux Journal* 2014, 2.

Rokem A, Yeatman JD, Pestilli F, Kay KN, Mezer A, van der Walt S, et al. (2015) Evaluating the accuracy of diffusion MRI models in white matter. *PLOS ONE* 10, e0123272. doi: 10.1371/journal.pone.0123272

Salvador R, Peña A, Menon DK, Carpenter TA, Pickard JD, and Bullmore ET (2005) Formal characterization and extension of the linearized diffusion tensor model. *Human Brain Mapping* 24, 144–155. doi: 10.1002/hbm.20076

Schilling KG, Rheault F, Petit L, Hansen CB, Nath V, Yeh FC, et al. (2021) Tractography dissection variability: What happens when 42 groups dissect 14 white matter bundles on the same dataset? *NeuroImage* 243, 118502. doi: 10.1016/j.neuroimage.2021.118502

Smith SM, Jenkinson M, Woolrich MW, Beckmann CF, Behrens TEJ, Johansen-Berg H, et al. (2004) Advances in functional and structural MR image analysis and implementation as FSL. *NeuroImage* 23 (Suppl 1), S208–S219. doi: 10.1016/j.neuroimage.2004.07.051

Tax CMW, Grussu F, Kaden E, Ning L, Rudrapatna U, Evans CJ, et al. (2019) Cross-scanner and cross-protocol diffusion MRI data harmonisation: A benchmark database and evaluation of algorithms. *NeuroImage* 195, 285–299. doi: 10.1016/j.neuroimage.2019.01.077

Tournier JD, Smith RE, Raffelt D, Tabbara R, Dhollander T, Pietsch M, et al. (2019) MRtrix3: A fast, flexible and open software framework for medical image processing and visualisation. *NeuroImage* 202, 116137. doi: 10.1016/j.neuroimage.2019.116137

Veraart J, Sijbers J, Sunaert S, Leemans A, and Jeurissen B (2013) Weighted linear least squares estimation of diffusion MRI parameters: strengths, limitations, and pitfalls. *NeuroImage* 81, 335–346. doi: 10.1016/j.neuroimage.2013.05.028

Veraart J, Novikov DS, Christiaens D, Ades-aron B, Sijbers J, and Fieremans E (2016) Denoising of diffusion MRI using random matrix theory. *NeuroImage* 142, 394–406. doi: 10.1016/j.neuroimage.2016.08.016

## Tables

**Table 1. Tensor-fitting configurations compared.** Every arm received identical input. "Weights from" gives the source of the weights in the final fit, as documented by each project. MRtrix3's default weights its first step by the measured signal and its two later iterations by the predicted signal.

| Arm | Command | Estimator | Weights from | Toolkit default |
|---|---|---|---|---|
| FSL, default | `dtifit` | OLS | none | yes |
| FSL, weighted | `dtifit --wls` | WLS | measured signal | no |
| MRtrix3, default | `dwi2tensor` | WLS + 2 × IWLS | predicted signal | yes |
| MRtrix3, matched | `dwi2tensor -iter 0` | WLS | measured signal | no |
| DIPY, default | `TensorModel(fit_method="WLS")` | WLS | predicted signal (initial OLS fit) | yes |
| DIPY, non-linear | `fit_method="NLLS"` | NLLS | not applicable | no |
| DIPY, robust | `fit_method="RESTORE"` | RESTORE | not applicable | no |

**Table 2. Weighted fits as usually set up.** FSL `dtifit --wls`, MRtrix3 `dwi2tensor` at its default and DIPY WLS at its default, with identical input. Agreement is over FAST white matter (96,773 voxels on Stanford, 100,005 on Sherbrooke), restricted to voxels whose tensor is admissible in both arms of each pair; n gives the voxels compared. The difference is the first arm minus the second. MD in µm²/ms.

| Dataset | Comparison | n | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|---|---|
| Stanford | FSL vs. MRtrix3 | 96,770 | 0.9973 | 0.0156 | −0.0149 | 0.9775 | 0.0242 | −0.0242 |
|  | FSL vs. DIPY | 96,773 | 0.9975 | 0.0140 | −0.0133 | 0.9790 | 0.0237 | −0.0236 |
|  | MRtrix3 vs. DIPY | 96,770 | 0.9999 | 0.0017 | +0.0017 | 0.9999 | 0.0006 | +0.0006 |
| Sherbrooke | FSL vs. MRtrix3 | 94,781 | 0.9727 | 0.0330 | +0.0017 | 0.9420 | 0.0863 | −0.0863 |
|  | FSL vs. DIPY | 94,828 | 0.9724 | 0.0332 | +0.0043 | 0.9433 | 0.0858 | −0.0858 |
|  | MRtrix3 vs. DIPY | 96,799 | 0.9999 | 0.0026 | +0.0026 | 1.0000 | 0.0005 | +0.0005 |

**Table 3. The same comparison with the estimator matched.** MRtrix3 is constrained to one weighted fit (`dwi2tensor -iter 0`); in Table 2 it ran two reweighting iterations. Voxels as in Table 2. LoA is the 95% limit of agreement (1.96 SD of the difference). MD in µm²/ms.

| Dataset | Comparison | n | FA r | FA MAE | FA difference | FA LoA | MD r | MD MAE | MD difference | MD LoA |
|---|---|---|---|---|---|---|---|---|---|---|
| Stanford | FSL vs. MRtrix3 | 96,773 | 1.0000 | 0.0000 | 0.0000 | ±0.0000 | 1.0000 | 0.0000 | 0.0000 | ±0.0000 |
|  | FSL vs. DIPY | 96,773 | 0.9975 | 0.0140 | −0.0133 | ±0.0286 | 0.9790 | 0.0237 | −0.0236 | ±0.0355 |
|  | MRtrix3 vs. DIPY | 96,773 | 0.9975 | 0.0140 | −0.0133 | ±0.0286 | 0.9790 | 0.0237 | −0.0236 | ±0.0355 |
| Sherbrooke | FSL vs. MRtrix3 | 94,829 | 1.0000 | 0.0000 | 0.0000 | ±0.0000 | 1.0000 | 0.0000 | 0.0000 | ±0.0000 |
|  | FSL vs. DIPY | 94,828 | 0.9724 | 0.0332 | +0.0043 | ±0.0901 | 0.9433 | 0.0858 | −0.0858 | ±0.0863 |
|  | MRtrix3 vs. DIPY | 94,828 | 0.9724 | 0.0332 | +0.0043 | ±0.0901 | 0.9433 | 0.0858 | −0.0858 | ±0.0863 |

**Table 4. Changing the weights inside one toolkit.** The same DIPY WLS code was run twice on the same data: with its default weights (squared signal predicted by an initial OLS fit) and with measured-signal weights. Each run is compared with FSL `dtifit --wls` on the white matter voxels admissible in all three fits (96,773 on Stanford, 94,828 on Sherbrooke). The difference is DIPY minus FSL. MD in µm²/ms.

| Dataset | DIPY weights | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|---|
| Stanford | predicted (default) | 0.9975 | 0.0140 | +0.0133 | 0.9790 | 0.0237 | +0.0236 |
|  | measured (as FSL) | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| Sherbrooke | predicted (default) | 0.9724 | 0.0332 | −0.0043 | 0.9433 | 0.0858 | +0.0858 |
|  | measured (as FSL) | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |

**Table 5. Every estimator against the measured-signal fit, and the defaults against one another.** The reference is FSL `dtifit --wls`. Each dataset uses one voxel set: FAST white matter with an admissible tensor in all seven arms (96,770 voxels on Stanford, 94,641 on Sherbrooke). The difference is the arm minus the reference, or the first default minus the second. MAE/SD is the FA MAE divided by the SD of reference FA over the same voxels (0.1770 and 0.1964). MD in µm²/ms.

| Dataset | Arm | FA r | FA MAE | FA difference | MAE/SD | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|---|---|
| Stanford | MRtrix3 `-iter 0` | 1.0000 | 0.0000 | 0.0000 | 0.00 | 1.0000 | 0.0000 | 0.0000 |
|  | FSL default (OLS) | 0.9958 | 0.0114 | +0.0023 | 0.06 | 0.9826 | 0.0220 | +0.0220 |
|  | MRtrix3 default (IWLS) | 0.9973 | 0.0156 | +0.0149 | 0.09 | 0.9775 | 0.0242 | +0.0242 |
|  | DIPY WLS (default) | 0.9975 | 0.0140 | +0.0133 | 0.08 | 0.9794 | 0.0237 | +0.0236 |
|  | DIPY NLLS | 0.9986 | 0.0112 | +0.0106 | 0.06 | 0.9886 | 0.0176 | +0.0176 |
|  | DIPY RESTORE | 0.9983 | 0.0117 | +0.0108 | 0.07 | 0.9877 | 0.0177 | +0.0177 |
|  | *Defaults:* FSL vs. MRtrix3 | 0.9975 | 0.0139 | −0.0127 | 0.08 | 0.9983 | 0.0023 | −0.0022 |
|  | *Defaults:* FSL vs. DIPY | 0.9979 | 0.0125 | −0.0110 | 0.07 | 0.9991 | 0.0018 | −0.0016 |
|  | *Defaults:* MRtrix3 vs. DIPY | 0.9999 | 0.0017 | +0.0017 | 0.01 | 0.9999 | 0.0006 | +0.0006 |
| Sherbrooke | MRtrix3 `-iter 0` | 1.0000 | 0.0000 | 0.0000 | 0.00 | 1.0000 | 0.0000 | 0.0000 |
|  | FSL default (OLS) | 0.9658 | 0.0372 | −0.0036 | 0.19 | 0.9426 | 0.0859 | +0.0859 |
|  | MRtrix3 default (IWLS) | 0.9725 | 0.0330 | −0.0018 | 0.17 | 0.9421 | 0.0862 | +0.0862 |
|  | DIPY WLS (default) | 0.9722 | 0.0332 | −0.0043 | 0.17 | 0.9433 | 0.0857 | +0.0857 |
|  | DIPY NLLS | 0.9841 | 0.0250 | −0.0047 | 0.13 | 0.9724 | 0.0618 | +0.0618 |
|  | DIPY RESTORE | 0.9812 | 0.0267 | −0.0033 | 0.14 | 0.9708 | 0.0621 | +0.0621 |
|  | *Defaults:* FSL vs. MRtrix3 | 0.9947 | 0.0143 | −0.0018 | 0.07 | 0.9997 | 0.0013 | −0.0003 |
|  | *Defaults:* FSL vs. DIPY | 0.9947 | 0.0141 | +0.0007 | 0.07 | 0.9998 | 0.0013 | +0.0002 |
|  | *Defaults:* MRtrix3 vs. DIPY | 0.9999 | 0.0025 | +0.0025 | 0.01 | 1.0000 | 0.0005 | +0.0005 |

**Table 6. Accuracy against a known ground truth.** Synthetic phantoms with Rician noise; single-fibre region (true FA = 0.7071, true MD = 0.70 µm²/ms; 5,408 voxels per region). SNR refers to one b = 0 volume. Bias is estimate minus truth; its standard error was at most 0.0009 for FA and 0.0007 for MD. Supplementary Table S2 gives the isotropic region. MD in µm²/ms.

| SNR | Arm | Weights | FA bias | FA RMSE | MD bias | MD RMSE |
|---|---|---|---|---|---|---|
| 30 | FSL `--wls` | measured | −0.0039 | 0.0212 | −0.0065 | 0.0182 |
|  | MRtrix3 `-iter 0` | measured | −0.0039 | 0.0212 | −0.0065 | 0.0182 |
|  | DIPY WLS (default) | predicted | −0.0005 | 0.0206 | +0.0001 | 0.0171 |
|  | MRtrix3 default | predicted | +0.0003 | 0.0206 | +0.0004 | 0.0171 |
|  | FSL default (OLS) | none | +0.0003 | 0.0232 | +0.0004 | 0.0173 |
| 20 | FSL `--wls` | measured | −0.0081 | 0.0325 | −0.0147 | 0.0292 |
|  | MRtrix3 `-iter 0` | measured | −0.0081 | 0.0325 | −0.0147 | 0.0292 |
|  | DIPY WLS (default) | predicted | −0.0007 | 0.0309 | −0.0001 | 0.0256 |
|  | MRtrix3 default | predicted | +0.0010 | 0.0309 | +0.0007 | 0.0257 |
|  | FSL default (OLS) | none | +0.0013 | 0.0348 | +0.0007 | 0.0260 |
| 10 | FSL `--wls` | measured | −0.0257 | 0.0703 | −0.0542 | 0.0728 |
|  | MRtrix3 `-iter 0` | measured | −0.0257 | 0.0703 | −0.0542 | 0.0728 |
|  | DIPY WLS (default) | predicted | −0.0014 | 0.0614 | −0.0022 | 0.0516 |
|  | MRtrix3 default | predicted | +0.0046 | 0.0614 | +0.0006 | 0.0521 |
|  | FSL default (OLS) | none | +0.0068 | 0.0694 | +0.0011 | 0.0530 |

**Table 7. Offset between the weighting schemes: real data against noise on the real tensors.** Each value is measured-signal minus predicted-signal weighting. Voxels are FAST white matter with FA above 0.2 in the DIPY WLS fit, binned by that FA. Observed: FSL `dtifit --wls` minus DIPY WLS on unprocessed data. Simulated: in each voxel, the DIPY tensor and S₀ defined a noise-free signal. Rician noise was added at the voxel's MP-PCA σ (1.00σ) or at 1.27σ (the ratio measured on the Stanford b = 0 volumes, corrected for small-sample bias), and both schemes were refitted. Values are means over five noise draws, with standard errors of at most 0.0002. Voxels with an inadmissible fit were excluded from observed and simulated values alike (observed: 0.0% on Stanford and 5.9% on Sherbrooke; simulated: up to 0.0% and 11.6%). Supplementary Table S6 gives the other rules, and Supplementary Table S4 the simulation with idealised tensors. MD in µm²/ms.

| Dataset | FA bin | Voxels | FA observed | FA sim (1.00σ) | FA sim (1.27σ) | MD observed | MD sim (1.00σ) | MD sim (1.27σ) |
|---|---|---|---|---|---|---|---|---|
| Stanford | 0.2–0.3 | 17,608 | −0.0112 | −0.0069 | −0.0105 | −0.0207 | −0.0116 | −0.0181 |
|  | 0.3–0.4 | 14,351 | −0.0159 | −0.0098 | −0.0148 | −0.0235 | −0.0131 | −0.0203 |
|  | 0.4–0.5 | 13,097 | −0.0190 | −0.0118 | −0.0178 | −0.0252 | −0.0138 | −0.0214 |
|  | 0.5–0.6 | 8,654 | −0.0232 | −0.0145 | −0.0217 | −0.0291 | −0.0160 | −0.0244 |
|  | 0.6–0.7 | 5,123 | −0.0263 | −0.0165 | −0.0246 | −0.0341 | −0.0193 | −0.0290 |
|  | 0.7–1.0 | 3,031 | −0.0288 | −0.0184 | −0.0267 | −0.0518 | −0.0303 | −0.0438 |
|  | All | 61,864 | −0.0177 | −0.0110 | −0.0166 | −0.0261 | −0.0146 | −0.0223 |
| Sherbrooke | 0.2–0.3 | 18,448 | +0.0039 | −0.0003 | +0.0023 | −0.0703 | −0.0396 | −0.0617 |
|  | 0.3–0.4 | 17,466 | +0.0023 | +0.0002 | +0.0036 | −0.0803 | −0.0462 | −0.0712 |
|  | 0.4–0.5 | 14,468 | +0.0029 | +0.0004 | +0.0039 | −0.0906 | −0.0553 | −0.0845 |
|  | 0.5–0.6 | 12,885 | +0.0035 | −0.0002 | +0.0028 | −0.0978 | −0.0626 | −0.0952 |
|  | 0.6–0.7 | 10,604 | +0.0045 | −0.0010 | +0.0013 | −0.1026 | −0.0670 | −0.1013 |
|  | 0.7–1.0 | 13,915 | +0.0045 | −0.0014 | +0.0000 | −0.1128 | −0.0763 | −0.1132 |
|  | All | 87,786 | +0.0034 | −0.0002 | +0.0026 | −0.0889 | −0.0546 | −0.0827 |

**Table 8. Sensitivity to denoising.** Mean difference between the arms of Table 2, before and after MP-PCA denoising, each on the white matter voxels admissible in both arms. Denoising was applied once, to the data given to every arm. The difference is the first arm minus the second. MD in µm²/ms.

| Dataset | Comparison | FA difference, raw | FA difference, denoised | MD difference, raw | MD difference, denoised |
|---|---|---|---|---|---|
| Stanford | FSL vs. MRtrix3 | −0.0149 | −0.0092 | −0.0242 | −0.0140 |
|  | FSL vs. DIPY | −0.0133 | −0.0076 | −0.0236 | −0.0134 |
|  | MRtrix3 vs. DIPY | +0.0017 | +0.0016 | +0.0006 | +0.0005 |
| Sherbrooke | FSL vs. MRtrix3 | +0.0017 | −0.0013 | −0.0863 | −0.0362 |
|  | FSL vs. DIPY | +0.0043 | 0.0000 | −0.0858 | −0.0360 |
|  | MRtrix3 vs. DIPY | +0.0026 | +0.0013 | +0.0005 | +0.0002 |

**Table 9. Inadmissible tensor fits.** Arms of Table 2, before and after denoising. A fit is inadmissible when an eigenvalue is negative or the largest eigenvalue exceeds 3.0 µm²/ms. Each cell gives the number and percentage of FAST white matter voxels, then the percentage of all voxels in the brain mask. DIPY reports no negative eigenvalue because it replaces them with a small positive value; before that step, its WLS fit has a negative eigenvalue in 3.1% of Sherbrooke white matter voxels (Supplementary Table S12).

| Dataset | Data | Arm | Any | Negative eigenvalue | Largest eigenvalue > 3.0 |
|---|---|---|---|---|---|
| Stanford | raw | FSL `--wls` | 0 (0.00%) / 0.78% | 0 (0.00%) / 0.78% | 0 (0.00%) / 0.00% |
|  |  | MRtrix3 default | 3 (0.00%) / 0.49% | 3 (0.00%) / 0.38% | 0 (0.00%) / 0.17% |
|  |  | DIPY WLS | 0 (0.00%) / 0.22% | 0 (0.00%) / 0.00% | 0 (0.00%) / 0.22% |
|  | denoised | FSL `--wls` | 0 (0.00%) / 0.65% | 0 (0.00%) / 0.65% | 0 (0.00%) / 0.00% |
|  |  | MRtrix3 default | 4 (0.00%) / 0.51% | 4 (0.00%) / 0.40% | 0 (0.00%) / 0.14% |
|  |  | DIPY WLS | 0 (0.00%) / 0.20% | 0 (0.00%) / 0.00% | 0 (0.00%) / 0.20% |
| Sherbrooke | raw | FSL `--wls` | 5,176 (5.18%) / 7.28% | 5,176 (5.18%) / 6.28% | 0 (0.00%) / 1.01% |
|  |  | MRtrix3 default | 3,206 (3.21%) / 7.39% | 3,201 (3.20%) / 3.39% | 5 (0.00%) / 4.00% |
|  |  | DIPY WLS | 1 (0.00%) / 3.91% | 0 (0.00%) / 0.00% | 1 (0.00%) / 3.91% |
|  | denoised | FSL `--wls` | 3,771 (3.77%) / 5.60% | 3,771 (3.77%) / 4.07% | 0 (0.00%) / 1.53% |
|  |  | MRtrix3 default | 3,178 (3.18%) / 5.95% | 3,178 (3.18%) / 3.26% | 0 (0.00%) / 2.70% |
|  |  | DIPY WLS | 0 (0.00%) / 2.67% | 0 (0.00%) / 0.00% | 0 (0.00%) / 2.67% |

**Table 10. Estimator differences against test-retest variability on MASiVar.** Thirty-eight scans at b = 1000 s/mm² (Cohort I: one adult, 3 sessions, 11 scans on one scanner; Cohort II: five adults on four scanners, 27 scans), fitted unprocessed and after the dataset's PreQual preprocessing. Each arm is summarised by its mean over the scan's white matter (FA > 0.2 and an admissible tensor in all five arms). Variability is the coefficient of variation (%) of one estimator: within session and between sessions (Cohort I), between repeat sessions on one scanner, between scanners within a subject, and between subjects on one scanner (Cohort II). Offsets are the mean difference between arms as a percentage of the mean, with the range across scans. The last rows give the between-scanner CoV with the measured-signal estimator and with the three defaults.

| Quantity | FA, raw | FA, preprocessed | MD, raw | MD, preprocessed |
|---|---|---|---|---|
| Within-session CoV | 0.66–0.72 | 0.73–0.77 | 0.93–1.36 | 0.84–0.89 |
| Between-session CoV, Cohort I | 0.15–0.42 | 0.59–0.75 | 0.84–1.52 | 1.42–1.85 |
| Between-session CoV, Cohort II | 0.31–0.38 | 0.35–0.36 | 0.55–0.79 | 0.80–0.93 |
| Between-subject CoV | 2.55–2.70 | 2.48–2.52 | 1.23–1.45 | 1.21–1.22 |
| Offset, measured-signal vs. other linear arms (range) | 1.1–1.3 (0.2–2.2) | 0.4–0.6 (0.0–1.0) | 8.5–9.0 (3.1–15.0) | 2.8–2.9 (0.3–6.6) |
| Offset between toolkit defaults | 0.24–1.42 | 0.14–0.81 | 0.05–0.44 | 0.03–0.10 |
| Measured-signal offset, mean per scanner (1A, 1B, 2, 3) | −0.0069, −0.0024, −0.0039, −0.0041 | −0.0025, −0.0010, −0.0025, −0.0022 | −0.074, −0.051, −0.025, −0.031 | −0.035, −0.016, −0.009, −0.006 |
| Spearman ρ, offset against b = 0 SNR (n = 34) | +0.34 | −0.31 | +0.95 | +0.65 |
| Between-scanner CoV, three defaults | 3.20–3.26 | 3.36–3.40 | 2.93–3.07 | 3.04–3.07 |
| Between-scanner CoV, measured-signal weighting | 2.80 | 3.26 | 5.72 | 4.75 |

## Figure captions

**Figure 1.** Design of the comparison. Both datasets are open and need no credentials. Every arm receives identical input: one brain mask, one volume subset (b = 0 plus a single shell) and no preprocessing. Only the estimator varies. Arms are labelled by the source of their weights. FSL `--wls` and MRtrix3 `-iter 0` weight by the measured signal. MRtrix3's default and DIPY WLS weight by a predicted signal. FSL's default is unweighted. Statistics use white matter defined by a tissue segmentation, without any tensor fit, and tensors whose eigenvalues are admissible. The five linear-fit arms are scored against phantoms with known eigenvalues, and the weighting schemes are compared in simulations on each dataset's gradient table and on repeated scans from four scanners. Toolkit colours match Figure 2.

**Figure 2.** Agreement with the estimator matched, Stanford HARDI dataset: FSL `dtifit --wls`, MRtrix3 `dwi2tensor -iter 0` and DIPY WLS. Supplementary Figure S4 shows the Sherbrooke equivalent. Top row: FA maps from each toolkit, with identical input and one shared brain mask. Middle row: voxelwise FA for each pair over FAST white matter, restricted to tensors admissible in both arms, with Pearson r, MAE, the number of voxels and the identity line. Bottom row: Bland–Altman plots of the FA difference (first minus second) against the pair mean. The solid line is the mean difference, and the dashed lines are ±1.96 SD. FSL and MRtrix3 coincide, and both differ from DIPY by the same amount. Each panel names the command it ran. Where the axis of a Bland–Altman panel is narrower than the widest difference, the panel states how many voxels fall outside it.

**Figure 3.** The estimator offset on repeated scans from four scanners (MASiVar, b = 1000 s/mm²). (A, B) The difference in white matter mean MD between measured-signal weighting (FSL `dtifit --wls`, identical to MRtrix3 `dwi2tensor -iter 0`) and predicted-signal weighting (DIPY WLS), for each scan, against the scan's b = 0 SNR, on unprocessed data (A) and after the dataset's PreQual preprocessing (B). Colours and symbols identify the scanner. The four site 2 scans are absent because their SNR is undefined (Materials and methods). (C) White matter mean MD of each estimator for every unprocessed scan, grouped by scanner. The three toolkit defaults coincide; the measured-signal fit lies below them by an amount that varies between scans and between scanners.

**Figure 4.** The MD bias of measured-signal weighting and its reproduction by noise. (A) Bias of each linear estimator in the single-fibre region of the phantom (Table 6) as a function of the b = 0 SNR; noise increases to the right. (B, C) The observed offset between measured-signal and predicted-signal weighting on the real data, by FA bin (Table 7), against the offset produced by adding Rician noise to each voxel's own fitted tensor at the voxel's MP-PCA σ (1.00σ) and at the noise level measured on the Stanford b = 0 volumes (1.27σ), for the Stanford (B) and Sherbrooke (C) datasets. Colours of the estimators match Figure 2.
