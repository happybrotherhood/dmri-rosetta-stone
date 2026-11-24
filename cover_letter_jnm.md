Busra Mutlu Ipek
Department of Neuroimaging, King's College London
De Crespigny Park, London SE5 8AF, United Kingdom
busra.mutlu_ipek@kcl.ac.uk

Dear Editor,

Thank you for the opportunity to revise manuscript JNEUMETH-D-26-00997. I am submitting the revised version, now titled **"Estimator choice, not implementation, accounts for most of the difference in diffusion tensor fitting between FSL, MRtrix3 and DIPY"**, together with a point-by-point response to the two reviewers.

I am grateful to both reviewers. Their comments led to four additions that strengthen the manuscript, and to one correction.

## What has changed

- **A test-retest comparison (Reviewer 1).** All estimators were fitted to 38 repeated scans of the open MASiVar dataset, from one adult scanned within and between sessions and from five adults scanned on four scanners at three sites. The difference between weighting schemes is six to fifteen times the between-session variability of MD, and because it follows the SNR of each scan it raises between-scanner variability 1.6 to 1.9 times. The difference between the toolkit defaults is below test-retest variability. These results give the paper the practical relevance the reviewer asked for, and are new Table 10.
- **Admissibility judged on the eigenvalues (both reviewers).** The reviewers were right that a rule on FA and MD does not exclude a tensor with a negative eigenvalue. The rule now applies to the eigenvalues, every table states how many voxels each arm loses, and the comparisons are made on white matter defined by a tissue segmentation, without any tensor fit. With the corrected rule, DIPY given measured-signal weights reproduces FSL exactly, and the one residual difference in the first version is traced to DIPY's clipping of negative eigenvalues.
- **Robustness of the conclusion.** New simulations with crossing fibres and partial volume, with non-central χ noise, and with errors in the b-matrix, and new fits of the Sherbrooke b = 2000 s/mm² shell and of both shells together, show that the ranking of the estimators holds in every case, and that multi-shell input makes the toolkit defaults diverge as well.
- **Accuracy and agreement kept apart.** The title and conclusions no longer claim that implementation differences do not exist. Agreement between implementations is presented as a control, accuracy is assessed only against synthetic truth, and the Discussion says what the real data can and cannot show, including the limits set by the noise model and by spatial systematic errors.
- **Priority.** The Introduction now credits Salvador et al. (2005) for predicted-signal weighting and positions Veraart et al. (2013) as the study that quantified the cost of the alternative.

All numbers in the manuscript were regenerated on the new voxel set with the corrected rule. The main conclusions are unchanged. The structure of the tables is unchanged; one table and two figures were added.

## Reproducibility

The code, container definition and analysis scripts are available on GitHub under the MIT licence and archived on Zenodo (concept DOI 10.5281/zenodo.22106454). All three datasets are open and need no credentials. The Supplementary Material lists the commands that regenerate every table.

## Declarations

- This manuscript is original. It has not been published and is not under consideration elsewhere.
- I am the sole author and have approved the submitted version.
- I have no competing interests to declare.
- The work was carried out during a doctoral scholarship from the Republic of Türkiye Ministry of National Education (YLSY programme).
- The use of generative AI is declared in the manuscript, as required by Elsevier.

Thank you for considering the revised manuscript.

Yours sincerely,

Busra Mutlu Ipek
