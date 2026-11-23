# Source-to-implementation map

## [S1] Atmospheric model: professor and collaborators

E. Erdogan, M. Elamassie, I. Altunbas, G. K. Kurt, M. Uysal and H. Yanikomeroglu. *Modeling Atmospheric Attenuation in Vertical FSO Links: An Altitude-Aware Piecewise Framework*. IEEE Vehicular Technology Magazine, 2026. DOI: https://doi.org/10.1109/MVT.2026.3687349. Free author manuscript: https://arxiv.org/pdf/2604.18207 .

**Actually used:** Section III piecewise atmospheric exponential, Table I (1550 nm coefficient glossary) and Table II (five scenarios, geometric layers, conditional state weights), implemented in `src/atmosphere.py`. Main figures use `exp(-Q)` to trace equations; comparative dimensional audit retains `10^(-Q/10)` because coefficient tables are labeled dB/km. **The source itself is not experimentally reproduced here; there are no MODTRAN outputs or source figure digitalizations.**

The source's occurrence weights are often described as long-term fractions of time within an atmospheric slab. Treating independent state draws from these weights as a finite probability mixture is an explicit extension and independence assumption, not a verified joint atmospheric distribution.

## [S2] Multilayer airborne design: professor and collaborator

M. Elamassie and M. Uysal, *Multi-Layer Airborne FSO Systems: Performance Analysis and Optimization*, IEEE Transactions on Communications, vol. 73, no. 4, 2025, pp. 2522–2537. DOI https://doi.org/10.1109/TCOMM.2024.3471995 . Official professor list: https://faculty.ozyegin.edu.tr/mohammedelamassie/publications/ .

**Conceptual motivation:** combine atmospheric, geometry and pointing effects and ask a design question. **Not reproduced:** their multi-hop topology, random HAPS motion, bit error-rate formulas or power allocation.

## [S3] Active research group

TÜBİTAK 1001 — Project 125E806, Prof. M. Elamassie, Aug 2026–Aug 2029: https://faculty.ozyegin.edu.tr/mohammedelamassie/tubitak-1001-project-125e806/ .

**Fit:** atmospheric modeling, optical link reliability, pointing errors and optimization under changing conditions. **Do not present this project as part of the funded research.**

## [S4] Standard Gaussian FSO pointing model

A representative open-access discussion of Gaussian receiver-plane irradiance, finite circular aperture and zero-mean pointing jitter: https://pmc.ncbi.nlm.nih.gov/articles/PMC9370906/ . Our **exact aperture integral** is derived for an isotropic 2D Gaussian irradiance distribution rather than adopting the commonly used equivalent-beamwidth approximation.

**Numerical formula:** if receiver-plane irradiance is normalized `I(x,y)=(2/pi/w^2)*exp(-2||x-r||²/w²)`, then the integrated power over a circular receiver radius `a` is `ncx2.cdf((2a/w)^2, df=2, nc=(2r/w)^2)`. This follows because the Gaussian spot corresponds to a bivariate Gaussian random point with coordinate variance `w²/4`. Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ncx2.html . We independently verify it via radial numerical integration with a modified Bessel function.

## [S5] Distributionally robust optimization (DRO)

H. Rahimian and S. Mehrotra, *Frameworks and Results in Distributionally Robust Optimization*, Open Journal of Mathematical Optimization, 2022: https://ojmo.centre-mersenne.org/item/10.5802/ojmo.15.pdf . This is a standard research framework, including total variation (TV) ambiguity sets. Our five-scenario worst-case objective is a linear program; it can be solved by greedy probability-mass transfer, which we independently cross-check against `scipy.optimize.linprog`.

## [S6] Background atmospheric reference

ITU-R Recommendation P.835-7, *Reference Standard Atmospheres*: https://www.itu.int/rec/R-REC-P.835-7-202408-I/en . Atmospheric profiles are contextual background only; no measured local weather distribution was downloaded or computed from this standard.

## Explicitly *not* sourced from S1–S6

The cross-scenario prior `(clear=.76, pollution=.10, fog=.07, rain=.04, snow=.03)`, the TV radius `rho=.04`, transmitter optical power, receiver sensitivity threshold, beam divergence, 2D pointing jitter and the 92% target are **illustrative choices defined by this study**. They are not measurements, professor-provided experimental settings or estimates from ERA5.

## [S7] Independent technical standard used as checklist only

ITU-R Recommendation P.1814-1 (Sept. 2025), *Prediction methods required for the design of terrestrial free-space optical links*: https://www.itu.int/rec/R-REC-P.1814-1-202509-I/en . The recommended received-power margin distinguishes atmospheric, geometric, scintillation and system losses. **This project omits scintillation and measured receiver sensitivity; it is not standards-compliant link budgeting.**

## Related literature and software context

Related research includes H. Safi, A. Dargahi and J. Cheng, *Analytical Channel Model and Link Design Optimization for Ground-to-HAP Free-Space Optical Communications* (2020), and M. Polnik, A. Arulselvan and A. Riccardi, *Scheduling Space-to-Ground Optical Communication Under Cloud Cover Uncertainty* (2021). These provide relevant antecedents for analytical link design and robust weather decisions. No code from external repositories is included in this project. The principal implementation is self-contained and attributed above.
