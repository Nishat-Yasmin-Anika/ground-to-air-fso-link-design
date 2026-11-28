# Updating the FSO Research Repository

## Version 4.1.0

This refinement preserves the v4 scientific model
and numerical findings while improving validation,
documentation and reproducibility.

## Install dependencies

    python -m pip install -r requirements.txt

For the pinned reference environment:

    python -m pip install -r requirements.txt -r requirements-lock.txt

## Run automated verification

    python -m unittest discover -s tests -v
    python verify_manifest.py
    python build_notebook.py --check

## Numerical regression verification

Preserve reference tables before generating new results.

The following commands are for Linux or Google Colab:

    REF=$(mktemp -d)
    cp -r results/tables "$REF/tables"
    FAST_MODE=0 python run_study.py
    python compare_results.py "$REF/tables" results/tables
    python verify_manifest.py

Investigate numerical discrepancies before accepting
new reference results.

## Notebook regeneration

After modifying canonical source or documentation:

    python build_notebook.py
    python build_notebook.py --check

Do not edit the generated notebook independently.

## GitHub update

Extract the generated ZIP and upload its contents
to the existing repository root.

Do not upload the ZIP itself or an enclosing folder.
Preserve the Git history and original attribution.

## Scientific scope

The project demonstrates conditional optical-power
availability and robust receiver aperture design.

No experimental calibration, communication-level
BER validation or publication-level novelty is claimed.

Further physical modeling remains future research.
