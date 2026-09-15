"""
tensor_estimators.py
--------------------
The linear tensor estimators of FSL, MRtrix3 and DIPY, reimplemented so that
simulations fit synthetic data the way each toolkit fits real data.

A simulation that compares weighting schemes is only informative if its fits
behave like the toolkits'. Two details decide that, and neither is visible in
the name of the estimator: DIPY floors the signal at 1e-4 and clips negative
eigenvalues before computing FA, whereas FSL and MRtrix3 report the
eigenvalues unchanged. The arms below reproduce those details.

    ols        FSL dtifit (default)
    measured   FSL dtifit --wls and MRtrix3 dwi2tensor -iter 0:
               weights = squared measured signal
    iwls       MRtrix3 dwi2tensor (default): the measured-signal fit, then two
               reweightings by the squared predicted signal; the signal is
               floored at 1e-6 of the voxel's maximum, as dwi2tensor does
    predicted  DIPY TensorModel(fit_method="WLS"): OLS, then weights = squared
               predicted signal (Chung et al., 2006)

Every fit minimises  sum_i w_i (ln S_i - x_i beta)^2  with
beta = [ln S0, Dxx, Dyy, Dzz, Dxy, Dxz, Dyz].

Run directly, the module checks each arm against the published maps of the
real data and writes the agreement to tensor_estimators_check.txt.

Usage:
    python scripts/tensor_estimators.py
"""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
ARMS = ("ols", "measured", "iwls", "predicted")

FLOOR = 1.0              # FSL arms: keeps log and weights finite at zero
MRTRIX_SMALL = 1e-6      # dwi2tensor: small_intensity = 1e-6 * voxel maximum
DIPY_MIN_SIGNAL = 1e-4   # dipy.reconst.dti.MIN_POSITIVE_SIGNAL
DIPY_TOL = 1e-6          # DIPY clips eigenvalues at tol / -design_matrix.min()
CHUNK = 20000


def design(bvals, bvecs) -> np.ndarray:
    """Rows [1, -b gx^2, -b gy^2, -b gz^2, -2b gxgy, -2b gxgz, -2b gygz]."""
    b, g = np.asarray(bvals, float), np.asarray(bvecs, float)
    return np.column_stack([
        np.ones_like(b), -b * g[:, 0] ** 2, -b * g[:, 1] ** 2, -b * g[:, 2] ** 2,
        -2 * b * g[:, 0] * g[:, 1], -2 * b * g[:, 0] * g[:, 2],
        -2 * b * g[:, 1] * g[:, 2]])


def _solve(X, logy, w):
    A = np.einsum("vn,nij->vij", w, np.einsum("ni,nj->nij", X, X))
    rhs = (w * logy) @ X
    try:
        return np.linalg.solve(A, rhs[..., None])[..., 0]
    except np.linalg.LinAlgError:          # a voxel left with too few measurements
        return (np.linalg.pinv(A) @ rhs[..., None])[..., 0]


def _predicted_weights(X, beta):
    return np.exp(np.clip(2 * (beta @ X.T), -700, 700))


def fit(X, y, arm, keep=None) -> np.ndarray:
    """Fit every voxel (row of y). keep=False gives a measurement zero weight."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; choose from {ARMS}")
    y = np.asarray(y, float)
    out = np.empty((y.shape[0], 7))
    for s in range(0, y.shape[0], CHUNK):
        yy = y[s:s + CHUNK]
        base = np.ones_like(yy) if keep is None else keep[s:s + CHUNK].astype(float)
        if arm == "predicted":
            ly = np.log(np.maximum(yy, DIPY_MIN_SIGNAL))
            beta = _solve(X, ly, base)
            beta = _solve(X, ly, base * _predicted_weights(X, beta))
        else:
            if arm == "iwls":
                yf = np.maximum(yy, MRTRIX_SMALL * yy.max(axis=1, keepdims=True))
            else:
                yf = np.maximum(yy, FLOOR)
            ly = np.log(yf)
            if arm == "ols":
                beta = _solve(X, ly, base)
            else:
                beta = _solve(X, ly, base * yf ** 2)
                if arm == "iwls":
                    for _ in range(2):
                        beta = _solve(X, ly, base * _predicted_weights(X, beta))
        out[s:s + CHUNK] = beta
    return out


def tensor(beta) -> np.ndarray:
    D = np.empty(beta.shape[:-1] + (3, 3))
    D[..., 0, 0], D[..., 1, 1], D[..., 2, 2] = beta[..., 1], beta[..., 2], beta[..., 3]
    D[..., 0, 1] = D[..., 1, 0] = beta[..., 4]
    D[..., 0, 2] = D[..., 2, 0] = beta[..., 5]
    D[..., 1, 2] = D[..., 2, 1] = beta[..., 6]
    return D


def eigenvalues(X, beta, arm) -> np.ndarray:
    """Ascending eigenvalues, clipped as DIPY clips them for the DIPY arm."""
    ev = np.linalg.eigvalsh(tensor(beta))
    if arm == "predicted":
        ev = np.maximum(ev, DIPY_TOL / -X[:, 1:].min())
    return ev


def fa_md(ev):
    """FA and MD (um^2/ms) from eigenvalues in mm^2/s."""
    md = ev.mean(-1)
    den = np.sqrt((ev ** 2).sum(-1))
    with np.errstate(invalid="ignore", divide="ignore"):
        fa = np.sqrt(1.5) * np.sqrt(((ev - md[..., None]) ** 2).sum(-1)) / den
    return np.nan_to_num(fa), md * 1e3


def fit_fa_md(X, y, arm, keep=None):
    """Fit, then return FA, MD (um^2/ms) and the parameters."""
    beta = fit(X, y, arm, keep)
    fa, md = fa_md(eigenvalues(X, beta, arm))
    return fa, md, beta


def admissible(fa, md, fa_min=None):
    ok = (fa >= 0) & (fa <= 1) & (md > 0) & (md <= 3)
    return ok if fa_min is None else ok & (fa > fa_min)


def load_protocol(subj: str):
    """The data and gradient table every toolkit was given for this dataset."""
    import nibabel as nib
    d = ROOT / "data" / "hcp" / subj
    it = d / "dti_iter0"
    if (it / "subset_data.nii.gz").exists():
        data_p, bval_p, bvec_p = it / "subset_data.nii.gz", it / "subset.bvals", it / "subset.bvecs"
    else:
        dd = d / "T1w" / "Diffusion"
        data_p, bval_p, bvec_p = dd / "data.nii.gz", dd / "bvals", dd / "bvecs"
    bvals, bvecs = np.loadtxt(str(bval_p)), np.loadtxt(str(bvec_p))
    if bvecs.shape[0] == 3 and bvecs.shape[1] != 3:
        bvecs = bvecs.T
    return data_p, bvals, bvecs


# Published maps each arm must reproduce: (run directory, file prefix).
PUBLISHED = {
    "ols":       ("dti_iter0_fslols", "fsl_dti"),
    "measured":  ("dti_iter0", "fsl_dti"),
    "iwls":      ("dti", "mrt"),
    "predicted": ("dti_iter0", "dipy"),
}


def main():
    import nibabel as nib

    def load(p):
        return np.nan_to_num(np.asarray(nib.load(str(p)).dataobj, dtype=np.float64))

    out = ROOT / "tensor_estimators_check.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s, flush=True)
            fh.write(s + "\n")
        w("Reimplemented estimators against the toolkits' published maps")
        w("MD in um^2/ms.")
        for subj in ("stanford", "sherbrooke"):
            d = ROOT / "data" / "hcp" / subj
            data_p, bvals, bvecs = load_protocol(subj)
            X = design(bvals, bvecs)
            pub = {}
            for arm, (run, prefix) in PUBLISHED.items():
                pub[arm] = (load(d / run / f"{prefix}_FA.nii.gz"),
                            load(d / run / f"{prefix}_MD.nii.gz") * 1e3)
            fa_mrt0 = load(d / "dti_iter0" / "mrt_FA.nii.gz")
            md_mrt0 = load(d / "dti_iter0" / "mrt_MD.nii.gz") * 1e3

            # Fit once over every voxel any of the sets below can contain.
            big = (pub["measured"][0] > 0.2) | (pub["predicted"][0] > 0.2)
            data = np.asarray(nib.load(str(data_p)).dataobj, dtype=np.float32)
            Y = data[big].astype(np.float64)
            sig = load(d / "dti_denoised" / "noise_map.nii.gz")[big]
            nonpos = (Y <= 0).any(1)
            fits = {arm: fit(X, Y, arm) for arm in ARMS}
            famd = {arm: fa_md(eigenvalues(X, fits[arm], arm)) for arm in ARMS}

            w()
            w("=" * 84)
            w(subj)
            w("=" * 84)

            # 1. Each arm against the map it reproduces.
            wm = np.ones(pub["measured"][0].shape, bool)
            for fa_p, md_p in pub.values():
                wm &= admissible(fa_p, md_p, fa_min=0.2)
            wb = wm[big]
            w(f"1. Every arm against its toolkit map; white matter = FA > 0.2 and admissible "
              f"in every published arm ({int(wm.sum()):,} voxels)")
            w(f"  {'arm':<11}{'toolkit map':<24}{'mean|dFA|':>11}{'max|dFA|':>10}"
              f"{'n>0.001':>9}{'mean|dMD|':>11}")
            mismatch = {}
            for arm, (run, prefix) in PUBLISHED.items():
                fa, md = famd[arm]
                dfa = np.abs(fa[wb] - pub[arm][0][wm])
                dmd = np.abs(md[wb] - pub[arm][1][wm])
                mismatch[arm] = dfa > 1e-3
                w(f"  {arm:<11}{run + '/' + prefix:<24}{dfa.mean():>11.6f}{dfa.max():>10.4f}"
                  f"{int(mismatch[arm].sum()):>9,}{dmd.mean():>11.6f}")

            # 2. What the voxels that do not match have in common.
            low = (Y < 0.5 * sig[:, None]).any(1)
            w("2. Voxels differing by more than 0.001 in FA: % containing a measurement "
              "<= 0, and < 0.5 x MP-PCA sigma")
            for arm in ARMS:
                m = mismatch[arm]
                if m.sum():
                    w(f"  {arm:<11}{int(m.sum()):>7,} voxels: {100 * np.mean(nonpos[wb][m]):5.1f}% <= 0,"
                      f" {100 * np.mean(low[wb][m]):5.1f}% < 0.5 sigma   (all white matter: "
                      f"{100 * np.mean(nonpos[wb]):.2f}% and {100 * np.mean(low[wb]):.2f}%)")
                else:
                    w(f"  {arm:<11}      0 voxels")

            # 3. Does eigenvalue clipping account for the DIPY-FSL residual of Table 4?
            # Table 4 ran DIPY with measured-signal weights on signal floored at 1,
            # which is the 'measured' arm plus DIPY's clipping.
            fa_c, md_c = fa_md(eigenvalues(X, fits["measured"], "predicted"))
            fa_fsl, md_fsl = pub["measured"][0][big], pub["measured"][1][big]
            fa_dipy = pub["predicted"][0][big]
            t4 = ((fa_fsl > 0.2) & (fa_fsl <= 1) & (fa_dipy > 0.2) & (fa_dipy <= 1)
                  & (fa_c > 0.2) & (fa_c <= 1))
            fa_u, md_u = famd["measured"]
            w(f"3. Measured-signal fit against FSL --wls on Table 4's voxel set ({int(t4.sum()):,} voxels)")
            for label, f, m in (("with DIPY's eigenvalue clipping", fa_c, md_c),
                                ("without clipping", fa_u, md_u)):
                w(f"  {label:<33} FA MAE {np.mean(np.abs(f[t4] - fa_fsl[t4])):.6f}"
                  f"  FA bias {np.mean(f[t4] - fa_fsl[t4]):+.6f}"
                  f"  MD MAE {np.mean(np.abs(m[t4] - md_fsl[t4])):.6f}")

            # 4. The wider limits of agreement between FSL --wls and MRtrix3 -iter 0.
            # Table 3: FA > 0.2 in all three toolkits, FA within [0, 1] in the pair.
            fa_m0 = fa_mrt0[big]
            t3 = ((fa_fsl > 0.2) & (fa_m0 > 0.2) & (fa_dipy > 0.2)
                  & (fa_fsl >= 0) & (fa_fsl <= 1) & (fa_m0 >= 0) & (fa_m0 <= 1))
            diff = (fa_fsl - fa_m0)[t3]
            far = np.abs(diff) > 1e-3
            w(f"4. FSL --wls against MRtrix3 -iter 0 on Table 3's voxel set ({int(t3.sum()):,} voxels)")
            w(f"  95% limits of agreement +/-{1.96 * diff.std():.5f}; voxels differing by more "
              f"than 0.001: {int(far.sum())} ({100 * far.mean():.3f}%), of which "
              f"{int((far & nonpos[t3]).sum())} contain a measurement <= 0; limits without "
              f"them +/-{1.96 * diff[~far].std():.5f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
