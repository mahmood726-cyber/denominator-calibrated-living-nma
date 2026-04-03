from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Provenance:
    source_id: str
    source_type: str
    locator: str
    confidence: float = 1.0
    source_file: str | None = None
    quote: str | None = None
    parser_name: str | None = None


@dataclass(slots=True)
class RegistryRecord:
    domain: str
    trial_id: str
    registry_id: str
    short_name: str
    condition: str
    population: str
    treatment: str
    comparator: str
    outcome_key: str
    outcome_label: str
    follow_up_months: float
    planned_sample_size: int
    randomized_sample_size: int
    design: str = "rct"
    reported: bool = True
    registry_status: str = "completed"


@dataclass(slots=True)
class PublicationRecord:
    publication_id: str
    trial_id: str
    pmid: str
    title: str
    journal: str
    year: int
    publication_date: str
    endpoint_key: str
    endpoint_reported: bool
    design: str = "rct"
    source_file: str | None = None


@dataclass(slots=True)
class ExtractionRecord:
    extraction_id: str
    publication_id: str
    trial_id: str
    endpoint_key: str
    effect_measure: str
    reported_effect: float
    reported_ci_lower: float
    reported_ci_upper: float
    log_effect: float
    log_ci_lower: float
    log_ci_upper: float
    standard_error: float
    treatment_events: int | None = None
    control_events: int | None = None
    treatment_n: int | None = None
    control_n: int | None = None
    source_text: str = ""
    provenance: Provenance | None = None


@dataclass(slots=True)
class EvidenceBundle:
    domain: str
    registry_records: list[RegistryRecord] = field(default_factory=list)
    publication_records: list[PublicationRecord] = field(default_factory=list)
    extraction_records: list[ExtractionRecord] = field(default_factory=list)


@dataclass(slots=True)
class LinkedTrialEvidence:
    trial_id: str
    registry_records: list[RegistryRecord] = field(default_factory=list)
    publication_records: list[PublicationRecord] = field(default_factory=list)
    extraction_records: list[ExtractionRecord] = field(default_factory=list)
    linkage_status: str = "unlinked"
    endpoint_reported: bool = False
    mean_provenance_confidence: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WitnessEstimate:
    name: str
    effect: float
    lower: float
    upper: float
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DecisionCapsule:
    effect: float
    lower: float
    upper: float
    disagreement_level: str
    recommended_action: str
    reversal_risk: float
    decision_regret: float
    witnesses: list[WitnessEstimate]
    evidence_integrity_profile: dict[str, Any] = field(default_factory=dict)
