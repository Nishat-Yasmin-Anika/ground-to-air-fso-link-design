<h1 align="center">Atmospheric-Model Sensitivity in Ground-to-Air FSO Receiver Design</h1>

<p align="center">
  <strong>Nishat Yasmin Anika</strong><br>
  Department of Electronics and Communication Engineering<br>
  Khulna University of Engineering &amp; Technology (KUET), Bangladesh
</p>

<p align="center">
  <a href="https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions/workflows/python-tests.yml"><img src="https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions/workflows/python-tests.yml/badge.svg?branch=main" alt="Numerical verification status"></a>
  <a href="https://colab.research.google.com/github/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/blob/main/notebooks/FSO_Link_Design_Colab.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#abstract">Abstract</a> ·
  <a href="#research-context-and-motivation">Motivation</a> ·
  <a href="#model-and-method">Method</a> ·
  <a href="#results-and-discussion">Results</a> ·
  <a href="#numerical-verification">Verification</a> ·
  <a href="#research-outlook">Outlook</a> ·
  <a href="#reproduction">Reproduction</a> ·
  <a href="#references">References</a>
</p>

<p align="center">
  <img src="assets/cover.svg" width="100%" alt="Illustration of a ground-to-air optical link through atmospheric layers">
</p>

## Abstract

<p align="justify">This numerical study explores how atmospheric attenuation assumptions influence receiver aperture sizing in ground-to-air free-space optical (FSO) links. It brings together altitude-dependent atmospheric layers, Gaussian beam collection through a circular aperture and random pointing errors. A total-variation (TV) ambiguity set is used to examine uncertainty in weather-scenario probabilities.</p>

<p align="justify">For an illustrative 3 km vertical link with a 92% received-power availability target and 15 µrad per-axis angular jitter, the calculated nominal receiver diameter is 9.47 cm under the literal dB/km interpretation of the published attenuation coefficients and 21.95 cm under the exponential equation as printed in the author manuscript. At a TV radius of 0.08, the latter case gives an availability ceiling of 89.2%. Under those assumptions, no finite aperture can meet the target. Quadrature, linear programming and Monte Carlo simulation are used to check the numerical calculations.</p>

<p align="justify">These results are conditional on the chosen model and parameters. The purpose is to understand the sensitivity of receiver design decisions, rather than to establish a measured link performance or a practical receiver specification.</p>

<p align="justify"><strong>Keywords:</strong> Free-space optics, atmospheric attenuation, pointing errors, Gaussian beam collection, receiver aperture, distributionally robust optimization.</p>

## Research context and motivation

<p align="justify">I began this project to better understand atmospheric propagation and optical link design in airborne communication systems. The work of Erdogan et al. [1] on altitude-dependent atmospheric attenuation and the study by Elamassie and Uysal [4] on multi-layer airborne FSO systems provided the main motivation for this exploration. Reading these studies encouraged me to examine how atmospheric conditions and pointing uncertainty can influence the size of an optical receiver.</p>

<p align="justify">The question I wanted to explore was whether a receiver sized for an assumed weather distribution would still meet its optical-power threshold if that distribution changed. I approached this question by implementing a simplified link model and examining the effects of its assumptions.</p>

<p align="justify">While working through the atmospheric model in the author manuscript of [1], I was unsure how to interpret the coefficient convention. The tables label the coefficients in dB/km, while the transmittance equation uses a natural exponential. I considered both interpretations using the printed coefficient values to see how the receiver design would change. This comparison is intended as a sensitivity study, not a conclusion about the intended convention or the accuracy of the original atmospheric model. The underlying atmospheric calibration has not been reproduced.</p>

<p align="justify">Two additional sensitivity cases consider the clear-weather layer described in the source text and a separate radiation-fog relation [2]. Established work on pointing errors [3] informs the optical model, while total variation [5] provides a way to represent uncertainty in the assumed weather probabilities.</p>

<p align="justify">I see this as a learning-oriented computational study and a starting point for further research. Feedback on the modelling assumptions and their interpretation would be valuable.</p>

## Model and method

<p align="center">
  <img src="assets/method.svg" width="100%" alt="Four stages of the model: atmospheric attenuation, Gaussian beam collection, optical-power availability and robust aperture sizing">
</p>

<p align="center"><em>Fig. 1. Calculation sequence for the receiver design problem.</em></p>

### Atmospheric attenuation

<p align="justify">For a receiver at altitude H and zenith angle θ, the slant path in the flat-layer approximation is H sec θ. Each intersected layer contributes its traversed distance to the integrated printed coefficient Q. The two power-transmittance interpretations are</p>

```math
Q=\sum_j c_jd_j
```

```math
T_{\mathrm{dB}}=10^{-Q/10},\qquad T_{\mathrm{exp}}=e^{-Q}.
```

<p align="justify">Here, the layer distance d is measured in kilometres. The units of Q depend on the interpretation. The literal dB/km conversion is used as the primary case, while the exponential form is retained for comparison with the equation as printed in the author manuscript [1].</p>

### Optical collection and pointing

<p align="justify">Received optical power is modelled as the product of transmitted power, optical efficiency, atmospheric transmittance and the fraction collected by the circular aperture. Under the assumed Gaussian beam profile, the collection fraction can be expressed exactly using a noncentral chi-square cumulative distribution function with two degrees of freedom.</p>

```math
P_r=P_t\eta T G(a,w,r)
```

```math
G(a,w,r)=F_{\chi'^2_2}\left(\frac{4a^2}{w^2};\frac{4r^2}{w^2}\right).
```

<p align="justify">The variables a, w and r denote aperture radius, Gaussian beam radius and radial pointing displacement, respectively. Independent zero-mean Gaussian pointing components with equal variance give a Rayleigh distribution for r. For each atmospheric state, the maximum displacement satisfying the received-power threshold is found numerically.</p>

### Aperture optimization

<p align="justify">Let Aᵢ(a) be the availability conditional on weather scenario i. Let p be the nominal probability vector and q an alternative vector. The ambiguity set is</p>

```math
\mathcal U_\rho=\left\{q\geq0:\ \sum_i q_i=1,\quad \frac12\sum_i\lvert q_i-p_i\rvert\leq\rho\right\}.
```

<p align="justify">The minimum aperture is sought subject to the worst-case availability constraint:</p>

```math
\begin{aligned}
\min_a\quad &a \\
\text{subject to}\quad &\min_{q\in\mathcal U_\rho}\sum_i q_i A_i(a)\geq A_{\mathrm{target}},\\
&0.025\leq a\leq0.50\quad\text{(metres)}.
\end{aligned}
```

<p align="justify">The inner problem is solved by transferring probability mass from scenarios with higher availability to those with lower availability. The outer search uses bisection because collection increases with aperture radius. An atmospheric availability ceiling helps distinguish targets that fail within the search interval from those that cannot be met at any finite aperture under the model.</p>

<p align="center">
  <a href="docs/MATHEMATICAL_DERIVATIONS.md">Mathematical derivations</a> ·
  <a href="docs/TECHNICAL_NOTE.md">Technical note</a>
</p>

<details>
<summary>Reference simulation parameters</summary>

| Parameter | Assumed value |
|---|---:|
| Wavelength | 1550 nm |
| Receiver altitude | 3 km |
| Zenith angle | 0° |
| Transmitted optical power | 50 mW |
| Optical efficiency | 0.70 |
| Beam waist radius | 25 mm |
| Divergence half-angle | 55 µrad |
| Per-axis angular jitter (standard deviation) | 15 µrad |
| Received-power threshold | 2 mW |
| Availability target | 0.92 |
| Reference TV radius | 0.04 |

<p align="justify">The assumed scenario probabilities for clear weather, pollution, fog, rain and snow are 0.76, 0.10, 0.07, 0.04 and 0.03, respectively. These are illustrative probabilities, not estimates from historical weather data. The received-power threshold is an assumed study parameter rather than a measured detector sensitivity.</p>

</details>

## Results and discussion

<p align="justify">Table 1 reports the minimum receiver diameter for a 92% probability of meeting or exceeding the assumed 2 mW threshold in the reference link. All entries are model-based calculations.</p>

<p align="center"><em>Table 1. Minimum receiver diameter (cm) under alternative atmospheric assumptions.</em></p>

| Atmospheric case | Nominal | ρ = 0.04 | ρ = 0.08 |
|---|---:|---:|---:|
| Table II, literal dB/km | 9.47 | 11.82 | 13.62 |
| Table II, exponential interpretation | 21.95 | 27.01 | Infeasible |
| Clear-weather prose alternative | 9.42 | 11.75 | 13.62 |
| Radiation-fog stress case | 15.65 | Infeasible | Infeasible |

<p align="justify">Under literal dB/km conversion, increasing the TV radius from zero to 0.04 raises the calculated diameter from 9.47 to 11.82 cm. The corresponding change under the exponential interpretation is from 21.95 to 27.01 cm. At ρ = 0.08, the latter case has an availability ceiling of 89.2%, below the target. The radiation-fog stress case also falls below the target at ρ = 0.04, with a ceiling of 89%. Under the stated assumptions, these cases cannot meet 92% at any finite aperture.</p>

<p align="center">
  <a href="results/figures/11_model_and_target_sensitivity.svg"><img src="results/figures/11_model_and_target_sensitivity.png" width="100%" alt="Receiver diameter and atmospheric feasibility bounds for four atmospheric cases"></a>
</p>

<p align="center"><em>Fig. 2. Receiver aperture requirements and atmospheric feasibility bounds across four atmospheric models for a 92% availability target.</em> <a href="results/figures/11_model_and_target_sensitivity.svg">Vector figure</a></p>

<p align="justify">The optical parameters remain fixed in Table 1. The differences therefore arise from the atmospheric assumptions and the uncertainty in weather probabilities rather than changes in transmitter power or beam geometry. The comparison helped me understand how strongly the receiver sizing calculation can depend on the atmospheric model. It does not establish which coefficient interpretation is physically correct.</p>

<details>
<summary>Additional results: pointing jitter and aperture size</summary>

<p align="center">
  <a href="results/figures/04_minimum_aperture_frontier.svg"><img src="results/figures/04_minimum_aperture_frontier.png" width="100%" alt="Minimum receiver diameter versus pointing angular jitter"></a>
</p>

<p align="center"><em>Fig. 3. Minimum receiver diameter versus per-axis angular jitter.</em> <a href="results/figures/04_minimum_aperture_frontier.svg">Vector figure</a></p>

<p align="center">
  <a href="results/figures/03_availability_vs_aperture.svg"><img src="results/figures/03_availability_vs_aperture.png" width="100%" alt="Nominal and robust received-power availability versus receiver aperture size"></a>
</p>

<p align="center"><em>Fig. 4. Received-power availability versus aperture size.</em> <a href="results/figures/03_availability_vs_aperture.svg">Vector figure</a></p>

</details>

<p align="center">
  <a href="results/README.md">Complete results gallery (12 figures and 11 CSV tables)</a> ·
  <a href="results/tables/09_model_and_target_sensitivity.csv">Source data for Table 1</a>
</p>

## Numerical verification

<p align="justify">To check the implementation, the Gaussian aperture integral is evaluated using independent Bessel and Cartesian quadrature formulations. A separately formulated linear program checks the TV probability-transfer solution. Monte Carlo simulations draw weather states and Gaussian pointing displacements directly. Wilson intervals describe sampling uncertainty in the estimated success probabilities.</p>

<p align="center">
  <a href="results/figures/08_monte_carlo_validation.svg"><img src="results/figures/08_monte_carlo_validation.png" width="100%" alt="Monte Carlo estimates with Wilson intervals compared with analytic availability"></a>
</p>

<p align="center"><em>Fig. 5. Monte Carlo estimates and analytic availability.</em> <a href="results/figures/08_monte_carlo_validation.svg">Vector figure</a></p>

<details>
<summary>Independent aperture integral comparison</summary>

<p align="center">
  <a href="results/figures/01_aperture_integral_validation.svg"><img src="results/figures/01_aperture_integral_validation.png" width="100%" alt="Gaussian aperture collection calculated by independent numerical integration methods"></a>
</p>

<p align="center"><em>Fig. 6. Numerical agreement between aperture integration methods.</em> <a href="results/figures/01_aperture_integral_validation.svg">Vector figure</a></p>

</details>

<p align="justify">The version 4.1.0 test suite contains 44 tests. GitHub Actions regenerates the full experiments and compares the 11 numerical tables against the committed reference results, with execution time excluded. SHA-256 hashes check the integrity of the generated artifacts and generating source files. These checks support numerical consistency and reproducibility within the stated model. They do not constitute experimental validation of the optical link.</p>

<p align="center">
  <a href="docs/COMPLEXITY_AND_VERIFICATION.md">Verification methods and computational complexity</a> ·
  <a href="https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions">Verification history</a>
</p>

## Limitations

<p align="justify">The atmospheric coefficients have not been calibrated against local measurements. Weather probabilities, layer independence, optical parameters and the TV radius are assumptions. Turbulence, scintillation, receiver field-of-view effects, detector noise and temporal tracking dynamics are not included.</p>

<p align="justify">Availability in this study refers to the probability of meeting a received-optical-power threshold. It is not measured uptime or bit-error-rate performance. The radiation-fog relation is used as a separate hypothetical sensitivity case and has not been validated for this airborne geometry. The results should therefore be interpreted within the stated assumptions rather than as general receiver design requirements.</p>

## Research outlook

<p align="justify">This work focuses on a single ground-to-air optical link. I would like to learn more about how altitude-dependent atmospheric conditions and platform motion influence pointing errors and the design of multi-layer airborne FSO networks. A possible next step would be to explore altitude selection and link optimization using more realistic atmospheric information.</p>

<p align="justify">I am also interested in connecting the optical collection model with practical receiver characteristics, including field of view, detector sensitivity, bandwidth and noise. This could help extend the study towards communication-level performance and terminal design. Both directions would require further modelling and validation beyond the present work.</p>

## Reproduction

<p align="justify">Open the <a href="https://colab.research.google.com/github/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/blob/main/notebooks/FSO_Link_Design_Colab.ipynb">standalone notebook in Google Colab</a> and select <strong>Runtime → Run all</strong>. The notebook runs on a CPU, generates its own source files, executes the tests and full experiments and exports the project. A Google Drive mount is not required.</p>

<p align="center">
  <a href="https://colab.research.google.com/github/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/blob/main/notebooks/FSO_Link_Design_Colab.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Run the standalone notebook in Google Colab"></a>
</p>

<details>
<summary>Local execution and regression comparison (Linux)</summary>

```bash
python -m pip install -r requirements.txt -r requirements-lock.txt
python -m unittest discover -s tests -v
python build_notebook.py --check
python verify_manifest.py

REF=$(mktemp -d)
cp -r results/tables "$REF/tables"
FAST_MODE=0 python run_study.py
python compare_results.py "$REF/tables" results/tables
python verify_manifest.py
```

<p align="justify">Run <code>python build_notebook.py</code> after editing any embedded source or documentation. Full mode uses 100,000 samples in the largest Monte Carlo runs. See the <a href="UPDATE_GITHUB.md">update instructions</a>.</p>

</details>

| Resource | Contents |
|---|---|
| [src/](src/) | Atmospheric and optical models |
| [run_study.py](run_study.py) | Experiments and figure generation |
| [tests/](tests/) | Mathematical and regression tests |
| [compare_results.py](compare_results.py) | Numerical table comparison |
| [notebooks/](notebooks/) | Standalone Colab notebook |
| [results/](results/README.md) | Figures, tables and metadata |
| [docs/](docs/) | Derivations, technical notes and source mapping |

## References

<ol>
  <li><p align="justify">E. Erdogan et al., “Modeling Atmospheric Attenuation in Vertical FSO Links: An Altitude-Aware Piecewise Framework,” <em>IEEE Vehicular Technology Magazine</em>, 2026. <a href="https://doi.org/10.1109/MVT.2026.3687349">DOI</a> · <a href="https://arxiv.org/html/2604.18207v1">Author manuscript</a>.</p></li>
  <li><p align="justify">M. Al Naboulsi, H. Sizun and F. de Fornel, “Fog attenuation prediction for optical and infrared waves,” <em>Optical Engineering</em>, vol. 43, pp. 319–329, 2004. See the <a href="docs/SOURCE_MAP.md">source map</a> for the coefficient relation, units and applicability.</p></li>
  <li><p align="justify">A. A. Farid and S. Hranilovic, “Outage Capacity Optimization for Free-Space Optical Links with Pointing Errors,” 2007. <a href="https://doi.org/10.1109/JLT.2007.899174">DOI</a>.</p></li>
  <li><p align="justify">M. Elamassie and M. Uysal, “Multi-Layer Airborne FSO Systems: Performance Analysis and Optimization,” 2025. <a href="https://doi.org/10.1109/TCOMM.2024.3471995">DOI</a>.</p></li>
  <li><p align="justify">H. Rahimian and S. Mehrotra, “Frameworks and Results in Distributionally Robust Optimization,” 2022. <a href="https://doi.org/10.5802/ojmo.15">DOI</a>.</p></li>
</ol>

<p align="justify">The <a href="docs/SOURCE_MAP.md">source-to-implementation map</a> records the provenance of the coefficients and equations and identifies the additional assumptions made in this study.</p>

## Citation and license

<p align="justify">See <a href="CITATION.cff">CITATION.cff</a> for the software citation. The original scientific publications should be cited separately when their models are used. The code is distributed under the <a href="LICENSE">MIT License</a>.</p>

<p align="justify">AI tools assisted implementation and review. The author is responsible for the scientific assumptions and findings. Suggestions and corrections are welcome.</p>
