"""
noise_level_uncertainty.py
--------------------------
How well the noise level of each dataset is known, and what the data say
about the noise distribution after reconstruction (Reviewer 2, point 1).

1. Independent estimates of sigma in white matter (FAST white matter of arms.py):
     MP-PCA        median of the dwidenoise noise map (the manuscript's sigma)
     b = 0 SD      Stanford only: temporal SD over the ten b = 0 volumes,
                   corrected for the small-sample bias of the SD
     PIESNO        DIPY's estimator (Koay et al., 2009), from the background
                   of each slice, assuming N = 1 channel
     residuals     robust SD of the residuals of the predicted-signal fit, in
                   the diffusion-weighted volumes; an upper bound, because
                   residuals also carry model misfit
     background    Sherbrooke only: Rician-corrected mean of the magnitude in
                   corner regions far from the head (sigma = mean / sqrt(pi/2))
   The Stanford background is not usable: 45% of its voxels are exactly
   zero and the rest carry ghosting.

2. Bootstrap confidence interval for the ratio used in the manuscript,
   1.268 = median over voxels of (b = 0 SD / MP-PCA sigma) / 0.9628: voxels
   resampled 2,000 times.

3. Noise distribution in the Sherbrooke background. For magnitude noise from
   L complex channels (non-central chi, here central because there is no
   signal), the quantile ratios of the distribution do not depend on sigma
   and narrow as L grows. The observed ratios are compared with simulated
   ones for L = 1, 2, 4, 8, 16, and the Rician-corrected mean is compared
   with the MP-PCA sigma of the nearest white matter.

Usage:
    python scripts/noise_level_uncertainty.py

Outputs:
    noise_level_uncertainty.txt
"""
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tensor_estimators as te  # noqa: E402
from arms import ROOT, brain_mask, load, wm_mask  # noqa: E402

B0_MAX = 50
GAUSS10 = 0.9628     # median of s / sigma for the SD of ten Gaussian samples
BOOT = 2000


def mad_sd(a):
    return 1.4826 * np.median(np.abs(a - np.median(a)))


def quantile_ratios(v):
    q = np.percentile(v, [10, 25, 50, 75, 90])
    return q[3] / q[1], q[4] / q[0], q[2] / v.mean()


def simulated_ratios(L, rng, n=200000):
    s = sum(rng.normal(size=n) ** 2 for _ in range(2 * L))
    return quantile_ratios(np.sqrt(s))


def main():
    lines = []

    def w(s=""):
        print(s, flush=True)
        lines.append(s)

    rng = np.random.default_rng(7)
    w("Noise level: independent estimates, uncertainty, and the noise distribution after reconstruction")
    for subj in ("stanford", "sherbrooke"):
        data_p, bvals, bvecs = te.load_protocol(subj)
        full_p = ROOT / "data" / "hcp" / subj / "T1w" / "Diffusion" / "data.nii.gz"
        img = nib.load(str(data_p))
        data = np.asarray(img.dataobj, dtype=np.float32)
        wm = wm_mask(subj)
        sig_map = load(ROOT / "data" / "hcp" / subj / "dti_denoised" / "noise_map.nii.gz")
        sig = np.median(sig_map[wm])
        w()
        w("=" * 90)
        w(f"{subj}: {int(wm.sum()):,} white-matter voxels")
        w("=" * 90)
        w("1. Estimates of sigma in white matter")
        w(f"  MP-PCA (manuscript)            {sig:8.2f}")
        b0 = data[..., bvals < B0_MAX]
        if b0.shape[-1] >= 5:
            sd = b0[wm].std(axis=1, ddof=1)
            ratio = sd / sig_map[wm]
            est = np.median(sd) / GAUSS10
            w(f"  b = 0 temporal SD, corrected   {est:8.2f}   ({b0.shape[-1]} volumes; median SD {np.median(sd):.2f})")
            boots = [np.median(ratio[rng.integers(0, ratio.size, ratio.size)]) / GAUSS10 for _ in range(BOOT)]
            lo, hi = np.percentile(boots, [2.5, 97.5])
            w(f"2. Ratio b = 0 SD / MP-PCA sigma, corrected: {np.median(ratio) / GAUSS10:.3f}, "
              f"95% bootstrap CI {lo:.3f}-{hi:.3f} over voxels ({BOOT} resamples)")
            w(f"   The ratio is also a property of the voxel: its interquartile range over voxels is "
              f"{np.percentile(ratio, 25) / GAUSS10:.3f}-{np.percentile(ratio, 75) / GAUSS10:.3f}")
        else:
            w(f"  b = 0 temporal SD              n/a       (one b = 0 volume)")
        try:
            from dipy.denoise.noise_estimate import piesno
            full = np.asarray(nib.load(str(full_p)).dataobj, dtype=np.float32)
            s_p, _ = piesno(full, N=1, return_mask=True)
            s_p = np.asarray(s_p)
            s_p = s_p[np.isfinite(s_p) & (s_p > 0)]
            w(f"  PIESNO (N = 1), per slice     {np.median(s_p):8.2f}   (IQR {np.percentile(s_p, 25):.2f}-"
              f"{np.percentile(s_p, 75):.2f}, {s_p.size} slices)")
        except Exception as e:   # noqa: BLE001
            w(f"  PIESNO failed: {e}")
        X = te.design(bvals, bvecs)
        Y = data[wm].astype(np.float64)
        beta = te.fit(X, Y, "predicted")
        resid = Y - np.exp(np.clip(beta @ X.T, -700, 700))
        rs = mad_sd(resid[:, bvals > B0_MAX].ravel())
        w(f"  residuals, robust SD (upper bound) {rs:8.2f}   = {rs / sig:.3f} x MP-PCA sigma")

        if subj == "sherbrooke":
            w("3. Noise distribution in the background (corner regions, b = 0 volume)")
            vol = data[..., int(np.argmin(bvals))]
            nx, ny, nz = vol.shape
            brain = brain_mask(subj)
            c = np.zeros(vol.shape, bool)
            k = 12
            for sx in (slice(2, 2 + k), slice(nx - 2 - k, nx - 2)):
                for sy in (slice(2, 2 + k), slice(ny - 2 - k, ny - 2)):
                    c[sx, sy, 3:nz - 3] = True
            c &= ~brain
            v = vol[c].astype(float)
            w(f"  {int(c.sum()):,} corner voxels: mean {v.mean():.2f}, median {np.median(v):.2f}, "
              f"SD {v.std():.2f}, zeros {100 * np.mean(v == 0):.1f}%")
            w(f"  Rician-corrected sigma = mean / sqrt(pi/2) = {v.mean() / np.sqrt(np.pi / 2):.2f}; "
              f"MP-PCA sigma in white matter {sig:.2f}; MP-PCA sigma in the corner voxels "
              f"{np.median(sig_map[c & (sig_map > 0)]) if (c & (sig_map > 0)).any() else float('nan'):.2f}")
            obs = quantile_ratios(v)
            w(f"  {'':<14}{'p75/p25':>9}{'p90/p10':>9}{'median/mean':>13}")
            w(f"  {'observed':<14}{obs[0]:>9.3f}{obs[1]:>9.3f}{obs[2]:>13.3f}")
            for L in (1, 2, 4, 8, 16):
                r = simulated_ratios(L, rng)
                w(f"  {'L = ' + str(L):<14}{r[0]:>9.3f}{r[1]:>9.3f}{r[2]:>13.3f}")
        else:
            w("3. Background not usable for the noise distribution: "
              f"{100 * np.mean(data[..., int(np.argmin(bvals))][~brain_mask(subj)] == 0):.0f}% of voxels "
              "outside the brain are exactly zero and the rest carry ghosting")

    out = ROOT / "noise_level_uncertainty.txt"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
