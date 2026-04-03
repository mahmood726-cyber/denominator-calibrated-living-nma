# Roadmap

## Phase 0: Framing

### Goals

- Lock the estimand for the first therapeutic area.
- Define primary and secondary outcomes.
- Freeze the simulation axes and historical backtest protocol.

### Exit criteria

- `PROJECT_SPEC.md` signed off
- first simulation config locked
- first backtest config locked

## Phase 1: Evidence graph

### Deliverables

- registry-publication linkage schema
- provenance schema for extracted outcomes
- treatment/outcome/timepoint graph representation

### Exit criteria

- at least one curated example network
- consistent identifiers across registry, publication, and extraction records

## Phase 2: Witness models

### Deliverables

- classic publication-only witness
- denominator-adjusted witness
- selection-adjusted witness
- extraction-aware witness
- interval-specific survival witness for non-PH settings

### Exit criteria

- deterministic fit outputs on example inputs
- unit tests for witness behavior and warnings

## Phase 3: Arbitration and validation

### Deliverables

- disagreement-sensitive interval arbitration
- false reassurance, coverage, regret, and reversal metrics
- locked simulation suite

### Exit criteria

- arbitrated intervals never narrower than the widest conflicting witness
- validation gates encoded in config

## Phase 4: Historical backtesting

### Deliverables

- time-sliced evidence snapshots
- replay workflow across historical cutoffs
- decision reversal analysis

### Exit criteria

- at least one full replay study completed
- reproducible capsule outputs per cutoff

## Phase 5: Manuscript and release

### Deliverables

- methods manuscript
- artifact bundle with hashes
- public release tag and archive package

### Exit criteria

- release candidate bundle generated
- figures and tables regenerated from locked configs
