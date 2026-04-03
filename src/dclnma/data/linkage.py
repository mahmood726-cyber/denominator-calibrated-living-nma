from __future__ import annotations

from collections import defaultdict

from .models import EvidenceBundle, ExtractionRecord, LinkedTrialEvidence
from ..witnesses.base import WitnessContext


def inverse_variance_pool(extractions: list[ExtractionRecord]) -> tuple[float, float]:
    if not extractions:
        raise ValueError("At least one extraction record is required.")
    weights = [1.0 / (record.standard_error**2) for record in extractions]
    total_weight = sum(weights)
    pooled = sum(weight * record.log_effect for weight, record in zip(weights, extractions)) / total_weight
    pooled_se = (1.0 / total_weight) ** 0.5
    return pooled, pooled_se


def link_trial_evidence(bundle: EvidenceBundle, outcome_key: str) -> list[LinkedTrialEvidence]:
    registry_by_trial = defaultdict(list)
    for record in bundle.registry_records:
        if record.outcome_key == outcome_key:
            registry_by_trial[record.trial_id].append(record)

    publications_by_trial = defaultdict(list)
    for record in bundle.publication_records:
        if record.endpoint_key == outcome_key:
            publications_by_trial[record.trial_id].append(record)

    extractions_by_trial = defaultdict(list)
    for record in bundle.extraction_records:
        if record.endpoint_key == outcome_key:
            extractions_by_trial[record.trial_id].append(record)

    trial_ids = sorted(set(registry_by_trial) | set(publications_by_trial) | set(extractions_by_trial))
    linked = []
    for trial_id in trial_ids:
        registry_records = registry_by_trial[trial_id]
        publication_records = publications_by_trial[trial_id]
        extraction_records = extractions_by_trial[trial_id]

        if registry_records and publication_records and extraction_records:
            status = "complete"
        elif registry_records and not publication_records:
            status = "registry_only"
        elif publication_records and extraction_records:
            status = "publication_only"
        else:
            status = "partial"

        confidences = [
            record.provenance.confidence for record in extraction_records if record.provenance is not None
        ]
        mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        endpoint_reported = any(record.endpoint_reported for record in publication_records)
        notes: list[str] = []
        if not publication_records:
            notes.append("no linked publication")
        if publication_records and not endpoint_reported:
            notes.append("publication exists but endpoint not reported")
        if not extraction_records:
            notes.append("no extraction records")

        linked.append(
            LinkedTrialEvidence(
                trial_id=trial_id,
                registry_records=registry_records,
                publication_records=publication_records,
                extraction_records=extraction_records,
                linkage_status=status,
                endpoint_reported=endpoint_reported,
                mean_provenance_confidence=mean_confidence,
                notes=notes,
            )
        )
    return linked


def summarize_linkage(linked_trials: list[LinkedTrialEvidence]) -> dict:
    if not linked_trials:
        return {
            "trial_count": 0,
            "complete_count": 0,
            "registry_only_count": 0,
            "publication_only_count": 0,
            "partial_count": 0,
            "mean_provenance_confidence": 0.0,
        }

    complete_count = sum(1 for trial in linked_trials if trial.linkage_status == "complete")
    registry_only_count = sum(1 for trial in linked_trials if trial.linkage_status == "registry_only")
    publication_only_count = sum(1 for trial in linked_trials if trial.linkage_status == "publication_only")
    partial_count = sum(1 for trial in linked_trials if trial.linkage_status == "partial")
    mean_provenance_confidence = sum(trial.mean_provenance_confidence for trial in linked_trials) / len(linked_trials)
    return {
        "trial_count": len(linked_trials),
        "complete_count": complete_count,
        "registry_only_count": registry_only_count,
        "publication_only_count": publication_only_count,
        "partial_count": partial_count,
        "mean_provenance_confidence": mean_provenance_confidence,
    }


def build_witness_context(bundle: EvidenceBundle, outcome_key: str) -> WitnessContext:
    linked_trials = link_trial_evidence(bundle, outcome_key)
    extraction_records = [
        record for record in bundle.extraction_records if record.endpoint_key == outcome_key
    ]
    pooled_effect, pooled_se = inverse_variance_pool(extraction_records)
    registry_records = [record for record in bundle.registry_records if record.outcome_key == outcome_key]
    publication_records = [record for record in bundle.publication_records if record.endpoint_key == outcome_key]
    return WitnessContext(
        domain=bundle.domain,
        outcome_key=outcome_key,
        registry_records=registry_records,
        publication_records=publication_records,
        extraction_records=extraction_records,
        linked_trials=linked_trials,
        observed_effect=pooled_effect,
        observed_se=pooled_se,
    )
