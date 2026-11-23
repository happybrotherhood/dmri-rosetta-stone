# Highlights

- Given the same estimator, FSL and MRtrix3 return the same tensor in every voxel
- Toolkits differ mainly in the estimator they apply by default
- FSL's --wls weights by the measured signal, a scheme known to bias MD
- Its MD offset exceeds test-retest variability and grows as SNR falls
- The estimator and the source of its weights identify a fit; the toolkit does not
