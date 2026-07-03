from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dclnma.data.io import load_evidence_bundle
from dclnma.data.linkage import inverse_variance_pool
from dclnma.data.models import (
    EvidenceBundle,
    ExtractionRecord,
    Provenance,
    RegistryRecord,
)
from dclnma.data.network import (
    DisconnectedNetworkError,
    build_treatment_network,
    require_connected_network,
)
from dclnma.living import (
    LivingPoolState,
    assert_living_equivalence,
    living_update,
    order_invariance_report,
)


def _registry(trial_id: str, treatment: str, comparator: str, outcome_key: str) -> RegistryRecord:
    return RegistryRecord(
        domain="cardio",
        trial_id=trial_id,
        registry_id=f"NCT-{trial_id}",
        short_name=trial_id.upper(),
        condition="condition",
        population="adults",
        treatment=treatment,
        comparator=comparator,
        outcome_key=outcome_key,
        outcome_label="label",
        follow_up_months=12.0,
        planned_sample_size=1000,
        randomized_sample_size=900,
    )


def _extraction(trial_id: str, log_effect: float, se: float, outcome_key: str) -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id=f"ext-{trial_id}",
        publication_id=f"pub-{trial_id}",
        trial_id=trial_id,
        endpoint_key=outcome_key,
        effect_measure="HR",
        reported_effect=0.9,
        reported_ci_lower=0.8,
        reported_ci_upper=1.0,
        log_effect=log_effect,
        log_ci_lower=log_effect - 0.2,
        log_ci_upper=log_effect + 0.2,
        standard_error=se,
        provenance=Provenance(source_id="s", source_type="pdf", locator="l", confidence=0.9),
    )


class NetworkConnectivityTests(unittest.TestCase):
    OUTCOME = "cv_death_or_hf_hospitalization"

    def _star_bundle(self) -> EvidenceBundle:
        return EvidenceBundle(
            domain="cardio",
            registry_records=[
                _registry("t1", "drug_a", "placebo", self.OUTCOME),
                _registry("t2", "drug_b", "placebo", self.OUTCOME),
            ],
        )

    def test_connected_star_network(self) -> None:
        network = build_treatment_network(self._star_bundle(), self.OUTCOME)
        self.assertTrue(network.is_connected)
        self.assertEqual(network.node_count, 3)  # drug_a, drug_b, placebo
        self.assertEqual(network.edge_count, 2)
        self.assertEqual(len(network.components), 1)
        # require_connected_network returns the network unchanged when connected.
        self.assertIs(require_connected_network(network), network)

    def test_disconnected_network_is_detected_and_rejected(self) -> None:
        bundle = EvidenceBundle(
            domain="cardio",
            registry_records=[
                _registry("t1", "drug_a", "placebo", self.OUTCOME),
                # Second island: drug_c vs drug_d shares no node with the first.
                _registry("t2", "drug_c", "drug_d", self.OUTCOME),
            ],
        )
        network = build_treatment_network(bundle, self.OUTCOME)
        self.assertFalse(network.is_connected)
        self.assertEqual(len(network.components), 2)
        with self.assertRaises(DisconnectedNetworkError):
            require_connected_network(network)

    def test_empty_network_is_rejected(self) -> None:
        network = build_treatment_network(EvidenceBundle(domain="cardio"), self.OUTCOME)
        self.assertEqual(network.node_count, 0)
        with self.assertRaises(DisconnectedNetworkError):
            require_connected_network(network)

    def test_edges_carry_trial_ids(self) -> None:
        network = build_treatment_network(self._star_bundle(), self.OUTCOME)
        edge_trials = {edge.key: edge.trial_ids for edge in network.edges}
        self.assertIn(("drug_a", "placebo"), edge_trials)
        self.assertEqual(edge_trials[("drug_a", "placebo")], ["t1"])

    def test_real_cardio_datasets_are_connected(self) -> None:
        # cardio_hf_sglt2: two SGLT2 drugs vs placebo (multiple trials per drug
        # collapse onto 2 unique edges through the shared placebo node).
        # cardio_af_doac: four DOACs each vs warfarin -> 5 nodes, 4 edges.
        cases = [
            ("cardio_hf_sglt2", "cv_death_or_hf_hospitalization", 3, 2),
            ("cardio_af_doac", "stroke_or_systemic_embolism", 5, 4),
        ]
        for dataset_name, outcome_key, expected_nodes, expected_edges in cases:
            with self.subTest(dataset_name=dataset_name):
                bundle = load_evidence_bundle(ROOT / "data" / dataset_name)
                network = build_treatment_network(bundle, outcome_key)
                self.assertTrue(network.is_connected)
                self.assertEqual(network.node_count, expected_nodes)
                self.assertEqual(network.edge_count, expected_edges)


class LivingEquivalenceTests(unittest.TestCase):
    OUTCOME = "cv_death_or_hf_hospitalization"

    def _records(self) -> list[ExtractionRecord]:
        return [
            _extraction("t1", -0.30, 0.068, self.OUTCOME),
            _extraction("t2", -0.28, 0.071, self.OUTCOME),
            _extraction("t3", -0.23, 0.067, self.OUTCOME),
            _extraction("t4", -0.19, 0.059, self.OUTCOME),
        ]

    def test_living_pool_matches_batch_pool(self) -> None:
        records = self._records()
        state = LivingPoolState()
        for record in records:
            state.add(record)
        batch_effect, batch_se = inverse_variance_pool(records)
        self.assertAlmostEqual(state.pooled_effect, batch_effect, places=12)
        self.assertAlmostEqual(state.pooled_se, batch_se, places=12)

    def test_assert_living_equivalence_reports_equivalent(self) -> None:
        report = assert_living_equivalence(self._records())
        self.assertTrue(report["equivalent"])
        self.assertLessEqual(report["effect_gap"], 1e-12)
        self.assertLessEqual(report["se_gap"], 1e-12)

    def test_living_equivalence_on_real_datasets(self) -> None:
        cases = [
            ("cardio_hf_sglt2", "cv_death_or_hf_hospitalization"),
            ("cardio_af_doac", "stroke_or_systemic_embolism"),
        ]
        for dataset_name, outcome_key in cases:
            with self.subTest(dataset_name=dataset_name):
                bundle = load_evidence_bundle(ROOT / "data" / dataset_name)
                records = [r for r in bundle.extraction_records if r.endpoint_key == outcome_key]
                report = assert_living_equivalence(records)
                self.assertTrue(report["equivalent"])

    def test_order_invariance(self) -> None:
        report = order_invariance_report(self._records())
        self.assertTrue(report["order_invariant"])
        self.assertLessEqual(report["effect_gap"], 1e-9)

    def test_trajectory_length_and_monotone_precision(self) -> None:
        trajectory = living_update(self._records())
        self.assertEqual(len(trajectory), 4)
        # Adding evidence can only tighten (or hold) the pooled SE.
        ses = [step["pooled_se"] for step in trajectory]
        for earlier, later in zip(ses, ses[1:]):
            self.assertLessEqual(later, earlier + 1e-15)

    def test_incremental_snapshot_equals_batch_prefix(self) -> None:
        # Each living snapshot must equal a batch pool over the prefix seen so far.
        records = self._records()
        trajectory = living_update(records)
        for i, step in enumerate(trajectory, start=1):
            prefix_effect, prefix_se = inverse_variance_pool(records[:i])
            self.assertAlmostEqual(step["pooled_effect"], prefix_effect, places=12)
            self.assertAlmostEqual(step["pooled_se"], prefix_se, places=12)

    def test_empty_records_raise(self) -> None:
        with self.assertRaises(ValueError):
            living_update([])
        with self.assertRaises(ValueError):
            assert_living_equivalence([])

    def test_nonpositive_se_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LivingPoolState().add(_extraction("t", -0.1, 0.0, self.OUTCOME))
        with self.assertRaises(ValueError):
            LivingPoolState().add(_extraction("t", -0.1, -0.5, self.OUTCOME))


if __name__ == "__main__":
    unittest.main()
