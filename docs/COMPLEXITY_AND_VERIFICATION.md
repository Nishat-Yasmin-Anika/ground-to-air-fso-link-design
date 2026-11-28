# Complexity and verification

Let S be weather scenarios, K the maximum number of joint atmospheric slab states, L the number of layers, B inner inverse-overlap iterations and D outer aperture bisections. Enumeration O(SKL), conditional probability O(SKB) CDF evaluations, TV mass transfer O(S log S), aperture search O(D(SKB+S log S)). MC O(NL) random draws plus N numerical CDF evaluations, O(N) working memory. Exact analytic results do not depend on MC sample count.

Run `python -m unittest discover -s tests -v` (44 automated mathematical, numerical and regression tests), `FAST_MODE=0 python run_study.py` and `python verify_manifest.py`. The new multi-case MC experiment uses three fixed seeds in four cases and compares both probability and analytic mean power using conservative five-standard-error diagnostic tolerances. Wilson intervals are individual sampling intervals, not model uncertainty. `results/metadata/manifest.json` contains SHA-256 fingerprints of the generating source and results (manifest itself excluded). A successful check shows integrity, not empirical validity. Figures are numerical outputs; SVG metadata and runtime can vary by environment. The notebook is built from canonical sources and checked by `python build_notebook.py --check`.


## Numerical Regression Verification

Version 4.1 introduces automated comparison of regenerated
CSV tables against previously committed reference tables.

The verification checks:

- All 11 expected CSV filenames.
- Column names and row counts.
- Numerical values with relative tolerance 1e-8 and
  absolute tolerance 1e-9.
- Exact sample counts, random seeds and feasibility statuses.
- Consistency of missing and NaN values.

Execution timings are excluded from comparison.

The GitHub Actions workflow preserves the committed
reference tables before running the full experiments
with FAST_MODE=0.

Any unexpected numerical discrepancy causes the
verification workflow to fail.

The reference scientific dependency versions are recorded
in requirements-lock.txt. The environment that actually
generated the committed results is recorded separately
in results/metadata/environment.json.

Changes in numerical libraries or random sampling
implementations may cause regression failures and must
be investigated before accepting new reference results.

Regression agreement establishes computational
reproducibility, not independent physical validation.
