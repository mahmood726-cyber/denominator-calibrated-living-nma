from __future__ import annotations

import csv
import json
import math
from pathlib import Path


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _to_int(value: str) -> int:
    return int(value)


def _to_float(value: str) -> float:
    return float(value)


def _transform_registry_rows(rows: list[dict[str, str]]) -> list[dict]:
    transformed: list[dict] = []
    for row in rows:
        transformed.append(
            {
                "domain": row["domain"],
                "trial_id": row["trial_id"],
                "registry_id": row["registry_id"],
                "short_name": row["short_name"],
                "condition": row["condition"],
                "population": row["population"],
                "treatment": row["treatment"],
                "comparator": row["comparator"],
                "outcome_key": row["outcome_key"],
                "outcome_label": row["outcome_label"],
                "follow_up_months": _to_float(row["follow_up_months"]),
                "planned_sample_size": _to_int(row["planned_sample_size"]),
                "randomized_sample_size": _to_int(row["randomized_sample_size"]),
                "design": row.get("design", "rct"),
                "reported": _to_bool(row.get("reported", "true")),
                "registry_status": row.get("registry_status", "completed"),
            }
        )
    return transformed


def _transform_publication_rows(rows: list[dict[str, str]]) -> list[dict]:
    transformed: list[dict] = []
    for row in rows:
        transformed.append(
            {
                "publication_id": row["publication_id"],
                "trial_id": row["trial_id"],
                "pmid": row["pmid"],
                "title": row["title"],
                "journal": row["journal"],
                "year": _to_int(row["year"]),
                "publication_date": row["publication_date"],
                "endpoint_key": row["endpoint_key"],
                "endpoint_reported": _to_bool(row.get("endpoint_reported", "true")),
                "design": row.get("design", "rct"),
                "source_file": row.get("source_file") or None,
            }
        )
    return transformed


def _transform_extraction_rows(rows: list[dict[str, str]]) -> list[dict]:
    transformed: list[dict] = []
    for row in rows:
        reported_effect = _to_float(row["reported_effect"])
        reported_ci_lower = _to_float(row["reported_ci_lower"])
        reported_ci_upper = _to_float(row["reported_ci_upper"])
        log_effect = math.log(reported_effect)
        log_ci_lower = math.log(reported_ci_lower)
        log_ci_upper = math.log(reported_ci_upper)
        standard_error = (log_ci_upper - log_ci_lower) / (2 * 1.96)
        transformed.append(
            {
                "extraction_id": row["extraction_id"],
                "publication_id": row["publication_id"],
                "trial_id": row["trial_id"],
                "endpoint_key": row["endpoint_key"],
                "effect_measure": row["effect_measure"],
                "reported_effect": reported_effect,
                "reported_ci_lower": reported_ci_lower,
                "reported_ci_upper": reported_ci_upper,
                "log_effect": log_effect,
                "log_ci_lower": log_ci_lower,
                "log_ci_upper": log_ci_upper,
                "standard_error": standard_error,
                "treatment_events": _to_int(row["treatment_events"]) if row.get("treatment_events") else None,
                "control_events": _to_int(row["control_events"]) if row.get("control_events") else None,
                "treatment_n": _to_int(row["treatment_n"]) if row.get("treatment_n") else None,
                "control_n": _to_int(row["control_n"]) if row.get("control_n") else None,
                "source_text": row.get("source_text", ""),
                "provenance": {
                    "source_id": row["source_id"],
                    "source_type": row["source_type"],
                    "locator": row["locator"],
                    "confidence": _to_float(row.get("confidence", "1.0")),
                    "source_file": row.get("source_file") or None,
                    "quote": row.get("quote") or None,
                    "parser_name": row.get("parser_name") or None,
                },
            }
        )
    return transformed


def _write_json(path: Path, payload: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def build_canonical_dataset(raw_dir: str | Path, out_dir: str | Path) -> dict:
    raw_root = Path(raw_dir)
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    registry_records = _transform_registry_rows(_read_csv(raw_root / "registry_export.csv"))
    publication_records = _transform_publication_rows(_read_csv(raw_root / "publication_export.csv"))
    extraction_records = _transform_extraction_rows(_read_csv(raw_root / "extraction_export.csv"))

    _write_json(out_root / "registry_records.json", registry_records)
    _write_json(out_root / "publication_records.json", publication_records)
    _write_json(out_root / "extraction_records.json", extraction_records)

    return {
        "raw_dir": str(raw_root),
        "out_dir": str(out_root),
        "registry_count": len(registry_records),
        "publication_count": len(publication_records),
        "extraction_count": len(extraction_records),
    }
