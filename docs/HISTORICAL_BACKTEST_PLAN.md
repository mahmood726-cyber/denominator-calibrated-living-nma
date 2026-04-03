# Historical Backtest Plan

## Core question

Would the calibrated pipeline have produced fewer overconfident treatment
recommendations if it had only seen the evidence available at earlier time
cutoffs?

## Protocol

1. Select a therapeutic area with multiple major RCT publications over time.
2. Define fixed evidence cutoffs by date.
3. For each cutoff:
   - include only registry entries, publications, and outcomes available by
     that date
   - run witness models and arbitration
   - store the resulting decision capsule
4. Compare each early capsule with the later evidence state.

## Main outcomes

- early recommendation vs later recommendation
- early interval coverage relative to later pooled effect
- reversal count
- regret difference between classic and arbitrated workflows

## Good first domains

- cardio-renal event-driven trials
- cardiometabolic treatment classes with staged publication history
- oncology settings with known non-PH behavior

## Practical rule

The backtest should be strict about what was knowable at each date. Do not leak
later endpoint data or later registry reconciliations into earlier cutoffs.
