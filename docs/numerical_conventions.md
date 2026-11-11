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
| Floor applied to the signal before the log | initial fit gives S0; measurements below 0.01 S0 set to 0.01 S0; refit (`fdt/dtifit.cc`) | 1e-6 × the voxel's maximum signal | 1e-4 (`MIN_POSITIVE_SIGNAL`) | all documented and tested (see below) |
| Measurements ≤ 0 | raised to the floor | raised to the floor | raised to the floor | as above |
| Negative eigenvalues | reported unchanged | reported unchanged | clipped to a small positive value before FA and MD | tested: negative eigenvalues in FSL and MRtrix3 output, none in DIPY's; DIPY's unclipped values recovered by the reimplementation (`admissibility_analysis.txt`) |
| Frame of the stored tensor | FSL voxel frame: x reversed for images with a positive determinant (both datasets) | scanner coordinates | the frame of the b-vectors supplied (here FSL's) | tested: FSL's Dxy and Dxz change sign relative to MRtrix3's, Dyz does not (`admissibility_analysis.txt`, section 4) |
| Order of the stored components | Dxx Dxy Dxz Dyy Dyz Dzz | Dxx Dyy Dzz Dxy Dxz Dyz | 3 × 3 matrix | documented (MRtrix3: `dwi2tensor -help`) |
| b-value scaling by b-vector norm | none | applied by default when b-vectors are not unit length | none | not relevant here: every diffusion-weighted b-vector has norm 1.00000 ± 0.00001 |
| Units | b in s/mm², D in mm²/s | same | same | tested |
| Precision of the stored maps | float32 NIfTI | float32 | float64 in memory; float32 as written here | tested; differences at the 1e-7 level in white matter are at float32 resolution |

## What the agreement shows

In FAST white matter, FSL `--wls` and MRtrix3 `-iter 0` agree in FA, MD and all
six tensor components with median absolute differences below 1e-7 and
1 − r of about 1e-11, the resolution of the float32 maps.

Over the whole brain on Stanford, 3.6% of voxels (6,687) differ by more than
0.001 in FA (maximum 0.204). The cause was found in `fdt/dtifit.cc`
(git.fmrib.ox.ac.uk/fsl/fdt): `dtifit` fits once with log(S) = 0 for S <= 0
(and, under `--wls`, weight 1 for S <= 0), takes S0 from that fit, replaces
every measurement below 0.01 S0 by 0.01 S0, and fits again. MRtrix3 floors at
1e-6 of the voxel maximum. All 6,687 voxels are ones in which FSL's 1% floor
binds. A NumPy reimplementation of FSL's rule reproduces `dtifit --wls` over
the whole brain to a mean absolute FA difference of 1.3e-4 and `dtifit` (OLS)
to 1.3e-4; the 517 voxels still differing by more than 0.001 all contain a
measurement at or below zero. The floor binds in 218 white matter voxels, so
the comparison in white matter is unaffected. Table S11 of the supplement
records the rule.
