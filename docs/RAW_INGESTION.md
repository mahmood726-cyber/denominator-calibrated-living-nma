# Raw Ingestion

## Purpose

Convert simple CSV exports into the canonical DCLNMA dataset format.

## Expected files

Each raw source directory should contain:

- `registry_export.csv`
- `publication_export.csv`
- `extraction_export.csv`

## Command

```bash
dclnma build-canonical-dataset --raw-dir raw_sources/cardio_hf_sglt2 --out-dir generated/cardio_hf_sglt2
```

## Transformation behavior

- Registry and publication rows are normalized into typed canonical records.
- Extraction rows are transformed from reported HR-scale values into:
  - `log_effect`
  - `log_ci_lower`
  - `log_ci_upper`
  - `standard_error`
- Provenance columns are wrapped into a nested `provenance` object.

## Current raw source examples

- `raw_sources/cardio_hf_sglt2/`
- `raw_sources/cardio_af_doac/`

## Optional bridge from RCT Extractor

If your extraction layer comes from `rct-extractor-v2`, use the bridge first to
create `extraction_export.csv`, then run `build-canonical-dataset`.
