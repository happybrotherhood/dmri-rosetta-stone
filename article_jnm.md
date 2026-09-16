# Diffusion MRI toolkits differ in which estimator they use, not in how they implement the tensor fit

**Busra Mutlu**¹\*

¹ Department of Neuroimaging, King's College London, London, United Kingdom

\* **Corresponding author.** Busra Mutlu, Department of Neuroimaging, King's College London, De Crespigny Park, London SE5 8AF, United Kingdom. E-mail: [KCL EMAIL]

## Abstract

**Background.** Veraart et al. (2013) showed that weighting a linear tensor fit by the measured signal biases the estimates. Weights from a predicted signal reduce this bias. Whether widely used toolkits follow this result has not been measured.

**New method.** We fitted tensors with FSL, MRtrix3 and DIPY on two open datasets. Every input was held identical, so the estimator rather than the toolkit varied. The weighting schemes were tested against Rician-noise phantoms and against simulations on the real gradient tables.

**Results.** FSL `--wls` and MRtrix3 `-iter 0` implement the same estimator and return matching tensors (r = 1.0000). The toolkits differ in the estimator they apply. MRtrix3 and DIPY weight by a predicted signal by default. FSL fits ordinary least squares by default; its `--wls` option weights by the measured signal. In the phantom's anisotropic region, that scheme had the largest bias. At SNR 10 it underestimated FA by 0.026 and MD by 0.054 µm²/ms; the other linear fits stayed within 0.007 of truth. On real data it differed from every other estimator by 0.023–0.119 µm²/ms in MD. The toolkit defaults agreed with one another within 0.004 µm²/ms.

**Comparison with existing methods.** Earlier work documents variability between analysis pipelines. Here, the variability from the tensor fit is traced to one estimator, selected by a command-line flag.

**Conclusions.** For FSL and MRtrix3, implementation is not the variable; the estimator is. Its MD bias grows as SNR falls, and can therefore differ between groups. Methods sections should report the estimator and its weighting, not only the toolkit.

**Keywords:** diffusion MRI; tensor fitting; weighted least squares; estimator bias; signal-to-noise ratio; reproducibility; software defaults

## Introduction

Diffusion MRI (dMRI) is the main non-invasive technique for probing white matter microstructure in the living brain (Basser et al., 1994; Jones, 2010). Fractional anisotropy (FA) and mean diffusivity (MD), derived from the diffusion tensor, remain its most widely reported measures. They are used in studies of development, ageing and disease (Beaulieu, 2002; Jones, 2010).

Three open-source packages dominate their computation: FSL (Smith et al., 2004; Jenkinson et al., 2012), MRtrix3 (Tournier et al., 2019) and DIPY (Garyfallidis et al., 2014). Each fits the tensor. Methods sections usually name the package, as if that identified the computation.

Whether it does is a question of reproducibility. Analyses of the same data diverge when the pipeline, the analysing group or the scanner changes (Maier-Hein et al., 2017; Schilling et al., 2021; Tax et al., 2019). The fitting procedure is also a recognised pitfall of tensor analysis (Jones and Cercignani, 2010). These studies vary many choices at once, so a narrower question remains open. When only the software performing the tensor fit differs, how far do the toolkits disagree? And what inside the software is responsible?

The estimation literature suggests where to look. A linear fit to the log-signal is usually weighted, because the logarithm distorts the noise (Salvador et al., 2005; Koay et al., 2006). The weights can come from the measured signal or from a signal predicted by an earlier fit. Veraart et al. (2013) compared the two. They described the resulting loss of accuracy as surprisingly high. Iteratively updated weights from a predicted signal performed better, in some cases better than non-linear least squares.

Whether the toolkits apply this result has not been examined. Each relevant choice is documented. MRtrix3 states that `dwi2tensor` reweights its fit twice. DIPY cites Chung et al. (2006) for its weights. FSL lists `--wls` in its help text. The manuals show that the components differ. They do not show whether two implementations of one estimator agree. Nor do they show which configurations carry the bias, how large it is at a realistic signal-to-noise ratio (SNR), or how it compares with the effect of changing toolkit.

We measured these directly. All three toolkits ran in one container on byte-identical data from two open datasets. We varied the estimator and swapped the weights inside one toolkit. We then scored the configurations against phantoms with known eigenvalues and against simulations on the real gradient tables. Every value can be regenerated from openly available data.

## Materials and methods

### Data

Two open datasets from the DIPY project were analysed. Neither requires registration. The Stanford HARDI dataset (Rokem et al., 2015) has 160 volumes: 10 at b = 0 and 150 directions at b = 2000 s/mm². Voxels are 2 mm isotropic (matrix 81 × 106 × 76). The Sherbrooke 3-shell dataset (Garyfallidis et al., 2014) has 193 volumes: one at b = 0 and 64 directions at each of b = 1000, 2000 and 3500 s/mm². Voxels are 2 mm isotropic (matrix 128 × 128 × 60). It has no dedicated acquisition paper, so we used it as an independent acquisition rather than a characterised reference. The two datasets differ in site, protocol, b-value, angular sampling and number of b = 0 volumes.

SNR was measured rather than inferred from the protocol. The noise standard deviation was the median, over white matter, of the noise map from MRtrix3 `dwidenoise` (Marchenko–Pastur PCA, MP-PCA; Veraart et al., 2016). The noise map was computed from each dataset's full series, before shell selection. SNR is the mean signal of one b = 0 volume, or of the fitted shell, divided by this value. Throughout, white matter means voxels with FA > 0.2. The SNR of a single b = 0 volume was 32.1 for Stanford and 10.8 for Sherbrooke. The SNR of the fitted shell was 9.5 for Stanford (b = 2000 s/mm²) and 5.9 for Sherbrooke (b = 1000 s/mm²). As a check, noise was also measured directly on Stanford, which has 10 b = 0 volumes. In each white matter voxel, the SD across those volumes was divided by the MP-PCA σ, and the median ratio was 1.23. The SD of ten samples is biased low; dividing by its median for Gaussian noise (0.963) gives 1.28. This ratio may include motion and physiological fluctuation, which also affect the fit. The SNRs above may therefore be overestimates.

### Comparison design

Figure 1 summarises the design. Each fitting configuration is called an arm. Every arm received identical input: the same unprocessed volumes, the same gradient table and one shared brain mask from DIPY `median_otsu`. No preprocessing was applied, because any preprocessing step is itself a toolkit-specific choice. Denoising was tested separately. The results therefore describe the fitting stage, not a complete pipeline.

The single-tensor model assumes monoexponential decay, which does not hold across shells. FSL `dtifit` and MRtrix3 `dwi2tensor` fit every volume they receive, whereas DIPY expects the user to select a shell. Multi-shell input would therefore have given the toolkits different data. We extracted the b = 0 and b = 1000 s/mm² volumes of the Sherbrooke data (65 of 193) once and gave them to every arm. The Stanford data are single-shell and were used whole.

For each pair of arms, we computed three statistics over white matter: the voxelwise Pearson correlation (r), the mean absolute error (MAE), and the Bland–Altman mean difference with 95% limits of agreement. MD is reported in µm²/ms. Statistics used only voxels with physically admissible values in the two arms being compared (Table 4 applies the FA criterion only). FA had to lie within [0, 1]. MD had to be above zero and at most 3.0 µm²/ms (3.0 × 10⁻³ mm²/s), the diffusivity of free water at body temperature.

This restriction matters. Unconstrained linear fits can return negative eigenvalues, which push FA above one and MD below zero. Such values dominate a correlation. On the Stanford data, 124 inadmissible voxels (0.19% of white matter) lower the MD agreement between MRtrix3 and DIPY from r = 0.9965 to r = 0.110. They also raise the MAE tenfold. For three arms, the number of fits with FA above one or MD at or below zero is also reported (see Results).

### Estimators compared

Table 1 lists the arms. At their defaults, the three toolkits use three different estimators:

- FSL `dtifit` performs ordinary least squares (OLS).
- MRtrix3 `dwi2tensor` performs weighted least squares (WLS) with measured-signal weights. It then runs two iterations of reweighted least squares (IWLS), with weights from the predicted signal.
- DIPY performs one WLS fit. Its weights come from the signal predicted by a preliminary OLS fit (Chung et al., 2006).

Four non-default arms were added. FSL `dtifit --wls` is FSL's weighted option. MRtrix3 `dwi2tensor -iter 0` stops after the first, measured-signal step, so MRtrix3 and FSL can be compared on one estimator. DIPY's non-linear least squares (NLLS) and RESTORE (Chang et al., 2005) test whether a pattern is specific to weighted linear fits. Both used DIPY's defaults; for RESTORE, the noise level is estimated from the residuals. MRtrix3's final weights come from a predicted signal, so its default is grouped with the predicted-signal schemes.

### Manipulating the weighting scheme

This test asks whether the source of the weights, rather than the software, explains why DIPY differs. DIPY's WLS fit was run twice on the same data. The first run used its default predicted-signal weights. The second used the squared measured signal as weights. Each run was compared with FSL `dtifit --wls`. Signals were floored at 1 before both fits, so that a zero-valued voxel cannot make the weighted design matrix singular.

### Accuracy against a known ground truth

Agreement between toolkits does not show which one is accurate. We therefore built synthetic phantoms with known eigenvalues at SNR 30, 20 and 10. This range runs from about the single-b = 0 SNR of the Sherbrooke data (10.8) to just below that of the Stanford data (32.1). With the corrected noise estimate (see Data), those two SNRs become 8.4 and 25.1. Each 30 × 30 × 30-voxel phantom has three regions:

- an isotropic region (eigenvalues 0.9, 0.9 and 0.9 µm²/ms; FA = 0, MD = 0.90 µm²/ms);
- a single-fibre region (1.4, 0.35 and 0.35 µm²/ms; FA = 0.7071, MD = 0.70 µm²/ms), oriented left–right in one half and superior–inferior in the other;
- a crossing-fibre region, excluded from scoring because no single tensor is correct there.

The fitted scheme had 10 b = 0 volumes and 30 directions at b = 1000 s/mm². Noise was Rician, as in magnitude images (Gudbjartsson and Patz, 1995). Gaussian noise with standard deviation 1000/SNR was added to the real and imaginary channels, and the magnitude was taken. S₀ was 1000 in the fibre regions, so SNR is as stated there. The isotropic region had S₀ = 800, so its SNR was 24, 16 and 8. Two voxels were trimmed from each in-plane edge of the volume, and one slice from each end of every region. This left 5,408 scored voxels per region. The five linear-fit arms were scored: FSL default and `--wls`, MRtrix3 default and `-iter 0`, and DIPY WLS. For each, we report bias (estimate minus truth), its standard error across voxels, and root-mean-square error (RMSE).

### Simulation on the real acquisition protocols

The phantom has one tensor shape and one gradient scheme, but the real datasets differ from it and from each other. We asked what noise alone predicts for each acquisition, in two simulations. Both used the exact gradient tables given to the toolkits. For Stanford, this was 10 b = 0 volumes and 150 directions at b = 2000 s/mm². For Sherbrooke, it was one b = 0 volume and 64 directions at b = 1000 s/mm².

The first simulation was simplified. Tensors were axially symmetric, with MD = 0.70 µm²/ms, FA from 0.25 to 0.80 and random orientation. S₀ and σ were the same in every voxel. Rician noise was added at SNR 10, 20, 30 and 50, and at each dataset's measured SNR. Each condition had 10,000 voxels. All four linear estimators were fitted to the same noisy voxels. For each, we report bias with its Monte Carlo standard error, and RMSE.

The second simulation kept the properties of the real data. It used the voxels with FA above 0.2 in the DIPY WLS fit, binned by that FA. In each voxel, the DIPY tensor and S₀ defined a noise-free signal, with negative eigenvalues clipped at zero. Rician noise was added at the voxel's own MP-PCA σ, and at 1.28 times that σ (see Data). Both weighting schemes were then refitted. Each noise level was simulated five times with independent noise. We report the mean; standard errors were at most 0.0006. Voxels and bins were not defined from the measured-signal fit, because that fit is the one whose offset is being measured. Non-physical fits were treated identically in observed and simulated data. The main rule excluded a voxel when either fit was physically inadmissible. As sensitivity analyses, FA was instead clipped to [0, 1] and MD to [0, 3] µm²/ms, or all values were kept as fitted. As an upper bound on the noise, we found the σ at which the simulated residuals were as widely spread as the real ones, measured by a robust SD. Real residuals also contain model misfit, so this bound overstates the noise.

Both simulations used the toolkits' linear estimators reimplemented in NumPy, so that noise, voxels and single measurements could be controlled. The reimplementations include each toolkit's signal floor, MRtrix3's two reweightings, and, for the DIPY arm only, DIPY's eigenvalue clipping. On the real data, they matched the published maps of FSL `--wls`, MRtrix3's default and DIPY WLS to a mean absolute FA difference below 0.00001 on both datasets. FSL's OLS default was matched to 0.0002. For that arm, however, 1.0–1.8% of voxels differed by more than 0.001. Of these, 82% on Stanford and over 99% on Sherbrooke contained a measurement below half the noise SD. Across all white matter voxels, the corresponding figures were 5% and 10%.

On the real data, we computed the same difference, FSL `--wls` minus DIPY WLS, over the voxels of the second simulation and in the same bins. The simplified simulation used the bin centres as FA values, except for the widest bin (0.7–1.0), which was simulated at 0.80.

Four further analyses addressed possible artefacts and the disagreement between the two simulations. First, each Sherbrooke volume given to the toolkits was matched by content to its source volume, and the b-value and direction of the two were compared. Second, the real data were refitted without diffusion-weighted measurements more than 3σ below the predicted signal, as signal dropout or misalignment would produce. They were also refitted without any measurement beyond ±3σ. Third, each voxel's real residuals were shuffled across gradient directions and added back to the fitted signal. This keeps the size of the residuals but breaks their link to direction. The exclusions and the shuffle were repeated on noise-only data at 1.28σ, as a control. Fourth, the idealisations of the simplified simulation were imposed one at a time on the real tensors: MD of 0.70 µm²/ms, axial symmetry, random orientation, and uniform S₀ and σ. Uniform σ alone was also tested.

### Sensitivity to denoising

We repeated the comparison of Table 2 on denoised data. MRtrix3 `dwidenoise` (MP-PCA; Veraart et al., 2016) was applied once to the full series, before shell selection. The denoised data were given to every arm, so the estimator remained the only variable. Giving each toolkit its own denoiser would not have been fairer: FSL has none, so it would have fitted noisier data. Eddy-current and motion correction were not tested.

### Execution environment and reproducibility

Running three toolkits on byte-identical input is the practical obstacle to this kind of comparison. We removed it with one Docker container (Merkel, 2014) that bundles FSL 6.0.7, MRtrix3 3.0.8 and DIPY 1.12.1 with Python 3.12. The same data pass through every toolkit without reinstallation or format conversion. The container also serves an interactive interface, which is described in Supplementary Section S1 but not evaluated here. Every results table is produced by a script in the repository, and Supplementary Section S6 lists the commands.

## Results

### As usually configured, the weighted fits make FSL appear anomalous

We first compared the weighted fits as they are usually set up (Table 2). FSL was run with `--wls`, its weighted option. MRtrix3 and DIPY were run at their defaults, which both weight. MRtrix3 and DIPY agreed closely (FA r = 0.9990 on Stanford and 0.9966 on Sherbrooke). FSL differed from both (FA r = 0.9604–0.9652 and 0.8897–0.9157). At face value, FSL appears anomalous.

The offsets did not behave like an implementation difference. FSL's MD was lower on both datasets, by 0.032–0.033 µm²/ms on Stanford and 0.127 µm²/ms on Sherbrooke. Its FA offset, however, changed sign. FSL was 0.018 lower than MRtrix3 on Stanford and 0.014 higher on Sherbrooke. This inconsistency prompted the checks below.

### Given the same estimator, FSL and MRtrix3 return the same tensor

MRtrix3's default is not a single weighted fit. It is WLS followed by two IWLS iterations. The comparison above therefore set reweighting against a single weighted fit, and attributed the result to the toolkit.

Constraining MRtrix3 to one weighted fit (`-iter 0`) reversed the grouping (Table 3; Figure 2). FSL and MRtrix3 then agreed to numerical precision in almost every voxel. For FA and MD on both datasets, r = 1.0000 and the MAE was below 0.0001. The 95% limits of agreement are ±0.0018 FA units on Stanford and ±0.0001 on Sherbrooke. The wider Stanford limits come from 57 voxels (0.09%) that differ by more than 0.001. In 40 of them, a measurement is at or below zero, which the two programs handle differently. Without these voxels, the limits are ±0.0001. At the same time, MRtrix3 moved away from DIPY, to FA r = 0.9602 and 0.8895. This was the distance that had separated FSL from DIPY.

Two separately developed implementations of the same closed-form estimator return the same tensor. That is expected if both are correct, and it rules out hidden implementation differences. The apparent toolkit effect was an estimator effect.

### What separates DIPY is the source of its weights

DIPY still differs even with MRtrix3 matched. MRtrix3 documents its first step as weighted by the measured signal. FSL `--wls` reproduces that step to numerical precision, so it also uses measured-signal weights. DIPY, in contrast, takes its weights from a signal predicted by a preliminary OLS fit.

The arms therefore group by the source of their weights, not by software (Tables 2 and 3):

- within the measured-signal group (FSL `--wls`, MRtrix3 `-iter 0`), FA r = 1.0000;
- within the predicted-signal group (DIPY, MRtrix3 default), FA r = 0.9990 on Stanford and 0.9966 on Sherbrooke;
- between the groups, FA r = 0.9601–0.9652 on Stanford and 0.8895–0.9157 on Sherbrooke.

We tested this grouping directly by changing the weights inside DIPY (Table 4). With measured-signal weights, DIPY's FA difference from FSL fell from an MAE of 0.0222 to 0.0003 on Stanford. On Sherbrooke it fell from 0.0468 to 0.0035. Its MD difference fell from 0.0320 to 0.0001 µm²/ms on Stanford, and from 0.1224 to 0.0022 µm²/ms on Sherbrooke. Changing one argument inside one toolkit removed almost all of the difference attributed to the choice of toolkit.

### In MD, measured-signal weighting differs from every other estimator

Table 5 compares every arm with the measured-signal fit, on one voxel set per dataset.

In MD, the pattern was consistent. OLS, IWLS, predicted-signal WLS, NLLS and RESTORE all differed from the measured-signal fit. The MAE was 0.023–0.032 µm²/ms on Stanford and 0.083–0.119 µm²/ms on Sherbrooke. The measured-signal fit was always the lower one. In contrast, the three toolkit defaults agreed with one another within 0.004 µm²/ms on both datasets.

In FA, the pattern holds on Sherbrooke. There, the other estimators differed from the measured-signal fit by 0.037–0.049, or 0.19–0.25 standard deviations (SD) of white matter FA. The defaults differed from one another by at most 0.018. On Stanford, the pattern is less sharp. The other estimators differed from the measured-signal fit by 0.017–0.024 (0.12–0.17 SD). However, FSL's OLS default was about as far from the two predicted-signal defaults (0.019–0.021) as from the measured-signal fit (0.017).

The comparison inside FSL shows what this means for a user. Switching `dtifit` from its default to `--wls` changed FA by an MAE of 0.0171 on Stanford and 0.0489 on Sherbrooke. It changed MD by 0.028 and 0.118 µm²/ms. Replacing FSL `--wls` with MRtrix3 at the same estimator changed neither. A flag inside one toolkit moves the result further than a change of toolkit at a fixed estimator.

### Against ground truth, measured-signal weighting is the most biased scheme

The phantoms showed which estimator is accurate (Table 6).

At SNR 30, in the single-fibre region, the measured-signal arms underestimated FA by 0.0039 and MD by 0.0065 µm²/ms. Standard errors were 0.0003 or less. Every other arm was within 0.0005 of truth in both metrics.

As SNR fell, the measured-signal bias grew. At SNR 20 it was −0.0081 in FA and −0.0147 µm²/ms in MD. At SNR 10 it was −0.0257 and −0.0542 µm²/ms. The other arms stayed within 0.0013 of truth at SNR 20 and within 0.007 at SNR 10. At SNR 10, FSL's OLS default (+0.0068) and MRtrix3's default (+0.0046) showed small but detectable positive FA biases. In the isotropic region, noise raised FA in every arm, least in the measured-signal arms. Only the measured-signal arms underestimated MD by a substantial amount (Supplementary Table S2).

The MD bias grew as theory predicts. Relative to SNR 30, it was 2.3 times larger at SNR 20 and 8.3 times larger at SNR 10. A bias caused by the correlation between weights and noise should scale with 1/SNR², which gives factors of 2.25 and 9. The FA bias grew more slowly, by 2.1 and 6.6 times.

Measured-signal weighting also had a higher RMSE than predicted-signal weighting at every SNR. In FA, the RMSE was 0.0212 against 0.0206 at SNR 30, and 0.0703 against 0.0614 at SNR 10. In MD, it was 0.0182 against 0.0171, and 0.0728 against 0.0516–0.0521. FSL's OLS default was close to unbiased, but it had the highest FA RMSE at SNR 30 and 20 (0.0232 and 0.0348). These results reproduce the finding of Veraart et al. (2013) for the configurations the toolkits distribute.

The phantom has ten b = 0 volumes, so we repeated the comparison in simulations on the two real gradient tables (Supplementary Table S3). There, measured-signal weighting had the largest MD bias and the largest MD RMSE of the four linear estimators in every condition. In FA, the result depended on the protocol. On the Stanford table, it had the largest FA bias in every condition, and the largest FA RMSE in all but one (SNR 50, FA 0.80). On the Sherbrooke table, with one b = 0 volume and b = 1000 s/mm², noise raised FA in most conditions, especially at low FA. The negative bias of measured-signal weighting partly offset this rise. Its absolute FA bias was therefore smaller than that of predicted-signal weighting in 21 of 30 conditions. It was the largest of the four estimators in only 8. Its FA RMSE was within 4% of the best estimator at SNR 20 and above, and 1.4–16.3% higher at SNR near 10.

### Noise on the real tensors reproduces most of the offsets

The MP-PCA SNR of the two datasets, 32.1 and 10.8, spans the phantom range; with the corrected noise estimate, Sherbrooke falls just below it (8.4). The MD offset between the weighting groups was about four times larger on Sherbrooke (−0.127 against −0.034 µm²/ms). We tested whether noise explains the offsets (Table 7).

The simplified simulation did not reproduce them (Supplementary Table S4). On Stanford, it matched the observed FA offset within 0.003 below FA 0.5, but fell short at higher FA (−0.0137 against −0.0410 in the most anisotropic bin). On Sherbrooke, it predicted the opposite sign: lower FA with measured-signal weighting, by 0.0045–0.0128, where the data showed higher FA, by 0.0099–0.0237. For MD on both datasets, it reproduced the sign of the offset but only 35–62% of its size.

Noise added to each voxel's own tensor reproduced the offsets much better. At the MP-PCA σ, it reproduced 71% of the Stanford FA offset and 57% of its MD offset, and 40% and 63% on Sherbrooke. At 1.28σ, the noise level measured on the Stanford b = 0 volumes, the shares were higher. The simulation reproduced 101% of the Stanford FA offset (−0.0167 against −0.0165) and 83% of its MD offset (−0.0279 against −0.0336). On Sherbrooke, it reproduced 89% of the FA offset (+0.0129 against +0.0145) and 87% of the MD offset (−0.1110 against −0.1270). At the upper bound set by the residuals, 1.39σ on Stanford and 1.33σ on Sherbrooke, the FA and MD shares were 115% and 93% on Stanford, and 99% and 92% on Sherbrooke.

The measured-signal fit was non-physical in 0.6% of these voxels on Stanford and 5.3% on Sherbrooke. On Sherbrooke, this made the FA offset depend on how such fits are treated (Supplementary Table S6). Clipping FA to [0, 1] raised the observed offset to +0.0195, and keeping values as fitted raised it to +0.0239. Treated the same way, noise-only data reproduced 94% and 106% of these FA offsets, and 86% and 91% of the MD offsets. On Stanford, the shares changed by at most 3.3 percentage points.

By bin, the match was close except in Stanford's most anisotropic voxels. On Stanford at 1.28σ, the simulated FA offset was within 0.003 of the observed offset in every bin below FA 0.7. Above it, the simulated offset was −0.0248 against −0.0410, and the MD offset −0.0451 against −0.0719. On Sherbrooke, the simulated FA offset was within 0.008 of the observed offset in every bin: smaller below FA 0.5 and larger above.

No single idealisation of the simplified simulation reversed the Sherbrooke sign under every rule (Supplementary Table S5). At the MP-PCA σ, setting MD to 0.70 µm²/ms, against a real white matter median of 0.594, reduced the FA offset from +0.0058 to +0.0020. Axial symmetry reduced it to +0.0029, and uniform S₀ and σ nearly removed it (−0.0001). Uniform σ alone increased it (+0.0088), so the relevant variation is in S₀. Random orientation had no effect. All four together reversed the offset under every rule (−0.0081 to −0.0086), close to the simplified simulation. Its opposite sign therefore comes from the combination of its idealisations, not from any one of them.

Checks of the real residuals found no pipeline error and no signal dropout (Supplementary Table S7). All 65 Sherbrooke volumes matched their source volumes and gradient entries, and no volume had more than three times the median rate of measurements below −3σ. Residuals beyond ±3σ were 1.7–2.4 times as common as in noise-only data at 1.28σ. Removing them changed the offsets more than in noise-only data, most for Sherbrooke FA (−45% against −29%) and Stanford MD (−20% against −10%). Shuffling the residuals across gradient directions changed the FA offset in the same direction in real and noise-only data (−66% against −70% on Sherbrooke, +46% against +28% on Stanford). The dependence of the FA offset on direction is therefore largely a property of noise.

Stanford's most anisotropic voxels, where noise fell short, showed a clear angular pattern. In voxels with FA of 0.6 or more, the median residual was negative at oblique angles and +0.89σ along the fibre, against +0.32σ in noise-only data. This pattern is consistent with a single tensor failing to fit the angular profile of the signal at b = 2000 s/mm². On Sherbrooke, at b = 1000 s/mm², the pattern was weak (+0.31σ against +0.19σ).

Denoising reduced the real-data offsets but did not remove them (Table 8). The MD offset between FSL `--wls` and MRtrix3's default fell by 44% on Stanford (from −0.0330 to −0.0186 µm²/ms). On Sherbrooke, it fell by 61% (from −0.1271 to −0.0494 µm²/ms). The FA offset shrank but kept opposite signs on the two datasets (−0.0134 and +0.0034). The small FA bias between MRtrix3 and DIPY changed little (from +0.0027 to +0.0026 on Stanford, and from +0.0053 to +0.0031 on Sherbrooke).

### Non-physical tensor fits

The arms differed in how often they returned non-physical values, FA above one or MD at or below zero (Table 9). Both arise from negative eigenvalues. DIPY WLS returned none in any of its four runs (both datasets, with and without denoising). This reflects an implementation choice rather than a better fit. When DIPY decomposes the tensor, it replaces negative eigenvalues with a small non-negative value. FSL and MRtrix3 report them unchanged. FSL and MRtrix3 returned them in 0.40% and 0.27% of white matter voxels on unprocessed Stanford data. On Sherbrooke, the rates were 3.97% and 2.03%.

Which of the two produced more was not stable. FSL produced more on unprocessed data. After denoising, MRtrix3 produced slightly more FA values above one on Stanford (0.29% against 0.23%). The rate tracked acquisition quality. It was roughly 4 to 11 times higher on Sherbrooke than on Stanford, for both toolkits, both metrics, and with or without denoising.

## Discussion

### What the toolkit label does and does not specify

The central result is that FSL and MRtrix3 return the same tensor when given the same estimator. Two separately developed implementations agree at r = 1.0000, with limits of agreement no wider than ±0.0018 FA units. For these two toolkits, implementation is not the variable.

What varies is the estimator each toolkit applies by default, and the command does not show it. `dwi2tensor dwi.mif tensor.mif` and `dtifit -k data -o out ...` look like the same operation in two dialects. In fact, one performs iteratively reweighted least squares and the other ordinary least squares.

In MD, the defaults agree with one another within 0.004 µm²/ms. Measured-signal weighting, which FSL users reach through `--wls`, differs from each default by 0.028–0.119 µm²/ms. In FA, it is equally distinct on Sherbrooke, at 0.23–0.25 SD of white matter FA from the defaults. On Stanford, however, FSL's OLS default differs from the other two defaults about as much as from the measured-signal fit.

This changes what "software-related variability" means for the tensor fit. The differences in our first analysis were real, but they were not differences between codebases. They were differences between estimators, bundled as defaults or options. The two have different remedies. A codebase difference needs the developers to act. An estimator difference can be removed by the analyst with one command-line argument.

### Alternative explanations tested

Six alternative explanations could undermine these conclusions. Each was tested directly.

- **The toolkits are implemented differently.** With the estimator matched, FSL and MRtrix3 agreed at r = 1.0000 (Table 3).
- **The software, not the weights, causes the difference.** Swapping the weights inside DIPY removed almost all of it (Table 4).
- **The pattern is specific to weighted linear fits.** In MD, OLS, IWLS, NLLS and RESTORE all differed from the measured-signal fit, in the same direction (Table 5).
- **All schemes are equally accurate.** Against known eigenvalues with Rician noise, measured-signal weighting was the most biased in the single-fibre region, and more so at lower SNR (Table 6). In simulations of both real protocols, it had the largest MD bias and error; its FA ranking depended on the protocol (Supplementary Table S3).
- **A few non-physical fits distort the statistics.** They would, so all statistics use admissible voxels only (Methods).
- **Noise alone explains the real-data differences.** Largely. Noise was added to each voxel's own tensor at the measured noise level. It reproduced 89–106% of the FA offsets and 80–91% of the MD offsets on the two datasets, depending on how non-physical fits are treated (Table 7; Supplementary Table S6). It falls short in Stanford's most anisotropic voxels, whose residuals show the pattern expected of single-tensor misfit. No gradient-table error or signal dropout was found (Results). Denoising reduced the MD offset by 44–61% (Table 8).

### The literature has an answer, and most defaults follow it

Veraart et al. (2013) reported that measured-signal weights degrade accuracy and that predicted-signal weights perform better. Our phantoms reproduce this for the configurations the toolkits distribute: in the single-fibre region, measured-signal weighting was the only scheme with a substantial MD bias, and its bias grew as SNR fell. On simulated versions of the two real protocols, its MD bias and error were the largest in every condition. Its FA bias was the largest in every condition on the Stanford protocol, but in only 8 of 30 on the Sherbrooke protocol. There it partly offset the upward FA bias that noise causes at low FA.

MRtrix3 and DIPY use predicted-signal weights by default, so both follow the recommendation. FSL's OLS default was close to unbiased in the phantom, though with the highest FA RMSE. The concern is FSL's weighted option. `--wls` implements the single-step measured-signal weighting that Veraart et al. caution against. A user may reasonably see `--wls` as the more principled choice. That user gets the scheme Veraart et al. advise against.

We do not propose a new estimator or contradict the existing recommendation. We show which configurations of widely used toolkits carry the documented bias. We also show that the command does not reveal it, and how large it is at a realistic SNR.

### Why a systematic offset matters

A constant bias would cancel if every participant were processed the same way. This bias is not constant, because it depends on SNR. Consider two groups with identical tissue, scanned at SNR 20 and 30 and both fitted with measured-signal weights (Supplementary Table S3, true FA 0.45). On the Stanford protocol, they would differ in MD by 0.021 µm²/ms and in FA by 0.020, about 0.14 SD of white matter FA. On the Sherbrooke protocol, they would differ in MD by 0.011 µm²/ms but in FA by only 0.0003, which is within the simulation's Monte Carlo error (standard error 0.0005). With predicted-signal weighting, the MD difference was below 0.001 µm²/ms on both protocols, and the FA difference was 0.0011 and 0.0027. The MD bias is therefore the concern that holds on both protocols. Whether FA is also affected depends on the protocol.

Groups do differ in SNR in practice. Scanner, site, coil and protocol all affect it, as do participant factors that alter image quality. Measured-signal weighting turns such differences into apparent differences in microstructure. This matters most for multi-site pooling, normative reference values and comparisons between cohorts acquired differently.

### The reporting problem

Methods sections usually record the toolkit and its version. On this evidence, that is the wrong level of description. Two studies reporting "MRtrix3 3.0.8" may have used different estimators if one passed `-iter 0`. Two studies reporting different toolkits may have used the same one. The toolkit name alone does not tell a reader what was computed.

What is needed is short: the estimator, the source of its weights, and any non-default fitting argument. Reporting checklists could require it. Our own first analysis shows the cost of leaving it out: it compared IWLS with WLS and wrongly concluded that one toolkit was anomalous.

### Non-physical fits as a quality indicator

DIPY's WLS fit returned no non-physical values in its four runs. FSL and MRtrix3 returned them in 0.14–3.97% of white matter voxels, depending on metric, acquisition and preprocessing. DIPY's zero count follows from its clipping of negative eigenvalues, so it does not show that DIPY fits better. The ranking of FSL and MRtrix3 was not stable.

The count is more useful as a diagnostic than as a ranking. It tracked acquisition quality, at roughly 4 to 11 times higher on Sherbrooke, and it is cheap to compute. It is also a source of error in agreement statistics. Left in place, 0.19% of white matter voxels reduced an MD correlation from r = 0.9965 to r = 0.110. Agreement statistics on tensor maps should use admissible voxels only, and should report how many were excluded.

### Limitations

The real-data analysis uses one subject from each of two datasets. This is enough for the central claim, that two implementations of one estimator agree, because that is a property of the software rather than the sample. It is not enough to describe how the difference between schemes varies across acquisitions.

Part of the real-data offsets remains unexplained. At the noise level measured on Stanford, noise on the real tensors leaves 13–17% of the MD offsets unexplained under the main rule, and 9–20% across the three rules. It also falls short in Stanford's most anisotropic voxels. That noise level is uncertain. It was measured on Stanford only, because Sherbrooke has a single b = 0 volume. The SD across b = 0 volumes may also include motion and physiological fluctuation. On Sherbrooke, the observed and simulated FA offsets also depend on how non-physical fits are treated; the reproduced share ranges from 89% to 106% across the three rules. The simulated ground truth is the DIPY fit of the noisy data, which on Sherbrooke is itself raised in FA by noise. Single-tensor misfit fits the angular pattern of the Stanford residuals but was not tested directly. Partial volume, eddy-current distortion and motion were not tested.

Eddy-current and motion correction were not applied. Denoising was the only preprocessing step whose effect on the fit was examined. The results therefore describe the fitting stage on unprocessed and denoised data, not a complete pipeline. Only FA and MD from the single tensor were examined.

The toolkits do differ in one implementation detail: DIPY clips negative eigenvalues, whereas FSL and MRtrix3 do not. This affects the voxels where the fit fails. It also accounts for the small residual difference between DIPY and FSL when both use measured-signal weights (FA MAE 0.0035 on Sherbrooke; Table 4). Without clipping, the same computation reproduces FSL `--wls` to a mean absolute FA difference below 0.00001 (Methods).

The phantom contains one anisotropic tensor shape and one gradient scheme, with Rician noise and no artefacts. DIPY's NLLS and RESTORE fits were not scored against it. The simulations use reimplemented estimators. These reproduce FSL `--wls`, MRtrix3's default and DIPY WLS to numerical precision in almost every voxel, and FSL's OLS default closely (Methods). At very low diffusion-weighted SNR, every scheme is biased in MD, and in FA except at the lowest true FA. SNR 10 on the Stanford gradient table (b = 2000 s/mm²) is such a case (Supplementary Table S3). Finally, defaults can change between releases; our results refer to FSL 6.0.7, MRtrix3 3.0.8 and DIPY 1.12.1.

## Conclusion

Given identical input and the same estimator, FSL and MRtrix3 return the same diffusion tensor. Differences between these toolkits at the fitting stage are therefore mainly differences between estimators, not implementations. The estimators are hidden behind defaults and options. MRtrix3 reweights its fit twice. DIPY takes its weights from a predicted signal. FSL performs ordinary least squares unless `--wls` is passed.

Which weighting scheme is more accurate in MD is already established. Veraart et al. (2013) showed that measured-signal weights degrade accuracy, and our phantoms and protocol simulations confirm it for the default configurations. MRtrix3 and DIPY follow the recommendation by default. FSL's weighted option does not, and nothing in the interface tells the user.

The practical consequence concerns reporting. The toolkit and version do not describe what was computed. The estimator and the source of its weights do, and they take one line to report.

## CRediT authorship contribution statement

**Busra Mutlu:** Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft, Writing – review and editing.

## Declaration of competing interest

The author declares that she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Funding

This work was carried out during a doctoral scholarship funded by the Republic of Türkiye Ministry of National Education (YLSY programme). The funder had no role in study design; in the collection, analysis or interpretation of data; in the writing of the report; or in the decision to submit the article for publication.

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used Claude (Anthropic) to assist with drafting and editing the manuscript and with writing analysis code. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## Data availability

The source code, Dockerfile and analysis scripts are openly available at https://github.com/happybrotherhood/dmri-rosetta-stone under the MIT licence. The version reported here is archived on Zenodo as release v1.1.0, under the concept DOI 10.5281/zenodo.22106454. This DOI always resolves to the latest version and lists every archived release. Both datasets, Stanford HARDI and Sherbrooke 3-shell, are distributed openly by the DIPY project at https://dipy.org and are retrieved by `scripts/fetch_sample_data.py`. No registration or credentials are needed to reproduce any result. Supplementary Section S6 lists the commands that regenerate every table.

## Acknowledgements

The author thanks the DIPY project for distributing the Stanford HARDI and Sherbrooke 3-shell datasets openly.

## References

Basser PJ, Mattiello J, and LeBihan D (1994) MR diffusion tensor spectroscopy and imaging. *Biophysical Journal* 66, 259–267. doi: 10.1016/S0006-3495(94)80775-1

Beaulieu C (2002) The basis of anisotropic water diffusion in the nervous system – a technical review. *NMR in Biomedicine* 15, 435–455. doi: 10.1002/nbm.782

Chang LC, Jones DK, and Pierpaoli C (2005) RESTORE: Robust estimation of tensors by outlier rejection. *Magnetic Resonance in Medicine* 53, 1088–1095. doi: 10.1002/mrm.20426

Chung S, Lu Y, and Henry RG (2006) Comparison of bootstrap approaches for estimation of uncertainties of DTI parameters. *NeuroImage* 33, 531–541. doi: 10.1016/j.neuroimage.2006.07.001

Garyfallidis E, Brett M, Amirbekian B, Rokem A, Van Der Walt S, Descoteaux M, et al. (2014) Dipy, a library for the analysis of diffusion MRI data. *Frontiers in Neuroinformatics* 8, 8. doi: 10.3389/fninf.2014.00008

Gudbjartsson H and Patz S (1995) The Rician distribution of noisy MRI data. *Magnetic Resonance in Medicine* 34, 910–914. doi: 10.1002/mrm.1910340618

Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, and Smith SM (2012) FSL. *NeuroImage* 62, 782–790. doi: 10.1016/j.neuroimage.2011.09.015

Jones DK (ed.) (2010) *Diffusion MRI: Theory, Methods, and Applications*. Oxford: Oxford University Press.

Jones DK and Cercignani M (2010) Twenty-five pitfalls in the analysis of diffusion MRI data. *NMR in Biomedicine* 23, 803–820. doi: 10.1002/nbm.1543

Koay CG, Chang LC, Carew JD, Pierpaoli C, and Basser PJ (2006) A unifying theoretical and algorithmic framework for least squares methods of estimation in diffusion tensor imaging. *Journal of Magnetic Resonance* 182, 115–125. doi: 10.1016/j.jmr.2006.06.020

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

**Table 2. Weighted fits as usually set up.** FSL `dtifit --wls`, MRtrix3 `dwi2tensor` at its default and DIPY WLS at its default, with identical input. Agreement is over white matter voxels (FA > 0.2 in all three), restricted to admissible values in both arms of each pair. The difference is the first arm minus the second. MD in µm²/ms.

*Stanford HARDI (65,002 white matter voxels)*

| Comparison | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 0.9652 | 0.0247 | −0.0181 | 0.9402 | 0.0333 | −0.0330 |
| FSL vs. DIPY | 0.9604 | 0.0228 | −0.0158 | 0.9368 | 0.0325 | −0.0322 |
| MRtrix3 vs. DIPY | 0.9990 | 0.0029 | +0.0027 | 0.9965 | 0.0012 | +0.0009 |

*Sherbrooke 3-shell, b = 0 and b = 1000 s/mm² (111,032 white matter voxels)*

| Comparison | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 0.9157 | 0.0460 | +0.0139 | 0.9020 | 0.1271 | −0.1271 |
| FSL vs. DIPY | 0.8897 | 0.0504 | +0.0148 | 0.9012 | 0.1272 | −0.1272 |
| MRtrix3 vs. DIPY | 0.9966 | 0.0059 | +0.0053 | 0.9991 | 0.0029 | −0.0009 |

**Table 3. The same comparison with the estimator matched.** MRtrix3 is constrained to one weighted fit (`dwi2tensor -iter 0`); in Table 2 it ran two reweighting iterations. The white matter mask is redefined from these three fits, so the voxel sets differ slightly from Table 2 (65,009 and 111,083 voxels). The difference is the first arm minus the second. MD in µm²/ms.

*Stanford HARDI*

| Comparison | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| FSL vs. DIPY | 0.9601 | 0.0228 | −0.0158 | 0.9367 | 0.0325 | −0.0322 |
| MRtrix3 vs. DIPY | 0.9602 | 0.0228 | −0.0158 | 0.9366 | 0.0325 | −0.0322 |

*Sherbrooke 3-shell*

| Comparison | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|
| FSL vs. MRtrix3 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| FSL vs. DIPY | 0.8895 | 0.0505 | +0.0149 | 0.9013 | 0.1274 | −0.1274 |
| MRtrix3 vs. DIPY | 0.8895 | 0.0505 | +0.0149 | 0.9012 | 0.1274 | −0.1274 |

**Table 4. Changing the weights inside one toolkit.** The same DIPY WLS code was run twice on the same data: with its default weights (squared signal predicted by an initial OLS fit) and with measured-signal weights. Each run is compared with FSL `dtifit --wls`. The difference is DIPY minus FSL. Voxels have FA above 0.2 and at most 1 in all three fits (64,629 on Stanford, 105,311 on Sherbrooke). MD in µm²/ms.

| Dataset | DIPY weights | FA r | FA MAE | FA difference | MD r | MD MAE | MD difference |
|---|---|---|---|---|---|---|---|
| Stanford | predicted (default) | 0.9662 | 0.0222 | +0.0152 | 0.9579 | 0.0320 | +0.0317 |
|  | measured (as FSL) | 0.9989 | 0.0003 | −0.0001 | 0.9982 | 0.0001 | +0.0001 |
| Sherbrooke | predicted (default) | 0.9173 | 0.0468 | −0.0201 | 0.9136 | 0.1224 | +0.1224 |
|  | measured (as FSL) | 0.9949 | 0.0035 | −0.0023 | 0.9962 | 0.0022 | +0.0022 |

**Table 5. Every estimator against the measured-signal fit, and the defaults against one another.** The reference is FSL `dtifit --wls`. Each dataset uses one voxel set: FA > 0.2, with admissible FA and MD in all seven arms (63,859 voxels on Stanford, 102,981 on Sherbrooke). The difference is the arm minus the reference, or the first default minus the second. MAE/SD is the FA MAE divided by the SD of reference FA over the same voxels (0.1464 and 0.1957). MD in µm²/ms.

| Dataset | Arm | FA r | FA MAE | FA difference | MAE/SD | MD MAE | MD difference |
|---|---|---|---|---|---|---|---|
| Stanford | MRtrix3 `-iter 0` | 1.0000 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 |
|  | FSL default (OLS) | 0.9686 | 0.0171 | −0.0014 | 0.12 | 0.0282 | +0.0280 |
|  | MRtrix3 default (IWLS) | 0.9697 | 0.0242 | +0.0184 | 0.17 | 0.0321 | +0.0319 |
|  | DIPY WLS (default) | 0.9703 | 0.0217 | +0.0156 | 0.15 | 0.0310 | +0.0308 |
|  | DIPY NLLS | 0.9788 | 0.0179 | +0.0125 | 0.12 | 0.0229 | +0.0228 |
|  | DIPY RESTORE | 0.9746 | 0.0186 | +0.0127 | 0.13 | 0.0233 | +0.0229 |
|  | *Defaults:* FSL vs. MRtrix3 | 0.9923 | 0.0213 | −0.0198 | 0.15 | 0.0040 | −0.0039 |
|  | *Defaults:* FSL vs. DIPY | 0.9938 | 0.0189 | −0.0171 | 0.13 | 0.0030 | −0.0029 |
|  | *Defaults:* MRtrix3 vs. DIPY | 0.9998 | 0.0027 | +0.0027 | 0.02 | 0.0010 | +0.0010 |
| Sherbrooke | MRtrix3 `-iter 0` | 1.0000 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 |
|  | FSL default (OLS) | 0.9151 | 0.0489 | −0.0173 | 0.25 | 0.1177 | +0.1177 |
|  | MRtrix3 default (IWLS) | 0.9238 | 0.0444 | −0.0144 | 0.23 | 0.1190 | +0.1190 |
|  | DIPY WLS (default) | 0.9195 | 0.0458 | −0.0185 | 0.23 | 0.1184 | +0.1184 |
|  | DIPY NLLS | 0.9413 | 0.0369 | −0.0182 | 0.19 | 0.0826 | +0.0826 |
|  | DIPY RESTORE | 0.9370 | 0.0384 | −0.0170 | 0.20 | 0.0837 | +0.0837 |
|  | *Defaults:* FSL vs. MRtrix3 | 0.9901 | 0.0175 | −0.0029 | 0.09 | 0.0028 | −0.0013 |
|  | *Defaults:* FSL vs. DIPY | 0.9899 | 0.0175 | +0.0012 | 0.09 | 0.0028 | −0.0007 |
|  | *Defaults:* MRtrix3 vs. DIPY | 0.9989 | 0.0043 | +0.0041 | 0.02 | 0.0013 | +0.0006 |

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

**Table 7. Offset between the weighting schemes: real data against noise on the real tensors.** Each value is measured-signal minus predicted-signal weighting. Voxels have FA above 0.2 in the DIPY WLS fit and are binned by that FA. Observed: FSL `dtifit --wls` minus DIPY WLS on unprocessed data. Simulated: in each voxel, the DIPY tensor and S₀ defined a noise-free signal. Rician noise was added at the voxel's MP-PCA σ (1.00σ) or at 1.28σ (the ratio measured on the Stanford b = 0 volumes, corrected for small-sample bias), and both schemes were refitted. Values are means over five noise draws, with standard errors of at most 0.0006. Voxels with a non-physical fit were excluded from observed and simulated values alike (observed: 0.6% on Stanford and 5.3% on Sherbrooke; simulated: up to 0.5% and 7.9%). Supplementary Table S6 gives the other rules, and Supplementary Table S4 the simplified simulation. MD in µm²/ms.

| Dataset | FA bin | Voxels | FA observed | FA sim (1.00σ) | FA sim (1.28σ) | MD observed | MD sim (1.00σ) | MD sim (1.28σ) |
|---|---|---|---|---|---|---|---|---|
| Stanford | 0.2–0.3 | 21,125 | −0.0077 | −0.0085 | −0.0106 | −0.0339 | −0.0210 | −0.0290 |
|  | 0.3–0.4 | 15,544 | −0.0140 | −0.0108 | −0.0155 | −0.0301 | −0.0176 | −0.0257 |
|  | 0.4–0.5 | 13,722 | −0.0186 | −0.0125 | −0.0185 | −0.0285 | −0.0161 | −0.0243 |
|  | 0.5–0.6 | 8,994 | −0.0231 | −0.0148 | −0.0223 | −0.0313 | −0.0175 | −0.0265 |
|  | 0.6–0.7 | 5,292 | −0.0272 | −0.0166 | −0.0249 | −0.0364 | −0.0204 | −0.0306 |
|  | 0.7–1.0 | 3,483 | −0.0410 | −0.0169 | −0.0248 | −0.0719 | −0.0319 | −0.0451 |
|  | All | 68,160 | −0.0165 | −0.0117 | −0.0167 | −0.0336 | −0.0193 | −0.0279 |
| Sherbrooke | 0.2–0.3 | 31,692 | +0.0099 | −0.0035 | +0.0022 | −0.1431 | −0.0818 | −0.1112 |
|  | 0.3–0.4 | 23,496 | +0.0154 | +0.0030 | +0.0110 | −0.1302 | −0.0764 | −0.1045 |
|  | 0.4–0.5 | 17,700 | +0.0168 | +0.0066 | +0.0157 | −0.1235 | −0.0760 | −0.1066 |
|  | 0.5–0.6 | 14,910 | +0.0137 | +0.0092 | +0.0177 | −0.1144 | −0.0765 | −0.1092 |
|  | 0.6–0.7 | 11,823 | +0.0124 | +0.0120 | +0.0195 | −0.1097 | −0.0768 | −0.1115 |
|  | 0.7–1.0 | 17,567 | +0.0237 | +0.0228 | +0.0289 | −0.1157 | −0.0933 | −0.1301 |
|  | All | 117,188 | +0.0145 | +0.0058 | +0.0129 | −0.1270 | −0.0800 | −0.1110 |

**Table 8. Sensitivity to denoising.** Mean difference between the arms of Table 2, before and after MP-PCA denoising. Denoising was applied once, to the data given to every arm. The difference is the first arm minus the second. MD in µm²/ms.

| Dataset | Comparison | FA difference, raw | FA difference, denoised | MD difference, raw | MD difference, denoised |
|---|---|---|---|---|---|
| Stanford | FSL vs. MRtrix3 | −0.0181 | −0.0134 | −0.0330 | −0.0186 |
|  | FSL vs. DIPY | −0.0158 | −0.0110 | −0.0322 | −0.0178 |
|  | MRtrix3 vs. DIPY | +0.0027 | +0.0026 | +0.0009 | +0.0009 |
| Sherbrooke | FSL vs. MRtrix3 | +0.0139 | +0.0034 | −0.1271 | −0.0494 |
|  | FSL vs. DIPY | +0.0148 | +0.0048 | −0.1272 | −0.0502 |
|  | MRtrix3 vs. DIPY | +0.0053 | +0.0031 | −0.0009 | −0.0011 |

**Table 9. Non-physical tensor fits in the white matter mask.** Arms of Table 2. Number of voxels with FA above one or MD at or below zero, with the percentage of the mask in parentheses, before and after denoising.

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

## Figure captions

**Figure 1.** Design of the comparison. Both datasets are open and need no credentials. Every arm receives identical input: one brain mask, one volume subset (b = 0 plus a single shell) and no preprocessing. Only the estimator varies. Arms are labelled by the source of their weights. FSL `--wls` and MRtrix3 `-iter 0` weight by the measured signal. MRtrix3's default and DIPY WLS weight by a predicted signal. FSL's default is unweighted. Statistics use physically admissible voxels only; otherwise a small number of inadmissible voxels can dominate a correlation. The five linear-fit arms are scored against phantoms with known eigenvalues. The weighting schemes are also compared in simulations on each dataset's gradient table, with idealised tensors and with each voxel's own fitted tensor. Toolkit colours match Figure 2.

**Figure 2.** Agreement with the estimator matched, Stanford HARDI dataset: FSL `dtifit --wls`, MRtrix3 `dwi2tensor -iter 0` and DIPY WLS. Supplementary Figure S4 shows the Sherbrooke equivalent. Top row: FA maps from each toolkit, with identical input and one shared brain mask. Middle row: voxelwise FA for each pair over white matter (FA > 0.2 in all three), with Pearson r, MAE and the identity line. Bottom row: Bland–Altman plots of the FA difference (first minus second) against the pair mean. The solid line is the mean difference, and the dashed lines are ±1.96 SD. FSL and MRtrix3 coincide (r = 1.0000, limits ±0.0018), and both differ from DIPY by the same amount. Inadmissible voxels are excluded. Each panel names the command it ran. Where the axis of a Bland–Altman panel is narrower than the widest difference, the panel states how many voxels fall outside it.
