# Complexity, named algorithms, verification and performance

## Algorithms and mathematical identities

| Task | Method | Why |
|---|---|---|
| Layered optical attenuation | Beer–Lambert law, 2026 published piecewise coefficients | Source-compatible atmospheric baseline (with unit audit) |
| Circular-aperture capture | Noncentral chi-squared CDF (Marcum-Q equivalent) | Exact 2D Gaussian aperture integral, rather than disk-sampling MC |
| Mean aperture collection | Convolution of 2D Gaussian random variables | Independent closed-form check |
| Pointing jitter | Bivariate Gaussian displacement, Rayleigh radial law | Exact conditional probability of captured-power threshold |
| Root solver | Brent–Dekker bracketed scalar root finding | Stable inversion of monotone aperture overlap and minimum aperture |
| Scenario probabilities | Exact finite-state enumeration | Deterministic result for small state spaces |
| Uncertain weather mix | TV-distance distributionally robust optimization | Explicit worst-case chance constraint |
| Cross-check of TV solution | HiGHS LP via SciPy `linprog` | Independent solver validation |
| Stochastic verification | NumPy PCG64, independent MC weather and x/y displacements | Tests full simulation pathway independently of derived CDF |
| Confidence interval | Wilson score interval, 95% nominal coverage | Avoids naive normal-approximation interval at high availability |
| Numerical quadrature check | SciPy adaptive quadrature, scaled modified Bessel `i0e` | Independent exact geometry computation |

## Formal complexity

Let **S** be the number of weather scenarios (5), **L** the number of active atmospheric layers per scenario, **K** the maximum number of categorical joint states per scenario (product of per-layer counts), **B** the number of numerical iterations to solve one radial threshold and **M** the number of tested receiver apertures, with SciPy CDF treated as a numerical primitive whose internal cost depends on its arguments.

- Atmospheric finite-state enumeration: `O(S * K * L)` operations, `O(K)` transient memory per scenario.
- A conditional availability evaluation at a fixed receiver radius/jitter: at most `O(S * K * B)` noncentral chi-squared CDF evaluations plus categorical arithmetic.
- TV worst-case mass-transfer sort: `O(S log S)` time and `O(S)` space, negligible with S=5. Independent LP check has polynomial solver cost; it is **not** used inside the main sweep.
- Minimum-aperture design via bracketed root solving, with **D** outer iterations: `O(D * (S*K*B + S log S))` time, `O(K+S)` temporary memory.
- Vectorized Monte Carlo with N draws and L active slabs: `O(N*L)` total random/array operations and `O(N)` working memory. MC is used for verification only; the exact solver determines the main plot and optimization.
- Saving 10 pairs of plot files incurs rendering and disk I/O that dominate end-to-end runtime at these problem sizes; runtime is **not** a proxy for scientific validity.

## Runtime and output artifacts

`results/metadata/runtime.json` stores a local wall-clock benchmark from the producing run and whether FAST_MODE was used. `results/metadata/environment.json` lists installed versions. `results/metadata/manifest.json` lists every generated file's size in bytes and SHA-256 checksum, permitting the professor to audit artifact provenance. Actual Colab execution time and peak memory may differ.

**FAST_MODE=1:** 20,000 draws in the largest MC check. **FAST_MODE=0:** 100,000. Every other result is unchanged. Neither requires a GPU.

## Verification versus validation

24 automated tests check physical/mathematical invariants, analytic/quadrature agreement, independent MC agreement, weather marginalization and the greedy-vs-LP optimum. Passing these tests is **software/numerical verification**. It is *not* external atmospheric or detector validation. The published article itself reports MODTRAN comparisons; this portfolio does not recreate them.
