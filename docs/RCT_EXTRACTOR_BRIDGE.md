# RCT Extractor Bridge

## Purpose

Convert `rct-extractor-v2` JSONL results into the `extraction_export.csv`
format used by the DCLNMA raw-ingestion pipeline.

## Target format

The bridge targets the real JSONL shape seen in local extractor outputs under:

- `<extractor_output_dir>/rct-extractor-v2/output/.../results.jsonl`
- `<extractor_output_dir>/rct-extractor-v2/output/.../results_ai_validated.jsonl`

It reads:

- `study_id`
- `status`
- `pdf_path`
- `best_match`
- `top_extractions`

and maps them into `extraction_export.csv`.

## Command

```bash
dclnma bridge-rct-extractor \
  --results-jsonl raw_sources/cardio_hf_sglt2/sample_rct_extractor_results.jsonl \
  --mapping-csv raw_sources/cardio_hf_sglt2/rct_extractor_mapping.csv \
  --out-csv generated/cardio_hf_sglt2/extraction_export.csv
```

## Mapping file

The mapping CSV links extractor `study_id` values to canonical DCLNMA keys:

- `study_id`
- `trial_id`
- `publication_id`
- `endpoint_key`

Optional fields such as `source_id` and `extraction_id` can also be supplied.

## Automatic mapping generation

If the extractor `study_id` embeds a PMID in the form
`rct_trial__<pmid>__...`, you can generate the mapping automatically from the
canonical publication metadata under `data/`:

```bash
dclnma generate-study-mapping \
  --results-jsonl raw_sources/cardio_hf_sglt2/sample_rct_extractor_results.jsonl \
  --data-root data \
  --out-csv generated/cardio_hf_sglt2/auto_mapping.csv
```

## Typical workflow

1. Run `rct-extractor-v2` on a PDF set and collect the JSONL output.
2. Generate the mapping CSV from canonical metadata, or prepare it manually.
3. Run `bridge-rct-extractor` to create `extraction_export.csv`.
4. Run `build-canonical-dataset` on the raw source directory.
