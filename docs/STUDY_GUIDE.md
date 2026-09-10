# From the Diffusion Signal to the Paper's Claim

## A study guide

This guide builds the paper from the ground up. It starts with the signal a
scanner measures, derives why a tensor fit needs weights at all, shows where
the two weighting schemes come from and why one is worse, then follows the
experimental path we actually took — including the two places where our
conclusion was wrong and how each error was found.

Nothing is assumed except that you know what an MRI image is. Every number
quoted is from the paper's own tables.

**How to use it.** Sections 1–3 are the theory you need in order to say why the
question matters. Section 4 is what each toolkit does. Section 5 is our path,
in causal order. Section 6 is the numbers. Section 7 is how to defend it.

---

## 1. What is measured, and why it becomes a regression problem

### 1.1 The signal

A diffusion-weighted scan applies a pair of gradient pulses along a direction
**g**, with a strength summarised by the *b*-value. Water molecules that move
along **g** during the interval between pulses lose phase coherence, so the
measured signal drops. The more freely water moves along **g**, the more signal
is lost.

For one direction, the Stejskal–Tanner relation gives

```
S_i  =  S_0 · exp( −b_i · ĝ_iᵀ D ĝ_i )
```

where

- `S_i` is the signal measured with gradient direction `ĝ_i` at b-value `b_i`
- `S_0` is the signal with no diffusion weighting (a *b = 0* volume)
- `D` is the **diffusion tensor**: a 3×3 symmetric positive-definite matrix

`D` is what we want. It has six independent entries — three on the diagonal,
three off — because it is symmetric. Together with `S_0`, that is **seven
unknowns**.

### 1.2 Why a fit is needed

One measurement gives one equation. Seven unknowns need at least seven
measurements: one *b = 0* and six non-collinear directions. In practice we
acquire far more — 160 volumes in the Stanford dataset, 193 in Sherbrooke —
because the measurements are noisy, and averaging over many directions
suppresses noise.

So the system is **overdetermined**: more equations than unknowns, no exact
solution, and we must choose a tensor that fits the measurements *best* by some
criterion. That choice of criterion is the **estimator**. Everything in this
paper is about that choice.

### 1.3 Making it linear

The relation above is non-linear in `D` — `D` sits inside an exponential.
Taking the natural logarithm removes it:

```
ln S_i  =  ln S_0  −  b_i · ĝ_iᵀ D ĝ_i
```

The right-hand side is now **linear** in the seven unknowns. Writing
`y_i = ln S_i` and collecting the unknowns into a vector

```
β  =  [ ln S_0 , D_xx , D_yy , D_zz , D_xy , D_xz , D_yz ]ᵀ
```

with row *i* of a design matrix `X` given by

```
x_i  =  [ 1 , −b_i g_x² , −b_i g_y² , −b_i g_z² ,
              −2b_i g_x g_y , −2b_i g_x g_z , −2b_i g_y g_z ]
```

the whole acquisition becomes one linear system:

```
y  =  X β        (N equations, 7 unknowns, N ≫ 7)
```

> **★ Why this matters.** Log-linearisation is what makes tensor fitting fast
> enough to run on a whole brain in seconds, and it is why every toolkit offers
> it. It is also the source of the entire problem this paper is about. Read on.

### 1.4 From the tensor to FA and MD

Once `D` is estimated, diagonalise it to get eigenvalues `λ₁ ≥ λ₂ ≥ λ₃` —
the diffusivities along the ellipsoid's three axes. Then

```
MD  =  (λ₁ + λ₂ + λ₃) / 3                          mean diffusivity

              √(3/2) · √[ (λ₁−MD)² + (λ₂−MD)² + (λ₃−MD)² ]
FA  =  ────────────────────────────────────────────────────    fractional anisotropy
                      √( λ₁² + λ₂² + λ₃² )
```

MD is the average diffusivity. FA measures how unequal the eigenvalues are:
0 when all three are equal (a sphere), approaching 1 when one dominates (a
cigar). These two numbers are what dMRI studies report, and what a difference
in estimator ultimately moves.

Note one consequence that will return in Section 6: the linear fit is
**unconstrained**. Nothing in `y = Xβ` forces the eigenvalues to be positive.
A noisy voxel can produce a negative `λ₃`, which drives MD below zero and FA
above 1 — values that no tissue can have.

---

## 2. The estimators, derived

This is the technical core. Four estimators follow from each other, each fixing
the previous one's flaw and introducing its own.

### 2.1 Ordinary least squares (OLS)

The simplest criterion: choose the `β` that minimises the sum of squared
residuals, every measurement counting equally.

```
β̂_OLS  =  argmin  Σ ( y_i − x_iᵀ β )²   =   (XᵀX)⁻¹ Xᵀ y
```

This is FSL `dtifit`'s default. It is one matrix inversion, it is fast, and by
the Gauss–Markov theorem it is the **best linear unbiased estimator** —
*provided one condition holds*.

That condition is **homoscedasticity**: every `y_i` must have the same noise
variance.

### 2.2 Why that condition fails — the key derivation

Noise enters in the *signal*, not in the log-signal. Write the measurement as

```
S_i  =  s_i  +  ε_i ,        ε_i ~ N(0, σ²)
```

where `s_i` is the true signal. The noise variance `σ²` is set by the receiver
coil and is roughly the same for every volume — it does not know what b-value
was used.

Now take the log, and expand to first order around `s_i`:

```
y_i  =  ln( s_i + ε_i )  ≈  ln s_i  +  ε_i / s_i
```

Therefore

```
Var( y_i )  ≈  σ² / s_i²
```

**Read that carefully.** The noise in the *signal* is constant. The noise in
the *log-signal* is not — it is inversely proportional to the squared signal.

And the signal is not constant across measurements. Diffusion weighting
attenuates it: `s_i = S_0 exp(−b·D)`. At b = 2000 s/mm² in white matter the
signal can fall to a fifth of the b = 0 value, so the log-signal variance rises
by a factor of ~25.

> **★ The consequence.** After log-linearisation, the strongly diffusion-weighted
> measurements — precisely the ones carrying the diffusion information — are the
> noisiest, by a wide margin. OLS treats them as equally reliable as the b = 0
> volumes. Its central assumption is violated, so it is no longer the best
> estimator. It remains *unbiased* in the linear model, but it is *inefficient*:
> it throws away precision by trusting the noisiest points too much.

(A second, smaller issue: because `E[ln(s+ε)] ≈ ln s − σ²/2s²`, the log
transform itself introduces a small downward bias in `y`. Non-linear fitting —
Section 2.7 — avoids this. Linear fitting cannot.)

### 2.3 Weighted least squares (WLS), and where the weights come from

The standard fix for non-constant variance is to weight each residual by the
inverse of its variance, so unreliable measurements count less:

```
β̂_WLS  =  argmin  Σ w_i ( y_i − x_iᵀ β )²   =   (XᵀWX)⁻¹ XᵀW y
```

with `W = diag(w₁ … w_N)`. Generalised least squares theory gives the optimal
choice directly:

```
w_i  =  1 / Var(y_i)  =  s_i² / σ²
```

The `σ²` is the same for every measurement, and scaling all weights by a
constant does not change the minimiser. So it drops out, and the optimal
weights are simply

```
w_i  =  s_i²          — weight each measurement by its squared true signal
```

This is elegant: strongly attenuated measurements are automatically
down-weighted, by exactly the right amount. It is the estimator Basser's
original framework and Koay et al. (2006) set out, and it is what every toolkit
means by "weighted least squares".

### 2.4 The problem hiding in that formula

Look again at the optimal weight:

```
w_i  =  s_i²
```

`s_i` is the **true** signal. We do not have it. That is the entire reason we
are fitting in the first place.

So `s_i` must be replaced by something we do have. There are exactly two
candidates, and this is the fork the paper is about.

| Scheme | Weight used | Rationale |
|---|---|---|
| **Measured-signal weighting** | `w_i = S_i²` | Use the measurement. One pass, no extra cost. |
| **Predicted-signal weighting** | `w_i = Ŝ_i²` | Run a rough fit first, use its prediction `Ŝ_i`. Two passes. |

Both are called "WLS". Both appear in shipped toolkits. They are not the same
estimator, and they do not give the same answer.

### 2.5 Why measured-signal weighting is biased

WLS is unbiased **only if the weights are independent of the observations.**
That is the assumption behind `E[β̂] = β`:

```
E[ β̂ − β ]  =  (XᵀWX)⁻¹ Xᵀ E[ W e ]        where  e = y − Xβ
```

If `W` is fixed, `E[W e] = W E[e] = 0`, and the estimator is unbiased. But if
`w_i = S_i²`, then `w_i` and `e_i` are functions of the **same** noise draw
`ε_i`, and the expectation no longer vanishes.

The mechanism, stated plainly:

- A measurement that happens to come out **high** by noise has `e_i > 0`
  *and* gets a **large** weight `S_i²`.
- A measurement that happens to come out **low** by noise has `e_i < 0`
  *and* gets a **small** weight.

So the fit systematically listens more to the upward noise excursions than to
the downward ones. The weights, which exist to suppress noise, are themselves
made of noise — and they suppress it asymmetrically.

**The direction of the resulting bias is checkable.** Up-weighting the high
measurements means the fit is pulled towards *less* attenuation, which reads as
*lower* diffusivity. So MD should come out too low. Our phantom confirms it:
MD bias is **−0.0408 µm²/ms** at SNR 10, negative, as the mechanism predicts.
FA is also biased low (−0.0177), consistent with the most attenuated
direction — the one along the fibre, carrying the largest `λ₁` — being the one
whose weight is smallest and most noise-corrupted, so `λ₁` is pulled down and
the ellipsoid is compressed.

### 2.6 Why predicted-signal weighting is better, and by how much

Chung et al. (2006) proposed the two-pass fix, and it is what Veraart et al.
(2013) call **multi-step weighting**:

1. Fit once, cheaply — by OLS — to get a first estimate `β̂⁽⁰⁾`.
2. Compute the model prediction `Ŝ_i = exp( x_iᵀ β̂⁽⁰⁾ )`.
3. Refit with `w_i = Ŝ_i²`.

Why this helps: `Ŝ_i` is built from **all N measurements**, not from `S_i`
alone. The influence of any single noise draw `ε_i` on `Ŝ_i` is its leverage,
roughly `p/N` — with 7 parameters and 160 volumes, about **4%**. So the
correlation between weight and residual, which is the source of the bias, is
cut by roughly that factor.

The weights are no longer independent of the data — they cannot be, since they
come from the data — but they are *nearly* independent of the residual they
multiply. That is enough.

### 2.7 Why the bias depends on SNR — and a prediction we can test

This is the most useful part of the theory, because it tells us where to look.

Expand the measured weight around the true signal:

```
S_i²  =  s_i² (1 + ε_i/s_i)²  ≈  s_i² ( 1 + 2 ε_i / s_i )
```

and recall `e_i ≈ ε_i / s_i`. The covariance driving the bias is then

```
Cov( S_i² , e_i )  ≈  s_i² · 2 · Var( ε_i / s_i )  =  2 σ²
```

Expressed relative to the weight's own scale `s_i²`, that is

```
relative bias  ∝  2 σ² / s_i²  =  2 / SNR_i²
```

> **★ The prediction.** The bias from measured-signal weighting scales as
> **1 / SNR²**. Halving the SNR should roughly *quadruple* it. At high SNR it
> should be invisible.

This is testable against our own phantom, which was run at three noise levels.
Taking SNR 30 as the baseline:

| SNR | MD bias (measured) | Observed ratio to SNR 30 | Predicted by 1/SNR² |
|---|---|---|---|
| 30 | −0.0050 | 1.00 | 1.00 |
| 20 | −0.0110 | 2.20 | 2.25 |
| 10 | −0.0408 | 8.16 | 9.00 |

| SNR | FA bias (measured) | Observed ratio | Predicted |
|---|---|---|---|
| 30 | −0.0021 | 1.00 | 1.00 |
| 20 | −0.0048 | 2.29 | 2.25 |
| 10 | −0.0177 | 8.43 | 9.00 |

The agreement is close at SNR 20 and runs about 9% below prediction at SNR 10,
which is what one expects: the derivation is first-order in `ε/s`, and that
approximation degrades as the noise grows.

**Say this out loud when you present the work.** The scaling law was derived
from the mechanism, not fitted to the data, and the data follow it. That is
what turns "we observed a difference" into "we understand the difference."

### 2.8 Iteratively reweighted least squares (IWLS)

If one reweighting from a prediction helps, repeat it: refit, recompute the
prediction, reweight, again. Each pass uses a better `Ŝ_i` than the last.

MRtrix3 `dwi2tensor` does this **twice by default.** This is not an obscure
detail — it is why our first conclusion was wrong (Section 5.2).

### 2.9 Non-linear least squares (NLLS) and RESTORE

Both avoid the log transform altogether, fitting the exponential model
directly:

```
β̂_NLLS  =  argmin  Σ ( S_i − exp( x_iᵀ β ) )²
```

This sidesteps the heteroscedasticity *and* the log-transform bias, at the cost
of iterative optimisation and a dependence on the starting point. **RESTORE**
adds robust outlier rejection on top, down-weighting measurements that a
first fit cannot explain — designed for motion and cardiac-pulsation artefacts.

We include both as extra arms because a reviewer will ask whether the effect is
an artefact of linear fitting. It is not: Table 6 shows every estimator we
tested, linear and non-linear, sits apart from the measured-signal weighted fit,
and the spread among them is smaller than their common distance from it.

### 2.10 Summary of the chain

| Estimator | Fixes | Introduces |
|---|---|---|
| **OLS** | — | ignores that log-signal noise is not constant |
| **WLS, measured weights** | the unequal variance | weights correlated with residuals → bias ∝ 1/SNR² |
| **WLS, predicted weights** | that correlation, by ~p/N | needs a first pass |
| **IWLS** | residual weight error, iteratively | cost; convergence to check |
| **NLLS** | log transform entirely | iterative, start-dependent |
| **RESTORE** | outliers | more parameters to choose |

> **★ The one sentence to remember.** "Weighted least squares" names a family,
> not an algorithm. Its members differ in where the weights come from, and that
> difference is not cosmetic — it changes whether the estimator is biased.

---

## 3. What the literature had already settled

**Koay et al. (2006)** set out the unifying framework for least-squares
estimation in DTI — the derivations in Section 2 are that framework.

**Veraart et al. (2013)**, *NeuroImage* 81:335–346, is the paper ours starts
from. They compared exactly the two schemes of Section 2.4: weighting by the
squares of the **measured** signals against weighting by the squares of a
**predicted** signal from an earlier estimate. Their findings:

1. The negative effect of measured-signal weighting on accuracy was, in their
   words, surprisingly high.
2. Multi-step (predicted-signal) weighting performed better.
3. In some cases it even outperformed non-linear least squares.

**So the question of which to use is not open.** It was answered in 2013.

That is what makes this paper's framing possible, and it is the framing to
defend. We are not claiming a discovery. We are asking a different question:

> A decade after the estimation question was settled, do the three toolkits the
> field actually uses apply the answer? And if they do not, what does that cost
> at the SNR of a real acquisition?

---

## 4. What each toolkit actually does

Each of these facts is documented by the project that made it. None of them is
visible in the command a user types.

| Toolkit | Command | Default estimator | Weight source |
|---|---|---|---|
| **FSL** | `dtifit` | OLS | — |
| **FSL** | `dtifit --wls` | WLS, single pass | **measured** |
| **MRtrix3** | `dwi2tensor` | WLS + **2 IWLS iterations** | predicted |
| **MRtrix3** | `dwi2tensor -iter 0` | WLS, single pass | **measured** |
| **DIPY** | `TensorModel(fit_method="WLS")` | WLS, two-pass | predicted |

Three observations follow, and they are the paper's structure:

1. **FSL's `--wls` implements the scheme Veraart advises against.** A user who
   reads "weighted least squares" in the FSL help text and turns it on has
   selected the less accurate member of the family, with nothing to tell them so.

2. **MRtrix3's default is not plain WLS.** It is WLS plus two reweightings — a
   *different estimator* from FSL `--wls`, despite both being called WLS. This is
   the fact that made our first conclusion wrong.

3. **Nothing is exposed.** `dtifit --wls`, `dwi2tensor`, and
   `fit_method="WLS"` all read, in a methods section, as "we fitted tensors by
   weighted least squares". They are three different computations.

---

## 5. The path we took, in causal order

Each step below exists because the previous step's result made it necessary.
This section is the one to narrate in person.

### 5.1 Step 1 — Measure the disagreement, holding everything else fixed

**Why.** Published work reports pipeline-level variability, which mixes
masking, preprocessing, and fitting. To ask about fitting alone, everything
else must be identical.

**What we did.** One shared brain mask for all three fits. Identical volumes,
bvals, bvecs. No preprocessing — because any preprocessing step is itself a
toolkit-specific choice, and applying one tool's preprocessing to all three
would confound the comparison it is meant to enable. For the multi-shell
Sherbrooke data, one shell extracted **once** and handed to all three, since
DIPY selects a shell internally while FSL and MRtrix3 silently fit everything
they are given.

**What we found.** MRtrix3 and DIPY agreed closely (r = 0.9990, MAE 0.0029).
FSL sat apart from both (r ≈ 0.91). Bland–Altman showed a systematic offset in
every FSL pairing, not symmetric scatter.

**The obvious reading: FSL is the outlier.** That is what we wrote first.

### 5.2 Step 2 — The first correction: FSL was not the outlier

**Why we looked again.** Two things did not fit.

- The FA offset **reversed sign** between datasets: FSL lower on Stanford by
  0.018, higher on Sherbrooke by 0.014. A genuine implementation difference
  should not flip direction with the acquisition.
- The claim rested on all three running the same estimator. We had not verified
  that.

**What we did.** Read the documentation. MRtrix3 `dwi2tensor` performs WLS
followed by **two iterations of reweighting** by default. FSL `--wls` and DIPY
perform a single weighted fit. We had been comparing IWLS against WLS against
WLS and attributing the difference to the toolkit.

We reran with `dwi2tensor -iter 0`, which stops after the first weighted fit.

**What we found.** The grouping inverted completely:

```
FSL --wls  vs  MRtrix3 -iter 0      r = 1.0000,  MAE = 0.0000
```

Identical. Two independently written codebases, in different languages, by
different groups — to numerical precision the same tensor. And MRtrix3 now sat
*away* from DIPY, where before it had agreed with it.

**What this forced.** Implementation is not the variable. The finding was not
"FSL differs"; it was "the default estimator differs". The whole paper had to be
rebuilt around that.

> **★ Why this result is worth more than it looks.** r = 1.0000 sounds like a
> sanity check. It is the load-bearing result. The field's phrase
> "software-related variability" presumes that implementation is what varies.
> Showing it is *exactly zero* removes that explanation and forces the question
> onto the estimator, where it can actually be answered.

### 5.3 Step 3 — Isolate what separates DIPY

**Why.** With the estimator matched, FSL and MRtrix3 became identical but DIPY
still differed. Something else was going on.

**What we did.** Traced DIPY's implementation: it weights by a **predicted**
signal, citing Chung et al. (2006). FSL and MRtrix3 weight by the **measured**
signal. That is the fork of Section 2.4.

Correspondence is not proof, so we manipulated it directly. DIPY accepts
user-supplied weights, so **the same DIPY code was run twice on the same data**
— once with its default predicted-signal weights, once with measured-signal
weights — and each compared against FSL.

**What we found.**

| | FA MAE vs FSL | MD MAE vs FSL |
|---|---|---|
| DIPY default (predicted weights) | 0.0222 | 0.0320 |
| DIPY with measured weights | **0.0003** | **0.0001** |

The disagreement collapsed by 98–99%. On Sherbrooke: FA 0.0468 → 0.0035.

**Why this is the strongest design element in the paper.** It is not a
correlation between a documented difference and an observed one. One thing was
changed, inside one codebase, on one dataset, and the effect appeared and
disappeared with it. That is a controlled manipulation of the proposed cause.

### 5.4 Step 4 — Ask whether either scheme is actually wrong

**Why.** Everything so far compares toolkits to each other. With no truth to
compare against, none of it can say which is *closer to correct*.

**What we did.** Built a synthetic phantom whose generating eigenvalues are
known exactly:

```
isotropic region      0.9, 0.9, 0.9   ×10⁻³ mm²/s  →  FA 0.0000, MD 0.90
single-fibre region   1.4, 0.35, 0.35 ×10⁻³ mm²/s  →  FA 0.7071, MD 0.70
```

A crossing-fibre region exists in the phantom but is **excluded from scoring**:
no single tensor is correct there by construction, so scoring it would measure
the model's inadequacy rather than the estimator's. Voxels within two of a
region boundary are also excluded, as they mix tissue types.

**What we found at SNR 30.** Both schemes recover the truth to within 0.002 FA,
with identical RMSE of 0.021.

**What we concluded, and it was wrong.** We wrote: *neither weighting is wrong.*

### 5.5 Step 5 — The second correction: SNR 30 was the wrong place to look

**Why we looked again.** Because Veraart et al. (2013) had compared these exact
two schemes and found the measured-signal one clearly damaging. Our result
contradicted an established finding, and when that happens the burden is on the
new result.

**What we did.** Re-read the mechanism. The objection to measured-signal
weighting is that the weights are *correlated with the noise*. Section 2.7 shows
that correlation scales as 1/SNR². So the effect is **noise-dependent by
construction** — and SNR 30 is a favourable acquisition, the regime where it
should be smallest.

A single noise level cannot test a noise-dependent effect. We regenerated the
phantom at **SNR 20 and SNR 10**, spanning to what a high b-value shell
actually delivers.

**What we found.**

| SNR | Measured-signal FA bias | Predicted-signal FA bias | Measured MD bias | Predicted MD bias |
|---|---|---|---|---|
| 30 | −0.0021 | +0.0014 | −0.0050 | +0.0017 |
| 20 | −0.0048 | +0.0030 | −0.0110 | +0.0039 |
| 10 | **−0.0177** | +0.0111 | **−0.0408** | +0.0172 |

Veraart's result, reproduced cleanly. At SNR 10 the measured-signal scheme
carries **2.4× the MD bias**, and higher RMSE at every noise level tested. And
the bias grows at the 1/SNR² rate the derivation predicts (Section 2.7).

**What this forced.** The claim "neither is wrong" was deleted. The paper was
reframed: the literature settled which scheme is preferable, and the paper's
contribution is that the toolkits have not followed.

> **★ Both errors had the same cause.** Both times we assumed that two things
> called by the same name were the same thing — "WLS" in three manuals meant
> three different computations, and "the phantom test" at one SNR meant
> something different from the phantom test as a test of a noise-dependent
> effect. That is *the paper's own subject*, and we walked into it twice before
> noticing.
>
> This is the right thing to say out loud, not to hide. It is the strongest
> available evidence that the analysis was checked rather than assumed, and it
> makes the paper's point better than the paper does.

### 5.6 Step 6 — Put the effect on a scale that can be weighed

**Why.** "FA differs by 0.017" means nothing without a reference. Is that large?

**What we did.** Expressed each difference against the standard deviation of FA
across white matter voxels in the same data.

**What we found.** Differences run 0.12–0.26 SD. And the sharpest comparison is
**within one toolkit**: changing FSL from its default to `--wls` moves FA by
**0.12 SD on Stanford and 0.26 SD on Sherbrooke** — while replacing FSL with
MRtrix3 at a matched estimator moves it by **0.0000**.

> **★ The most quotable result in the paper.** One flag inside FSL changes FA
> more than replacing FSL with a different toolkit entirely. A quarter of a
> standard deviation is the same order as the group effects dMRI studies are
> powered to detect — produced by a command-line argument that appears in no
> methods section we have read.

### 5.7 Step 7 — Rule out the remaining alternative explanations

Each of these exists to close a specific reviewer objection.

| Check | Objection it closes | Result |
|---|---|---|
| **Second dataset** (Sherbrooke) | one-off artefact of one acquisition | replicates; noisier data shows a larger effect, as 1/SNR² predicts |
| **MP-PCA denoising**, applied once, given to all three | the effect is just noise | shrinks by 44–61%, does not close |
| **Five estimators** incl. NLLS, RESTORE | artefact of linear fitting | all sit apart from measured-signal WLS; spread among them smaller than their common distance from it |
| **Non-physical voxel counts** | a filtering artefact | DIPY produced none; FSL and MRtrix3 did, at SNR-dependent rates |
| **Physical plausibility filter** | failed fits driving the correlation | necessary: unfiltered, a few hundred bad voxels drop MD agreement from r = 0.997 to r = 0.118 |

The last row deserves emphasis, because it is a methodological trap worth
knowing about. Unconstrained linear fitting returns negative eigenvalues in
noisy voxels. Pearson correlation is dominated by extremes, so a few hundred
such voxels out of hundreds of thousands were enough to make a genuine
agreement of r = 0.997 look like r = 0.118 — while changing the mean absolute
error by under 2%. We restrict statistics to FA ∈ [0,1] and
0 < MD ≤ 3.0 × 10⁻³ mm²/s (the diffusivity of free water at body temperature),
and report the excluded counts as a result in their own right.

---

## 6. The numbers, and exactly what each one licenses

| Result | Value | What it licenses — and what it does not |
|---|---|---|
| FSL `--wls` vs MRtrix3 `-iter 0` | r = 1.0000, MAE 0.0000 | Implementation is not the variable. Says nothing about accuracy. |
| MRtrix3 default vs DIPY | r = 0.9990 | Both apply predicted-signal weighting. |
| FSL vs MRtrix3 at defaults | r = 0.9157 | Toolkits at defaults do differ — but the cause is the default, not the code. |
| DIPY with measured weights vs FSL | MAE 0.0222 → 0.0003 | The weighting scheme *is* the cause. Controlled manipulation, not correlation. |
| Phantom, SNR 30 | biases < 0.002 FA | At favourable SNR the choice barely matters. Not evidence that it never matters. |
| Phantom, SNR 10 | MD bias −0.0408 vs +0.0172 | Measured-signal weighting is less accurate, as Veraart reported. |
| Bias scaling across SNR | ratios 2.20, 8.16 vs predicted 2.25, 9.00 | The mechanism of Section 2.7 is the right one. |
| Effect on real data | 0.12–0.26 SD of WM FA | The effect is of a size that matters for study conclusions. |
| Within-FSL flag change | 0.12 / 0.26 SD | Estimator choice dominates toolkit choice. |
| After MP-PCA denoising | shrinks 44–61%, persists | Not a noise artefact; not fixable by denoising. |
| Brain mask Dice | > 0.90 all pairs, 21% volume spread | Masks agree by Dice yet differ substantially in volume; ordering flips between datasets. |

### What the paper does not claim

Be precise about this — over-claiming is the fastest route to rejection.

- **Not** that FSL is broken. OLS is a defensible estimator; `--wls` is a
  documented option. The point is that the choice is invisible.
- **Not** a new estimator, or a new recommendation. Veraart's stands.
- **Not** that toolkit choice never matters. It matters at defaults — because
  the defaults differ, not because the code does.
- **Not** a claim about how the effect varies with acquisition. One subject per
  dataset cannot support that, and we do not assert it.

---

## 7. Defending the work

### 7.1 The honest statement of the contribution

Say it in this order, and do not soften it:

1. **It is not a discovery.** Every component is documented by its own project.
   Veraart settled which scheme is more accurate in 2013.
2. **It is a translation gap, measured.** A decade on, the three most used
   toolkits still ship different answers as defaults, and users cannot see which
   they are getting.
3. **The magnitudes are new.** Nobody had reported what it costs, at which SNR,
   or that it exceeds the effect of changing toolkit.
4. **It is directly actionable.** Report the estimator, not just the toolkit.
5. **It is fully reproducible.** Open data, open code, one DOI, four commands,
   no credentials.

> *"We did not find a new estimator problem. We found that the field has one,
> already solved in the literature, still sitting in the defaults — and we
> measured what it costs."*

### 7.2 Questions you will be asked

**"Have you read Veraart 2013?"**
Yes — it is the paper's starting point, cited in abstract, introduction and
discussion. We reproduce its result for the specific configurations these
toolkits ship, add the SNR dependence the mechanism predicts, and show the
recommendation has not reached the defaults.

**"Your reference arm is the scheme the literature discourages. Deliberate?"**
Yes. It is the arm two toolkits reach when asked for "weighted least squares",
so it is the one users most often believe they are getting. The discussion
states plainly that it is the less accurate of the two.

**"r = 1.0000 is just a sanity check."**
It is, and that is the point. The field's framing assumes implementation is the
variable. Showing it is exactly zero removes that explanation and moves the
question to where it can be answered.

**"Your phantom uses Gaussian noise; dMRI noise is Rician."**
Correct, and stated as a limitation. The phantom tests accuracy against a known
truth, not noise modelling. It reproduces the expected ordering and the
predicted 1/SNR² scaling across three noise levels, which is what it was built
to test. Rician noise is the natural extension.

**"One subject per dataset."**
Stated in limitations. The central claim — that two implementations of one
estimator agree — needs no sample, because the answer is exact equality. The
accuracy claims rest on a phantom with known truth, not on the subjects. What
one subject cannot support is how the between-scheme difference varies with
acquisition, and we do not claim it.

**"Why no preprocessing? That's not a real pipeline."**
Deliberate, and the alternative is worse. Any preprocessing step is itself a
toolkit-specific choice. Note the asymmetry we cannot escape: FSL ships no
denoiser. Giving each toolkit "its own" preprocessing would leave FSL fitting
noisier data, and the difference would no longer be attributable to the fit. So
preprocessing is either absent (main analysis) or identical for all three
(sensitivity analysis, Table 8). Both are reported.

**"Could this be an artefact of linear fitting?"**
No. NLLS and RESTORE, which avoid the log transform entirely, both sit apart
from the measured-signal weighted fit, and the spread among all five estimators
is smaller than their common distance from it.

**"So which should I use?"**
Predicted-signal weighting — MRtrix3 and DIPY apply it by default. In FSL that
means knowing that `--wls` is not that scheme. More important than the choice
is recording it.

### 7.3 If asked what you would do next

- Rician noise in the phantom, and a wider SNR range.
- More subjects, to characterise how the effect varies with acquisition.
- Beyond the tensor: does the same defaults gap exist for CSD, NODDI, kurtosis?
- The obvious practical step: a flag, or a line in the output header, that
  records which estimator was applied.

---

## Rapid recall

| Cue | Say this |
|---|---|
| What is the paper? | Toolkit differences in tensor fitting are estimator differences, not implementation differences — and the estimator the literature recommends is not the default everywhere. |
| Why do weights exist at all? | Log-linearising makes the log-signal variance σ²/s², so the high-b measurements are the noisiest. OLS ignores that. |
| Where does w = S² come from? | Optimal WLS weight is 1/Var(y_i) = s_i²/σ²; the σ² cancels. |
| What is the fork? | s_i is unknown. Substitute the measured signal, or a predicted one. |
| Why is measured worse? | The weight and the residual share a noise draw, so upward excursions get more influence. Biased by construction. |
| How much worse? | Bias ∝ 1/SNR². Invisible at 30, clear at 10 — and our three SNR levels follow that law. |
| Strongest single result | FSL and MRtrix3 agree at r = 1.0000, MAE 0.0000, when the estimator is matched. |
| Strongest design element | DIPY run twice on the same data, weights swapped: disagreement drops 98%. |
| Most quotable result | One flag inside FSL changes FA more than replacing FSL with another toolkit. |
| Prior work | Veraart et al. (2013) settled which scheme is better. Koay et al. (2006) gave the framework. |
| Novelty, honestly | Not a discovery; a measured translation gap, with magnitudes nobody had reported. |
| Biggest limitation | One subject per dataset; Gaussian not Rician phantom noise; tensor model only. |
| If it all collapses to one line | "Weighted least squares" is a family, not an algorithm — and the family members are not equally good. |
