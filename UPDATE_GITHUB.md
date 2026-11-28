# Merge v4 into the existing repository

1. Download and extract the GitHub update ZIP. It contains repository-relative paths; do not upload an extra wrapper folder. Preserve the existing `.git` folder, LICENSE, CITATION.cff, assets and author attribution.
2. Replace README.md, `docs/`, `src/`, `tests/`, `run_study.py`, `requirements.txt`, `results/`, and `notebooks/FSO_Link_Design_Colab.ipynb` with the supplied versions. Add `build_notebook.py`, `verify_manifest.py`, `requirements-lock.txt`, `UPDATE_GITHUB.md` and the workflow. Delete obsolete result files before replacing `results/`; do not mix v3 figures with v4 tables.
3. Run the tests and verify the supplied manifest before committing. To modify models later, edit the canonical Python source; regenerate the notebook using `python build_notebook.py`, run `python run_study.py` and verify the manifest. Never hand-edit a generated CSV or plot.
4. Review `docs/SOURCE_MAP.md` and all model assumptions. Commit only after the repository owner accepts the scientific scope; no physical calibration has been established.

Example commands from an existing local clone (after merging files):

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python verify_manifest.py
python build_notebook.py --check
git status
git add README.md UPDATE_GITHUB.md docs src tests results notebooks run_study.py requirements.txt requirements-lock.txt verify_manifest.py build_notebook.py .github/workflows/python-tests.yml
git commit -m "Audit FSO assumptions, fix solver, expand reproducibility checks"
git push
```

The standalone Colab notebook is independently usable: Run all writes the project to a dedicated subdirectory, runs tests and experiments, and exports a merge ZIP. The GitHub repository has not been modified remotely by this delivery.
