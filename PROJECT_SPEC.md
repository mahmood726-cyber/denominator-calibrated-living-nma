# Denominator-Calibrated Living Network Meta-Analysis

## Working title

Denominator-Calibrated Living Network Meta-Analysis: an end-to-end framework for extraction-aware, selection-aware, and regret-calibrated evidence synthesis

## One-sentence concept

Build a network meta-analysis system that combines trial registries, publications, PDF-extracted outcomes, and conservative multi-model arbitration to estimate treatment effects while explicitly modeling missing trials, missing endpoints, extraction uncertainty, and model disagreement.

## Why this is worth doing

Most meta-analysis pipelines still behave as if the published literature is the full data-generating process. Your recent projects already cover the missing parts separately: effect extraction, registry denominators, bias correction, advanced NMA, non-proportional hazards, audit trails, and decision arbitration. The novel step is to join those components into one calibrated system and validate whether it reduces reversals and false reassurance when evidence is incomplete.

## Primary aims

1. Estimate treatment effects in a living NMA while adjusting for publication missingness, endpoint missingness, and silent-trial bias using registry denominators.
2. Propagate extraction uncertainty from PDF-level effect recovery into downstream treatment estimates.
3. Arbitrate across multiple witnesses rather than trusting a single model: classic NMA, denominator-adjusted NMA, selection-adjusted NMA, and survival-aware NMA where applicable.
4. Evaluate the system on calibration and decision quality, not only pooled effects.

## Core methodological idea

Each treatment contrast or network node gets four evidence witnesses:

- `Classic witness`: publication-only pairwise/NMA estimate.
- `Denominator witness`: registry denominator plus silent-shift model.
- `Selection witness`: publication/endpoint missingness-adjusted estimate.
- `Extraction witness`: estimate after propagating uncertainty from automated PDF extraction confidence and provenance quality.

These witnesses feed a conservative arbitration layer:

- If witnesses agree, keep the tighter calibrated interval.
- If witnesses disagree, inflate uncertainty and downgrade decisions.
- If survival evidence shows non-proportional hazards, switch from a single pooled HR to interval-specific treatment effects.

The primary output is not just `theta_hat`; it is a decision object:

- pooled effect or interval-specific effect
- calibrated uncertainty interval
- reversal risk
- decision regret score
- evidence integrity profile

## Proposed workflow

1. Ingest registry records and publication metadata.
2. Extract reported effects from PDFs or tables with provenance traces.
3. Link publications to registry denominator counts and endpoint availability.
4. Build a living evidence graph for treatments, outcomes, timepoints, and designs.
5. Fit witness models.
6. Run conservative arbitration.
7. Emit a signed evidence capsule and updateable dashboard output.

## Validation plan

### Simulation

- Generate trial networks with controllable publication bias, endpoint suppression, and extraction noise.
- Compare classic NMA, bias-adjusted NMA, denominator-calibrated NMA, and arbitrated NMA.
- Primary metrics: coverage, false reassurance, reversal rate, regret, interval width inflation, and ranking stability.

### Historical backtesting

- Reconstruct what the evidence base looked like at several historical cutoffs.
- Run the pipeline at each cutoff.
- Test whether later evidence confirmed or overturned earlier conclusions.
- Main question: does denominator-calibrated arbitration reduce overconfident early recommendations?

## Minimum viable project

Phase 1 should target one therapeutic area with:

- 3 to 6 active treatments
- at least 1 major time-to-event outcome
- meaningful registry-publication mismatch
- enough PDFs to stress-test extraction

Best fit candidates are cardiometabolic or cardio-renal topics because you already have review assets and event-driven outcomes there.

## Expected deliverables

- Python package for the calibrated living NMA engine
- linked benchmark dataset with registry-publication mappings
- simulation suite with locked gates
- manuscript figures for workflow, calibration, and backtesting
- paper-ready reproducibility bundle

## Paper angle

This should be framed as a methods-and-validation project, not a software demo. The key claim is:

> Evidence synthesis is more trustworthy when missingness, extraction uncertainty, and model disagreement are treated as first-class statistical objects rather than post hoc caveats.

## Draft manuscript title

Denominator-Calibrated Living Network Meta-Analysis: integrating registry denominators, automated evidence extraction, and conservative arbitration for calibrated treatment-effect estimation
