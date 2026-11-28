# Atmospheric-Model Sensitivity in Ground-to-Air FSO Receiver Design

<p align="center">
  <b>Nishat Yasmin Anika</b><br>
  Department of Electronics and Communication Engineering<br>
  Khulna University of Engineering &amp; Technology (KUET), Bangladesh
</p>

<p align="center">
  <a href="https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions/workflows/python-tests.yml"><img src="https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions/workflows/python-tests.yml/badge.svg" alt="Numerical verification"></a>
  <a href="https://colab.research.google.com/github/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/blob/main/notebooks/FSO_Link_Design_Colab.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#abstract">Abstract</a> · <a href="#model-and-method">Model</a> · <a href="#results-and-discussion">Results</a> · <a href="#numerical-verification">Verification</a> · <a href="#reproduction">Reproduction</a> · <a href="#references">References</a>
</p>

<p align="center"><img src="assets/cover.svg" width="100%" alt="Ground-to-air free-space optical link"></p>

## Abstract

<p align="justify">The receiver aperture required for a ground-to-air free-space optical (FSO) link depends on atmospheric attenuation, beam spreading and pointing errors. This study examines how different interpretations of published atmospheric attenuation coefficients affect the aperture needed to meet a prescribed received-power availability. A layered atmospheric model is combined with exact integration of a displaced Gaussian beam over a circular receiver. The weather-scenario probabilities are allowed to vary within a total-variation (TV) ambiguity set. For a 3 km vertical link with a 92% availability target and 15 µrad per-axis pointing jitter, the nominal receiver diameter is 9.47 cm under literal power-decibel conversion and 21.95 cm under the equation-as-printed exponential interpretation. At a TV radius of 0.08, the latter cannot attain the target at any finite aperture. Independent quadrature, linear programming and Monte Carlo simulations are used to check the calculations. The reported values are conditional on the assumed optical parameters and weather distributions.</p>

**Keywords:** Free-space optical communication, atmospheric attenuation, Gaussian beams, pointing errors, receiver aperture, distributionally robust optimization.

## Research context

<p align="justify">Erdogan et al. [1] describe altitude-dependent attenuation using horizontal atmospheric layers with scenario-specific coefficients. Their tables label the coefficients in dB/km, while the transmittance equation uses a natural exponential. The two readings of the printed coefficients produce different power transmittances. This work retains them as separate cases and examines their effect on receiver sizing. A second comparison uses the clear-weather description in the text of the same source, and a third replaces the fog coefficients with a radiation-fog relation [2]. The original coefficient generation and atmospheric calibration are outside the scope of this study. Earlier work on pointing errors [3] and multilayer airborne optical links [4] provides the optical-link context. The probability ambiguity set follows the total-variation formulation used in distributionally robust optimization [5].</p>

## Model and method

<p align="center"><img src="assets/method.svg" width="100%" alt="Atmospheric layers, optical collection and availability calculation"></p>
<p align="center"><em>Fig. 1. Calculation sequence for the receiver design problem.</em></p>

<p align="justify">For receiver altitude H and zenith angle θ, the length of the link in the flat-layer approximation is H sec θ. Within each atmospheric scenario, the path crosses a finite set of categorical layer states. For a particular state combination, the integrated printed coefficient is Q. The primary model uses the power-decibel interpretation and the alternative uses the exponential form printed in [1]:</p>

$$
Q=\sum_j c_j d_j,\qquad T_{\mathrm{dB}}=10^{-Q/10},\qquad T_{\mathrm{exp}}=e^{-Q}.
$$

<p align="justify">The received optical power is the product of the transmitted power, optical efficiency, atmospheric transmittance and the fraction of the Gaussian beam collected by the receiver. For a circular aperture of radius a, beam radius w and radial displacement r, the collection fraction can be expressed as a noncentral chi-square cumulative distribution function.</p>

$$
P_r=P_t\eta T G(a,w,r),\qquad G(a,w,r)=F_{\chi'^2_2}\left(\frac{4a^2}{w^2};\frac{4r^2}{w^2}\right).
$$

<p align="justify">Independent zero-mean Gaussian pointing displacements give a Rayleigh distribution for the radial displacement. For each atmospheric state, the maximum displacement compatible with the power threshold is found numerically. The resulting conditional success probabilities are averaged over the layer states to obtain the availability Aᵢ for each weather scenario. For nominal scenario probabilities p and an alternative distribution q, the aperture design problem is</p>

$$
\min_{a\in[0.025,\,0.50]\,\mathrm{m}} a\quad\text{subject to}\quad \min_{\boldsymbol q\in\mathcal U_\rho}\sum_i q_i A_i(a)\geq A_{\mathrm{target}},
$$

$$
\mathcal U_\rho=\left\{\boldsymbol q\geq0:\sum_i q_i=1,\;\frac12\sum_i |q_i-p_i|\leq\rho\right\}.
$$

<p align="justify">The inner minimization transfers probability from scenarios with higher availability to those with lower availability. The outer minimization uses bisection because availability is nondecreasing with aperture radius. An atmospheric feasibility ceiling is calculated separately to distinguish an insufficient aperture search interval from a target that cannot be met by any finite aperture.</p>

The full derivations and implementation mapping are in the [mathematical supplement](docs/MATHEMATICAL_DERIVATIONS.md) and [technical note](docs/TECHNICAL_NOTE.md).

<details>
<summary>Reference simulation parameters</summary>

| Quantity | Assumed value |
|---|---:|
| Optical wavelength | 1550 nm |
| Receiver altitude | 3 km |
| Zenith angle | 0° |
| Transmitter optical power | 50 mW |
| Optical efficiency | 0.70 |
| Beam waist radius | 25 mm |
| Divergence half-angle | 55 µrad |
| Per-axis angular jitter (standard deviation) | 15 µrad |
| Received-power threshold | 2 mW |
| Availability target | 0.92 |
| Reference TV radius | 0.04 |

The nominal probabilities of clear weather, pollution, fog, rain and snow are 0.76, 0.10, 0.07, 0.04 and 0.03, respectively. The probabilities and optical parameters are illustrative.

</details>

## Results and discussion

<p align="justify">Table 1 gives the minimum receiver diameter for the reference link. The target is a 92% probability of meeting or exceeding the 2 mW received-power threshold.</p>

<p align="center"><em>Table 1. Minimum receiver diameter (cm) for a 92% availability target.</em></p>

| Atmospheric case | Nominal (ρ = 0) | ρ = 0.04 | ρ = 0.08 |
|---|---:|---:|---:|
| Table II, literal dB/km | 9.47 | 11.82 | 13.62 |
| Table II, exponential interpretation | 21.95 | 27.01 | Infeasible |
| Clear-weather prose alternative | 9.42 | 11.75 | 13.62 |
| Radiation-fog stress case | 15.65 | Infeasible | Infeasible |

<p align="justify">With the literal dB/km interpretation, increasing ρ from zero to 0.04 raises the required diameter from 9.47 to 11.82 cm. For the exponential interpretation, the same change raises it from 21.95 to 27.01 cm. At ρ = 0.08, the atmospheric ceiling of the exponential case is 89.2%, below the specified 92% target. Enlarging the receiver cannot recover power that has already been lost in the atmosphere. The radiation-fog case reaches a ceiling of 89% at ρ = 0.04 and is therefore also infeasible at that target.</p>

<p align="center"><a href="results/figures/11_model_and_target_sensitivity.svg"><img src="results/figures/11_model_and_target_sensitivity.png" width="95%" alt="Receiver diameter and feasibility for alternative atmospheric models and availability targets"></a></p>
<p align="center"><em>Fig. 2. Aperture requirements across atmospheric cases and availability targets. Select the figure for the vector version.</em></p>

<p align="justify">The results in Table 1 isolate the consequences of changing the atmospheric assumptions while holding the remaining link parameters fixed. They do not resolve which coefficient interpretation is physically correct. The separate clear-weather and radiation-fog cases show how changes to individual atmospheric layers affect the same design problem.</p>

<details>
<summary>Pointing jitter and aperture sensitivity</summary>

<p align="center"><a href="results/figures/04_minimum_aperture_frontier.svg"><img src="results/figures/04_minimum_aperture_frontier.png" width="95%" alt="Minimum aperture diameter versus pointing jitter"></a></p>
<p align="center"><em>Fig. 3. Aperture requirements as a function of per-axis pointing jitter.</em></p>

<p align="center"><a href="results/figures/03_availability_vs_aperture.svg"><img src="results/figures/03_availability_vs_aperture.png" width="95%" alt="Availability as a function of aperture size"></a></p>
<p align="center"><em>Fig. 4. Received-power availability versus receiver aperture.</em></p>

</details>

All [12 figures, 11 numerical tables and simulation metadata](results/README.md) are available. The values in Table 1 are taken from [the model and target sensitivity table](results/tables/09_model_and_target_sensitivity.csv).

## Numerical verification

<p align="justify">The Gaussian aperture expression is checked by independent Bessel and Cartesian quadrature. A separate linear program checks the probability-transfer solution. Monte Carlo simulations sample atmospheric states and Gaussian pointing displacements directly, rather than drawing successes from the analytic availability. Wilson intervals describe the sampling uncertainty of the simulated success proportions.</p>

<p align="center"><a href="results/figures/08_monte_carlo_validation.svg"><img src="results/figures/08_monte_carlo_validation.png" width="85%" alt="Monte Carlo comparison with exact availability"></a></p>
<p align="center"><em>Fig. 5. Monte Carlo estimates and analytic received-power availability.</em></p>

<p align="justify">Version 4.1.0 contains 44 automated tests. The continuous integration workflow also regenerates the full experiments and compares all 11 CSV tables against the committed results, excluding execution time. File hashes check the integrity of the generated artifacts. These tests assess numerical agreement within the model.</p>

<details>
<summary>Independent aperture integral comparison</summary>

<p align="center"><a href="results/figures/01_aperture_integral_validation.svg"><img src="results/figures/01_aperture_integral_validation.png" width="85%" alt="Comparison of independent Gaussian aperture integration methods"></a></p>
<p align="center"><em>Fig. 6. Numerical verification of the circular-aperture integral.</em></p>

</details>

[Verification methods and computational complexity](docs/COMPLEXITY_AND_VERIFICATION.md) · [GitHub Actions](https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/actions)

## Limitations

<p align="justify">The atmospheric coefficients have not been calibrated against local weather observations. Layer-state independence and the nominal weather probabilities are assumptions, and the TV radius is a sensitivity parameter. The Gaussian beam is an equivalent intensity profile with assumed divergence and waist. The model omits turbulence, scintillation, receiver field-of-view effects, photodetector noise and temporal pointing dynamics. Availability denotes the probability that collected optical power meets or exceeds a threshold. No bit-error rate or measured link uptime is reported. The radiation-fog relation is used only as a separate coefficient sensitivity case. Experimental verification of these assumptions and receiver specifications would be required before applying the design to hardware.</p>

## Reproduction

[Open the standalone notebook in Google Colab](https://colab.research.google.com/github/Nishat-Yasmin-Anika/ground-to-air-fso-link-design/blob/main/notebooks/FSO_Link_Design_Colab.ipynb) and select **Runtime → Run all**. The notebook uses CPU computation, creates the source files, runs the tests and full experiments and exports the results. No Google Drive mount is needed.

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

Use `python build_notebook.py` after editing a canonical file. Full mode uses 100,000 samples in the largest Monte Carlo runs. See [update instructions](UPDATE_GITHUB.md) for the notebook and repository workflow.

</details>

| Resource | Description |
|---|---|
| [src/](src/) | Atmospheric and optical link models |
| [run_study.py](run_study.py) | Numerical experiments and figures |
| [tests/](tests/) | Mathematical and regression tests |
| [compare_results.py](compare_results.py) | Numerical table comparison |
| [notebooks/](notebooks/) | Standalone research notebook |
| [results/](results/README.md) | Figures, tables and run metadata |
| [docs/](docs/) | Derivations, source mapping and technical notes |

## References

1. E. Erdogan et al., “Modeling Atmospheric Attenuation in Vertical FSO Links: An Altitude-Aware Piecewise Framework,” *IEEE Vehicular Technology Magazine*, 2026. [DOI](https://doi.org/10.1109/MVT.2026.3687349) · [Author manuscript](https://arxiv.org/html/2604.18207v1).
2. M. Al Naboulsi, H. Sizun and F. de Fornel, “Fog attenuation prediction for optical and infrared waves,” *Optical Engineering*, vol. 43, pp. 319–329, 2004. The coefficient relation, units and validity range used here are documented in the [source map](docs/SOURCE_MAP.md).
3. A. A. Farid and S. Hranilovic, “Outage Capacity Optimization for Free-Space Optical Links with Pointing Errors,” 2007. [DOI](https://doi.org/10.1109/JLT.2007.899174).
4. M. Elamassie and M. Uysal, “Multi-Layer Airborne FSO Systems: Performance Analysis and Optimization,” 2025. [DOI](https://doi.org/10.1109/TCOMM.2024.3471995).
5. H. Rahimian and S. Mehrotra, “Frameworks and Results in Distributionally Robust Optimization,” 2022. [DOI](https://doi.org/10.5802/ojmo.15).

The [source-to-implementation map](docs/SOURCE_MAP.md) identifies the equations and data adopted from these references and the assumptions added in this study.

## Citation and license

Software citation metadata are available in [CITATION.cff](CITATION.cff). Cite the relevant scientific publications separately when using their models. The code is distributed under the [MIT License](LICENSE).

AI tools assisted implementation and review. The author is responsible for the scientific assumptions and findings.
