Busra Mutlu Ipek
Department of Neuroimaging, King's College London
De Crespigny Park, London SE5 8AF, United Kingdom
busra.mutlu_ipek@kcl.ac.uk

Dear Editor,

I am pleased to submit the manuscript **"Diffusion MRI toolkits differ in which estimator they use, not in how they implement the tensor fit"** for consideration as a Research Article in the *Journal of Neuroscience Methods*.

## Why this work fits the journal

The *Journal of Neuroscience Methods* publishes rigorous comparisons of methods. This manuscript is such a comparison. It is not a software paper. A container is used only as the apparatus that lets FSL, MRtrix3 and DIPY run on byte-identical data. All data are public, and every result can be regenerated.

## What the study shows

- **FSL and MRtrix3 return the same tensor when given the same estimator** (r = 1.0000). The differences reported between these two toolkits are not due to implementation.
- **The toolkits differ in the estimator they apply by default.** MRtrix3 and DIPY weight the fit by a predicted signal. FSL uses ordinary least squares, and its `--wls` option weights by the measured signal.
- **Measured-signal weighting is the most biased scheme in MD.** In Rician-noise phantoms at SNR 10, it underestimated MD by 0.054 µm²/ms and FA by 0.026, while the other linear fits stayed within 0.007 of truth. Its MD bias grew with 1/SNR². In simulations of both real acquisition protocols, its MD bias was the largest in every condition.

## Why it matters

Veraart et al. (2013) showed that measured-signal weights degrade accuracy. This manuscript shows which options of widely used toolkits still carry that bias. The command line does not reveal it. Because its MD bias depends on SNR, it can create apparent group differences when groups are scanned at different SNR. The practical message is simple: methods sections should report the estimator, not only the toolkit.

## Questions a reviewer is likely to ask, and how the manuscript answers them

1. **Are the toolkits simply implemented differently?** No. With the estimator matched, FSL and MRtrix3 agree at r = 1.0000 (Table 3).
2. **Is the weighting scheme really the cause?** Yes. Swapping the weights inside DIPY removes almost all of its difference from FSL (Table 4).
3. **Is the finding limited to weighted linear fits?** No. In MD, OLS, IWLS, non-linear least squares and RESTORE all differ from the measured-signal fit in the same direction (Table 5).
4. **Which scheme is accurate?** Phantoms with known eigenvalues and Rician noise, at three SNR levels, answer this directly (Table 6). Simulations on both real gradient tables show that the MD result holds on each protocol, while the FA result depends on the protocol (Supplementary Table S3).
5. **Could a few non-physical fits distort the statistics?** They would, so they were excluded. All statistics use physically admissible voxels only, and the number of non-physical fits is reported (Table 9).
6. **Does noise explain the real-data differences?** Largely. Noise was added to each voxel's own fitted tensor, at the noise level measured on the Stanford b = 0 volumes. It reproduces 89–106% of the FA offsets and 80–91% of the MD offsets, depending on how non-physical fits are treated (Table 7; Supplementary Table S6). It falls short in Stanford's most anisotropic voxels, where the residuals show the pattern expected of single-tensor misfit. I found no gradient-table error or signal dropout, and the remaining offsets are reported as a limitation.

## Openness and reproducibility

The code, container definition and analysis scripts are available on GitHub under the MIT licence and archived on Zenodo (concept DOI 10.5281/zenodo.22106454). Both datasets are distributed openly by the DIPY project and need no credentials. The Supplementary Material lists the commands that regenerate every table.

## Declarations

- This manuscript is original. It has not been published and is not under consideration elsewhere.
- I am the sole author and have approved the submitted version.
- I have no competing interests to declare.
- The work was carried out during a doctoral scholarship from the Republic of Türkiye Ministry of National Education (YLSY programme).
- The use of generative AI is declared in the manuscript, as required by Elsevier.

Thank you for considering this manuscript.

Yours sincerely,

Busra Mutlu Ipek
