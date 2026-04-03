# Cardio Data Schema

## Purpose

Define the canonical record types for the first cardio ingestion pipeline.

## Entities

### `RegistryRecord`

One row per trial-outcome registration target.

Required keys:

- `domain`
- `trial_id`
- `registry_id`
- `short_name`
- `condition`
- `population`
- `treatment`
- `comparator`
- `outcome_key`
- `outcome_label`
- `follow_up_months`
- `planned_sample_size`
- `randomized_sample_size`

### `PublicationRecord`

One row per linked publication-outcome report.

Required keys:

- `publication_id`
- `trial_id`
- `pmid`
- `title`
- `journal`
- `year`
- `publication_date`
- `endpoint_key`
- `endpoint_reported`

### `ExtractionRecord`

One row per extracted treatment-effect statement.

Required keys:

- `extraction_id`
- `publication_id`
- `trial_id`
- `endpoint_key`
- `effect_measure`
- `reported_effect`
- `reported_ci_lower`
- `reported_ci_upper`
- `log_effect`
- `log_ci_lower`
- `log_ci_upper`
- `standard_error`
- `provenance`

### `Provenance`

Nested object used by `ExtractionRecord`.

Required keys:

- `source_id`
- `source_type`
- `locator`

Recommended keys:

- `confidence`
- `source_file`
- `quote`
- `parser_name`

## Linkage logic

`trial_id` is the primary join key across registry, publication, and extraction
layers. `endpoint_key` is the secondary filter used to isolate one estimand at
a time.

## Design note

The canonical extraction layer stores both reported HR-scale values and
derived log-scale values so pooling and human review can coexist without
recomputing the transformation each time.

## Current seeded datasets

- `data/cardio_hf_sglt2/` for heart failure SGLT2 inhibitor trials
- `data/cardio_af_doac/` for anticoagulation trials in atrial fibrillation
