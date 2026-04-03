# Simulation Design

## Objective

Stress-test competing evidence-synthesis strategies when the published
literature is incomplete and extracted evidence is noisy.

## Candidate methods

- classic publication-only NMA
- denominator-adjusted witness
- selection-adjusted witness
- extraction-aware witness
- conservative arbitrated capsule

## Scenario axes

### Missingness

- silent-trial rate: low, moderate, high
- endpoint missingness: none, partial, severe
- publication selection strength: weak, moderate, strong

### Structural complexity

- network size: 3, 5, 7 treatments
- heterogeneity: low, moderate, high
- design mix: RCT only vs mixed RCT/NRS
- survival shape: proportional hazards vs non-PH

### Data quality

- extraction noise: none, low, moderate
- provenance quality: high vs mixed
- registry linkage completeness: full vs partial

## Primary estimands

- node-level treatment effect
- treatment ranking stability
- interval-specific survival effect where applicable

## Primary metrics

- coverage
- false reassurance
- reversal rate
- mean decision regret
- interval width inflation
- ranking instability

## Gate philosophy

The arbitrated method does not need the narrowest interval. It needs better
calibration and lower overconfident error under incomplete evidence.

## Suggested simulation outputs

- `global_metrics.csv`
- `scenario_metrics.csv`
- `node_capsules.jsonl`
- `manifest.json`
