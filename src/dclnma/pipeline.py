from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .arbitration.rules import arbitrate_witnesses
from .data.io import load_evidence_bundle
from .data.linkage import build_witness_context, link_trial_evidence, summarize_linkage
from .data.models import DecisionCapsule, EvidenceBundle, ExtractionRecord, Provenance
from .witnesses.base import (
    ClassicWitness,
    DenominatorWitness,
    ExtractionWitness,
    SelectionWitness,
    WitnessContext,
)


class LivingNMAPipeline:
    def __init__(self, config: dict, config_path: Path | None = None):
        self.config = config
        self.config_path = config_path

    @classmethod
    def from_config(cls, path: str | Path) -> "LivingNMAPipeline":
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        return cls(config=config, config_path=config_path)

    def _resolve_path(self, raw_path: str | None) -> Path | None:
        if raw_path is None:
            return None
        candidate = Path(raw_path)
        if candidate.is_absolute() or self.config_path is None:
            return candidate
        return self.config_path.parent.joinpath(candidate).resolve()

    def load_bundle(self) -> EvidenceBundle | None:
        dataset_dir = self._resolve_path(self.config.get("dataset_dir"))
        if dataset_dir is None:
            return None
        return load_evidence_bundle(dataset_dir)

    def describe(self) -> dict:
        description = {
            "project": self.config.get("project", "dclnma"),
            "study_area": self.config.get("study_area"),
            "outcome": self.config.get("outcome"),
            "outcome_key": self.config.get("outcome_key"),
            "master_seed": self.config.get("master_seed"),
            "keys": sorted(self.config.keys()),
        }
        bundle = self.load_bundle()
        if bundle is not None and self.config.get("outcome_key"):
            linked_trials = link_trial_evidence(bundle, self.config["outcome_key"])
            description["dataset_summary"] = summarize_linkage(linked_trials)
            description["dataset_dir"] = str(self._resolve_path(self.config.get("dataset_dir")))
        return description

    def build_demo_capsule(self, observed_effect: float, observed_se: float) -> DecisionCapsule:
        context = WitnessContext(
            domain="demo",
            outcome_key="demo_outcome",
            observed_effect=observed_effect,
            observed_se=observed_se,
            extraction_records=[
                ExtractionRecord(
                    extraction_id="demo-extraction-1",
                    publication_id="demo-publication-1",
                    trial_id="demo-trial-1",
                    endpoint_key="demo_outcome",
                    effect_measure="HR",
                    reported_effect=0.89,
                    reported_ci_lower=0.82,
                    reported_ci_upper=0.97,
                    log_effect=observed_effect,
                    log_ci_lower=observed_effect - 1.96 * observed_se,
                    log_ci_upper=observed_effect + 1.96 * observed_se,
                    standard_error=observed_se,
                    provenance=Provenance(
                        source_id="demo-pdf",
                        source_type="pdf",
                        locator="page=8;table=2",
                        confidence=0.9,
                    ),
                )
            ],
        )
        witnesses = self._estimate_witnesses(context)
        return arbitrate_witnesses(witnesses)

    def build_configured_capsule(self) -> DecisionCapsule:
        bundle = self.load_bundle()
        outcome_key = self.config.get("outcome_key")
        if bundle is None or not outcome_key:
            raise ValueError("Config must define dataset_dir and outcome_key for a configured capsule.")
        context = build_witness_context(bundle, outcome_key)
        witnesses = self._estimate_witnesses(context)
        return arbitrate_witnesses(witnesses)

    @staticmethod
    def _estimate_witnesses(context: WitnessContext) -> list:
        return [
            ClassicWitness().estimate(context),
            DenominatorWitness().estimate(context),
            SelectionWitness().estimate(context),
            ExtractionWitness().estimate(context),
        ]

    @staticmethod
    def capsule_to_dict(capsule: DecisionCapsule) -> dict:
        return asdict(capsule)
