from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dclnma.arbitration.rules import ArbitrationPolicy, arbitrate_witnesses
from dclnma.data.builders import build_canonical_dataset
from dclnma.data.extractor_bridge import bridge_rct_extractor_jsonl
from dclnma.data.io import load_evidence_bundle
from dclnma.data.linkage import build_witness_context, link_trial_evidence, summarize_linkage
from dclnma.data.study_mapping import generate_study_mapping
from dclnma.data.models import WitnessEstimate
from dclnma.pipeline import LivingNMAPipeline
from dclnma.validation.metrics import coverage_rate, false_reassurance_rate, mean_decision_regret


class ArbitrationTests(unittest.TestCase):
    def test_high_disagreement_forces_research(self) -> None:
        witnesses = [
            WitnessEstimate(name="a", effect=-0.20, lower=-0.35, upper=-0.05),
            WitnessEstimate(name="b", effect=0.18, lower=0.02, upper=0.34),
        ]
        capsule = arbitrate_witnesses(witnesses, ArbitrationPolicy(disagreement_low=0.05, disagreement_high=0.1))
        self.assertEqual(capsule.disagreement_level, "high")
        self.assertEqual(capsule.recommended_action, "research")


class ValidationMetricTests(unittest.TestCase):
    def test_metrics_smoke(self) -> None:
        self.assertAlmostEqual(coverage_rate([(-0.2, 0.1), (-0.1, 0.05)], [0.0, -0.2]), 0.5)
        self.assertAlmostEqual(false_reassurance_rate(["recommend", "research"], [0.1, -0.3]), 0.5)
        self.assertAlmostEqual(
            mean_decision_regret(["recommend", "do_not_use", "research"], [0.2, -0.1, -0.4]),
            3.5 / 3.0,
        )


class CardioDatasetTests(unittest.TestCase):
    def test_load_cardio_bundles(self) -> None:
        cases = [
            ("cardio_hf_sglt2", "cv_death_or_hf_hospitalization", 0.05),
            ("cardio_af_doac", "stroke_or_systemic_embolism", 0.07),
        ]
        for dataset_name, outcome_key, se_upper in cases:
            with self.subTest(dataset_name=dataset_name):
                dataset_dir = ROOT / "data" / dataset_name
                bundle = load_evidence_bundle(dataset_dir)
                self.assertEqual(bundle.domain, "cardio")
                self.assertEqual(len(bundle.registry_records), 4)
                self.assertEqual(len(bundle.publication_records), 4)
                self.assertEqual(len(bundle.extraction_records), 4)

                linked = link_trial_evidence(bundle, outcome_key)
                summary = summarize_linkage(linked)
                self.assertEqual(summary["trial_count"], 4)
                self.assertEqual(summary["complete_count"], 4)
                self.assertAlmostEqual(summary["mean_provenance_confidence"], 0.98)

                context = build_witness_context(bundle, outcome_key)
                self.assertLess(context.observed_effect, 0.0)
                self.assertLess(context.observed_se, se_upper)


class RawIngestionTests(unittest.TestCase):
    def test_build_canonical_dataset_from_raw_sources(self) -> None:
        cases = [
            ("cardio_hf_sglt2", "cv_death_or_hf_hospitalization"),
            ("cardio_af_doac", "stroke_or_systemic_embolism"),
        ]
        for dataset_name, outcome_key in cases:
            with self.subTest(dataset_name=dataset_name):
                raw_dir = ROOT / "raw_sources" / dataset_name
                with tempfile.TemporaryDirectory() as tmp_dir:
                    summary = build_canonical_dataset(raw_dir=raw_dir, out_dir=tmp_dir)
                    self.assertEqual(summary["registry_count"], 4)
                    self.assertEqual(summary["publication_count"], 4)
                    self.assertEqual(summary["extraction_count"], 4)

                    bundle = load_evidence_bundle(tmp_dir)
                    context = build_witness_context(bundle, outcome_key)
                    self.assertLess(context.observed_effect, 0.0)


class ExtractorBridgeTests(unittest.TestCase):
    def test_generate_study_mapping_from_canonical_data(self) -> None:
        source_root = ROOT / "raw_sources" / "cardio_hf_sglt2"
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = Path(tmp_dir) / "auto_mapping.csv"
            summary = generate_study_mapping(
                results_jsonl=source_root / "sample_rct_extractor_results.jsonl",
                data_root=ROOT / "data",
                out_csv=out_csv,
            )
            self.assertEqual(summary["mapped_rows"], 2)
            self.assertEqual(summary["unmatched_count"], 1)
            mapping_text = out_csv.read_text(encoding="utf-8")
            self.assertIn("pub_dapa_hf_2019", mapping_text)
            self.assertIn("pub_deliver_2022", mapping_text)

    def test_bridge_rct_extractor_jsonl_to_raw_export(self) -> None:
        source_root = ROOT / "raw_sources" / "cardio_hf_sglt2"
        with tempfile.TemporaryDirectory() as tmp_raw_dir, tempfile.TemporaryDirectory() as tmp_out_dir:
            tmp_raw = Path(tmp_raw_dir)
            shutil.copy2(source_root / "registry_export.csv", tmp_raw / "registry_export.csv")
            shutil.copy2(source_root / "publication_export.csv", tmp_raw / "publication_export.csv")

            auto_mapping = tmp_raw / "auto_mapping.csv"
            mapping_summary = generate_study_mapping(
                results_jsonl=source_root / "sample_rct_extractor_results.jsonl",
                data_root=ROOT / "data",
                out_csv=auto_mapping,
            )
            self.assertEqual(mapping_summary["mapped_rows"], 2)

            bridge_summary = bridge_rct_extractor_jsonl(
                results_jsonl=source_root / "sample_rct_extractor_results.jsonl",
                mapping_csv=auto_mapping,
                out_csv=tmp_raw / "extraction_export.csv",
                effect_types={"HR"},
            )
            self.assertEqual(bridge_summary["written_rows"], 2)
            self.assertEqual(bridge_summary["skipped_unmapped"], 1)

            build_summary = build_canonical_dataset(raw_dir=tmp_raw, out_dir=tmp_out_dir)
            self.assertEqual(build_summary["extraction_count"], 2)

            bundle = load_evidence_bundle(tmp_out_dir)
            context = build_witness_context(bundle, "cv_death_or_hf_hospitalization")
            self.assertEqual(len(bundle.extraction_records), 2)
            self.assertLess(context.observed_effect, 0.0)


class PipelineTests(unittest.TestCase):
    def test_demo_capsule_contains_four_witnesses(self) -> None:
        pipeline = LivingNMAPipeline({"project": "dclnma"})
        capsule = pipeline.build_demo_capsule(observed_effect=-0.12, observed_se=0.04)
        self.assertEqual(len(capsule.witnesses), 4)
        self.assertIn(capsule.recommended_action, {"recommend", "research", "do_not_use"})

    def test_configured_cardio_capsules_run(self) -> None:
        configs = [
            ROOT / "configs" / "cardio_hf_sglt2_example.json",
            ROOT / "configs" / "cardio_af_doac_example.json",
        ]
        for config in configs:
            with self.subTest(config=config.name):
                pipeline = LivingNMAPipeline.from_config(config)
                capsule = pipeline.build_configured_capsule()
                self.assertEqual(len(capsule.witnesses), 4)
                self.assertLess(capsule.effect, 0.0)
                self.assertIn(capsule.disagreement_level, {"low", "mid", "high"})


if __name__ == "__main__":
    unittest.main()
