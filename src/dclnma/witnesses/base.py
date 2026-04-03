from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..data.models import (
    ExtractionRecord,
    LinkedTrialEvidence,
    PublicationRecord,
    RegistryRecord,
    WitnessEstimate,
)


@dataclass(slots=True)
class WitnessContext:
    domain: str = "unknown"
    outcome_key: str = "unspecified"
    registry_records: list[RegistryRecord] = field(default_factory=list)
    publication_records: list[PublicationRecord] = field(default_factory=list)
    extraction_records: list[ExtractionRecord] = field(default_factory=list)
    linked_trials: list[LinkedTrialEvidence] = field(default_factory=list)
    observed_effect: float = 0.0
    observed_se: float = 0.1


class WitnessModel(ABC):
    name: str

    @abstractmethod
    def estimate(self, context: WitnessContext) -> WitnessEstimate:
        raise NotImplementedError


class ClassicWitness(WitnessModel):
    name = "classic"

    def estimate(self, context: WitnessContext) -> WitnessEstimate:
        width = 1.96 * context.observed_se
        return WitnessEstimate(
            name=self.name,
            effect=context.observed_effect,
            lower=context.observed_effect - width,
            upper=context.observed_effect + width,
            metadata={
                "basis": "publication_only",
                "trial_count": len({record.trial_id for record in context.publication_records}),
                "outcome_key": context.outcome_key,
            },
        )


class DenominatorWitness(WitnessModel):
    name = "denominator"

    def estimate(self, context: WitnessContext) -> WitnessEstimate:
        registry_trials = {record.trial_id for record in context.registry_records}
        reported_trials = {
            record.trial_id
            for record in context.publication_records
            if record.endpoint_reported and record.endpoint_key == context.outcome_key
        }
        silent_fraction = 0.0
        if registry_trials:
            silent_fraction = max(0.0, 1.0 - len(reported_trials) / len(registry_trials))
        adjustment = 0.08 * silent_fraction
        adjusted_effect = context.observed_effect + adjustment
        width = 1.96 * context.observed_se * (1.0 + silent_fraction)
        warnings: list[str] = []
        if silent_fraction > 0:
            warnings.append("registry-publication gap adjustment applied")
        return WitnessEstimate(
            name=self.name,
            effect=adjusted_effect,
            lower=adjusted_effect - width,
            upper=adjusted_effect + width,
            warnings=warnings,
            metadata={
                "basis": "registry_denominator",
                "registry_trial_count": len(registry_trials),
                "reported_trial_count": len(reported_trials),
                "silent_fraction": silent_fraction,
            },
        )


class SelectionWitness(WitnessModel):
    name = "selection"

    def estimate(self, context: WitnessContext) -> WitnessEstimate:
        publication_records = [
            record for record in context.publication_records if record.endpoint_key == context.outcome_key
        ]
        endpoint_missing_fraction = 0.0
        if publication_records:
            missing_count = sum(1 for record in publication_records if not record.endpoint_reported)
            endpoint_missing_fraction = missing_count / len(publication_records)
        adjustment = 0.05 * endpoint_missing_fraction
        adjusted_effect = context.observed_effect + adjustment
        width = 1.96 * context.observed_se * (1.0 + endpoint_missing_fraction)
        warnings: list[str] = []
        if endpoint_missing_fraction > 0:
            warnings.append("endpoint-missingness adjustment applied")
        return WitnessEstimate(
            name=self.name,
            effect=adjusted_effect,
            lower=adjusted_effect - width,
            upper=adjusted_effect + width,
            warnings=warnings,
            metadata={
                "basis": "publication_endpoint_missingness",
                "publication_count": len(publication_records),
                "endpoint_missing_fraction": endpoint_missing_fraction,
            },
        )


class ExtractionWitness(WitnessModel):
    name = "extraction"

    def estimate(self, context: WitnessContext) -> WitnessEstimate:
        mean_confidence = 1.0
        if context.extraction_records:
            mean_confidence = sum(
                record.provenance.confidence for record in context.extraction_records
            ) / len(context.extraction_records)
        inflation = 1.0 + max(0.0, 1.0 - mean_confidence)
        width = 1.96 * context.observed_se * inflation
        warnings: list[str] = []
        if mean_confidence < 0.95:
            warnings.append("provenance confidence inflation applied")
        return WitnessEstimate(
            name=self.name,
            effect=context.observed_effect,
            lower=context.observed_effect - width,
            upper=context.observed_effect + width,
            warnings=warnings,
            metadata={
                "basis": "pdf_extraction",
                "mean_confidence": mean_confidence,
                "extraction_count": len(context.extraction_records),
            },
        )
