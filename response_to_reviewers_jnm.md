# Response to Reviewers

Manuscript JNEUMETH-D-26-00997, revised title: "Estimator choice, not implementation, accounts for most of the difference in diffusion tensor fitting between FSL, MRtrix3 and DIPY"

I thank both reviewers for their careful reading and for comments that have improved the manuscript considerably. Every comment is answered below, with the page and line numbers of the revised manuscript where the change can be found. Line numbers run continuously through the manuscript.

Four changes affect the whole manuscript and are summarised here so that they need not be repeated under each point.

1. **Admissibility is now judged on the eigenvalues.** Both reviewers pointed out that a rule on FA and MD does not exclude a tensor with a negative eigenvalue. A fit is now admissible when all three eigenvalues are non-negative and the largest does not exceed 3.0 µm²/ms (p. 7, line 142). Every table states how many voxels each arm loses to the rule.
2. **The voxel set is defined without any tensor fit.** White matter is taken from a two-channel FSL FAST segmentation of the mean b = 0 and mean diffusion-weighted images (p. 7, line 136), so the same voxels are used for every arm. A stricter threshold gives the same conclusions (Supplementary Table S10).
3. **All numbers were regenerated** on this voxel set with the corrected rule, for every table and figure. The conclusions are unchanged; the values differ from the first version, and the specific differences are noted under the relevant points.
4. **The title, abstract and conclusions no longer make a categorical claim** about implementation differences (p. 1, line 1; p. 25, line 524; p. 32, line 670).

The new analyses asked for by the reviewers appear as new sections of the Methods (p. 5, line 88; p. 11, lines 236 to 245; p. 12, line 256; p. 13, line 268), new sections of the Results (p. 18, line 382; p. 21, line 431; p. 21, lines 442 and 450; p. 23, line 475), new Table 10, and new Supplementary Tables S8 to S15 and Figure S5. The repository has been updated and will be archived as release v1.2.0 on Zenodo under the existing concept DOI.

---

## Reviewer 1

### General concerns

**G1. The first takeaway, that implementation does not matter for closed-form linear estimators built on the same linear algebra libraries, is expected.**

I agree that agreement between two implementations of a closed-form estimator is expected in principle, and the revised manuscript no longer presents it as a finding in its own right. Its role is now that of a control: only once implementation is shown not to matter can the differences reported between toolkits be attributed to the estimator (Introduction, p. 3, line 60; Discussion, p. 24, line 505).

The agreement is nevertheless worth establishing, because the toolkits differ in the steps that surround the linear algebra: the signal floor, the treatment of non-positive measurements, the b-vector convention, the numerical precision and the handling of negative eigenvalues. These are now listed in Supplementary Table S11, with a statement of which entries were tested on the data. Two of them do produce differences: DIPY's clipping of negative eigenvalues changes values in 3% of Sherbrooke white matter voxels, and FSL and MRtrix3 differ in low-signal voxels outside white matter because they floor the signal differently, FSL at 1% of S₀ and MRtrix3 at 10⁻⁶ of the voxel maximum, as the FSL source code shows and a reimplementation confirms (Results, p. 15, line 310). Both are now reported, and they are the reason the title says "most of the difference" rather than all of it (Discussion, p. 25, line 524).

**G2. The second takeaway is not novel. Weighting by the OLS-predicted signal has been standard since Salvador et al. (2005), and is the default of the 3D Slicer DTI module.**

I thank the reviewer for this correction. The abstract and Introduction now credit Salvador et al. (2005) for showing that the weights should come from the signal predicted by a preliminary fit, with the option of iterative refinement, and position Veraart et al. (2013) as the study that quantified the cost of taking the weights from the measured signal instead (p. 1, line 8; p. 3, line 48). The Discussion and Conclusion were revised in the same way (p. 27, line 574; p. 32, line 670).

The manuscript does not claim the bias as a new finding. Its contribution is to show which configurations of the three most used toolkits implement each scheme, that FSL's only weighted option implements the one the literature advises against, and how large the resulting differences are next to test-retest variability (Introduction, p. 3, line 60). On 3D Slicer: its documentation for the DWIToDTIEstimation module offers least squares and weighted least squares, and describes the latter as weighting the samples by their intensity magnitude, without stating whether the intensity is the measured or a fitted value. I therefore did not add Slicer to the manuscript as an example of either scheme.

**G3. That reporting the toolkit and version is insufficient is common sense rather than a scientific finding.**

I agree, and the recommendation has been moved from the headline conclusions to a short section of the Discussion, where it is presented as a consequence of the results rather than as a result (p. 29, line 621). The abstract keeps one sentence on reporting, because the journal's structured abstract asks for the practical conclusion.

### Specific concerns

**S1. The choice of datasets: a single b = 2000 shell for Sherbrooke, the outer shells of Stanford excluded, the same resolution in both, and missing acquisition details.**

I apologise that the description of the two datasets was not clear enough, and I have rewritten it (p. 4, line 71) and added a table of acquisition parameters (Supplementary Table S8). To clarify: the Stanford HARDI dataset is single-shell, with 10 b = 0 volumes and 150 directions at b = 2000 s/mm², and was used whole. The Sherbrooke dataset has three shells, at b = 1000, 2000 and 3500 s/mm², of which the main analysis used b = 1000 s/mm².

The reviewer's underlying question is well taken, and the revised manuscript answers it with data. All seven arms were also fitted to the Sherbrooke b = 2000 s/mm² shell, so that the two datasets are compared at the same b-value (Methods, p. 12, line 256; Results, p. 23, line 475; Supplementary Table S16). At b = 2000 s/mm² the offset of measured-signal weighting from every other estimator grows to 0.12 µm²/ms in MD, as expected from the lower diffusion-weighted SNR, and the grouping of the arms is the same as at b = 1000 s/mm². The angular pattern of the Stanford residuals at b = 2000 s/mm², which is consistent with the limit of the tensor model that the reviewer describes, is reported in the Results (p. 20, line 423) and in the Limitations.

On acquisition details: Supplementary Table S8 gives the scanner, coil, sequence, TE, voxel size, matrix and gradient scheme of the Stanford data from Rokem et al. (2015). The Sherbrooke dataset has no acquisition paper. The only documented fact, stated by one of its authors on the DIPY mailing list in 2015, is that it was acquired on a 1.5 T Siemens scanner; the timing, coil and model are not recorded anywhere, and the table says so explicitly rather than leaving the entries blank. For neither dataset is the parallel-imaging factor or the reconstruction documented, and the consequences for the noise model are addressed under Reviewer 2, point 1.

On diversity: the test-retest data added in this revision (point S5) come from four scanners of three vendors at three sites, with voxel sizes of 1.9 to 2.5 mm, and give the comparison the range of acquisitions the reviewer asked for.

**S2. Only one shell at a time; multi-shell input not tested; the statement that DIPY cannot fit multi-shell data; the claim that the tensor model does not hold across shells is an oversimplification.**

The reviewer is right, and the statement about DIPY was inaccurate: DIPY's TensorModel fits every volume in the gradient table, as FSL and MRtrix3 do. The sentence has been removed, the use of one shell is now described as a design choice that separates the choice of shell from the choice of estimator, and the statement about the model is qualified (Methods, p. 12, line 256).

All seven arms were fitted to the Sherbrooke b = 1000 and 2000 s/mm² shells together (Results, p. 23, line 475; Supplementary Table S16). The result adds something to the paper. On one shell the three toolkit defaults agree within 0.0005 µm²/ms in MD. With both shells they differ by up to 0.012 µm²/ms, because the weighting now also decides how the two shells are balanced, while the measured-signal fit stays 0.13 µm²/ms below them, and FSL `--wls` and MRtrix3 `-iter 0` still agree exactly. This is discussed in a new section (p. 29, line 614).

**S3. The admissibility filter masks degeneracies; the spatial distribution of invalid voxels is not reported; the MD bound should apply to the largest eigenvalue.**

I agree on all three points.

The admissibility rule now applies to the eigenvalues: all three must be non-negative and the largest must not exceed 3.0 µm²/ms (p. 7, line 142). Table 9 reports the failures by type (negative eigenvalue, largest eigenvalue above the bound) for every arm, in white matter and in the whole brain, before and after denoising, and Supplementary Table S12 adds the four remaining arms and DIPY's fit before its eigenvalue clipping. On Sherbrooke the measured-signal fit has a negative eigenvalue in 5.2% of white matter voxels; the FA and MD rule of the first version missed 3.8% of white matter for that arm.

The spatial distribution is reported in Supplementary Figure S5 and in the last block of Supplementary Table S12: on Stanford, 91 to 99% of inadmissible voxels lie within two voxels of the brain edge; on Sherbrooke, 76 to 78% lie in clusters of ten or more voxels, half of them in or next to cerebrospinal fluid, and half contain a measurement below half the noise SD (Results, p. 23, line 486).

Degeneracy is now treated as a result in its own right rather than only as a nuisance (Discussion, p. 30, line 629), and the main comparisons are also given over every white matter voxel without exclusion, with robust summaries, in Supplementary Table S12.

**S4. The synthetic ground truth is a single pure tensor; crossing fibres and partial volume are not tested; Table 6 is therefore of limited relevance.**

I agree that a single tensor is a limited test, and I have followed the reviewer's suggestion. Nine scenarios were simulated on both real gradient tables at three SNR levels: one fibre, two fibres crossing at 30°, 60° and 90°, the fibre with 10%, 30% and 50% free water, and the fibre with 30% and 50% grey matter. Where no single tensor is correct, each estimator is scored against its own fit to the noise-free signal, which isolates the effect of noise from the effect of the mismatch (Methods, p. 11, line 236; Results, p. 18, line 382; Supplementary Table S13).

In every scenario, at every SNR and on both protocols, measured-signal weighting has the largest MD bias and the largest MD RMSE, and the offset between the weighting schemes grows with the free-water fraction because free water lowers the diffusion-weighted signal. Crossing fibres and partial volume change the value every estimator converges to, but not the ranking of the estimators. Table 6 is now presented as the replication of Veraart et al. (2013) for the distributed configurations (p. 10, line 197), with the model-mismatch simulations as the test of whether its conclusion survives.

**S5. The practical significance of the differences is unclear; compare them with test-retest variability on a test-retest database.**

I thank the reviewer for this suggestion, which I consider the most important addition to the revised manuscript. All five linear arms were fitted to 38 scans of the open MASiVar dataset: one adult scanned in three sessions on consecutive days with three or four scans per session, and five adults scanned on four scanners of three vendors at three sites. The data were analysed unprocessed, as in the rest of the paper, and again after the dataset's own PreQual preprocessing, so that preprocessing is not a choice made here (Methods, p. 5, line 88, and p. 13, line 268; Results, p. 22, line 450; Table 10).

The results answer the reviewer's question directly. For a fixed estimator, MD varied by 0.9 to 1.4% within a session, 0.6 to 1.5% between sessions and 1.2 to 1.5% between subjects. The difference between the toolkit defaults was 0.05 to 0.4%, below the within-session variability. The difference between implementations at a matched estimator was zero to the precision of the output. The difference between weighting schemes was 8.5 to 9.0% of MD on unprocessed data and 2.8 to 2.9% after preprocessing, six to fifteen times the between-session variability.

The reviewer's point about a constant shift is also addressed. A constant offset would cancel in any study that uses one estimator. This offset is not constant: it ranged from 0.3 to 15% between scans, it followed the SNR of each scan within a scanner as well as between scanners, and its mean on one scanner was three times its mean on another. As a result, measured-signal weighting raised the between-scanner variability of MD by a factor of 1.9 on unprocessed data and 1.6 on preprocessed data, while leaving within-session and between-subject variability unchanged (Discussion, p. 28, line 591). For FA, the effect is small at b = 1000 s/mm² and falls below within-session variability after preprocessing, and the manuscript says so (p. 29, line 602).

**S6. The emphasis on containers is overstated and at odds with the paper's message.**

I agree. The container does not keep data identical; identical input is a property of the files. Its only roles are to fix the software versions, which matters because defaults can change between releases, and to make the analysis easy to reproduce. The claim about byte-identical data has been removed throughout, and the description of the execution environment has been reduced to one short paragraph (p. 14, line 282). The interactive interface is now mentioned only in the Supplement.

---

## Reviewer 2

**Preamble. The main contribution is the identification and comparison of toolkit configurations rather than the discovery of a new bias mechanism; agreement between implementations does not establish physical accuracy.**

I agree with this characterisation, and the revised manuscript states the contribution in these terms (Abstract, p. 1; Introduction, p. 3, line 60). A new section of the Discussion, "Agreement is not accuracy", separates the two kinds of evidence: accuracy is assessed only against synthetic ground truth, and on real data the manuscript reports agreement and difference, not error (p. 25, line 532). The Results headings and the Conclusion were revised to keep the distinction.

**1. Signal quality, noise model and estimator reliability: low diffusion-weighted SNR; the Rician assumption not established for multichannel reconstructions; the 1.28 factor not validated on Sherbrooke; DIPY tensors fitted to noisy data are not independent ground truth; specify the post-reconstruction noise model, the uncertainty in σ and the treatment of the noise floor; qualify claims that noise accounts for a fraction of the differences.**

I agree with each of these points, and the revised manuscript addresses them as follows.

*Noise model.* The reconstruction of both datasets is undocumented, and the manuscript now says so (p. 4, line 80). What the data themselves say is reported in a new paragraph (p. 6, line 113) and in Supplementary Table S9. The Sherbrooke background, examined in corner regions far from the head, is narrower than a Rayleigh distribution, and its quantile ratios lie between those of one and two complex channels, which is consistent with a multi-channel reconstruction. The Stanford background cannot be examined because 39% of its voxels outside the brain are exactly zero and the rest carry ghosting. In consequence the simulations were repeated with non-central χ noise from 4 and 8 channels (Methods, p. 12, line 242; Results, p. 21, line 431; Supplementary Table S14). The noise floor then biases every estimator, and this shared bias exceeds the difference between weighting schemes, which shrinks but keeps its sign. The manuscript now states that at low SNR the choice of estimator does not compensate for the noise floor and no linear estimator is accurate, which is the reviewer's point.

*Uncertainty in σ.* The ratio measured on the Stanford b = 0 volumes is 1.27 with a 95% bootstrap confidence interval over voxels of 1.26 to 1.27, but the ratio itself varies from voxel to voxel (interquartile range 1.04 to 1.53), because the SD across volumes also contains motion and physiological fluctuation; both are reported (p. 6, line 113). Independent estimates of σ are given: PIESNO agrees with MP-PCA on Stanford (17.4 against 18.0), whereas on Sherbrooke PIESNO (15.1) and the background (15.9) are both below the MP-PCA value in white matter (22.3), which is consistent with noise that varies across the image. The manuscript no longer applies the Stanford ratio to Sherbrooke as if it were validated there; it reports the Sherbrooke results at the MP-PCA σ, at 1.27σ and at the bound set by the residuals, and says which estimate each number depends on.

*Claims about the fraction explained.* The shares reproduced by noise are now given as a range across noise levels and rules rather than as one number, the simulation on fitted tensors is described as a self-consistency check rather than as ground truth (p. 31, line 645), and the Sherbrooke FA offset, which is small, is no longer interpreted (p. 20, line 417). With the corrected voxel set the shares are 93% of the Stanford FA offset, 86% of its MD offset and 93% of the Sherbrooke MD offset at the measured noise level (Table 7), and the shortfall in Stanford's most anisotropic voxels reported in the first version is no longer present.

*Treatment of the noise floor.* Supplementary Table S11 records the signal floor and the treatment of non-positive measurements in each toolkit, and the non-central χ simulation quantifies the floor as a percentage of S₀ at each SNR. No correction of the magnitude noise floor was applied before fitting; the Limitations say so, and note that such a correction would reduce the bias every estimator shares and that its effect on the difference between weighting schemes was not tested (p. 31, line 645). Because σ varies across the image, the simulation on the real tensors adds noise at each voxel's own σ from the MP-PCA map rather than at one value (p. 6, line 113).

*Low diffusion-weighted SNR.* The SNR of the fitted shell is 10.0 on Stanford and 6.3 on Sherbrooke, and the test-retest scans span b = 0 SNR 16 to 37. The Discussion now states that estimator choice cannot compensate for inadequate signal and that no estimator is optimal under all conditions (p. 21, line 441).

**2. Spatial systematic errors: replacing the effective b-matrix with the nominal one introduces errors that neither denoising nor the estimator removes; state whether gradient-nonlinearity correction was applied; discuss how uncharacterised SSE limits interpretation; effects need not be additive.**

No gradient-nonlinearity correction was applied, because neither dataset provides the gradient-field information it would need, and the manuscript now states this (p. 12, line 245). A new paragraph of the Limitations (p. 31, line 659) and the section "Agreement is not accuracy" (p. 25, line 532) cite Krzyżak et al. (2024, 2025) and state that absolute FA and MD on real data remain limited by uncharacterised spatial systematic errors, that these may dominate as stochastic error falls, and that their effects need not be additive with those of the estimator.

To test whether such errors alter the comparison between estimators, the signal was generated with a per-voxel b-matrix that differed from the nominal one and fitted with the nominal one (Methods, p. 12, line 245; Results, p. 21, line 442; Supplementary Table S15). Scale errors that vary from voxel to voxel within ±2% or ±5% and gradient tilts with SD 1° or 3° changed no arm's bias by more than 0.001. A systematic scale error of ±5% shifted the MD of every arm by 5%, and its interaction with the weighting bias was 0.005 to 0.009 µm²/ms, so the two effects are not exactly additive, as the reviewer anticipated; the ranking of the estimators and the sign of their differences were unchanged in every case. Because every arm receives the same input, such errors affect all arms, and the comparison between them is robust to the sizes tested. They do limit the absolute values, and the manuscript says so.

**3. Physical admissibility: FA in [0, 1] and 0 < MD ≤ 3.0 do not guarantee a positive-semidefinite tensor; report negative eigenvalues; distinguish raw tensors from DIPY's clipped ones; repeat the comparisons on a common, independently defined voxel mask with exclusion counts.**

I thank the reviewer for this correction; the example given is right, and the rule of the first version did not exclude tensors with a negative eigenvalue. The revised manuscript makes four changes.

The admissibility rule is now defined on the eigenvalues (p. 7, line 142), and the reviewer's example is used in the text to explain why. Table 9 reports negative eigenvalues for every arm, and Supplementary Table S12 gives DIPY's fit before and after its clipping: before clipping, DIPY WLS has a negative eigenvalue in 3.1% of Sherbrooke white matter voxels, the same rate as FSL's OLS default.

All comparisons are made on a common voxel mask defined independently of the estimators, from a two-channel FAST segmentation of the mean b = 0 and mean diffusion-weighted images (p. 7, line 136), and every table states how many voxels each arm loses to the admissibility rule. A stricter tissue threshold gives the same conclusions (Supplementary Table S10).

The consequences of the correction are reported rather than hidden. Every number in Tables 2 to 9 changed; for example, the Sherbrooke MD offset between the weighting schemes is 0.086 µm²/ms rather than 0.127, because the voxels the old rule admitted with a negative eigenvalue were the ones in which the measured-signal fit was most biased. With the corrected rule, DIPY given measured-signal weights reproduces FSL `--wls` exactly (Table 4), and the residual of the first version is traced entirely to DIPY's clipping (p. 16, line 334). Disagreement in low-signal voxels, which the independent mask includes and the old mask did not, is reported separately (p. 15, line 310).

**4. The outliers in Figure 2: r = 1.0000 is rounded; characterise the 23 points outside the axis and the 57 voxels above 0.001; compare all six tensor components; document signal flooring, precision and conventions; avoid categorical claims in the title and conclusions.**

All of this has been done.

*Quantiles and components.* Supplementary Table S12 gives the median, 95th, 99th and 99.9th percentiles and the maximum of the absolute difference between FSL `--wls` and MRtrix3 `-iter 0` in FA, MD and all six tensor components, after bringing both tensors into one frame (FSL stores the tensor in its voxel frame with x reversed; the sign of Dxy and Dxz changes relative to MRtrix3, and the manuscript says so). In white matter the median differences are below 10⁻⁷, 1 − r is about 10⁻¹¹, and the largest FA difference is 1.1 × 10⁻⁴ on Stanford and 5.4 × 10⁻⁵ on Sherbrooke (Results, p. 15, line 303). The same agreement holds at b = 2000 s/mm², with both shells, on denoised data and on all 38 test-retest scans.

*The voxels that differ.* Figure 2 is now drawn on the independent white matter mask, where no voxel falls outside the axis of the FSL–MRtrix3 panel. Over the whole brain mask, 3.6% of Stanford voxels differ by more than 0.001 in FA, with a largest difference of 0.20; they lie outside white matter, 78% contain a measurement below half the noise SD, and their eigenvalues differ between the two programs, so the difference arises in the fit (p. 15, line 310). The cause is now identified. The two programs floor the signal differently before taking its logarithm: MRtrix3 at 10⁻⁶ of the voxel maximum, and FSL, as its source code shows, at 1% of the S₀ estimated by an initial fit. All 6,687 differing voxels are voxels in which FSL's floor binds, and a reimplementation of FSL's rule reproduces `dtifit --wls` there to a mean absolute FA difference of 0.00002 and over the whole brain to 0.00013 (Supplementary Table S11 and the paragraph below it). On Sherbrooke only ten brain voxels differ by more than 0.001.

*Conventions.* Supplementary Table S11 documents, for each toolkit, the signal floor, the treatment of non-positive measurements, the frame and order of the stored tensor, the b-value scaling convention, the numerical precision and the eigenvalue handling, and states which entries were tested on the data and which come from documentation.

*Title and conclusions.* The title is now "Estimator choice, not implementation, accounts for most of the difference in diffusion tensor fitting between FSL, MRtrix3 and DIPY". The Discussion states why "most" rather than "all" (p. 25, line 524), and the Conclusion describes very close agreement for the configurations and versions tested rather than the absence of implementation differences (p. 32, line 670).

**Closing remarks. The work provides useful evidence on computational reproducibility but does not establish which estimator yields the most physically accurate metrics; correct the admissibility criterion, analyse the low-signal outliers, and separate estimator agreement from measurement accuracy.**

Each of the three requests has been met: the admissibility criterion is defined on the eigenvalues (point 3), the low-signal outliers are characterised (point 4), and a new section of the Discussion separates agreement from accuracy and lists what limits the latter on real data: noise, model mismatch and spatial systematic errors (point 2 and p. 25, line 532). The manuscript no longer claims that any estimator yields the most physically accurate metrics on real data; accuracy is stated only for the synthetic conditions under which it was measured, and the real data are used to show how large the differences are and how they behave.

I thank both reviewers again. The manuscript is more careful and more useful for their comments.

Busra Mutlu Ipek
