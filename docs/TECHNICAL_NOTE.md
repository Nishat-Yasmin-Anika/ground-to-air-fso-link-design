# Technical note — Uncertainty-aware receiver design for ground-to-air FSO links

**Status:** computational research portfolio and method demonstration; not peer-reviewed, not measured or calibrated.  
**Date:** 23 November 2026.  
**Motivated by:** E. Erdogan, M. Elamassie *et al.*, IEEE Vehicular Technology Magazine (2026), and M. Elamassie & M. Uysal, IEEE Transactions on Communications (2025). See [source mapping](SOURCE_MAP.md).

## Abstract

Aerial free-space optical (FSO) links face heterogeneous atmospheric extinction and stochastic misalignment. This note formulates the receiver-aperture design problem when the *distribution of atmospheric scenarios itself is uncertain*. We adapt the altitude-resolved atmospheric scenario coefficients of Erdogan *et al.* (2026) and combine them with an exact Gaussian-beam circular-aperture integral. Under a specified zero-mean Gaussian pointing model, conditional optical-power availability is available from an inverse aperture-overlap calculation and a Rayleigh radial cumulative distribution. We optimize receiver size for nominal and total-variation distributionally robust weather mixtures, with exact finite-state probabilities instead of high-variance simulation-only estimates. Independent Bessel numerical quadrature, linear programming, Monte Carlo samples and analytic special cases validate the implementation internally. For an illustrative 3 km vertical link, a 92% availability target and 15 µrad per-axis jitter, the computed required receiver diameter changes from approximately 22 cm (nominal weather probabilities) to 27 cm when allowing a 4% weather-probability shift. These conclusions are **conditional on hypothetical device/meteorological inputs and a source coefficient-unit ambiguity**; they are not calibrated field reliability or verified equipment requirements.

## 1. Motivation and specific contribution

The source paper [S1] characterizes atmospheric transmission of a vertical/slant beam through successive altitude bands. The professor's later/related work [S2] considers pointing and geometry in multi-hop airborne FSO systems. Our **intellectual extension** is to combine a physically interpretable exact aperture integral with the layered atmospheric categories and formulate a *chance-constrained design question under distributional uncertainty*:

> What is the smallest aperture diameter that maintains target *modeled optical-power availability* if a specified amount of probability may shift between five weather categories?

Neither the distributionally robust optimization method nor the aperture formula is claimed as newly invented. The independent contribution is the transparent integration, exact conditional probability reduction, numerical verification and uncertainty/feasibility analysis in a small reproducible study.

## 2. Definitions and 1550 nm propagation assumptions

FSO = free-space optical; UAV = unmanned aerial vehicle; HAPS = high-altitude platform station; NTN = non-terrestrial network; TV = total variation; CDF = cumulative distribution function; BER = bit error rate; MC = Monte Carlo; SD = standard deviation; LP = linear program; µrad = microradian; dB = decibel; dBm = decibels relative to one milliwatt; MODTRAN = MODerate resolution atmospheric TRANsmission software; SHA-256 = Secure Hash Algorithm 256-bit; ERA5 = fifth generation ECMWF atmospheric reanalysis.

We consider a **ground-to-air, single, straight optical path** of geometric length `L=H/cos(zeta)` for altitude `H` and zenith angle `zeta` from local vertical. Flat horizontal atmospheric slabs are adopted as an approximation. Let `d_j` be the beam distance in atmospheric slab j. At 1550 nm, the five *conditional* scenarios and the within-slab coefficients/weights come from [S1] Table II. We represent each slab's weather state by `C_j`, independently across slabs for numerical tractability; this is a **new assumption**, not a meteorological finding.

The source prints an effective transmittance `T_eff=exp(-sum_j d_j sum_k p_jk * coefficient_jk)`. Its coefficient tables are labeled dB/km, which instead implies `T_db=10^(-sum_j d_j coefficient_j/10)` if read literally. Both interpretations are retained for an audit; the headline study uses the **equation-as-printed** convention. Source equations and plotted curves are consistent in approximate scale under the direct exponential convention; neither version is calibrated here with external transmission data. Source [S1] contains the original comparison to MODTRAN, which we do not reproduce.

## 3. Optical beam and aperture physics

We use a normalized Gaussian intensity at the receiver plane with 1/e² intensity beam radius `w` and 2D displacement vector **r**:

`I(x,y|r) = [2/(pi w²)] * exp(-2*||(x,y)-r||²/w²).`

The receiver has a circular aperture radius `a`; its captured fraction is the integral of `I` over `x²+y² <= a²`. A 2D Gaussian integral gives an **exact** expression:

`G(a,r,w) = F_{chi'^2_2(lambda)}((2a/w)²), lambda=(2r/w)²`,

where `F` denotes the **noncentral chi-squared cumulative distribution function** (equivalently related to the Marcum Q-function). The implementation uses `scipy.stats.ncx2.cdf`. The independent radial Bessel quadrature check is described in Section 7.

We use `w=sqrt(w0²+(theta_div L)²)` as a *simplified receiver-plane beam-radius parametrization*. This is a convenient paraxial illustration, not rigorous Gaussian propagation through turbulence. A physically specified beam would require telescope and laser optics parameters or a Fresnel/Gaussian beam propagation model.

## 4. Optical-power availability with pointing jitter

Let `(X,Y)~N(0,sigma_r² I)` be independent, zero-mean transverse pointing displacements at the receiver; `sigma_r=L*sigma_theta`, where `sigma_theta` is per-axis angular SD (in radians). The radial displacement `R=sqrt(X²+Y²)` is **Rayleigh distributed**. We neglect boresight bias and correlation. For atmospheric transmittance `T`, instantaneous collected optical power is

`P_rx = P_tx * eta_opt * T * G(a,R,w)`.

Define modeled optical-power availability `A=P(P_rx >= P_min)`. For each state, required capture is `g_req=P_min/(P_tx eta_opt T)`. Since `G` decreases monotonically with `R`, find the unique threshold `r_star` such that `G(a,r_star,w)=g_req` when `0<g_req<G(a,0,w)`. Then

`P(success | T) = 1 - exp(-r_star²/(2 sigma_r²))`,

with the obvious zero/one edge cases. `r_star` is computed by **Brent's method** with bracket expansion. This is *not* a bit-error-rate or detector-noise analysis. Weather is a categorical state per scenario; exact within-scenario probability is `A_s=sum_k p_{k|s} P(success | T_{sk})`. For this study the number of states is small, so direct enumeration is preferable to MC for the central results.

## 5. Research question: distributionally robust aperture design

Let `s=1..5` index the five weather scenarios. Their across-scenario probabilities are **not available from [S1]**. We declare a *hypothetical nominal prior* `q=(.76,.10,.07,.04,.03)` in the order (clear, pollution, fog, rain, snow). Thus nominal availability is `A_nom(a)=sum_s q_s A_s(a)`.

If the true scenario mix `p` is not precisely known, take the TV ambiguity set

`U(q,rho)={p>=0, sum p=1, 0.5*sum_s |p_s-q_s| <= rho}`.

The modeled worst-case availability is `A_rob(a)=min_{p in U(q,rho)} sum_s p_s A_s(a)`. The inner optimization is **linear programming**; for five states it is solved exactly by transferring up to `rho` probability mass from high-success to low-success weather categories. An independent SciPy HiGHS LP confirms the mass-transfer computation.

The design seeks the smallest radius `a*` satisfying the **chance constraint** `A_rob(a*) >= target`. Since aperture collection and conditional availability do not decrease as `a` increases, **bisection/Brent root finding** is appropriate. For a fixed set of parameters, the ambiguity radius is not a statistical confidence interval and a feasible design does not guarantee actual availability without valid physical models and empirical weather probabilities.

## 6. Required whole-design coefficient sensitivity

The source's dB/km table and its `exp(-Q)` equations produce substantially different received-power factors. It is insufficient merely to compare the two transmittance conventions in a secondary plot. **We now solve the full aperture-design and atmospheric-ceiling problem under both interpretations** in Figure 10 and Table 08. At 15 microradians per-axis jitter and a 92% illustrative availability target, the equation-as-printed nominal/4% TV-robust diameters are 21.95/27.01 cm; the literal dB/km counterparts are about 9.47/11.82 cm. At 8% TV, the former is globally infeasible while the latter remains feasible (~13.62 cm). Thus, no convention-independent hardware sizing or global infeasibility claim can be made. A supervisor should not be presented with a universal 4.89% threshold; it is a conditional diagnostic result.

## 7. Case study, ablations and findings

Default link: height 3 km, zenith 0°, nominal wavelength 1550 nm, transmitted optical power 50 mW, transmission efficiency 0.7, threshold 2 mW, initial beam radius 0.025 m, divergence 55 µrad, pointing jitter 15 µrad per axis, target availability 92%. These are **illustrative parameters**; no hardware provider or field dataset is implied.

Results (model-computed; `results/tables/02_minimum_aperture_frontier.csv`):

- **Nominal** minimum aperture **diameter ~21.95 cm** at 15 µrad.
- At TV radius **rho=0.04**, minimum diameter **~27.01 cm**: an increase of **~23% diameter** or **~51% collecting area**.
- At rho=0.08, the 92% target is **infeasible within the declared 1 m maximum diameter**. In this example the ceiling is set by severe weather states whose atmospheric transmission alone cannot achieve the required received power.
- Sensitivity with alternative **hypothetical** weather priors is in `06_alternate_illustrative_weather_priors.csv`. For a more-rain mixture, the robust 92% target is infeasible in the tested aperture range.
- Ten generated plots cover circular-aperture validation, unit-convention sensitivity, nominal/robust aperture trade-offs, weather-shift sensitivity, feasible regions, ablations and MC verification.

Figure 10 is the **controlling interpretive check**; Figure 04 shows the conditional design frontier under the paper-exponential convention. Figure 05 illustrates that uncertainty in scenario frequencies may dominate the effect of additional aperture beyond the atmospheric feasibility limit. Figure 02 shows that resolving the coefficient unit convention is essential before interpreting a physical link budget. Figure 09 gives an exact **atmospheric feasibility certificate**: in the limit of infinite aperture, `G -> 1` and a weather state passes if and only if `P_tx eta_opt T >= P_min`. The conditional ceiling `B_s = sum_k p_{k|s} 1{P_tx eta_opt T_sk >= P_min}` can be robustly aggregated with the same TV minimization. Under the **equation-as-printed convention only**, the nominal maximum is 96.4%, the robust maximum is 92.8% at rho=0.04 and 89.2% at rho=0.08. The critical break-even rho for a 92% target is approximately **0.048889**. This is a global infeasibility certificate **within the assumptions**, not just failure of a finite search grid.

## 8. Verification, computation cost and limits

**Independent mathematical cross-checks:** (i) zero-offset Gaussian aperture capture equals `1-exp(-2a²/w²)`; (ii) general-offset noncentral chi-squared CDF agrees with **independent radial quadrature involving the modified Bessel function I0**; (iii) pointing-averaged captured power has a closed form by Gaussian convolution, `E[G]=1-exp[-a²/{2(sigma_r²+w²/4)}]`; (iv) TV greedy solution agrees with **HiGHS linear programming** on random synthetic probability vectors; (v) exact availability agrees within sampling error with **independent MC** drawing weather and Gaussian offsets.

The reproducibility tests are in `tests/test_link.py`. Figure 08 uses **Wilson score 95% intervals** on independently sampled Bernoulli successes. Sampling intervals are statistical and do not measure atmosphere/model correctness. All code uses fixed seeds, logs dependencies and regenerates machine-readable outputs; the notebook runs without GPU.

**Important limitations:** fixed categorical state laws (no time correlation, causal meteorology or field weather calibration); flat horizontal atmospheric slabs; independent per-layer states; simplified beam divergence; no turbulence scintillation, no boresight error, no thermal/shot noise or photon statistics, no BER, no mobility trajectory, no power-consumption model, no regulatory safety assessment; source attenuation-unit convention unresolved. The modeled availability is not an engineering service-level guarantee. This work is *not* a validation against MODTRAN, ERA5, real instruments or the professor's experiment.

## 9. Possible extensions

A scientifically meaningful next step is to replace the hypothetical weather-scenario prior by **empirically estimated region/season-specific frequencies** and to assess *correlated* conditions along the slant path. The uncertainty radius could be calibrated against an **out-of-sample holdout**, unlike the arbitrary rho used here. A second step would add pointing boresight and turbulence/scintillation before computing receiver-dependent BER. This could reveal whether nominal link designs that look similar in mean power diverge in lower-tail availability, but that conclusion must be tested rather than assumed.

## References

See [SOURCE_MAP.md](SOURCE_MAP.md) for full citations, official URLs and distinctions between source-derived methods and our added assumptions.
