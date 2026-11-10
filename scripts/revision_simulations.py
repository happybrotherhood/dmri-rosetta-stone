"""
revision_simulations.py
-----------------------
Three simulations asked for in review, on the two real gradient tables, with
the toolkits' linear estimators reimplemented in tensor_estimators.py:

    ols        FSL dtifit (default)
    measured   FSL dtifit --wls, MRtrix3 dwi2tensor -iter 0
    iwls       MRtrix3 dwi2tensor (default)
    predicted  DIPY WLS (default)

A. Model mismatch (Reviewer 1, S4). Crossing fibres and partial volume, where
   no single tensor is the truth. Each estimator's reference is its own fit
   to the noise-free signal, so the bias reported is the effect of noise
   under model mismatch, separated from the effect of the mismatch itself
   (which the noise-free fits show). Scenarios: one fibre; two equal fibres
   crossing at 30, 60 and 90 degrees; white matter with 10-50% free water
   (isotropic, 3.0 um^2/ms); white matter with 30-50% grey matter
   (isotropic, 0.8 um^2/ms). Fibres: eigenvalues 1.4, 0.35, 0.35 um^2/ms
   (FA 0.71, MD 0.70).

B. Noise model (Reviewer 2, point 1). Non-central chi noise with L = 1
   (Rician), 4 and 8 channels at the same per-channel sigma, on single
   fibres of FA 0.45 and 0.71. The noise floor rises with L.

C. Spatially varying b-matrix errors (Reviewer 2, point 2). The signal is
   generated with a per-voxel b-matrix that differs from the nominal one, and
   the nominal one is used in the fit: b-value scale errors that vary from
   voxel to voxel (uniform within +/-2% or +/-5%), systematic scale errors
   (+5%, -5%), and direction errors (gradient tilted by a random angle with
   SD 1 or 3 degrees). Reported without noise and at SNR 20, with the
   additivity check bias(noise + error) - bias(noise) - bias(error).

SNR refers to one b = 0 volume (S0 = 1000, sigma = S0 / SNR). Each cell has
10,000 voxels with random fibre orientation and its own seed. Admissible
means all eigenvalues >= 0 and the largest <= 3.0 um^2/ms; every voxel enters
the statistics, as it would in a toolkit's output map. MD in um^2/ms.

Usage:
    python scripts/revision_simulations.py

Outputs:
    revision_simulations.txt
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tensor_estimators as te  # noqa: E402
from arms import admissible  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
N = 10000
S0 = 1000.0
PROTOCOLS = ("stanford", "sherbrooke")
ARMS = te.ARMS
FIBRE = np.array([1.4e-3, 0.35e-3, 0.35e-3])
FREE_WATER = 3.0e-3
GREY = 0.8e-3
LABEL = {"ols": "OLS (FSL default)", "measured": "measured (FSL --wls, MRtrix3 -iter 0)",
         "iwls": "IWLS (MRtrix3 default)", "predicted": "predicted (DIPY WLS)"}


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def random_directions(n, rng):
    return unit(rng.normal(size=(n, 3)))


def perpendicular(u, rng):
    v = rng.normal(size=u.shape)
    v -= (v * u).sum(1, keepdims=True) * u
    return unit(v)


def rotate(u, axis, angle):
    """Rodrigues rotation of unit vectors u about unit axes by angle (radians, per row)."""
    c, s = np.cos(angle)[:, None], np.sin(angle)[:, None]
    return u * c + np.cross(axis, u) * s + axis * (axis * u).sum(1, keepdims=True) * (1 - c)


def fibre_signal(bvals, bvecs, evals, dirs):
    """exp(-b g^T D g) for axially symmetric D with axis dirs (no S0)."""
    l1, l2 = evals[0], evals[1]
    cos2 = (dirs @ bvecs.T) ** 2
    return np.exp(-bvals[None, :] * (l2 + (l1 - l2) * cos2))


def isotropic_signal(bvals, d, n):
    return np.tile(np.exp(-bvals * d), (n, 1))


def rician(clean, sigma, rng):
    return np.sqrt((clean + rng.normal(0, sigma, clean.shape)) ** 2 + rng.normal(0, sigma, clean.shape) ** 2)


def ncchi(clean, sigma, L, rng):
    """Magnitude of L complex channels with the signal in one of them, per-channel sigma."""
    s = (clean + rng.normal(0, sigma, clean.shape)) ** 2 + rng.normal(0, sigma, clean.shape) ** 2
    for _ in range(L - 1):
        s += rng.normal(0, sigma, clean.shape) ** 2 + rng.normal(0, sigma, clean.shape) ** 2
    return np.sqrt(s)


def fit(X, y, arm):
    beta = te.fit(X, y, arm)
    ev = te.eigenvalues(X, beta, arm)
    fa, md = te.fa_md(ev)
    return fa, md, admissible(ev * 1e3)


def protocol(subj):
    _, bvals, bvecs = te.load_protocol(subj)
    return bvals, bvecs, te.design(bvals, bvecs)


# ---------------------------------------------------------------------------- A
def scenarios_a(bvals, bvecs, rng):
    u1 = random_directions(N, rng)
    one = fibre_signal(bvals, bvecs, FIBRE, u1)
    out = [("one fibre", one)]
    for deg in (30, 60, 90):
        u2 = rotate(u1, perpendicular(u1, rng), np.full(N, np.radians(deg)))
        out.append((f"two fibres, {deg} deg, 50/50", 0.5 * one + 0.5 * fibre_signal(bvals, bvecs, FIBRE, u2)))
    fw = isotropic_signal(bvals, FREE_WATER, N)
    for f in (0.1, 0.3, 0.5):
        out.append((f"fibre + {int(100 * f)}% free water", (1 - f) * one + f * fw))
    gm = isotropic_signal(bvals, GREY, N)
    for f in (0.3, 0.5):
        out.append((f"fibre + {int(100 * f)}% grey matter", (1 - f) * one + f * gm))
    return out


def section_a(w):
    w("A. Model mismatch: crossing fibres and partial volume")
    w("   Reference for each arm = its own fit to the noise-free signal (nf). Bias = noisy mean - nf;")
    w("   RMSE about nf. 'offset' = measured minus predicted weighting (noisy means).")
    for subj in PROTOCOLS:
        bvals, bvecs, X = protocol(subj)
        rng = np.random.default_rng(101 if subj == "stanford" else 102)
        scen = scenarios_a(bvals, bvecs, rng)
        for snr in (10, 20, 30):
            sigma = S0 / snr
            w()
            w(f"  {subj}, SNR {snr}")
            w(f"  {'scenario':<30}{'arm':<40}{'FA nf':>7}{'FA bias':>9}{'FA RMSE':>9}"
              f"{'MD nf':>8}{'MD bias':>9}{'MD RMSE':>9}{'inadm %':>9}")
            for k, (name, clean) in enumerate(scen):
                r = np.random.default_rng([1, snr, k, subj == "stanford"])
                noisy = rician(S0 * clean, sigma, r)
                res = {}
                for arm in ARMS:
                    fa0, md0, _ = fit(X, S0 * clean, arm)
                    fa, md, ok = fit(X, noisy, arm)
                    res[arm] = (fa0.mean(), fa.mean() - fa0.mean(), np.sqrt(np.mean((fa - fa0) ** 2)),
                                md0.mean(), md.mean() - md0.mean(), np.sqrt(np.mean((md - md0) ** 2)),
                                100 * np.mean(~ok), fa.mean(), md.mean())
                    v = res[arm]
                    w(f"  {name if arm == ARMS[0] else '':<30}{LABEL[arm]:<40}{v[0]:>7.3f}{v[1]:>+9.4f}"
                      f"{v[2]:>9.4f}{v[3]:>8.3f}{v[4]:>+9.4f}{v[5]:>9.4f}{v[6]:>9.2f}")
                w(f"  {'':<30}{'offset, measured - predicted':<40}{'':>7}"
                  f"{res['measured'][7] - res['predicted'][7]:>+9.4f}{'':>9}{'':>8}"
                  f"{res['measured'][8] - res['predicted'][8]:>+9.4f}")


# ---------------------------------------------------------------------------- B
def evals_for(fa, md=0.7e-3):
    k = np.sqrt(3 * fa ** 2 / (9 - 6 * fa ** 2))
    return np.array([md * (1 + 2 * k), md * (1 - k), md * (1 - k)])


def section_b(w):
    w()
    w("B. Noise model: non-central chi with L channels at the same per-channel sigma (L = 1 is Rician)")
    w("   Single fibre, MD 0.70. Bias = estimate minus truth; 'offset' = measured minus predicted.")
    for subj in PROTOCOLS:
        bvals, bvecs, X = protocol(subj)
        for fa_true in (0.45, 0.71):
            ev = evals_for(fa_true)
            w()
            w(f"  {subj}, true FA {fa_true:.2f}")
            w(f"  {'SNR':>5}{'L':>4}{'floor/S0 %':>12}" + "".join(f"{'MD bias ' + a:>18}" for a in ARMS)
              + f"{'MD offset':>11}{'FA offset':>11}")
            for snr in (10, 20, 30):
                sigma = S0 / snr
                for L in (1, 4, 8):
                    r = np.random.default_rng([2, snr, L, int(100 * fa_true), subj == "stanford"])
                    clean = S0 * fibre_signal(bvals, bvecs, ev, random_directions(N, r))
                    noisy = ncchi(clean, sigma, L, r)
                    floor = ncchi(np.zeros((2000, 1)), sigma, L, r).mean() / S0 * 100
                    res = {arm: fit(X, noisy, arm) for arm in ARMS}
                    w(f"  {snr:>5}{L:>4}{floor:>12.1f}"
                      + "".join(f"{res[a][1].mean() - 0.70:>+18.4f}" for a in ARMS)
                      + f"{res['measured'][1].mean() - res['predicted'][1].mean():>+11.4f}"
                      f"{res['measured'][0].mean() - res['predicted'][0].mean():>+11.4f}")


# ---------------------------------------------------------------------------- C
def perturbations(rng):
    return [
        ("none", None, None),
        ("scale uniform +/-2%", lambda n: rng.uniform(-0.02, 0.02, n), None),
        ("scale uniform +/-5%", lambda n: rng.uniform(-0.05, 0.05, n), None),
        ("scale +5% everywhere", lambda n: np.full(n, 0.05), None),
        ("scale -5% everywhere", lambda n: np.full(n, -0.05), None),
        ("direction tilt SD 1 deg", None, 1.0),
        ("direction tilt SD 3 deg", None, 3.0),
    ]


def perturbed_signal(bvals, bvecs, ev, dirs, scale, tilt, rng):
    """Signal under a per-voxel b-matrix that differs from the nominal one."""
    n = dirs.shape[0]
    b = bvals[None, :] * (1 + (scale(n)[:, None] if scale else 0))
    if tilt:
        # each voxel's gradients tilted by one random rotation of angle ~ N(0, tilt)
        axis = random_directions(n, rng)
        ang = np.radians(rng.normal(0, tilt, n))
        g = np.stack([rotate(np.tile(bvecs[i], (n, 1)), axis, ang) for i in range(bvecs.shape[0])], 1)
        cos2 = np.einsum("nij,nj->ni", g, dirs) ** 2
    else:
        cos2 = (dirs @ bvecs.T) ** 2
    l1, l2 = ev[0], ev[1]
    return np.exp(-b * (l2 + (l1 - l2) * cos2))


def section_c(w):
    w()
    w("C. b-matrix errors: signal generated with a perturbed b-matrix, fitted with the nominal one")
    w("   Bias = estimate minus truth (um^2/ms for MD). 'nonadd' = bias(noise+error) - bias(noise) - bias(error).")
    for subj in PROTOCOLS:
        bvals, bvecs, X = protocol(subj)
        for fa_true in (0.45, 0.71):
            ev = evals_for(fa_true)
            w()
            w(f"  {subj}, true FA {fa_true:.2f}, MD 0.70")
            w(f"  {'perturbation':<26}{'noise':<8}{'arm':<40}{'FA bias':>9}{'MD bias':>9}"
              f"{'MD offset':>11}{'FA nonadd':>11}{'MD nonadd':>11}")
            rng = np.random.default_rng([3, int(100 * fa_true), subj == "stanford"])
            dirs = random_directions(N, rng)
            base = {}
            for name, scale, tilt in perturbations(rng):
                clean = S0 * perturbed_signal(bvals, bvecs, ev, dirs, scale, tilt, rng)
                for snr in (None, 20):
                    y = clean if snr is None else rician(clean, S0 / snr, rng)
                    res = {arm: fit(X, y, arm) for arm in ARMS}
                    base[(name, snr)] = res
                    for arm in ARMS:
                        fa, md = res[arm][0].mean() - fa_true, res[arm][1].mean() - 0.70
                        na = ""
                        if name != "none" and snr is not None:
                            nfa = fa - (base[("none", 20)][arm][0].mean() - fa_true) \
                                - (base[(name, None)][arm][0].mean() - fa_true)
                            nmd = md - (base[("none", 20)][arm][1].mean() - 0.70) \
                                - (base[(name, None)][arm][1].mean() - 0.70)
                            na = f"{nfa:>+11.4f}{nmd:>+11.4f}"
                        off = (f"{res['measured'][1].mean() - res['predicted'][1].mean():>+11.4f}"
                               if arm == "measured" else f"{'':>11}")
                        w(f"  {name if arm == ARMS[0] else '':<26}"
                          f"{('none' if snr is None else str(snr)) if arm == ARMS[0] else '':<8}"
                          f"{LABEL[arm]:<40}{fa:>+9.4f}{md:>+9.4f}{off}{na}")


def main():
    lines = []

    def w(s=""):
        print(s, flush=True)
        lines.append(s)

    w("Revision simulations on the real gradient tables (tensor_estimators.py arms)")
    w("Stanford: 10 b = 0 + 150 at b = 2000; Sherbrooke: 1 b = 0 + 64 at b = 1000. S0 = 1000, "
      f"{N:,} voxels per cell.")
    section_a(w)
    section_b(w)
    section_c(w)
    out = ROOT / "revision_simulations.txt"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
