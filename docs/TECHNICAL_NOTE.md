# Technical note — Uncertainty-aware receiver design for ground-to-air FSO links

**Status:** computational research portfolio and method demonstration; not peer-reviewed, not measured or calibrated.  
**Date:** 23 November 2026.  
**Motivated by:** E. Erdogan, M. Elamassie *et al.*, IEEE Vehicular Technology Magazine (2026), and M. Elamassie & M. Uysal, IEEE Transactions on Communications (2025). See [source mapping](SOURCE_MAP.md).

## Abstract

Aerial free-space optical (FSO) links face heterogeneous atmospheric extinction and stochastic misalignment. This note formulates the receiver-aperture design problem when the *distribution of atmospheric scenarios itself is uncertain*. We adapt the altitude-resolved atmospheric scenario coefficients of Erdogan *et al.* (2026) and combine them with an exact Gaussian-beam circular-aperture integral. Under a specified zero-mean Gaussian pointing model, conditional optical-power availability is available from an inverse aperture-overlap calculation and a Rayleigh radial cumulative distribution. We optimize receiver size for nominal and total-variation distributionally robust weather mixtures, with exact finite-state probabilities instead of high-variance simulation-only estimates. Independent Bessel numerical quadrature, linear programming, Monte Carlo samples and analytic special cases validate the implementation internally. For an illustrative 3 km vertical link, a 92% availability target and 15 µrad per-axis jitter, the computed required receiver diameter changes from approximately 22 cm (nominal weather probabilities) to 27 cm when allowing a 4% weather-probability shift. These conclusions are **conditional on hypothetical device/meteorological inputs and a source coefficient-unit ambiguity**; they are not calibrated field reliability or verified equipment requirements.

## 1. Motivation and study design

The source paper [S1] characterizes atmospheric transmission of a vertical/slant beam through successive altitude bands. Elamassie and Uysal [S2] examine geometry and pointing effects in multi-layer airborne FSO systems. This study combines a physically interpretable exact aperture integral with the layered atmospheric categories and formulate a *chance-constrained design question under distributional uncertainty*:

> What is the smallest aperture diameter that maintains target *modeled optical-power availability* if a specified amount of probability may shift between five weather categories?

Neither the distributionally robust optimization method nor the aperture formula is claimed as newly invented. The focus is on transparent model integration, conditional probability reduction, numerical verification and sensitivity analysis within a reproducible case study.

## 2. Definitions and 1550 nm propagation assumptions

**Abbreviations.** FSO: free-space optical; UAV: unmanned aerial vehicle; HAPS: high-altitude platform station; NTN: non-terrestrial network; TV: total variation; CDF: cumulative distribution function; BER: bit error rate; MC: Monte Carlo; SD: standard deviation; LP: linear program; dB: decibel; dBm: decibels relative to one milliwatt; MODTRAN: MODerate resolution atmospheric TRANsmission software; SHA-256: Secure Hash Algorithm 256-bit; ERA5: fifth-generation ECMWF atmospheric reanalysis.

The platform altitude is $H$, the zenith angle from local vertical is $\zeta$, and the slant path is

$$
L = \frac{H}{\cos\zeta}.
$$

We use flat atmospheric slabs as an approximation. Let $d_j$ denote the optical path length inside atmospheric layer $j$, and let $C_j$ denote its weather state. The within-layer coefficients and occurrence weights are taken from [S1], Tables I–II, for a 1550 nm wavelength. Independently drawing layer states is an **additional modeling assumption**; it is not an observed joint weather distribution.

For a state-specific attenuation sum $Q=\sum_j d_j c_{j,C_j}$, the source's equation-as-printed convention is

$$
T_{\mathrm{paper}}=\exp(-Q).
$$

Because its coefficient table is labeled dB/km, we also calculate the literal-decibel alternative

$$
T_{\mathrm{dB}}=10^{-Q/10}.
$$

The resulting design conclusions differ materially. Neither interpretation is independently calibrated in this project. The source paper's MODTRAN comparison is not reproduced.

## 3. Optical beam and circular-aperture collection

For a receiver-plane, normalized two-dimensional Gaussian irradiance with $1/e^2$ intensity radius $w$ and displacement vector $\mathbf r$, the irradiance is

$$
I(x,y\mid\mathbf r)=\frac{2}{\pi w^2}
\exp\!\left(-\frac{2\left\|[x,y]^\top-\mathbf r\right\|_2^2}{w^2}\right).
$$

Let $a$ be the radius of a circular receiver aperture and $r=\|\mathbf r\|_2$. Integration over the aperture gives the exact collected-power fraction

$$
G(a,r,w)=F_{\chi^{\prime 2}_{2}(\lambda)}\!\left(\frac{4a^2}{w^2}\right),
\qquad\lambda=\frac{4r^2}{w^2},
$$

where $F_{\chi^{\prime 2}_{2}(\lambda)}$ is the CDF of the **noncentral chi-squared distribution** with two degrees of freedom and noncentrality parameter $\lambda$. This form is implemented with `scipy.stats.ncx2.cdf`, then checked against an independent Bessel-function quadrature.

We use the illustrative receiver-plane beam radius

$$
w=\sqrt{w_0^2+(\theta_{\mathrm{div}}L)^2}.
$$

This convenient paraxial radius parametrization does not model optical turbulence or a fully specified laser/telescope transmitter.

## 4. Pointing error and received-power availability

Let independent, zero-mean transverse pointing errors $X$ and $Y$ have common SD $\sigma_r=L\sigma_\theta$, where $\sigma_\theta$ is the angular SD per axis. Their radial magnitude has a Rayleigh distribution:

$$
X,Y\sim\mathcal N(0,\sigma_r^2),\qquad
R=\sqrt{X^2+Y^2}\sim\operatorname{Rayleigh}(\sigma_r).
$$

With atmospheric transmittance $T$, optical efficiency $\eta_{\mathrm{opt}}$ and transmitted power $P_{\mathrm{tx}}$, the collected optical power is

$$
P_{\mathrm{rx}}=P_{\mathrm{tx}}\,\eta_{\mathrm{opt}}\,T\,G(a,R,w).
$$

Define **received-power availability**, not BER or end-to-end network uptime, by

$$
A=\Pr(P_{\mathrm{rx}}\ge P_{\min}).
$$

For fixed $T$, the minimum required capture fraction is $g_{\mathrm{req}}=P_{\min}/(P_{\mathrm{tx}}\eta_{\mathrm{opt}}T)$. When it lies strictly between zero and the aligned capture $G(a,0,w)$, solve $G(a,r_\star,w)=g_{\mathrm{req}}$ for the critical radial pointing offset $r_\star$. Then

$$
\Pr(\mathrm{success}\mid T)=
1-\exp\!\left(-\frac{r_\star^2}{2(L\sigma_\theta)^2}\right).
$$

Zero/one edge cases are handled explicitly in the code. The threshold inversion uses bracket expansion with Brent's method. The exact within-scenario availability $A_s$ sums this conditional probability over the finite weather states in scenario $s$; Monte Carlo is reserved for an independent stochastic check.

## 5. Distributionally robust receiver-aperture design

The five weather scenarios are indexed by $s=1,\ldots,5$. Since [S1] does not provide probabilities **across** those scenarios, this study explicitly assumes the illustrative prior

$$
q=(0.76,\ 0.10,\ 0.07,\ 0.04,\ 0.03)
$$

in the order **clear, pollution, fog, rain, snow**. The nominal availability is $A_{\mathrm{nom}}(a)=\sum_s q_s A_s(a)$.

The total-variation (TV) ambiguity set, with radius $\rho$, is

$$
\mathcal U(q,\rho)=\left\{p\in\mathbb R^5:\ p_s\ge0,\ \sum_s p_s=1,\ \frac12\|p-q\|_1\le\rho\right\}.
$$

The worst-case modeled availability and minimum-aperture design are

$$
A_{\mathrm{rob}}(a)=\min_{p\in\mathcal U(q,\rho)}\sum_s p_s A_s(a),
$$

$$
a^\star(\rho,\sigma_\theta)=\min\left\{a\ge0:\ \min_{p\in\mathcal U(q,\rho)}\sum_s p_s A_s(a,\sigma_\theta)\ge A_{\mathrm{target}}\right\}.
$$

The inner finite-state optimization is solved by **probability-mass transfer**, with an independent **HiGHS linear-programming (LP)** check. The outer scalar aperture problem uses bracketed **Brent–Dekker root finding** and feasibility checks. The term *distributionally robust* refers to the mathematical ambiguity set; $\rho$ is **not** a measured uncertainty or confidence interval. These methods are established techniques, not novel algorithms claimed by this project.

## 6. Sensitivity to atmospheric coefficient interpretation

The coefficient table's dB/km labels and the source's `exp(-Q)` equations imply different transmittance factors. Because this discrepancy propagates to receiver sizing, the complete aperture-design and atmosphere-limited feasibility calculations are evaluated under **both interpretations** (Figure 10 and Table 08). With 15 µrad per-axis jitter and a 92% illustrative availability target, the equation-as-printed model yields nominal and 4% TV-robust diameters of 21.95 cm and 27.01 cm; the literal dB/km interpretation yields approximately 9.47 cm and 11.82 cm. At 8% TV uncertainty, the equation-as-printed model is globally infeasible under the stated assumptions, while the alternative remains feasible (~13.62 cm). Therefore, neither the predicted receiver dimensions nor the atmospheric feasibility limit should be treated as convention-independent hardware requirements. The ~4.89% critical TV radius belongs **only** to the equation-as-printed convention in this illustrative case.

## 7. Case study, ablations and findings

Default link: height 3 km, zenith 0°, nominal wavelength 1550 nm, transmitted optical power 50 mW, transmission efficiency 0.7, threshold 2 mW, initial beam radius 0.025 m, divergence 55 µrad, pointing jitter 15 µrad per axis, target availability 92%. These are **illustrative parameters**; no hardware provider or field dataset is implied.

**Parameter-selection rationale.** The configuration defines a tractable threshold-limited example in which atmospheric extinction, pointing displacement and aperture geometry all contribute to changes in modeled availability. The nominal weather prior and TV radius are selected for scenario comparison, not statistically estimated from meteorological measurements. The optical parameters do not represent a verified commercial transmitter or receiver. The 92% target and 1 m design search bound are demonstration settings rather than a service-level agreement or a hardware design requirement.

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
