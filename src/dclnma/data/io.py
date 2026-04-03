from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import EvidenceBundle, ExtractionRecord, Provenance, PublicationRecord, RegistryRecord


def _read_records(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError(f"Expected a list of records in {file_path}.")
        return payload
    if file_path.suffix.lower() == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    raise ValueError(f"Unsupported record format: {file_path.suffix}")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def _to_int(value: Any) -> int:
    return int(value)


def _to_float(value: Any) -> float:
    return float(value)


def load_registry_records(path: str | Path) -> list[RegistryRecord]:
    records = []
    for raw in _read_records(path):
        records.append(
            RegistryRecord(
                domain=str(raw["domain"]),
                trial_id=str(raw["trial_id"]),
                registry_id=str(raw["registry_id"]),
                short_name=str(raw["short_name"]),
                condition=str(raw["condition"]),
                population=str(raw["population"]),
                treatment=str(raw["treatment"]),
                comparator=str(raw["comparator"]),
                outcome_key=str(raw["outcome_key"]),
                outcome_label=str(raw["outcome_label"]),
                follow_up_months=_to_float(raw["follow_up_months"]),
                planned_sample_size=_to_int(raw["planned_sample_size"]),
                randomized_sample_size=_to_int(raw["randomized_sample_size"]),
                design=str(raw.get("design", "rct")),
                reported=_to_bool(raw.get("reported", True)),
                registry_status=str(raw.get("registry_status", "completed")),
            )
        )
    return records


def load_publication_records(path: str | Path) -> list[PublicationRecord]:
    records = []
    for raw in _read_records(path):
        records.append(
            PublicationRecord(
                publication_id=str(raw["publication_id"]),
                trial_id=str(raw["trial_id"]),
                pmid=str(raw["pmid"]),
                title=str(raw["title"]),
                journal=str(raw["journal"]),
                year=_to_int(raw["year"]),
                publication_date=str(raw["publication_date"]),
                endpoint_key=str(raw["endpoint_key"]),
                endpoint_reported=_to_bool(raw["endpoint_reported"]),
                design=str(raw.get("design", "rct")),
                source_file=str(raw["source_file"]) if raw.get("source_file") else None,
            )
        )
    return records


def load_extraction_records(path: str | Path) -> list[ExtractionRecord]:
    records = []
    for raw in _read_records(path):
        provenance_raw = raw.get("provenance") or {}
        provenance = Provenance(
            source_id=str(provenance_raw["source_id"]),
            source_type=str(provenance_raw["source_type"]),
            locator=str(provenance_raw["locator"]),
            confidence=_to_float(provenance_raw.get("confidence", 1.0)),
            source_file=str(provenance_raw["source_file"]) if provenance_raw.get("source_file") else None,
            quote=str(provenance_raw["quote"]) if provenance_raw.get("quote") else None,
            parser_name=str(provenance_raw["parser_name"]) if provenance_raw.get("parser_name") else None,
        )
        records.append(
            ExtractionRecord(
                extraction_id=str(raw["extraction_id"]),
                publication_id=str(raw["publication_id"]),
                trial_id=str(raw["trial_id"]),
                endpoint_key=str(raw["endpoint_key"]),
                effect_measure=str(raw["effect_measure"]),
                reported_effect=_to_float(raw["reported_effect"]),
                reported_ci_lower=_to_float(raw["reported_ci_lower"]),
                reported_ci_upper=_to_float(raw["reported_ci_upper"]),
                log_effect=_to_float(raw["log_effect"]),
                log_ci_lower=_to_float(raw["log_ci_lower"]),
                log_ci_upper=_to_float(raw["log_ci_upper"]),
                standard_error=_to_float(raw["standard_error"]),
                treatment_events=_to_int(raw["treatment_events"]) if raw.get("treatment_events") not in {None, ""} else None,
                control_events=_to_int(raw["control_events"]) if raw.get("control_events") not in {None, ""} else None,
                treatment_n=_to_int(raw["treatment_n"]) if raw.get("treatment_n") not in {None, ""} else None,
                control_n=_to_int(raw["control_n"]) if raw.get("control_n") not in {None, ""} else None,
                source_text=str(raw.get("source_text", "")),
                provenance=provenance,
            )
        )
    return records


def load_evidence_bundle(dataset_dir: str | Path) -> EvidenceBundle:
    root = Path(dataset_dir)
    registry_records = load_registry_records(root / "registry_records.json")
    publication_records = load_publication_records(root / "publication_records.json")
    extraction_records = load_extraction_records(root / "extraction_records.json")
    domain = registry_records[0].domain if registry_records else "unknown"
    return EvidenceBundle(
        domain=domain,
        registry_records=registry_records,
        publication_records=publication_records,
        extraction_records=extraction_records,
    )
