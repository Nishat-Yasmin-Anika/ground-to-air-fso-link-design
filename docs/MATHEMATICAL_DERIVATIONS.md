# Mathematical Derivations

## Ground-to-Air Free-Space Optical Receiver Design

**Author:** Nishat Yasmin Anika  
**Department:** Electronics and Communication Engineering, KUET

This document derives the mathematical expressions implemented
in `src/atmosphere.py` and `src/fso_link.py`.

The derivations establish internal mathematical consistency
under declared assumptions. They do not establish empirical
accuracy or experimental validation.

[Project overview](../README.md) |
[Scientific source map](SOURCE_MAP.md) |
[Technical note](TECHNICAL_NOTE.md)

---

## 1. Notation and Assumptions

| Symbol | Definition | Unit |
|---|---|---|
| $H$ | Receiver altitude | km |
| $\theta$ | Zenith angle from local vertical | rad |
| $L$ | Total slant-path length | m |
| $d_j$ | Path length inside atmospheric layer j | km |
| $c_{jk}$ | Printed atmospheric coefficient | convention-dependent |
| $Q$ | Integrated printed attenuation coefficient | convention-dependent |
| $T$ | Atmospheric power transmittance | dimensionless |
| $\lambda$ | Optical wavelength | m |
| $w_0$ | Transmitter beam waist radius | m |
| $w$ | Receiver-plane beam radius | m |
| $\Theta$ | Beam divergence half-angle | rad |
| $a$ | Receiver aperture radius | m |
| $r$ | Radial pointing displacement | m |
| $\sigma$ | Per-axis displacement standard deviation | m |
| $G$ | Optical collection fraction | dimensionless |
| $P_t$ | Transmitted optical power | mW |
| $\eta$ | Optical efficiency | dimensionless |
| $P_{\min}$ | Received-power threshold | mW |
| $A_i$ | Conditional scenario availability | dimensionless |
| $\rho$ | Total-variation ambiguity radius | dimensionless |

### Model assumptions

- Flat Earth and horizontally stratified atmospheric layers.
- Ground transmitter at zero reference altitude.
- A circular receiver aperture normal to the nominal beam.
- Isotropic Gaussian-equivalent receiver-plane intensity.
- Independent zero-mean Gaussian pointing components.
- Independent atmospheric layer states within each scenario.
- Pointing displacement independent of atmospheric states.
- Fixed transmitter power and optical efficiency.
- No turbulence, scintillation, detector noise or BER model.

All weather priors and optical hardware parameters are
illustrative unless explicitly identified as literature inputs.

---

## 2. Atmospheric Layer Geometry

For receiver altitude $H$ and zenith angle $\theta$,

$$
L = \frac{1000H}{\cos\theta}.
$$

The factor 1000 converts kilometres to metres.

For atmospheric layer j extending from altitude $b_j$
to altitude $t_j$, the intersected vertical thickness is

$$
h_j = \max(0,\min(H,t_j)-b_j).
$$

Therefore, the slant-path length within that layer is

$$
d_j = \frac{h_j}{\cos\theta}.
$$

For contiguous layers covering the entire link,

$$
\sum_j d_j = \frac{H}{\cos\theta}.
$$

The implemented layer model is restricted to an altitude
of at most 30 km and a zenith angle of at most 70 degrees.

This is a flat-Earth geometric approximation.

**Implementation:** `path_lengths_km()` and `Link.length_m`.

---

## 3. Beer-Lambert Atmospheric Attenuation

Let $\alpha(s)$ denote a power extinction coefficient.

The local optical-power differential equation is

$$
\frac{dP}{ds}=-\alpha(s)P(s).
$$

Dividing by optical power and integrating,

$$
\int_{P_t}^{P_r}\frac{dP}{P}
=
-\int_0^L\alpha(s)\,ds.
$$

Hence,

$$
T=\frac{P_r}{P_t}
=
\exp\left(-\int_0^L\alpha(s)\,ds\right).
$$

For piecewise constant extinction,

$$
T=\exp\left(-\sum_j\alpha_jd_j\right).
$$

The extinction coefficients and path lengths must use
compatible length units.

### 3.1 Power-decibel conversion

For integrated attenuation $Q_{\mathrm{dB}}$,

$$
Q_{\mathrm{dB}}=-10\log_{10}T.
$$

Rearranging,

$$
T=10^{-Q_{\mathrm{dB}}/10}.
$$

Consequently, the relationship between power attenuation
coefficient in dB/km and extinction in inverse kilometres is

$$
\alpha=\frac{\ln 10}{10}\gamma.
$$

### 3.2 Implemented coefficient interpretations

Define the integrated printed coefficient as

$$
Q=\sum_j c_jd_j.
$$

The primary interpretation is

$$
T_{\mathrm{dB}}=10^{-Q/10}.
$$

The legacy interpretation is

$$
T_{\mathrm{legacy}}=e^{-Q}.
$$

Their corresponding attenuation values in dB are

$$
\mathcal L_{\mathrm{dB}}=Q
$$

and

$$
\mathcal L_{\mathrm{legacy}}
=\frac{10Q}{\ln 10}.
$$

These interpretations are kept separate because the source
manuscript's printed units and exponential convention
require further reconciliation.

The legacy branch reproduces the equation-as-printed
interpretation, not the source's original MODTRAN validation.

**Implementation:** `transmittance_from_q()`,
`loss_db_from_q()`.

**Reference:** S1 in `SOURCE_MAP.md`.

---

## 4. Atmospheric State Probabilities

Suppose layer j has categorical states k with probabilities
$p_{jk}$ and printed coefficients $c_{jk}$.

The probabilities satisfy

$$
\sum_k p_{jk}=1.
$$

For one selected state in every active layer,

$$
Q_{\boldsymbol{k}}=\sum_jd_jc_{j,k_j}.
$$

Assuming conditional independence across layers,

$$
p_{\boldsymbol{k}}=\prod_jp_{j,k_j}.
$$

The expected atmospheric transmittance is therefore

$$
\mathbb E[T]
=
\sum_{\boldsymbol{k}}
p_{\boldsymbol{k}}f(Q_{\boldsymbol{k}}),
$$

where $f(Q)$ is the selected attenuation convention.

### 4.1 Effective versus expected transmittance

The effective transmittance is

$$
T_{\mathrm{eff}}=f(\mathbb E[Q]).
$$

In general,

$$
f(\mathbb E[Q])\ne\mathbb E[f(Q)].
$$

Both exponential attenuation mappings are convex in Q.

By Jensen's inequality,

$$
\mathbb E[f(Q)]\geq f(\mathbb E[Q]).
$$

Thus the transmittance of the mean coefficient must not
be confused with mean transmittance.

### 4.2 Factorized expectation

For either convention,

$$
f(Q)=e^{-\kappa Q},
$$

where $\kappa=1$ for the legacy convention and
$\kappa=\ln(10)/10$ for literal dB conversion.

Under layer independence,

$$
\mathbb E[T]
=
\prod_j\left[
\sum_k p_{jk}e^{-\kappa d_jc_{jk}}
\right].
$$

This expression avoids explicit enumeration when only
mean atmospheric transmittance is required.

An atmospheric loss-budget exceedance probability is

$$
\Pr(\mathcal L>B)
=
\sum_{\boldsymbol{k}}p_{\boldsymbol{k}}
\mathbf 1\{\mathcal L_{\boldsymbol{k}}>B\}.
$$

This quantity is not receiver outage probability.

**Implementation:** `exact_distribution()`,
`exact_statistics()`, `effective_transmittance()`,
`mean_transmittance_factorized()`.

---

## 5. Gaussian Beam Propagation

The implemented Gaussian-equivalent beam radius is

$$
w(L)=\sqrt{w_0^2+(\Theta L)^2}.
$$

The radius w describes the 1/e-squared intensity radius.

For a beam originating at its waist, the Gaussian-equivalent
beam-quality relationship is

$$
\Theta=\frac{M^2\lambda}{\pi w_0}.
$$

Consequently,

$$
M^2=\frac{\pi w_0\Theta}{\lambda}.
$$

The existing illustrative parameters are

- Wavelength: 1550 nm.
- Beam waist radius: 25 mm.
- Divergence half-angle: 55 microradians.

These imply a Gaussian-equivalent beam propagation factor
of approximately 2.79.

This factor is not a measured beam-quality value.
A nonideal beam need not possess a perfectly Gaussian
intensity profile. The Gaussian-equivalent profile
is an explicit simplifying assumption.

**Implementation:** `Link.beam_radius_m`,
`Link.implied_m_squared()` (property).

**Reference:** S3 in `SOURCE_MAP.md`.

---

## 6. Exact Circular-Aperture Collection

The normalized displaced Gaussian intensity is

$$
I(x,y)=\frac{2}{\pi w^2}
\exp\left[-\frac{2((x-r)^2+y^2)}{w^2}\right].
$$

Its integral over the entire transverse plane is unity:

$$
\int_{\mathbb R^2}I(x,y)\,dx\,dy=1.
$$

The fraction captured by a circular aperture of radius a is

$$
G(a,w,r)
=
\iint_{x^2+y^2\leq a^2}I(x,y)\,dx\,dy.
$$

### 6.1 Aligned Gaussian beam

For zero displacement, radial integration gives

$$
G(a,w,0)
=
\int_0^a
\frac{4s}{w^2}e^{-2s^2/w^2}\,ds.
$$

Hence,

$$
G(a,w,0)=1-e^{-2a^2/w^2}.
$$

### 6.2 Noncentral chi-square derivation

The normalized intensity corresponds to independent
Gaussian transverse coordinates:

$$
X\sim\mathcal N(r,w^2/4),
\qquad
Y\sim\mathcal N(0,w^2/4).
$$

Then

$$
\frac{4(X^2+Y^2)}{w^2}
\sim
\chi'^2_2\left(\frac{4r^2}{w^2}\right).
$$

Therefore,

$$
G(a,w,r)
=
F_{\chi'^2_2}
\left(
\frac{4a^2}{w^2};
\frac{4r^2}{w^2}
\right).
$$

This is exact for the assumed circular aperture and
normalized isotropic Gaussian intensity.

It is not an approximate equivalent-beamwidth formula.

**Implementation:** `gaussian_aperture_capture()`.

---

## 7. Independent Bessel Integration

Using polar coordinates about the aperture center,

$$
(x-r)^2+y^2=s^2+r^2-2sr\cos\phi.
$$

Substituting into the two-dimensional integral,

$$
G=
\frac{2}{\pi w^2}
\int_0^a s e^{-2(s^2+r^2)/w^2}
\int_0^{2\pi}e^{4sr\cos\phi/w^2}
\,d\phi\,ds.
$$

Using the modified Bessel identity

$$
\int_0^{2\pi}e^{z\cos\phi}d\phi
=2\pi I_0(z),
$$

we obtain

$$
G=
\int_0^a
\frac{4s}{w^2}
e^{-2(s^2+r^2)/w^2}
I_0\left(\frac{4sr}{w^2}\right)ds.
$$

For numerical stability, define

$$
I_{0e}(z)=e^{-z}I_0(z),\qquad z\geq0.
$$

The integrand becomes

$$
G=
\int_0^a
\frac{4s}{w^2}
e^{-2(s-r)^2/w^2}
I_{0e}\left(\frac{4sr}{w^2}\right)ds.
$$

This provides an independent integration method for
verifying the noncentral chi-square calculation.

The test suite also uses Cartesian quadrature,
integrating transverse Gaussian slices independently.

**Implementation:** `capture_via_independent_quadrature()`.

---

## 8. Pointing Displacement

Let the horizontal and vertical pointing displacement
components be independent Gaussian variables:

$$
X_p,Y_p\sim\mathcal N(0,\sigma^2).
$$

Under the small-angle displacement approximation,

$$
\sigma=L\sigma_\theta,
$$

where $\sigma_\theta$ is the per-axis angular
standard deviation in radians.

The radial displacement is

$$
R=\sqrt{X_p^2+Y_p^2}.
$$

The joint density is

$$
f(x,y)=\frac{1}{2\pi\sigma^2}
e^{-(x^2+y^2)/(2\sigma^2)}.
$$

Transforming to polar coordinates and integrating over angle,

$$
f_R(r)=
\frac{r}{\sigma^2}
e^{-r^2/(2\sigma^2)},\qquad r\geq0.
$$

Thus R follows a Rayleigh distribution with CDF

$$
F_R(r)=1-e^{-r^2/(2\sigma^2)}.
$$

When $\sigma=0$, the displacement is deterministically zero.
That case must be handled separately.

This model excludes boresight bias, anisotropic jitter,
angle-of-arrival loss and temporal tracking dynamics.

---

## 9. Mean Gaussian Collection

The Gaussian optical intensity has per-axis variance

$$
\sigma_b^2=\frac{w^2}{4}.
$$

Independent Gaussian pointing displacement adds
another variance $\sigma^2$.

The convolution therefore produces a centered Gaussian with

$$
\sigma_{\mathrm{total}}^2=\frac{w^2}{4}+\sigma^2.
$$

Integrating over the circular aperture,

$$
\mathbb E[G]
=
1-\exp\left[
-\frac{a^2}{2(\sigma^2+w^2/4)}
\right].
$$

When pointing jitter approaches zero, this reduces to
the aligned Gaussian collection expression.

**Implementation:** `mean_capture_analytic()`.

---

## 10. Received Optical Power

The link model combines transmitter power,
fixed optical efficiency, atmospheric transmission
and Gaussian aperture collection:

$$
P_r=P_t\eta T G(a,w,R).
$$

The corresponding power-loss budget in dB is

$$
\mathcal L_{\mathrm{total}}
=
-10\log_{10}\eta
-10\log_{10}T
-10\log_{10}G.
$$

The expression is defined for strictly positive factors.

Under atmospheric and pointing independence,

$$
\mathbb E[P_r]
=
P_t\eta\mathbb E[T]\mathbb E[G].
$$

The calculation describes collected optical power,
not electrical SNR or communication BER.

---

## 11. Conditional Received-Power Availability

For a fixed atmospheric transmittance t, define the
required collection fraction as

$$
g_{\min}=\frac{P_{\min}}{P_t\eta t}.
$$

If t is zero or the required collection fraction is
at least unity, finite-aperture reception cannot
satisfy the threshold.

For a circular aperture and an isotropic Gaussian,
collection is nonincreasing with radial displacement.

Define the critical displacement by

$$
G(a,w,r_{\mathrm{crit}})=g_{\min}.
$$

For nonzero jitter and an achievable collection requirement,

$$
A(t,a)=
\Pr(R\leq r_{\mathrm{crit}})
=
1-\exp\left[
-\frac{r_{\mathrm{crit}}^2}{2\sigma^2}
\right].
$$

If the required collection equals the aligned maximum,
only zero displacement succeeds. This event has zero
probability under continuous, nonzero Rayleigh jitter.

For deterministic zero jitter,

$$
A(t,a)
=
\mathbf 1\{
P_t\eta tG(a,w,0)\geq P_{\min}
\}.
$$

The critical displacement is calculated numerically
using a bracketed scalar root finder.

**Implementation:** `critical_offset()`,
`success_probability_for_transmittance()`.

---

## 12. Weather-Mixture Availability

For weather scenario i, enumerate its atmospheric states
with conditional probabilities $p_{ik}$.

Its conditional availability is

$$
A_i(a)=\sum_kp_{ik}A(t_{ik},a).
$$

For an illustrative scenario probability vector

$$
\boldsymbol p=(0.76,0.10,0.07,0.04,0.03),
$$

the nominal availability is

$$
A_{\mathrm{nom}}(a)
=
\sum_{i=1}^{5}p_iA_i(a).
$$

The scenario ordering is clear, pollution, fog, rain and snow.

These outer scenario probabilities are hypothetical.
They are not estimated from ERA5 or historical weather data.

Availability here denotes a modeled snapshot probability,
not measured time-series uptime.

**Implementation:** `conditional_availability()`,
`availability()`.

---

## 13. Total-Variation Robust Optimization

The actual scenario probability vector q is assumed
to belong to the ambiguity set

$$
\mathcal U_\rho=
\left\{
\boldsymbol q:
q_i\geq0,\;
\sum_iq_i=1,\;
\frac12\sum_i|q_i-p_i|\leq\rho
\right\}.
$$

The robust availability is

$$
A_{\mathrm{rob}}(a)
=
\min_{\boldsymbol q\in\mathcal U_\rho}
\sum_iq_iA_i(a).
$$

### 13.1 Greedy probability transfer

Transferring probability mass delta from scenario j
to scenario i changes the objective by

$$
\Delta A=\delta(A_i-A_j).
$$

If $A_i<A_j$, the transfer reduces availability.

The greatest reduction per unit of transferred mass
is obtained by moving mass from the highest-availability
remaining donor to the lowest-availability available recipient.

The algorithm respects

- Available donor probability.
- Recipient probability capacity.
- Remaining total-variation budget.

Sorting and successive probability transfers solve the
finite-state linear objective, up to numerical tolerances.

### 13.2 Independent linear program

Introduce auxiliary nonnegative variables $u_i$ satisfying

$$
q_i-p_i\leq u_i,
\qquad
p_i-q_i\leq u_i.
$$

Then solve

$$
\min_{\boldsymbol q,\boldsymbol u}
\sum_iq_iA_i
$$

subject to

$$
\sum_iq_i=1,\qquad q_i\geq0,
$$

$$
u_i\geq0,\qquad \sum_i u_i\leq2\rho.
$$

The implemented LP independently verifies the
greedy probability-transfer solution.

The ambiguity radius represents an assumed uncertainty
budget, not an empirically established confidence region.

**Implementation:** `worst_case_tv_greedy()`,
`worst_case_tv_lp()`.

**Reference:** S5 in `SOURCE_MAP.md`.

---

## 14. Minimum Receiver-Aperture Optimization

The design objective is

$$
\min_a a
$$

subject to

$$
A_{\mathrm{rob}}(a)\geq A_{\mathrm{target}}.
$$

The implemented search interval is

$$
0.025\leq a\leq0.50\ \mathrm{m}.
$$

For fixed beam width and displacement, increasing the
circular aperture cannot reduce collected optical power,
because the collection region only increases.

Therefore, conditional, nominal and robust availability
are all nondecreasing with aperture radius.

This permits monotone bisection.

At each iteration,

$$
a_{\mathrm{mid}}
=
\frac{a_{\mathrm{lo}}+a_{\mathrm{hi}}}{2}.
$$

If the midpoint satisfies the target, it becomes
the feasible upper endpoint. Otherwise, it becomes
the infeasible lower endpoint.

The algorithm returns the feasible upper endpoint
with a radius tolerance of $10^{-7}$ m.

This formulation also handles discontinuous zero-jitter
availability steps.

If the lower bound already satisfies the requirement,
the lower bound is returned.

If the upper bound fails, no feasible aperture exists
inside the specified interval.

The reported receiver diameter is

$$
D=2a.
$$

**Implementation:** `min_aperture_for_target()`.

---

## 15. Atmospheric Feasibility Ceiling

For every finite aperture and finite Gaussian beam width,

$$
G(a,w,r)<1.
$$

Consequently, a necessary condition for successful
finite-aperture reception is

$$
P_t\eta t>P_{\min}.
$$

The inequality is strict because a finite Gaussian
aperture cannot capture exactly all transmitted power.

The scenario-level limiting availability is

$$
C_i=
\sum_kp_{ik}
\mathbf 1\{P_t\eta t_{ik}>P_{\min}\}.
$$

The nominal atmospheric ceiling is

$$
C_{\mathrm{nom}}=\sum_ip_iC_i.
$$

The robust atmospheric ceiling is

$$
C_{\mathrm{rob}}
=
\min_{\boldsymbol q\in\mathcal U_\rho}
\sum_iq_iC_i.
$$

If

$$
C_{\mathrm{rob}}<A_{\mathrm{target}},
$$

no finite aperture can satisfy the robust target.

Equality between the ceiling and target does not itself
establish finite-aperture feasibility.

The critical TV radius identifies the break-even
boundary of the atmospheric ceiling. It must not be
interpreted as a guarantee of finite-aperture feasibility.

**Implementation:** `weather_limited_ceiling()`,
`critical_tv_radius()`.

---

## 16. Monte Carlo Verification

For every simulated realization:

1. Draw a weather scenario.
2. Draw categorical atmospheric layer states.
3. Calculate atmospheric transmittance.
4. Draw two Gaussian pointing components.
5. Calculate radial displacement.
6. Evaluate Gaussian aperture collection.
7. Calculate received optical power.
8. Determine whether the power threshold is satisfied.

For N independent draws with K successes,

$$
\widehat A=\frac{K}{N}.
$$

Its binomial variance under the assumed simulation model is

$$
\operatorname{Var}(\widehat A)
=
\frac{A(1-A)}{N}.
$$

### 16.1 Wilson confidence interval

The Wilson interval is obtained by inverting the
binomial normal-score inequality:

$$
(\widehat A-A)^2
\leq
\frac{z^2 A(1-A)}{N}.
$$

Solving the resulting quadratic inequality gives
the interval center

$$
c=
\frac{\widehat A+z^2/(2N)}
{1+z^2/N}
$$

and half-width

$$
h=
\frac{z}{1+z^2/N}
\sqrt{
\frac{\widehat A(1-\widehat A)}{N}
+
\frac{z^2}{4N^2}
}.
$$

The confidence interval is

$$
[c-h,\;c+h].
$$

For the approximate 95 percent interval,

$$
z\approx1.959964.
$$

Monte Carlo agreement supports the probability
implementation under the simulated model.

It does not validate the atmospheric assumptions,
hardware performance or real-world availability.

**Implementation:** `sample_link()`, `wilson_score()`.

---

## 17. Reference Numerical Example

Consider the existing illustrative link:

| Parameter | Value |
|---|---:|
| Altitude | 3 km |
| Zenith angle | 0 degrees |
| Wavelength | 1550 nm |
| Transmitter power | 50 mW |
| Optical efficiency | 0.70 |
| Waist radius | 0.025 m |
| Divergence half-angle | 55 microradians |
| Per-axis angular jitter | 15 microradians |
| Receiver power threshold | 2 mW |
| Availability target | 0.92 |

The link length is

$$
L=3000\ \mathrm{m}.
$$

The Gaussian-equivalent beam radius is

$$
w=\sqrt{0.025^2+(55\times10^{-6}\times3000)^2}
\approx0.166883\ \mathrm{m}.
$$

The per-axis pointing displacement deviation is

$$
\sigma=3000\times15\times10^{-6}
=0.045\ \mathrm{m}.
$$

The available optical power before atmospheric and
aperture losses is

$$
P_t\eta=35\ \mathrm{mW}.
$$

For the primary clear-weather Table II scenario
at 3 km altitude,

$$
Q=3(0.034)=0.102.
$$

The two atmospheric interpretations give

$$
T_{\mathrm{dB}}=10^{-0.102/10}\approx0.976787
$$

and

$$
T_{\mathrm{legacy}}=e^{-0.102}\approx0.903030.
$$

The verified scenario-mixture optimization results are:

| Atmospheric interpretation | Nominal diameter | TV radius 0.04 |
|---|---:|---:|
| Literal dB/km | 9.472 cm | 11.816 cm |
| Legacy exponential | 21.947 cm | 27.009 cm |

The nominal and robust results combine all five
weather scenarios, not only the clear-weather example.

These dimensions are conditional numerical predictions.

See the complete generated results in
[the results directory](../results/README.md).

---

## 18. Computational Complexity and Limitations

Let J be the number of active atmospheric layers
and $K_j$ the number of states within layer j.

Explicit enumeration requires

$$
N_{\mathrm{states}}=\prod_{j=1}^J K_j.
$$

Its time complexity is approximately

$$
O\left(J\prod_{j=1}^J K_j\right).
$$

The factorized mean-transmittance calculation requires

$$
O\left(\sum_jK_j\right).
$$

For S weather scenarios, the greedy TV solver
requires sorting and probability transfer:

$$
O(S\log S).
$$

For aperture interval width W and absolute tolerance
epsilon, bisection requires approximately

$$
O\left(\log_2\frac{W}{\epsilon}\right)
$$

availability evaluations.

Actual runtime also depends on atmospheric enumeration,
noncentral chi-square evaluations and scalar root finding.

### Scientific limitations

- Atmospheric coefficient calibration remains unresolved.
- The two attenuation conventions are sensitivity cases.
- Weather frequencies and TV radii are illustrative.
- Layer-state independence is an assumption.
- The Gaussian-equivalent beam is not measured.
- Atmospheric turbulence and scintillation are excluded.
- Receiver noise, modulation and BER are excluded.
- The radiation-fog sensitivity model has conditional
  applicability; its original source requires further review.
- No experimental optical hardware validation is claimed.

The mathematical and numerical verification establishes
consistency of the implemented model, not universal
physical validity.

## References

The equation derivations use standard probability,
Gaussian optics, attenuation and optimization theory.

For original scientific references, coefficient provenance
and applicability qualifications, consult
[SOURCE_MAP.md](SOURCE_MAP.md).

Key references include:

1. Erdogan et al., DOI: 10.1109/MVT.2026.3687349.
2. Farid and Hranilovic, DOI: 10.1109/JLT.2007.899174.
3. Elamassie and Uysal, DOI: 10.1109/TCOMM.2024.3471995.
4. Rahimian and Mehrotra, DOI: 10.5802/ojmo.15.
5. ITU-R P.1814-1 and P.835-7.

These references provide theoretical and research context.
Their complete system results are not claimed to have
been independently reproduced.
