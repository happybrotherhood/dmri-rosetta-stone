"""
sherbrooke_fa_diagnosis.py
--------------------------
How much of each dataset's offset between the weighting schemes noise can
explain, and why a simplified simulation of the Sherbrooke protocol predicts
the opposite FA sign to the data.

Both schemes are fitted with tensor_estimators.py, which reproduces FSL
dtifit --wls and DIPY WLS on these data (tensor_estimators_check.txt).

Voxels and FA bins are taken from the DIPY fit alone (FA > 0.2, admissible).
DIPY clips negative eigenvalues, so its fit is always physically admissible;
the measured-signal fit is not, and selecting or binning voxels on its output
would select on the very offset being measured. Non-physical measured-signal
fits are handled by one of three rules, applied identically to observed and
simulated data, and every result is reported under the main rule:

  exclude   a voxel is left out when either fit is inadmissible (main rule)
  clip      FA is clipped to [0, 1] and MD to [0, 3] um^2/ms; no voxel removed
  keep      values are used as fitted; no voxel removed

Stages
  refit          the real data refitted, against the published maps
  pairing        each Sherbrooke subset volume matched to its source volume
  drop z<-3      real data refitted without measurements far below the prediction
  drop |z|>3     real data refitted without outliers in either direction
  permuted       fitted signal plus the voxel's real residuals shuffled across
                 directions: keeps their amplitudes, breaks their link to
                 gradient direction
  noise sweep    each voxel's own tensor (the DIPY fit, eigenvalues clipped at
                 zero) and S0, with Rician noise at a multiple of its MP-PCA sigma
  controls       the two exclusions and the shuffle applied to noise-only data
                 at the measured noise level, and its residual tail rates
  idealisations  the simplified simulation's assumptions imposed one at a time
                 on the real tensors

The noise scale is measured on Stanford's ten b = 0 volumes as the median over
white matter of (temporal SD / MP-PCA sigma), divided by the median of s / sigma
for ten Gaussian samples. Sherbrooke, which has one b = 0 volume, is given
Stanford's scale. The residual-matched scale is an upper bound, because real
residuals also carry model misfit. Every simulated stage is repeated with
independently seeded noise and reported as mean and standard error.

Usage:
    python scripts/sherbrooke_fa_diagnosis.py

Outputs:
    sherbrooke_fa_diagnosis.txt
"""

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy.stats import chi2

import tensor_estimators as te

ROOT = Path(__file__).parent.parent
EDGES = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0001]
LABELS = ["0.2-0.3", "0.3-0.4", "0.4-0.5", "0.5-0.6", "0.6-0.7", "0.7-1.0", "all"]
RULES = ("exclude", "clip", "keep")
K = 3.0                  # outlier threshold, in units of the voxel's MP-PCA sigma
B0_MAX = 50
REPEATS = 5
SEED = 2026


def load(p: Path) -> np.ndarray:
    return np.nan_to_num(np.asarray(nib.load(str(p)).dataobj, dtype=np.float64))


def binned(values, bins, sel) -> np.ndarray:
    out = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        m = sel & (bins >= lo) & (bins < hi)
        out.append(float(np.mean(values[m])) if m.any() else np.nan)
    out.append(float(np.mean(values[sel])))
    return np.array(out)


def mad_sd(a) -> float:
    return float(1.4826 * np.median(np.abs(a - np.median(a))))


def rician(clean, sigma, rng):
    return np.sqrt((clean + sigma * rng.normal(size=clean.shape)) ** 2
                   + (sigma * rng.normal(size=clean.shape)) ** 2)


def signal(X, beta):
    return np.exp(np.clip(beta @ X.T, -700, 700))


def beta_from(evals, vecs, l0):
    D = np.einsum("vij,vj,vkj->vik", vecs, evals, vecs)
    return np.column_stack([l0, D[:, 0, 0], D[:, 1, 1], D[:, 2, 2],
                            D[:, 0, 1], D[:, 0, 2], D[:, 1, 2]])


def axisym(evals):
    """Same FA and MD, with the two minor eigenvalues made equal (ascending order kept)."""
    m = evals.mean(1)
    fa = np.clip(np.sqrt(1.5) * np.sqrt(((evals - m[:, None]) ** 2).sum(1))
                 / np.maximum(np.sqrt((evals ** 2).sum(1)), 1e-12), 0, 0.999)
    k = np.sqrt(3 * fa ** 2 / (9 - 6 * fa ** 2))
    return np.column_stack([m * (1 - k), m * (1 - k), m * (1 + 2 * k)])


def random_rotation(n, rng):
    q, r = np.linalg.qr(rng.normal(size=(n, 3, 3)))
    return q * np.sign(np.einsum("vii->vi", r))[:, None, :]


def rule_offsets(fm, mm, fp, mp, bins) -> dict:
    """Measured minus predicted, binned, under each rule for non-physical fits."""
    every = np.ones(len(fm), bool)
    sel = te.admissible(fm, mm) & te.admissible(fp, mp)
    cf, cm = (lambda a: np.clip(a, 0, 1)), (lambda a: np.clip(a, 0, 3))
    return {
        "exclude": (binned(fm - fp, bins, sel), binned(mm - mp, bins, sel), float(sel.mean())),
        "clip": (binned(cf(fm) - cf(fp), bins, every), binned(cm(mm) - cm(mp), bins, every), 1.0),
        "keep": (binned(fm - fp, bins, every), binned(mm - mp, bins, every), 1.0),
    }


def fit_offsets(X, y, bins, keep=None):
    fm, mm, _ = te.fit_fa_md(X, y, "measured", keep)
    fp, mp, bp = te.fit_fa_md(X, y, "predicted", keep)
    return rule_offsets(fm, mm, fp, mp, bins), bp


class Result:
    """Binned offsets per rule: fa, md, fa_se, md_se (None for single fits), kept."""

    def __init__(self, per_rule, resid_sd=np.nan, z=None, controls=None):
        self.r = per_rule
        self.resid_sd, self.z, self.controls = resid_sd, z, controls or {}

    def __getitem__(self, rule):
        return self.r[rule]


def single(per_rule) -> Result:
    return Result({k: dict(fa=v[0], md=v[1], fa_se=None, md_se=None, kept=v[2])
                   for k, v in per_rule.items()})


def aggregate(runs) -> dict:
    """Mean and standard error across runs of rule_offsets output."""
    out = {}
    for rule in RULES:
        fa = np.array([run[rule][0] for run in runs])
        md = np.array([run[rule][1] for run in runs])
        se = (lambda a: a.std(0, ddof=1) / np.sqrt(len(runs))) if len(runs) > 1 else \
            (lambda a: np.full(a.shape[1], np.nan))
        out[rule] = dict(fa=fa.mean(0), md=md.mean(0), fa_se=se(fa), md_se=se(md),
                         kept=float(np.mean([run[rule][2] for run in runs])))
    return out


def repeated(make_y, X, bins, key, sig=None, dw=None, keep_z=False, controls=None) -> Result:
    """Independently seeded noise draws; optional noise-only controls on each draw."""
    runs, ctrl_runs = [], []
    resid_sd, z = np.nan, None
    for r in range(REPEATS):
        rng = np.random.default_rng([SEED, *key, r])
        y = make_y(rng)
        per_rule, bp = fit_offsets(X, y, bins)
        runs.append(per_rule)
        if sig is not None:
            zz = ((y - signal(X, bp)) / sig)[:, dw]
            if r == 0:
                resid_sd = mad_sd(zz)
                z = zz if keep_z else None
            if controls is not None:
                ctrl_runs.append(controls(y, bp, zz, rng))
    ctrl = {}
    if ctrl_runs:
        for label in ctrl_runs[0]:
            if label == "tails":
                ctrl["tails"] = tuple(float(np.mean([c["tails"][i] for c in ctrl_runs]))
                                      for i in (0, 1))
            else:
                ctrl[label] = Result(aggregate([c[label] for c in ctrl_runs]))
    return Result(aggregate(runs), resid_sd, z, ctrl)


def pairing_check(w):
    """Match every Sherbrooke subset volume to its source volume by content."""
    dd = ROOT / "data" / "hcp" / "sherbrooke" / "T1w" / "Diffusion"
    it = ROOT / "data" / "hcp" / "sherbrooke" / "dti_iter0"
    ob, ov = np.loadtxt(str(dd / "bvals")), np.loadtxt(str(dd / "bvecs"))
    ov = ov.T if ov.shape[0] == 3 else ov
    sb, sv = np.loadtxt(str(it / "subset.bvals")), np.loadtxt(str(it / "subset.bvecs"))
    sv = sv.T if sv.shape[0] == 3 else sv
    z = 30
    orig = np.asarray(nib.load(str(dd / "data.nii.gz")).dataobj[:, :, z, :], dtype=np.float64)
    sub = np.asarray(nib.load(str(it / "subset_data.nii.gz")).dataobj[:, :, z, :], dtype=np.float64)
    bad, matched = [], 0
    for j in range(sub.shape[-1]):
        err = np.abs(orig - sub[..., j:j + 1]).max(axis=(0, 1))
        i = int(np.argmin(err))
        if err[i] > 1e-3 * max(1.0, np.abs(sub[..., j]).max()):
            bad.append((j, "no identical source volume"))
            continue
        matched += 1
        if abs(ob[i] - sb[j]) > 1 or not np.allclose(ov[i], sv[j], atol=1e-4):
            bad.append((j, f"source vol {i}: b {ob[i]:.0f} vs {sb[j]:.0f}"))
    w(f"Gradient-table pairing (Sherbrooke subset vs original, slice {z}):")
    w(f"  {sub.shape[-1]} subset volumes, {matched} matched to a source volume by "
      f"content, {len(bad)} mismatches")
    for j, why in bad[:10]:
        w(f"  volume {j}: {why}")


def fmt(v, se=None, width=17):
    s = f"{v:+.4f}" if se is None or not np.isfinite(se) else f"{v:+.4f}±{se:.4f}"
    return f"{s:>{width}}"


def run(subj, si, w, k_common=None):
    data_p, bvals, bvecs = te.load_protocol(subj)
    X = te.design(bvals, bvecs)
    dw = bvals > B0_MAX
    n_b0 = int((~dw).sum())
    d = ROOT / "data" / "hcp" / subj
    it = d / "dti_iter0"

    fa_m_pub, fa_p_pub = load(it / "fsl_dti_FA.nii.gz"), load(it / "dipy_FA.nii.gz")
    md_m_pub = load(it / "fsl_dti_MD.nii.gz") * 1e3
    md_p_pub = load(it / "dipy_MD.nii.gz") * 1e3
    uni = te.admissible(fa_p_pub, md_p_pub, 0.2)
    bins = fa_p_pub[uni]
    Y = np.asarray(nib.load(str(data_p)).dataobj, dtype=np.float32)[uni].astype(np.float64)
    sig = load(d / "dti_denoised" / "noise_map.nii.gz")[uni][:, None]
    n = Y.shape[0]
    counts = [int(np.sum((bins >= lo) & (bins < hi)))
              for lo, hi in zip(EDGES[:-1], EDGES[1:])] + [n]

    w()
    w("=" * 110)
    w(f"{subj}: {n_b0} b=0 + {int(dw.sum())} directions at "
      f"b={int(np.round(bvals[dw].mean(), -2))};  {n:,} voxels with DIPY FA > 0.2 (bins by DIPY FA)")
    w("=" * 110)

    fm, mm, _ = te.fit_fa_md(X, Y, "measured")
    fp, mp, bp = te.fit_fa_md(X, Y, "predicted")
    w("Refit against the published maps, mean |difference| (maximum):")
    for label, f, m, fpub, mpub in (("measured  vs FSL --wls", fm, mm, fa_m_pub, md_m_pub),
                                    ("predicted vs DIPY WLS ", fp, mp, fa_p_pub, md_p_pub)):
        df, dm = np.abs(f - fpub[uni]), np.abs(m - mpub[uni])
        w(f"  {label}:  FA {df.mean():.6f} ({df.max():.4f})   MD {dm.mean():.6f} ({dm.max():.4f})")

    obs = single(rule_offsets(fa_m_pub[uni], md_m_pub[uni], fa_p_pub[uni], md_p_pub[uni], bins))
    w(f"  observed voxels kept under 'exclude': {100 * obs['exclude']['kept']:.1f}%")

    fitted = signal(X, bp)
    resid = Y - fitted
    zdw = (resid / sig)[:, dw]
    real = {"observed": obs}
    for label, mask in ((f"drop z<-{K:g}", zdw >= -K), (f"drop |z|>{K:g}", np.abs(zdw) <= K)):
        keep = np.ones_like(Y, bool)
        keep[:, dw] = mask
        real[label] = single(fit_offsets(X, Y, bins, keep)[0])

    def shuffle(res, fit_signal, rng):
        p = res.copy()
        idx = np.argsort(rng.random((res.shape[0], int(dw.sum()))), axis=1)
        p[:, dw] = np.take_along_axis(res[:, dw], idx, axis=1)
        return fit_signal + p
    real["permuted"] = repeated(lambda rng: shuffle(resid, fitted, rng), X, bins, key=(si, 1))

    for title, attr in (("FA, measured minus predicted ('exclude' rule)", "fa"),
                        ("MD, measured minus predicted, um^2/ms ('exclude' rule)", "md")):
        w()
        w(title)
        w(f"  {'FA bin':<9}{'voxels':>9}" + "".join(f"{k:>17}" for k in real))
        for r, lab in enumerate(LABELS):
            w(f"  {lab:<9}{counts[r]:>9,}" + "".join(
                fmt(v["exclude"][attr][r], None if v["exclude"][attr + "_se"] is None
                    else v["exclude"][attr + "_se"][r]) for v in real.values()))

    per_vol = np.mean(zdw < -K, axis=0) * 100
    order = np.argsort(per_vol)[::-1]
    dw_index = np.where(dw)[0]
    w()
    w("Residuals of the predicted-signal fit, diffusion-weighted measurements (z = r / MP-PCA sigma):")
    w(f"  median z {float(np.median(zdw)):+.2f};  below -{K:g}: {float(np.mean(zdw < -K)) * 100:.2f}%"
      f"   above +{K:g}: {float(np.mean(zdw > K)) * 100:.2f}%")
    w(f"  per volume, % of voxels below -{K:g}: median {float(np.median(per_vol)):.2f}%, worst five "
      + ", ".join(f"vol {dw_index[i]} {per_vol[i]:.1f}%" for i in order[:5]))
    w(f"  volumes above 3x the median rate: "
      f"{int(np.sum(per_vol > 3 * np.median(per_vol)))} of {int(dw.sum())}")
    real_sd = mad_sd(zdw)
    w(f"  robust SD of z: {real_sd:.3f}")

    if n_b0 >= 5:
        tsd = Y[:, ~dw].std(axis=1, ddof=1)
        k_raw = float(np.median(tsd / sig[:, 0]))
        c = float(np.sqrt(chi2.median(n_b0 - 1) / (n_b0 - 1)))
        k_corr = k_raw / c
        w(f"  b=0 temporal SD / MP-PCA sigma, median over voxels: {k_raw:.3f}")
        w(f"  divided by the median of s/sigma for {n_b0} Gaussian samples ({c:.4f}): {k_corr:.3f}")
    else:
        k_raw, k_corr = k_common
        w(f"  single b=0 volume: noise scale taken from Stanford "
          f"(x{k_raw:.3f} raw, x{k_corr:.3f} corrected)")
    kr, kc_key = round(k_raw, 3), round(k_corr, 3)

    ev, vec = np.linalg.eigh(te.tensor(bp))
    ev = np.clip(ev, 0, None)
    l0 = bp[:, 0]
    clean = signal(X, beta_from(ev, vec, l0))

    def controls(y, bp_, zz, rng):
        fit_ = signal(X, bp_)
        out = {}
        for label, mask in ((f"drop z<-{K:g}", zz >= -K), (f"drop |z|>{K:g}", np.abs(zz) <= K)):
            keep = np.ones_like(y, bool)
            keep[:, dw] = mask
            out[label] = fit_offsets(X, y, bins, keep)[0]
        out["permuted"] = fit_offsets(X, shuffle(y - fit_, fit_, rng), bins)[0]
        out["tails"] = (float(np.mean(zz < -K)) * 100, float(np.mean(zz > K)) * 100)
        return out

    scales = sorted({1.0, 1.15, 1.3, 1.5, 2.0, kr, kc_key})
    sweep = {}
    for code, sc in enumerate(scales):
        sweep[sc] = repeated(lambda rng, sc=sc: rician(clean, sig * sc, rng), X, bins,
                             key=(si, 10 + code), sig=sig, dw=dw,
                             keep_z=sc in (1.0, kc_key),
                             controls=controls if sc == kc_key else None)
    sds = np.array([sweep[s].resid_sd for s in scales])
    order = np.argsort(sds)
    bound = round(float(np.interp(real_sd, sds[order], np.array(scales)[order])), 3)
    if bound not in sweep:
        sweep[bound] = repeated(lambda rng: rician(clean, sig * bound, rng), X, bins,
                                key=(si, 30), sig=sig, dw=dw)
    k1, kc, kb = sweep[1.0], sweep[kc_key], sweep[bound]

    w()
    w(f"Noise on the real tensors at scaled MP-PCA sigma, 'exclude' rule (mean ± SE over {REPEATS} draws):")
    w(f"  {'scale':<26}{'FA all':>16}{'FA .5-.6':>10}{'FA .7-1':>10}{'MD all':>16}"
      f"{'resid SD':>10}{'kept %':>8}")
    oe = obs["exclude"]
    w(f"  {'observed':<26}{oe['fa'][-1]:>+16.4f}{oe['fa'][3]:>+10.4f}{oe['fa'][5]:>+10.4f}"
      f"{oe['md'][-1]:>+16.4f}{real_sd:>10.2f}{100 * oe['kept']:>8.1f}")
    for sc in sorted(sweep):
        s = sweep[sc]["exclude"]
        tags = [t for t, v in (("b0 raw", kr), ("b0 corrected", kc_key), ("residual bound", bound))
                if sc == v]
        label = f"x{sc:.3f}" + (f" ({', '.join(tags)})" if tags else "")
        w(f"  {label:<26}{s['fa'][-1]:>+9.4f}±{s['fa_se'][-1]:.4f}{s['fa'][3]:>+10.4f}"
          f"{s['fa'][5]:>+10.4f}{s['md'][-1]:>+9.4f}±{s['md_se'][-1]:.4f}"
          f"{sweep[sc].resid_sd:>10.2f}{100 * s['kept']:>8.1f}")

    w()
    w("Sensitivity to the rule for non-physical fits (observed and noise-only, same rule):")
    w(f"  {'rule':<9}{'':>3}{'FA obs':>9}{'FA x1.000':>11}{f'FA x{kc_key:.3f}':>11}"
      f"{f'FA x{bound:.3f}':>11}{'FA7-1 obs':>11}{f'FA7-1 x{kc_key:.2f}':>13}"
      f"{'MD obs':>9}{f'MD x{kc_key:.3f}':>11}{'FA share':>10}{'MD share':>10}")
    for rule in RULES:
        o, a, b, c = obs[rule], k1[rule], kc[rule], kb[rule]
        w(f"  {rule:<9}{'':>3}{o['fa'][-1]:>+9.4f}{a['fa'][-1]:>+11.4f}{b['fa'][-1]:>+11.4f}"
          f"{c['fa'][-1]:>+11.4f}{o['fa'][5]:>+11.4f}{b['fa'][5]:>+13.4f}"
          f"{o['md'][-1]:>+9.4f}{b['md'][-1]:>+11.4f}"
          f"{100 * b['fa'][-1] / o['fa'][-1]:>9.1f}%{100 * b['md'][-1] / o['md'][-1]:>9.1f}%")
    w("  shares at the measured noise level; at the residual bound: " + "; ".join(
        f"{rule} FA {100 * kb[rule]['fa'][-1] / obs[rule]['fa'][-1]:.1f}% "
        f"MD {100 * kb[rule]['md'][-1] / obs[rule]['md'][-1]:.1f}%" for rule in RULES))
    w("  shares at x1.000: " + "; ".join(
        f"{rule} FA {100 * k1[rule]['fa'][-1] / obs[rule]['fa'][-1]:.1f}% "
        f"MD {100 * k1[rule]['md'][-1] / obs[rule]['md'][-1]:.1f}%" for rule in RULES))
    for rule in RULES:
        ob, sb = obs[rule], kc[rule]
        w(f"  per bin at x{kc_key:.3f}, {rule}: FA " + "  ".join(
            f"{lab} {ob['fa'][i]:+.4f}/{sb['fa'][i]:+.4f}" for i, lab in enumerate(LABELS[:-1])))

    w()
    w(f"Checks of the remaining offset, 'exclude' rule: real data, and the same operation on "
      f"noise-only data at x{kc_key:.3f} (mean ± SE):")
    w(f"  {'':<14}{'FA real':>10}{'FA noise-only':>20}{'MD real':>10}{'MD noise-only':>20}")
    rows = [("as fitted", real["observed"], Result(kc.r)),
            (f"drop z<-{K:g}", real[f"drop z<-{K:g}"], kc.controls[f"drop z<-{K:g}"]),
            (f"drop |z|>{K:g}", real[f"drop |z|>{K:g}"], kc.controls[f"drop |z|>{K:g}"]),
            ("shuffled", real["permuted"], kc.controls["permuted"])]
    for label, rr, cc in rows:
        re_, ce = rr["exclude"], cc["exclude"]
        w(f"  {label:<14}{re_['fa'][-1]:>+10.4f}{fmt(ce['fa'][-1], ce['fa_se'][-1], 20)}"
          f"{re_['md'][-1]:>+10.4f}{fmt(ce['md'][-1], ce['md_se'][-1], 20)}")
    lo_t, hi_t = kc.controls["tails"]
    w(f"  residuals beyond -{K:g} / +{K:g} MP-PCA sigma: real {float(np.mean(zdw < -K)) * 100:.2f}% / "
      f"{float(np.mean(zdw > K)) * 100:.2f}%;  noise-only at x{kc_key:.3f} {lo_t:.2f}% / {hi_t:.2f}%")
    for label, rr, cc in rows[1:]:
        for attr in ("fa", "md"):
            base_r, base_c = rows[0][1]["exclude"][attr][-1], rows[0][2]["exclude"][attr][-1]
            w(f"  {label:<14} {attr.upper()} change: real {100 * (rr['exclude'][attr][-1] / base_r - 1):+.1f}%, "
              f"noise-only {100 * (cc['exclude'][attr][-1] / base_c - 1):+.1f}%")

    hi = bins >= 0.6
    v1 = np.linalg.eigh(te.tensor(bp[hi]))[1][..., -1]
    cos2 = (v1 @ bvecs[dw].T) ** 2
    cedges = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001]
    w()
    w("Residual z by angle between gradient and fibre (DIPY FA >= 0.6; cos^2 = 1 is along it).")
    w("The mean is sensitive to a few extreme residuals, so the median is given as well:")
    w(f"  {'':<22}" + "".join(f"{f'{a:.1f}-{min(b, 1):.1f}':>10}"
                              for a, b in zip(cedges[:-1], cedges[1:])))
    for stat_name, stat in (("mean", np.mean), ("median", np.median)):
        for name, zz in (("real", zdw), ("noise x1.000", k1.z), (f"noise x{kc_key:.3f}", kc.z)):
            zz = zz[hi]
            w(f"  {name + ' ' + stat_name:<22}" + "".join(
                f"{float(stat(zz[(cos2 >= a) & (cos2 < b)])):>+10.2f}"
                for a, b in zip(cedges[:-1], cedges[1:])))

    md_true = np.maximum(ev.mean(1), 1e-5)
    md07 = ev * (0.7e-3 / md_true)[:, None]
    flat_l0 = np.full(n, np.log(np.median(np.exp(l0))))
    flat_s = np.full_like(sig, np.median(sig))
    variants = [
        ("MD set to 0.70", lambda rng: (md07, vec, l0, sig)),
        ("axially symmetric", lambda rng: (axisym(ev), vec, l0, sig)),
        ("random orientation", lambda rng: (ev, random_rotation(n, rng), l0, sig)),
        ("uniform sigma", lambda rng: (ev, vec, l0, flat_s)),
        ("uniform S0 and sigma", lambda rng: (ev, vec, flat_l0, flat_s)),
        ("all four", lambda rng: (axisym(md07), random_rotation(n, rng), flat_l0, flat_s)),
    ]
    ideal = {"real tensors": k1}
    for code, (label, make) in enumerate(variants):
        def make_y(rng, make=make):
            e_, v_, l_, s_ = make(rng)
            return rician(signal(X, beta_from(e_, v_, l_)), s_, rng)
        ideal[label] = repeated(make_y, X, bins, key=(si, 40 + code))
    w()
    w(f"Real tensors: median MD {float(np.median(md_true)) * 1e3:.3f} um^2/ms, "
      f"median (l2-l3)/l2 {float(np.median((ev[:, 1] - ev[:, 0]) / np.maximum(ev[:, 1], 1e-9))):.2f}")
    w(f"Noise at MP-PCA sigma on the real tensors, one idealisation at a time (mean over {REPEATS} draws);")
    w("FA all under each rule, then 'exclude' bins and MD, and the largest SE in the row:")
    w(f"  {'tensors':<24}{'FA excl':>9}{'FA clip':>9}{'FA keep':>9}{'FA .5-.6':>10}{'FA .7-1':>10}"
      f"{'MD all':>10}{'max SE':>9}")
    for label, s in ideal.items():
        e = s["exclude"]
        max_se = float(np.nanmax([s[rule]["fa_se"][-1] for rule in RULES]
                                 + [e["fa_se"][3], e["fa_se"][5], e["md_se"][-1]]))
        w(f"  {label:<24}{s['exclude']['fa'][-1]:>+9.4f}{s['clip']['fa'][-1]:>+9.4f}"
          f"{s['keep']['fa'][-1]:>+9.4f}{e['fa'][3]:>+10.4f}{e['fa'][5]:>+10.4f}"
          f"{e['md'][-1]:>+10.4f}{max_se:>9.4f}")

    w()
    w(f"Table 7 values ('exclude' rule): observed, and noise on the real tensors at x1.000 and "
      f"x{kc_key:.3f} (mean ± SE over {REPEATS} draws)")
    w(f"  {'FA bin':<9}{'voxels':>9}{'FA obs':>9}{'FA x1.000':>18}{f'FA x{kc_key:.3f}':>18}"
      f"{'MD obs':>9}{'MD x1.000':>18}{f'MD x{kc_key:.3f}':>18}")
    a, b = k1["exclude"], kc["exclude"]
    for r, lab in enumerate(LABELS):
        w(f"  {lab:<9}{counts[r]:>9,}{oe['fa'][r]:>+9.4f}{fmt(a['fa'][r], a['fa_se'][r], 18)}"
          f"{fmt(b['fa'][r], b['fa_se'][r], 18)}{oe['md'][r]:>+9.4f}"
          f"{fmt(a['md'][r], a['md_se'][r], 18)}{fmt(b['md'][r], b['md_se'][r], 18)}")
    w(f"  voxels kept: observed {100 * oe['kept']:.1f}%, x1.000 {100 * a['kept']:.1f}%, "
      f"x{kc_key:.3f} {100 * b['kept']:.1f}%;  largest SE {max(np.nanmax(a['fa_se']), np.nanmax(b['fa_se']), np.nanmax(a['md_se']), np.nanmax(b['md_se'])):.4f}")
    return k_raw, k_corr


def main():
    out = ROOT / "sherbrooke_fa_diagnosis.txt"
    with open(out, "w") as fh:
        def w(s=""):
            print(s, flush=True)
            fh.write(s + "\n")
        w("How much of each offset between the weighting schemes does noise explain?")
        w("All differences: measured-signal minus predicted-signal weighting "
          "(FSL dtifit --wls minus DIPY WLS). MD in um^2/ms.")
        w()
        pairing_check(w)
        k = run("stanford", 0, w)
        run("sherbrooke", 1, w, k_common=k)
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()
