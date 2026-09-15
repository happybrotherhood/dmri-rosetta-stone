# Highlights

- FSL and MRtrix3 give matching tensors (r = 1.0000) with the same estimator
- Toolkits differ mainly in the estimator they apply by default
- FSL's --wls weights by the measured signal, a scheme known to bias estimates
- In anisotropic phantoms that scheme was most biased, more so as SNR fell
- Reporting the estimator, not only the toolkit, is needed for reproducibility
