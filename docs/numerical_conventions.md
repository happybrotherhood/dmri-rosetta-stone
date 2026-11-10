# Numerical conventions of the three tensor fits

Reviewer 2 (point 4) asked for the signal flooring, floating-point precision
and numerical conventions behind the comparison of FSL `dtifit` and MRtrix3
`dwi2tensor`. This table records them for the versions used (FSL 6.0.7,
MRtrix3 3.0.8, DIPY 1.12.1). The last column says how each entry is known:
**tested** means it was reproduced or measured on the data of this study;
**documented** means it comes from the toolkit's documentation or source and
was not tested separately.

| Convention | FSL `dtifit` | MRtrix3 `dwi2tensor` | DIPY `TensorModel` | How known |
|---|---|---|---|---|
| Default estimator | OLS | WLS, then 2 IWLS reweightings | WLS, weights from an OLS-predicted signal | documented; tested (`tensor_estimators_check.txt`) |
| Weighted option | `--wls`: weights = squared measured signal | `-iter 0`: stops after the measured-signal WLS step | `fit_method`; weights can be supplied | tested: FSL `--wls` = MRtrix3 `-iter 0` = DIPY with measured weights in white matter (`revision_tables.txt`, Tables 3 and 4) |
| Floor applied to the signal before the log | 1 in white matter (reimplementation with a floor of 1 reproduces FSL there); behaviour in low-signal voxels not reproduced by any floor tested | 1e-6 × the voxel's maximum signal | 1e-4 (`MIN_POSITIVE_SIGNAL`) | MRtrix3 and DIPY: documented and tested; FSL: tested in white matter only (see below) |
| Measurements ≤ 0 | raised to the floor | raised to the floor | raised to the floor | as above |
| Negative eigenvalues | reported unchanged | reported unchanged | clipped to a small positive value before FA and MD | tested: negative eigenvalues in FSL and MRtrix3 output, none in DIPY's; DIPY's unclipped values recovered by the reimplementation (`admissibility_analysis.txt`) |
| Frame of the stored tensor | FSL voxel frame: x reversed for images with a positive determinant (both datasets) | scanner coordinates | the frame of the b-vectors supplied (here FSL's) | tested: FSL's Dxy and Dxz change sign relative to MRtrix3's, Dyz does not (`admissibility_analysis.txt`, section 4) |
| Order of the stored components | Dxx Dxy Dxz Dyy Dyz Dzz | Dxx Dyy Dzz Dxy Dxz Dyz | 3 × 3 matrix | documented (MRtrix3: `dwi2tensor -help`) |
| b-value scaling by b-vector norm | none | applied by default when b-vectors are not unit length | none | not relevant here: every diffusion-weighted b-vector has norm 1.00000 ± 0.00001 |
| Units | b in s/mm², D in mm²/s | same | same | tested |
| Precision of the stored maps | float32 NIfTI | float32 | float64 in memory; float32 as written here | tested; differences at the 1e-7 level in white matter are at float32 resolution |

## What the agreement shows, and what remains open

In FAST white matter, FSL `--wls` and MRtrix3 `-iter 0` agree in FA, MD and all
six tensor components with median absolute differences below 1e-7 and
1 − r of about 1e-11, the resolution of the float32 maps. The largest FA
difference is 1.1e-4 on Stanford and 5.4e-5 on Sherbrooke.

Over the whole brain the agreement is weaker on Stanford: 3.6% of brain voxels
differ by more than 0.001 in FA (maximum 0.204). These voxels lie mostly
outside white matter, and 78% contain a measurement below half the noise SD.
Refitting them with the reimplemented estimator shows that MRtrix3's
behaviour there is reproduced by its documented floor (1e-6 × voxel maximum;
mean absolute FA difference 0.0008), whereas FSL's is reproduced neither by a
floor of 1, by no floor, nor by single-precision arithmetic. FSL's eigenvalues
differ from MRtrix3's in these voxels (mean 0.24 µm²/ms), so the difference
arises in the fit, not in the computation of FA. Which step of `dtifit`
causes it could not be determined without its source code. On Sherbrooke
(b = 1000 s/mm²) only 10 brain voxels differ by more than 0.001.
