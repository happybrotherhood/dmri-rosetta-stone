# Highlights

- FSL and MRtrix3 return matching tensors (r = 1.0000) with the same estimator
- Toolkits differ mainly in the estimator they apply by default
- FSL's --wls weights by the measured signal, a scheme known to bias estimates
- In the phantom's anisotropic region it is the most biased, more so at lower SNR
- Reporting the estimator, not only the toolkit, is what makes a fit reproducible
