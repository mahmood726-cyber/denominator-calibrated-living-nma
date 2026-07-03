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

Describe the treatment network and check connectivity (a network meta-analysis
requires a single connected component):

```bash
dclnma describe-network --config configs/cardio_hf_sglt2_example.json
```

Verify the living-update pool equals a from-scratch batch recompute for a config
(exit code 0 = equivalent):

```bash
dclnma living-benchmark --config configs/cardio_af_doac_example.json
```

## Living update and network connectivity

Because this is a *living* network meta-analysis, the pooled estimate must be
updatable as new trials arrive without silently drifting away from what a full
recompute would give.

- `dclnma.data.network` builds the treatment-comparison graph, computes its
  connected components, and exposes `require_connected_network`, which refuses
  to proceed on a **disconnected** (or empty) network — the standard NMA
  precondition of checking connectivity first.
- `dclnma.living` maintains an O(1)-per-record inverse-variance accumulator
  (`LivingPoolState`) and provides `assert_living_equivalence`, which pools the
  same records incrementally and in batch and asserts the two agree to numerical
  precision. `order_invariance_report` confirms the pooled estimate does not
  depend on the order trials arrive in.

The incremental path reuses `inverse_variance_pool`, so the living and batch
estimates are the same arithmetic — no pooled numbers change.

### Reproducible benchmark

`benchmarks/living_equivalence_benchmark.py` runs the living-vs-batch
equivalence check on every seeded cardio dataset and prints a table plus the
living trajectory. Run it from the repository root:

```bash
python benchmarks/living_equivalence_benchmark.py
```

Expected result: every dataset reports `PASS` with an `effect_gap` at
floating-point epsilon (≈1e-16), and the script exits 0. It doubles as a CI gate
for the living-update correctness contract.

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
