# From the Diffusion Signal to the Paper's Claim

## A study guide

This guide builds the paper from the ground up. It starts with the signal a
scanner measures, derives why a tensor fit needs weights at all, shows where the
two weighting schemes come from and why one is worse, then follows the path the
analysis actually took — including the four places where a conclusion was wrong
and how each error was found.

Nothing is assumed except that you know what an MRI image is. Every number is
from the paper's own tables and output files.

**How to use it.** Sections 1–3 are the theory you need in order to say why the
question matters. Section 4 is what each toolkit does. Section 5 is the path, in
causal order. Section 6 is the numbers and what each one licenses. Section 7 is
how to defend the work.

---

## 1. What is measured, and why it becomes a regression problem

### 1.1 The signal

A diffusion-weighted scan applies a pair of gradient pulses along a direction
**g**, with a strength summarised by the *b*-value. Water moving along **g**
loses phase coherence, so the measured signal drops. The more freely water moves
along **g**, the more signal is lost.

For one direction, the Stejskal–Tanner relation gives

```
S_i  =  S_0 · exp( −b_i · ĝ_iᵀ D ĝ_i )
```

where `S_i` is the signal measured with gradient direction `ĝ_i` at b-value
`b_i`, `S_0` is the signal without diffusion weighting, and `D` is the
**diffusion tensor**: a 3×3 symmetric positive-definite matrix.

`D` is what we want. It has six independent entries, because it is symmetric.
With `S_0`, that is **seven unknowns**.

### 1.2 Why a fit is needed

One measurement gives one equation. Seven unknowns need at least seven
measurements: one *b = 0* and six non-collinear directions. In practice we
acquire far more — 160 volumes in the Stanford dataset, 193 in Sherbrooke —
because the measurements are noisy.

So the system is **overdetermined**: more equations than unknowns, no exact
solution, and we must choose the tensor that fits best by some criterion. That
criterion is the **estimator**. The whole paper is about that choice.

### 1.3 Making it linear

The relation is non-linear in `D`, which sits inside an exponential. Taking the
logarithm removes it:

```
ln S_i  =  ln S_0  −  b_i · ĝ_iᵀ D ĝ_i
```

The right-hand side is now **linear** in the seven unknowns. Writing
`y_i = ln S_i`, collecting the unknowns into

```
β  =  [ ln S_0 , D_xx , D_yy , D_zz , D_xy , D_xz , D_yz ]ᵀ
```

and each measurement into a row of a design matrix `X`, the acquisition becomes

```
y  =  X β        (N equations, 7 unknowns, N ≫ 7)
```

> **★ Why this matters.** Log-linearisation is what makes tensor fitting fast
> enough to run on a whole brain in seconds, and it is why every toolkit offers
> it. It is also the source of the entire problem this paper is about.

### 1.4 From the tensor to FA and MD

Diagonalise `D` to get eigenvalues `λ₁ ≥ λ₂ ≥ λ₃`, the diffusivities along the
ellipsoid's three axes. Then

```
MD  =  (λ₁ + λ₂ + λ₃) / 3                          mean diffusivity

              √(3/2) · √[ (λ₁−MD)² + (λ₂−MD)² + (λ₃−MD)² ]
FA  =  ────────────────────────────────────────────────────    fractional anisotropy
                      √( λ₁² + λ₂² + λ₃² )
```

MD is the average diffusivity. FA measures how unequal the eigenvalues are: 0
for a sphere, approaching 1 for a cigar.

One consequence returns in Section 5: the linear fit is **unconstrained**.
Nothing forces the eigenvalues to be positive. A noisy voxel can produce a
negative `λ₃`, which drives MD below zero and FA above 1 — values no tissue can
have. How those voxels are handled turns out to matter.

---

## 2. The estimators, derived

### 2.1 Ordinary least squares (OLS)

Choose the `β` that minimises the sum of squared residuals, every measurement
counting equally:

```
β̂_OLS  =  argmin  Σ ( y_i − x_iᵀ β )²   =   (XᵀX)⁻¹ Xᵀ y
```

This is FSL `dtifit`'s default. By the Gauss–Markov theorem it is the **best
linear unbiased estimator** — provided every `y_i` has the same noise variance.

### 2.2 Why that condition fails — the key derivation

Noise enters the *signal*, not the log-signal. Write `S_i = s_i + ε_i` with
`ε_i ~ N(0, σ²)`, where `σ²` is set by the receiver coil and is about the same
for every volume. Expanding the logarithm to first order,

```
y_i  =  ln( s_i + ε_i )  ≈  ln s_i  +  ε_i / s_i        so    Var( y_i )  ≈  σ² / s_i²
```

The noise in the *signal* is constant. The noise in the *log-signal* is not: it
is inversely proportional to the squared signal. And the signal is not constant
across measurements, because diffusion weighting attenuates it. At b = 2000
s/mm² in white matter the signal can fall to a fifth of the b = 0 value, so the
log-signal variance rises about 25-fold.

> **★ The consequence.** After log-linearisation, the strongly weighted
> measurements — the ones carrying the diffusion information — are the noisiest.
> OLS treats them as equally reliable as the b = 0 volumes. It stays unbiased in
> the linear model, but it is inefficient.

### 2.3 Weighted least squares (WLS), and where the weights come from

Weight each residual by the inverse of its variance:

```
β̂_WLS  =  argmin  Σ w_i ( y_i − x_iᵀ β )²,     w_i  =  1 / Var(y_i)  =  s_i² / σ²
```

`σ²` is common to all measurements and scaling the weights changes nothing, so
the optimal weights are simply

```
w_i  =  s_i²          — weight each measurement by its squared true signal
```

### 2.4 The problem hiding in that formula

`s_i` is the **true** signal. We do not have it; that is why we are fitting. So
it must be replaced, and there are exactly two candidates. This is the fork.

| Scheme | Weight used | Rationale |
|---|---|---|
| **Measured-signal weighting** | `w_i = S_i²` | Use the measurement. One pass. |
| **Predicted-signal weighting** | `w_i = Ŝ_i²` | Fit roughly first, use its prediction. Two passes. |

Both are called "WLS". Both are shipped in real toolkits. They are not the same
estimator.

### 2.5 Why measured-signal weighting is biased

WLS is unbiased **only if the weights are independent of the observations**:

```
E[ β̂ − β ]  =  (XᵀWX)⁻¹ Xᵀ E[ W e ]        where  e = y − Xβ
```

If `W` is fixed, `E[W e] = 0`. But with `w_i = S_i²`, the weight and the
residual are functions of the **same** noise draw:

- a measurement that comes out **high** by noise has `e_i > 0` *and* a **large** weight;
- a measurement that comes out **low** has `e_i < 0` *and* a **small** weight.

The fit listens more to the upward excursions than to the downward ones. The
weights, which exist to suppress noise, are themselves made of noise.

**The direction is checkable.** Up-weighting the high measurements pulls the fit
towards less attenuation, which reads as lower diffusivity. In the phantom, MD
comes out low: −0.0065 µm²/ms at SNR 30 and −0.0542 at SNR 10.

### 2.6 Why predicted-signal weighting is better

Chung et al. (2006) proposed the two-pass fix, which Veraart et al. (2013) call
**multi-step weighting**:

1. Fit once by OLS to get `β̂⁽⁰⁾`.
2. Compute `Ŝ_i = exp( x_iᵀ β̂⁽⁰⁾ )`.
3. Refit with `w_i = Ŝ_i²`.

`Ŝ_i` is built from **all N measurements**, so the influence of any single noise
draw on it is its leverage, roughly `p/N` — about 4% with 7 parameters and 160
volumes. The correlation that caused the bias is cut by about that factor.

### 2.7 Why the bias depends on SNR — and a prediction we can test

Expanding the measured weight around the true signal,

```
S_i²  =  s_i² (1 + ε_i/s_i)²  ≈  s_i² ( 1 + 2 ε_i / s_i ),      e_i ≈ ε_i / s_i
Cov( S_i² , e_i )  ≈  2 σ²,      and relative to s_i²:   2 / SNR_i²
```

> **★ The prediction.** The bias scales as **1 / SNR²**. Halving the SNR should
> roughly quadruple it, and at high SNR it should be invisible.

The phantom was run at three noise levels, so this is testable. Taking SNR 30 as
the baseline, the theory predicts factors of 2.25 and 9.00:

| Quantity | SNR 20 / 30 | SNR 10 / 30 |
|---|---|---|
| Predicted by 1/SNR² | 2.25 | 9.00 |
| MD bias, observed | 2.3 | 8.3 |
| FA bias, observed | 2.1 | 6.6 |

MD follows the law closely. FA grows more slowly, which is expected: FA is a
ratio of eigenvalues and noise inflates it upward at the same time, so the two
effects partly cancel.

**Say this out loud when you present the work.** The scaling law was derived
from the mechanism, not fitted to the data, and the MD bias follows it.

### 2.8 IWLS, NLLS and RESTORE

If one reweighting from a prediction helps, repeat it. **MRtrix3 `dwi2tensor`
does this twice by default.** That is why our first conclusion was wrong
(Section 5.2).

**NLLS** avoids the log transform altogether, fitting the exponential model
directly; **RESTORE** adds robust outlier rejection. Both are included as extra
arms, because a reviewer will ask whether the effect is an artefact of linear
fitting. It is not: in MD every estimator we tested, linear and non-linear, sits
apart from the measured-signal fit.

### 2.9 Summary of the chain

| Estimator | Fixes | Introduces |
|---|---|---|
| **OLS** | — | ignores that log-signal noise is not constant |
| **WLS, measured weights** | the unequal variance | weights correlated with residuals → bias ∝ 1/SNR² |
| **WLS, predicted weights** | that correlation, by about p/N | needs a first pass |
| **IWLS** | residual weight error, iteratively | cost; convergence to check |
| **NLLS** | the log transform entirely | iterative, start-dependent |
| **RESTORE** | outliers | more parameters to choose |

> **★ The one sentence to remember.** "Weighted least squares" names a family,
> not an algorithm, and its members are not equally good.

---

## 3. What the literature had already settled

**Koay et al. (2006)** set out the unifying framework for least-squares
estimation in DTI; the derivations in Section 2 are that framework.

**Veraart et al. (2013)**, *NeuroImage* 81:335–346, compared exactly the two
schemes of Section 2.4: weighting by the squares of the **measured** signals
against weighting by the squares of a **predicted** signal. They found

1. measured-signal weighting damages accuracy — a loss they described as
   surprisingly high;
2. multi-step (predicted-signal) weighting performs better;
3. in some cases it even outperforms non-linear least squares.

**So which to use is not an open question in MD.** It was answered in 2013. That
is what makes this paper's framing possible:

> A decade after the estimation question was settled, do the three toolkits the
> field actually uses apply the answer? And if not, what does that cost at the
> SNR of a real acquisition?

---

## 4. What each toolkit actually does

Each fact below is documented by the project that made it. None of them is
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
   reads "weighted least squares" in the help text and turns it on has selected
   the less accurate member of the family, with nothing to say so.
2. **MRtrix3's default is not plain WLS.** It is WLS plus two reweightings — a
   different estimator from FSL `--wls`, despite both being called WLS.
3. **Nothing is exposed.** All three commands read, in a methods section, as "we
   fitted tensors by weighted least squares".

There are also two smaller implementation differences, which matter only when
you try to reproduce a toolkit exactly: DIPY floors the signal at 1e-4 and clips
negative eigenvalues; MRtrix3 floors at 1e-6 of each voxel's maximum.

---

## 5. The path the analysis took, in causal order

Each step exists because the previous step's result made it necessary. This is
the section to narrate in person.

### 5.1 Step 1 — Measure the disagreement, holding everything else fixed

**Why.** Published work reports pipeline-level variability, which mixes masking,
preprocessing and fitting. To ask about fitting alone, everything else must be
identical.

**What we did.** One shared brain mask for all three fits. Identical volumes,
bvals and bvecs. No preprocessing, because any preprocessing step is itself a
toolkit-specific choice. For multi-shell Sherbrooke, one shell extracted
**once** and handed to all three, since DIPY selects a shell internally while
FSL and MRtrix3 silently fit everything they are given.

**What we found.** MRtrix3 and DIPY agreed closely (FA r = 0.9990); FSL sat at
r ≈ 0.96. The obvious reading: FSL is the outlier. **That is what we wrote
first.**

### 5.2 Step 2 — The first correction: FSL was not the outlier

**Why we looked again.** The FA difference **reversed sign** between the two
datasets. A genuine implementation difference should not flip direction with the
acquisition.

**What we did.** Read the documentation. MRtrix3 `dwi2tensor` performs WLS
followed by **two reweighting iterations** by default. We had been comparing
IWLS against WLS against WLS and calling the difference a toolkit effect. We
reran with `-iter 0`.

**What we found.** The grouping inverted:

```
FSL --wls  vs  MRtrix3 -iter 0      r = 1.0000,  MAE < 0.0001
```

Two independently written codebases, same tensor. MRtrix3 then sat away from
DIPY, where before it had agreed with it.

> **★ Why r = 1.0000 is the load-bearing result.** The field's phrase
> "software-related variability" presumes that implementation is what varies.
> Showing it is *exactly zero* removes that explanation and forces the question
> onto the estimator, where it can be answered.

### 5.3 Step 3 — Isolate what separates DIPY

DIPY weights by a **predicted** signal, citing Chung et al. (2006); FSL and
MRtrix3 weight by the **measured** signal. Correspondence is not proof, so we
manipulated it: **the same DIPY code was run twice on the same data**, once with
its default weights and once with measured-signal weights.

| | FA MAE vs FSL | MD MAE vs FSL |
|---|---|---|
| DIPY default (predicted weights) | 0.0222 | 0.0320 |
| DIPY with measured weights | **0.0003** | **0.0001** |

The disagreement collapsed by 98–99%. One argument changed, inside one codebase,
on one dataset: a controlled manipulation of the proposed cause.

### 5.4 Step 4 — Ask whether either scheme is actually wrong

Comparing toolkits to each other cannot say which is closer to correct, so we
built phantoms with known eigenvalues. **At SNR 30 both schemes recovered the
truth to within 0.002 FA.** We wrote: *neither weighting is wrong.*

### 5.5 Step 5 — The second correction: SNR 30 was the wrong place to look

Veraart et al. had compared these two schemes and found the measured-signal one
clearly damaging. When a new result contradicts an established one, the burden is
on the new result — so we re-read the mechanism. The bias scales as 1/SNR²
(Section 2.7), so SNR 30 is precisely where it should be smallest.

At SNR 20 and 10 the effect appeared, and the MD bias grew at the predicted
rate. Veraart's result, reproduced for the configurations the toolkits
distribute. The claim "neither is wrong" was deleted.

### 5.6 Step 6 — The third correction: the simplified simulation was too idealised

To ask what noise alone predicts on each real protocol, we simulated the real
gradient tables. On Stanford it roughly matched the data. On Sherbrooke it
predicted the **opposite sign** for FA. We reported that as unexplained.

It was not a mystery in the data; it was the simulation. Its tensors had a fixed
MD of 0.70 µm²/ms (the real white matter median is 0.594), one axially symmetric
shape, random orientation, and the same S₀ and σ in every voxel. Imposed one at a
time on the real tensors, **no single idealisation reverses the sign under every
rule; all four together do.** With each voxel's own tensor, S₀ and noise level,
noise reproduces the observed sign.

### 5.7 Step 7 — The fourth correction: we had been selecting on the outcome

The first version of that analysis dropped a simulated voxel when the
measured-signal fit came out non-physical — which is exactly where the offset is
largest. The voxel set had already been chosen the same way, so the selection
applied twice. It made noise look as though it explained only 60% of the
Sherbrooke FA offset.

**The fix.** Voxels and FA bins now come from the DIPY fit alone, which never
returns a non-physical value. Non-physical measured-signal fits are handled by
one of three rules — exclude, clip, or keep — applied identically to observed
and simulated data, and all three are reported.

**What changed.** At the measured noise level, noise reproduces 101% of the
Stanford FA offset and 89–106% of the Sherbrooke FA offset, depending on the
rule. The "unexplained Sherbrooke FA offset" was mostly our own selection.

Two code errors were found in the same review and fixed: the reimplementation of
DIPY did not clip eigenvalues as DIPY does, and MRtrix3's signal floor is 1e-6 of
the voxel maximum, not 1. The noise ratio measured from the ten b = 0 volumes
also needed a small-sample correction, from 1.23 to 1.28.

> **★ What the four corrections have in common.** Every one came from assuming
> that two things with the same name, or the same-looking voxel set, were the
> same thing. "WLS" in three manuals meant three computations; "the phantom
> test" at one SNR meant something different from a test of a noise-dependent
> effect; "the simulation" meant an idealisation; "the voxels" meant a set
> already filtered by the arm under test.
>
> This is the paper's own subject, and we walked into it four times. Say so: it
> is the strongest available evidence that the analysis was checked rather than
> assumed.

### 5.8 Step 8 — Put the effect on a scale, and rule out the rest

- **A scale.** Differences run 0.09–0.25 SD of white matter FA. Within FSL,
  changing one flag moves FA by 0.0171 (Stanford) and 0.0489 (Sherbrooke), while
  replacing FSL with MRtrix3 at a matched estimator moves it by 0.0000.
- **A second dataset.** Sherbrooke replicates and, being noisier, shows a larger
  MD offset — as 1/SNR² predicts.
- **Denoising.** MP-PCA, applied once and given to all three, shrinks the MD
  offset by 44–61% but does not remove it.
- **Artefacts.** All 65 Sherbrooke volumes match their source volumes and
  gradient entries; no volume is an outlier. Real residuals do carry 1.7–2.4
  times as many outliers as noise-only data, and removing them changes the
  offsets more than in the control.
- **Non-physical fits.** DIPY returns none because it clips; FSL and MRtrix3
  return them in 0.14–3.97% of white matter voxels. Left in the statistics,
  0.19% of voxels drop an MD correlation from r = 0.9965 to r = 0.110.

---

## 6. The numbers, and exactly what each one licenses

| Result | Value | What it licenses — and what it does not |
|---|---|---|
| FSL `--wls` vs MRtrix3 `-iter 0` | r = 1.0000, MAE < 0.0001 | Implementation is not the variable. Says nothing about accuracy. |
| MRtrix3 default vs DIPY | r = 0.9990 | Both apply predicted-signal weighting. |
| FSL vs MRtrix3 at defaults | r = 0.9157 | Toolkits at defaults do differ — but the cause is the default, not the code. |
| DIPY with measured weights vs FSL | MAE 0.0222 → 0.0003 | The weighting scheme *is* the cause. A manipulation, not a correlation. |
| Phantom, SNR 30 | MD bias −0.0065 µm²/ms | At favourable SNR the cost is small. Not evidence that it never matters. |
| Phantom, SNR 10 | MD bias −0.0542, FA −0.0257 | Measured-signal weighting is the least accurate scheme there. |
| Bias growth across SNR | 2.3× and 8.3× in MD (predicted 2.25, 9.00) | The mechanism of Section 2.7 is the right one. |
| Protocol simulations | largest MD bias and RMSE in **every** condition | The MD result holds on both real protocols. |
| Protocol simulations, FA | largest on Stanford; on Sherbrooke largest in only 8 of 30 | The FA ranking is protocol-dependent. Do not overstate it. |
| Two groups at SNR 20 and 30 | MD differs by 0.021 (Stanford) and 0.011 (Sherbrooke) µm²/ms | An SNR difference can masquerade as a group difference in MD. |
| The same, in FA | 0.020 on Stanford; 0.0003 on Sherbrooke | In FA this depends on the protocol. |
| Noise on the real tensors, 1.28σ | 101% / 83% (Stanford), 89–106% / 86–91% (Sherbrooke) | Most of the real-data offsets are noise acting through the estimator. |
| What remains | 13–17% of the MD offsets, and Stanford's most anisotropic bin | Honestly unexplained; angular misfit is the plausible candidate, untested. |

### What the paper does not claim

- **Not** that FSL is broken. OLS is defensible; `--wls` is documented. The point
  is that the choice is invisible.
- **Not** a new estimator or a new recommendation. Veraart's stands.
- **Not** that measured-signal weighting is worst in FA everywhere. In MD, yes,
  in every condition tested; in FA, on the phantom and the Stanford protocol.
- **Not** a claim about how the effect varies with acquisition. Two subjects
  cannot support that.

---

## 7. Defending the work

### 7.1 The honest statement of the contribution

1. **It is not a discovery.** Every component is documented by its own project,
   and Veraart settled the accuracy question in 2013.
2. **It is a translation gap, measured.** A decade on, the three most used
   toolkits still ship different answers as defaults, and users cannot see which
   they are getting.
3. **The magnitudes are new.** Nobody had reported what it costs, at which SNR,
   or that it exceeds the effect of changing toolkit.
4. **It is directly actionable.** Report the estimator, not just the toolkit.
5. **It is fully reproducible.** Open data, open code, one DOI, no credentials.

> *"We did not find a new estimator problem. We found that the field has one,
> already solved in the literature, still sitting in the defaults — and we
> measured what it costs."*

### 7.2 Questions you will be asked

**"Have you read Veraart 2013?"** Yes — it is the starting point, cited in the
abstract, introduction and discussion. We reproduce its result for the shipped
configurations, add the SNR dependence the mechanism predicts, and show the
recommendation has not reached the defaults.

**"Your reference arm is the scheme the literature discourages. Deliberate?"**
Yes. It is the arm two toolkits reach when asked for "weighted least squares", so
it is the one users most often believe they are getting.

**"r = 1.0000 is just a sanity check."** It is, and that is the point. It removes
implementation as an explanation and moves the question to where it can be
answered.

**"Is measured-signal weighting always the worst?"** In MD, in every condition we
simulated, yes. In FA it depends on the protocol: on a single-b = 0, b = 1000
acquisition its negative FA bias partly cancels the upward bias that noise causes
in every estimator, so its absolute FA bias can be smaller. We say so explicitly.

**"How do you know the real-data differences are noise and not artefacts?"** We
simulated noise on each voxel's own fitted tensor, at a noise level measured from
the ten b = 0 volumes, and compared like with like. We also ran the outlier
exclusions and the residual shuffle on noise-only data as controls. What noise
does not reproduce is 13–17% of the MD offsets and Stanford's most anisotropic
bin.

**"Why three rules for non-physical fits?"** Because the measured-signal fit
returns FA above 1 in 5.3% of Sherbrooke voxels, and any rule that drops them
selects on the quantity being measured. Reporting all three rules shows how much
the answer depends on that choice: for the Sherbrooke FA offset, 89% to 106%.

**"Your phantom uses Gaussian noise."** No — Rician, as in magnitude images. It
does omit motion, eddy currents and partial volume, which is stated as a
limitation.

**"One subject per dataset."** Stated in limitations. The central claim needs no
sample, because the answer is exact equality. What two subjects cannot support is
how the between-scheme difference varies with acquisition, and we do not claim it.

**"So which should I use?"** Predicted-signal weighting, which MRtrix3 and DIPY
apply by default. In FSL that means knowing that `--wls` is not that scheme. More
important than the choice is recording it.

### 7.3 If asked what you would do next

- Rician noise with a spatially varying floor, and a wider SNR range.
- More subjects, to characterise how the effect varies with acquisition.
- Beyond the tensor: does the same defaults gap exist for CSD, NODDI, kurtosis?
- The practical step: a flag, or a line in the output header, recording which
  estimator was applied.

---

## Rapid recall

| Cue | Say this |
|---|---|
| What is the paper? | Toolkit differences in tensor fitting are estimator differences, not implementation differences — and the estimator the literature recommends is not the default everywhere. |
| Why do weights exist at all? | Log-linearising makes the log-signal variance σ²/s², so the high-b measurements are the noisiest. OLS ignores that. |
| Where does w = S² come from? | The optimal WLS weight is 1/Var(y_i) = s_i²/σ²; the σ² cancels. |
| What is the fork? | s_i is unknown. Substitute the measured signal, or a predicted one. |
| Why is measured worse? | The weight and the residual share a noise draw, so upward excursions get more influence. Biased by construction. |
| How much worse? | Bias ∝ 1/SNR². In the phantom the MD bias grew 2.3× and 8.3×, against 2.25 and 9.00 predicted. |
| Strongest single result | FSL and MRtrix3 agree at r = 1.0000 when the estimator is matched. |
| Strongest design element | DIPY run twice on the same data, weights swapped: the difference drops 98%. |
| Most useful for a reader | One flag inside FSL changes FA more than replacing FSL with another toolkit. |
| What did the real data need? | Noise on each voxel's own tensor at the measured noise level: it reproduces most of the offsets. |
| Prior work | Veraart et al. (2013) settled which scheme is better; Koay et al. (2006) gave the framework. |
| Novelty, honestly | Not a discovery; a measured translation gap, with magnitudes nobody had reported. |
| Biggest limitation | One subject per dataset; the unexplained Stanford high-FA bin; tensor model only. |
| If it all collapses to one line | "Weighted least squares" is a family, not an algorithm — and the members are not equally good. |
