# Highlights

- Given the same estimator, FSL and MRtrix3 return the same tensor in every voxel
- Toolkits differ mainly in the estimator they apply by default
- FSL's --wls weights by the measured signal, a scheme known to bias MD
- Its MD offset exceeds test-retest variability and grows as SNR falls
- Report the estimator and its weighting, not only the toolkit
