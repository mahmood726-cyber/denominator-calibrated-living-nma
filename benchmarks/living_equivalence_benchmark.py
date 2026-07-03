"""Reproducible benchmark: living-update == batch-recompute equivalence.

Runs the incremental "living" pooling engine against a from-scratch batch
recompute on every seeded cardio dataset, and prints a table showing that the
two agree to numerical precision. This is the correctness demonstration for the
living network meta-analysis: an incremental update must never drift from what a
full recompute would have produced.

Run from the repository root:

    python benchmarks/living_equivalence_benchmark.py

Exit code is 0 when every dataset passes the equivalence check, 1 otherwise, so
the script doubles as a CI gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dclnma.data.io import load_evidence_bundle
from dclnma.data.network import build_treatment_network, require_connected_network
from dclnma.living import assert_living_equivalence, living_update, order_invariance_report

# (dataset directory name, outcome key)
DATASETS = [
    ("cardio_hf_sglt2", "cv_death_or_hf_hospitalization"),
    ("cardio_af_doac", "stroke_or_systemic_embolism"),
]


def _records_for(dataset_name: str, outcome_key: str):
    bundle = load_evidence_bundle(ROOT / "data" / dataset_name)
    # Connectivity is a precondition for interpreting a network meta-analysis.
    network = require_connected_network(build_treatment_network(bundle, outcome_key))
    records = [r for r in bundle.extraction_records if r.endpoint_key == outcome_key]
    return network, records


def run() -> int:
    header = (
        f"{'dataset':<22}{'nodes':>6}{'edges':>6}{'trials':>7}"
        f"{'live_effect':>14}{'batch_effect':>14}{'effect_gap':>13}{'ok':>5}"
    )
    print(header)
    print("-" * len(header))

    all_ok = True
    for dataset_name, outcome_key in DATASETS:
        network, records = _records_for(dataset_name, outcome_key)
        report = assert_living_equivalence(records)
        order = order_invariance_report(records)
        ok = report["equivalent"] and order["order_invariant"]
        all_ok = all_ok and ok
        print(
            f"{dataset_name:<22}{network.node_count:>6}{network.edge_count:>6}"
            f"{report['n']:>7}{report['live_effect']:>14.6f}"
            f"{report['batch_effect']:>14.6f}{report['effect_gap']:>13.2e}"
            f"{'PASS' if ok else 'FAIL':>5}"
        )

    print()
    print("Living trajectory (cardio_hf_sglt2, pooled effect after each trial):")
    _, hf_records = _records_for(*DATASETS[0])
    for step in living_update(hf_records):
        print(
            f"  n={step['n']}  pooled_effect={step['pooled_effect']:+.6f}  "
            f"pooled_se={step['pooled_se']:.6f}  latest={step['trial_ids'][-1]}"
        )

    print()
    print("All datasets equivalent." if all_ok else "EQUIVALENCE FAILURE.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
