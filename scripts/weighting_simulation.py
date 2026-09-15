"""
weighting_simulation.py
-----------------------
Bias and error of every linear tensor estimator, simulated on the two real
acquisition protocols with idealised tensors.

The phantom (phantom_accuracy.py) has one gradient scheme with ten b = 0
volumes. The real datasets differ from it, and from each other: Sherbrooke has
a single b = 0 volume and a b = 1000 shell. This script asks whether each
estimator's bias and error depend on the protocol, using the exact gradient
tables the toolkits were given:

    stanford     10 b = 0 + 150 directions at b = 2000
    sherbrooke    1 b = 0 +  64 directions at b = 1000

Ground truth: axially symmetric tensors with MD = 0.70 um^2/ms, FA from 0.25 to
0.80, uniformly random orientation, S0 = 1000 and Rician noise with
sigma = S0 / SNR, at SNR 10, 20, 30 and 50 and at each dataset's measured SNR.
All four arms are fitted to the same noisy voxels with tensor_estimators.py,
which reproduces the toolkits' own maps:

    ols        FSL dtifit (default)
    measured   FSL dtifit --wls, MRtrix3 dwi2tensor -iter 0
    iwls       MRtrix3 dwi2tensor (default)
    predicted  DIPY WLS (default)

Reported per arm: bias (estimate minus truth) with its Monte Carlo standard
error, root-mean-square error (RMSE), and the percentage of voxels with a
physically inadmissible fit. Every voxel enters the bias, as it would in a
toolkit's output map. Each cell has its own seed, so cells do not depend on
the order in which they are run.

Usage:
    python scripts/weighting_simulation.py

Outputs:
    weighting_simulation.txt
"""

from pathlib import Path

import numpy as np

import tensor_estimators as te

ROOT = Path(__file__).parent.parent
N_VOX = 10000
S0 = 1000.0
MD = 0.7e-3
FAS = [0.25, 0.35, 0.45, 0.55, 0.65, 0.80]
SNRS = [10, 20, 30, 50]
PROTOCOLS = ("stanford", "sherbrooke")


def evals_for(fa: float) -> np.ndarray:
    """Axially symmetric eigenvalues [l1, l2, l2] with the requested FA and MD."""
    k = np.sqrt(3 * fa ** 2 / (9 - 6 * fa ** 2))
    return np.array([MD * (1 + 2 * k), MD * (1 - k), MD * (1 - k)])


def random_directions(n: int, rng) -> np.ndarray:
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def signals(bvals, bvecs, evals, dirs) -> np.ndarray:
    """S = S0 exp(-b g^T D g) for axially symmetric D with axis `dirs`."""
    l1, l2 = evals[0], evals[1]
    cos2 = (dirs @ bvecs.T) ** 2
    return S0 * np.exp(-bvals[None, :] * (l2 + (l1 - l2) * cos2))


def measured_snr() -> dict:
    """Single-b=0 SNR of each dataset, as written by snr_estimate.py."""
    p = ROOT / "snr_estimate.txt"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] in PROTOCOLS:
            out[parts[0]] = float(parts[-2])
    return out


def simulate(X, bvals, bvecs, fa, snr, rng) -> dict:
    sigma = S0 / snr
    clean = signals(bvals, bvecs, evals_for(fa), random_directions(N_VOX, rng))
    noisy = np.sqrt((clean + rng.normal(0, sigma, clean.shape)) ** 2
                    + rng.normal(0, sigma, clean.shape) ** 2)
    md_true = MD * 1e3
    res = {}
    for arm in te.ARMS:
        f, m, _ = te.fit_fa_md(X, noisy, arm)
        res[arm] = dict(
            fa_bias=float(f.mean() - fa), fa_se=float(f.std(ddof=1) / np.sqrt(N_VOX)),
            fa_rmse=float(np.sqrt(np.mean((f - fa) ** 2))),
            md_bias=float(m.mean() - md_true), md_se=float(m.std(ddof=1) / np.sqrt(N_VOX)),
            md_rmse=float(np.sqrt(np.mean((m - md_true) ** 2))),
            bad=float(100 * np.mean(~te.admissible(f, m))))
    return res


def main():
    snr_real = measured_snr()
    out = ROOT / "weighting_simulation.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s, flush=True)
            fh.write(s + "\n")
        w("Bias and error of each linear estimator on the real acquisition protocols")
        w(f"(simulation; Rician noise; axially symmetric tensors, MD true = 0.7000 um^2/ms; "
          f"{N_VOX} voxels per cell)")
        w("Bias = estimate minus truth; SE = Monte Carlo standard error of the bias;")
        w("inadm = % of voxels with FA outside [0, 1] or MD outside (0, 3]. MD in um^2/ms.")
        w("Arms: ols = FSL default; measured = FSL --wls / MRtrix3 -iter 0;")
        w("      iwls = MRtrix3 default; predicted = DIPY WLS default.")
        w("=" * 100)
        for pi, proto in enumerate(PROTOCOLS):
            _, bvals, bvecs = te.load_protocol(proto)
            X = te.design(bvals, bvecs)
            dw = bvals > 50
            w()
            w(f"{proto}: {int((~dw).sum())} b=0 + {int(dw.sum())} directions at "
              f"b={int(np.round(bvals[dw].mean(), -2))}")
            w(f"  {'SNR':>5}{'FA':>6}  {'arm':<10}{'FA bias':>9}{'SE':>8}{'RMSE':>8}"
              f"{'MD bias':>10}{'SE':>8}{'RMSE':>8}{'inadm%':>8}")
            grid = list(SNRS) + ([snr_real[proto]] if proto in snr_real else [])
            results = {}
            for snr in grid:
                tag = "*" if proto in snr_real and snr == snr_real[proto] else " "
                for fa in FAS:
                    rng = np.random.default_rng([2013, pi, int(round(snr * 10)), int(round(fa * 100))])
                    r = simulate(X, bvals, bvecs, fa, snr, rng)
                    results[(snr, fa)] = r
                    for arm in te.ARMS:
                        v = r[arm]
                        w(f" {tag}{snr:>5.1f}{fa:>6.2f}  {arm:<10}{v['fa_bias']:>+9.4f}{v['fa_se']:>8.4f}"
                          f"{v['fa_rmse']:>8.4f}{v['md_bias']:>+10.4f}{v['md_se']:>8.4f}"
                          f"{v['md_rmse']:>8.4f}{v['bad']:>8.2f}")
            if proto in snr_real:
                w(f"  * SNR measured on the real {proto} data (snr_estimate.txt)")

            # Two groups scanned at SNR 20 and 30 and fitted identically: the
            # apparent group difference is the change in bias between them.
            w()
            w(f"  {proto}: apparent difference between groups at SNR 20 and SNR 30 "
              f"(bias at 20 minus bias at 30; SE from the two independent cells)")
            w(f"  {'FA':>6}  {'arm':<10}{'FA diff':>9}{'SE':>8}{'MD diff':>10}{'SE':>8}")
            for fa in FAS:
                for arm in te.ARMS:
                    a, b = results[(20, fa)][arm], results[(30, fa)][arm]
                    w(f"  {fa:>6.2f}  {arm:<10}{a['fa_bias'] - b['fa_bias']:>+9.5f}"
                      f"{np.hypot(a['fa_se'], b['fa_se']):>8.5f}"
                      f"{a['md_bias'] - b['md_bias']:>+10.5f}{np.hypot(a['md_se'], b['md_se']):>8.5f}")

            # Every claim the manuscript counts over conditions, from unrounded values.
            n = len(results)
            w()
            w(f"  {proto}: counts over all {n} conditions and all four arms")
            for key in ("fa_bias", "md_bias", "fa_rmse", "md_rmse"):
                top = [c for c, r in results.items()
                       if max(te.ARMS, key=lambda a: abs(r[a][key])) == "measured"]
                others = sorted(set(results) - set(top))
                w(f"    measured has the largest |{key}| in {len(top)} of {n}"
                  + (f"; not in {others}" if others else ""))
            smaller = sum(1 for r in results.values()
                          if abs(r["measured"]["fa_bias"]) < abs(r["predicted"]["fa_bias"]))
            w(f"    |FA bias| of measured smaller than of predicted in {smaller} of {n}")
            w("    FA bias <= 0 in: " + ", ".join(
                f"{a} {sum(1 for r in results.values() if r[a]['fa_bias'] <= 0)}" for a in te.ARMS))
            for lo, hi, name in ((9, 12, "SNR near 10"), (19, 60, "SNR 20 and above")):
                ratios = [r["measured"][key] / min(r[a][key] for a in te.ARMS if a != "measured")
                          for (snr, fa), r in results.items() if lo <= snr <= hi
                          for key in ("fa_rmse",)]
                w(f"    FA RMSE of measured / best other arm, {name}: "
                  f"{min(ratios):.4f} to {max(ratios):.4f}")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
