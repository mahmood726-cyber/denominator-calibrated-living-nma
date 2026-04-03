# Denominator-Calibrated Living Network Meta-Analysis

This repository is a starter scaffold for an evidence-synthesis project that
combines registry denominators, publication linkage, PDF extraction
provenance, multi-witness modeling, and conservative arbitration in a living
network meta-analysis workflow.

## Project goal

The project aims to estimate treatment effects under incomplete evidence while
explicitly modeling:

- silent trials
- endpoint missingness
- publication missingness
- extraction uncertainty
- model disagreement
- non-proportional hazards when survival evidence requires it

The intended output is a calibrated decision capsule rather than only a pooled
effect estimate.

## Current scope

This scaffold includes:

- a project spec in [PROJECT_SPEC.md](PROJECT_SPEC.md)
- a milestone plan in [ROADMAP.md](ROADMAP.md)
- simulation and backtesting design docs under `docs/`
- example JSON configs under `configs/`
- canonical cardio datasets under `data/cardio_hf_sglt2/` and `data/cardio_af_doac/`
- raw cardio source exports under `raw_sources/`
- an `rct-extractor-v2` bridge for `extraction_export.csv` generation
- a minimal Python package under `src/dclnma/`
- smoke tests under `tests/`

## Quick start

Create a virtual environment, then run the package in editable mode:

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

Inspect an example config:

```bash
dclnma describe-config --config configs/simulation_baseline.json
```

Inspect the cardio example dataset:

```bash
dclnma describe-config --config configs/cardio_hf_sglt2_example.json
```

Inspect the second cardio example dataset:

```bash
dclnma describe-config --config configs/cardio_af_doac_example.json
```

Build a demo decision capsule:

```bash
dclnma demo-capsule --effect -0.12 --se 0.04
```

Build the linked cardio capsule from real seeded records:

```bash
dclnma build-cardio-capsule --config configs/cardio_hf_sglt2_example.json
```

Build the DOAC/AF capsule:

```bash
dclnma build-cardio-capsule --config configs/cardio_af_doac_example.json
```

Rebuild a canonical dataset from raw exports:

```bash
dclnma build-canonical-dataset --raw-dir raw_sources/cardio_hf_sglt2 --out-dir generated/cardio_hf_sglt2
```

Bridge `rct-extractor-v2` JSONL into an extraction export:

```bash
dclnma bridge-rct-extractor --results-jsonl raw_sources/cardio_hf_sglt2/sample_rct_extractor_results.jsonl --mapping-csv raw_sources/cardio_hf_sglt2/rct_extractor_mapping.csv --out-csv generated/cardio_hf_sglt2/extraction_export.csv
```

Generate a mapping CSV automatically from canonical publication metadata:

```bash
dclnma generate-study-mapping --results-jsonl raw_sources/cardio_hf_sglt2/sample_rct_extractor_results.jsonl --data-root data --out-csv generated/cardio_hf_sglt2/auto_mapping.csv
```

## Repository layout

```text
Denominator_Calibrated_Living_NMA/
  PROJECT_SPEC.md
  README.md
  ROADMAP.md
  pyproject.toml
  configs/
  data/
  docs/
  raw_sources/
  src/dclnma/
  tests/
```

## Recommended first build sequence

1. Finalize the initial therapeutic area and endpoint definitions.
2. Expand the cardio dataset beyond the seeded heart-failure and DOAC/AF examples.
3. Replace the heuristic witness adjustments with full estimators.
4. Lock the simulation suite and historical backtesting protocol.
5. Generate a reproducibility bundle for the methods paper.

## Design principle

Evidence incompleteness is treated as part of the data-generating process, not
as a discussion-section disclaimer.
