<p align="center">
  <img src="assets/cover.svg" width="100%" alt="Illustration of a ground station communicating optically with an aerial platform through atmospheric layers" />
</p>

<h1 align="center">Uncertainty-aware receiver design for ground-to-air FSO links</h1>

<p align="center">
  A computational study of <strong>atmospheric attenuation</strong>, <strong>beam pointing</strong> and <strong>receiver-aperture design</strong> for a single free-space optical link.
</p>

<p align="center">
  <strong>Nishat Yasmin Anika</strong> · Electronics and Communication Engineering · Khulna University of Engineering &amp; Technology (KUET)<br />
  <a href="notebooks/FSO_Link_Design_Colab.ipynb">Colab notebook</a> ·
  <a href="docs/TECHNICAL_NOTE.md">Technical note</a> ·
  <a href="results/">Figures &amp; tables</a>
</p>

<p align="center">
  <code>Python</code> &nbsp; <code>FSO propagation</code> &nbsp; <code>Numerical verification</code> &nbsp; <code>Robust optimization</code>
</p>

---

### The question

**If pointing jitter and the relative frequency of adverse weather are uncertain, how large must a circular optical receiver be to meet a target received-power availability?**

This project combines altitude-dependent atmospheric states with a Gaussian-beam aperture model. It computes conditional link success probabilities analytically, evaluates changes to the assumed weather distribution and solves for the smallest receiver diameter meeting an illustrative availability target.

It is an exploratory **single-link, received-power** model—not a calibrated FSO system, a bit-error-rate study or an experimental measurement.

<p align="center"><img src="assets/method.svg" width="100%" alt="Four-stage model: atmospheric propagation, Gaussian aperture collection, availability calculation, and robust receiver sizing" /></p>

### Three findings

The reference scenario is a **3 km vertical, 1550 nm** link with **15 microradians (µrad) per axis** angular pointing jitter and a **92% optical-power availability target**. Transmitter power, receiver threshold and the five weather-scenario frequencies are deliberately illustrative.

| Finding | Equation-as-printed convention | Literal dB/km convention |
|:--|--:|--:|
| Minimum nominal aperture diameter | **21.95 cm** | **9.47 cm** |
| Minimum diameter at 4% total-variation uncertainty | **27.01 cm** | **11.82 cm** |
| Result at 8% uncertainty | Atmosphere-limited infeasibility | **13.62 cm** |

**The most important finding is sensitivity to assumptions.** The atmospheric source lists attenuation coefficients with dB/km labels but uses the values directly in an exponential expression. The two interpretations produce materially different design outcomes; the numbers above must **not** be treated as equipment recommendations. See [source attribution and the coefficient discussion](docs/SOURCE_MAP.md).

### Results gallery

<table>
<tr>
<td width="50%" valign="top">
  <a href="results/figures/10_optimization_convention_sensitivity.png"><img src="results/figures/10_optimization_convention_sensitivity.png" alt="Comparison of receiver diameter and atmospheric feasibility across coefficient conventions" /></a>
  <strong>01 / Coefficient sensitivity</strong><br />
  The chosen interpretation of published attenuation coefficients changes both the required aperture and feasibility conclusion.
</td>
<td width="50%" valign="top">
  <a href="results/figures/04_minimum_aperture_frontier.png"><img src="results/figures/04_minimum_aperture_frontier.png" alt="Minimum receiver aperture as pointing jitter increases" /></a>
  <strong>02 / Receiver design frontier</strong><br />
  Larger pointing fluctuations increase the minimum aperture under the equation-as-printed convention.
</td>
</tr>
<tr>
<td width="50%" valign="top">
  <a href="results/figures/01_aperture_integral_validation.png"><img src="results/figures/01_aperture_integral_validation.png" alt="Independent numerical quadrature checks Gaussian aperture capture" /></a>
  <strong>03 / Independent geometry check</strong><br />
  The noncentral chi-squared cumulative distribution agrees with numerical integration of the same beam geometry.
</td>
<td width="50%" valign="top">
  <a href="results/figures/08_monte_carlo_validation.png"><img src="results/figures/08_monte_carlo_validation.png" alt="Monte Carlo simulation compared with exact optical-power availability" /></a>
  <strong>04 / Stochastic verification</strong><br />
  Sampled weather and pointing states are compared against the exact finite-state calculation using Wilson score intervals.
</td>
</tr>
</table>

All plots are generated from the Python experiment script. The repository contains **10 figures** (PNG and SVG), **8 CSV tables**, model configuration, a run manifest and numerical verification checks. **[View the complete figure gallery and every data table](results/)**.

### Mathematical model at a glance

The model is deliberately limited to *received optical-power availability* for one ground-to-air link. Platform altitude is $H$, zenith angle is $\zeta$, and slant range is $L=H/\cos\zeta$.

For an offset Gaussian beam with $1/e^2$ intensity radius $w$, aperture radius $a$ and displacement $r$, the collected-power fraction is a noncentral chi-squared cumulative distribution function:

$$
G(a,r,w)=F_{\chi^{\prime 2}_{2}(\lambda)}\!\left(\frac{4a^2}{w^2}\right),\qquad\lambda=\frac{4r^2}{w^2}.
$$

With atmospheric transmittance $T_{\mathrm{atm}}$, optical efficiency $\eta_{\mathrm{opt}}$ and radial pointing displacement $R$, received optical power and modeled availability are

$$
P_{\mathrm{rx}}=P_{\mathrm{tx}}\,\eta_{\mathrm{opt}}\,T_{\mathrm{atm}}\,G(a,R,w),\qquad
A=\Pr(P_{\mathrm{rx}}\ge P_{\min}).
$$

The design minimizes $a$ subject to a target on the worst-case modeled availability over an assumed weather-probability set. The **full derivation, Rayleigh pointing model, total-variation constraint and numerical solvers** are documented in the [technical note](docs/TECHNICAL_NOTE.md). The [source-to-implementation map](docs/SOURCE_MAP.md) identifies which elements come from the literature and which are illustrative assumptions of this study.

### Reproduce the study

**Google Colab (recommended).** Download [the notebook](notebooks/FSO_Link_Design_Colab.ipynb), open [Google Colab](https://colab.research.google.com/) and choose **File → Upload notebook → Runtime → Run all**. The notebook is self-contained and creates `github_results_upload.zip` containing the `results/` directory. No GPU is needed.

**Local Python 3.10+.** From the repository root:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_study.py
```

The script defaults to 20,000 Monte Carlo samples in its largest verification run. Set `FAST_MODE=0` to use 100,000 samples; the exact analytical outputs do not change. The `results/metadata/` directory records the configuration, library versions, runtime and SHA-256 hashes. Runtime depends on the host machine.

<details>
<summary><strong>Repository structure</strong></summary>

```text
.
├── assets/                 # Original static vector graphics for this README
├── notebooks/
│   └── FSO_Link_Design_Colab.ipynb
├── src/
│   ├── atmosphere.py        # Layered weather states and attenuation conventions
│   └── fso_link.py          # Circular-aperture capture, availability, robust design
├── run_study.py             # Figures, tables, and reproducibility metadata
├── tests/test_link.py       # Verification checks
├── results/
│   ├── figures/             # Numbered PNG + SVG scientific plots
│   ├── tables/              # Numbered CSV outputs
│   └── metadata/            # Run configuration, environment and checksums
├── docs/
│   ├── TECHNICAL_NOTE.md
│   ├── SOURCE_MAP.md
│   └── COMPLEXITY_AND_VERIFICATION.md
├── requirements.txt
└── LICENSE
```

</details>

### Methods and checks

| Component | Approach | Independent check |
|---|---|---|
| Layered atmosphere | Published 1550 nm piecewise states | Alternate unit-convention analysis |
| Circular-aperture capture | Noncentral chi-squared CDF | Modified-Bessel numerical quadrature |
| Pointing fluctuations | Independent Gaussian angular jitter | Rayleigh radial distribution and sampled offsets |
| Worst-case weather probabilities | Total-variation ambiguity set | HiGHS linear programming |
| Receiver dimension | Bracketed root finding | Monotonicity and feasibility tests |
| Probability estimate | Exact finite-state mixture | Monte Carlo and 95% Wilson score intervals |

The test suite contains **24 mathematical and implementation checks**. These establish internal numerical consistency, **not physical validation** against weather observations, receiver hardware or MODTRAN. Computation time and complexity are described in [`docs/COMPLEXITY_AND_VERIFICATION.md`](docs/COMPLEXITY_AND_VERIFICATION.md).

### Connection to the literature

This study is motivated by Prof. Mohammed Elamassie and collaborators' work on altitude-dependent optical attenuation and multi-layer airborne FSO performance. It extends those ideas into an **illustrative weather-distribution sensitivity and receiver-sizing exercise**; it does not reproduce their full communication-system models or claim a new analytical method.

1. E. Erdogan, M. Elamassie, I. Altunbas, G. K. Kurt, M. Uysal and H. Yanikomeroglu, *Modeling Atmospheric Attenuation in Vertical FSO Links: An Altitude-Aware Piecewise Framework*, 2026. [DOI](https://doi.org/10.1109/MVT.2026.3687349) · [Author manuscript](https://arxiv.org/abs/2604.18207).
2. M. Elamassie and M. Uysal, *Multi-Layer Airborne FSO Systems: Performance Analysis and Optimization*, *IEEE Transactions on Communications*, 2025. [DOI](https://doi.org/10.1109/TCOMM.2024.3471995).
3. Source-specific implementation choices and additional method references are mapped in [`docs/SOURCE_MAP.md`](docs/SOURCE_MAP.md).

### Scope and next step

The model excludes atmospheric scintillation, finite detector noise, nonzero boresight error, correlated weather and experimental receiver calibration. A useful next step would be to estimate weather-scenario probabilities from a specific location and season and test whether receiver designs remain reliable out of sample.

**Development note:** AI tools were used to assist with code development, documentation and visualization. The repository provides the mathematical formulations, references, numerical verification tests and reproducible results for technical review.
