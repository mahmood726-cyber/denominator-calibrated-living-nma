from __future__ import annotations

import csv
import json
from pathlib import Path


EXTRACTION_EXPORT_COLUMNS = [
    "extraction_id",
    "publication_id",
    "trial_id",
    "endpoint_key",
    "effect_measure",
    "reported_effect",
    "reported_ci_lower",
    "reported_ci_upper",
    "treatment_events",
    "control_events",
    "treatment_n",
    "control_n",
    "source_text",
    "source_id",
    "source_type",
    "locator",
    "confidence",
    "source_file",
    "quote",
    "parser_name",
    "study_id",
    "pdf_path",
    "automation_tier",
    "page_number",
    "se_method",
]


def _read_mapping(path: str | Path) -> dict[str, dict[str, str]]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["study_id"]: row for row in rows}


def _select_extraction(entry: dict, preferred_field: str) -> dict | None:
    if preferred_field == "best_match":
        candidate = entry.get("best_match")
        if isinstance(candidate, dict):
            return candidate
    for candidate in entry.get("top_extractions", []):
        if isinstance(candidate, dict):
            return candidate
    return None


def bridge_rct_extractor_jsonl(
    results_jsonl: str | Path,
    mapping_csv: str | Path,
    out_csv: str | Path,
    effect_types: set[str] | None = None,
    preferred_field: str = "best_match",
) -> dict:
    mapping = _read_mapping(mapping_csv)
    output_path = Path(out_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written_rows = 0
    skipped_status = 0
    skipped_unmapped = 0
    skipped_missing_effect = 0
    skipped_type = 0
    processed_rows = 0

    with Path(results_jsonl).open("r", encoding="utf-8") as handle, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=EXTRACTION_EXPORT_COLUMNS)
        writer.writeheader()

        for line in handle:
            line = line.strip()
            if not line:
                continue
            processed_rows += 1
            entry = json.loads(line)
            if entry.get("status") != "extracted":
                skipped_status += 1
                continue

            study_id = entry.get("study_id")
            mapping_row = mapping.get(study_id)
            if mapping_row is None:
                skipped_unmapped += 1
                continue

            extraction = _select_extraction(entry, preferred_field=preferred_field)
            if extraction is None:
                skipped_missing_effect += 1
                continue

            effect_type = extraction.get("type")
            if effect_types and effect_type not in effect_types:
                skipped_type += 1
                continue

            effect = extraction.get("effect_size")
            ci_lower = extraction.get("ci_lower")
            ci_upper = extraction.get("ci_upper")
            if effect is None or ci_lower is None or ci_upper is None:
                skipped_missing_effect += 1
                continue

            page_number = extraction.get("page_number")
            if page_number is None:
                locator = f"char={extraction.get('char_start', 0)}:{extraction.get('char_end', 0)}"
            else:
                locator = f"page={page_number}"

            row = {
                "extraction_id": mapping_row.get("extraction_id") or f"bridge_{study_id}",
                "publication_id": mapping_row["publication_id"],
                "trial_id": mapping_row["trial_id"],
                "endpoint_key": mapping_row["endpoint_key"],
                "effect_measure": effect_type,
                "reported_effect": effect,
                "reported_ci_lower": ci_lower,
                "reported_ci_upper": ci_upper,
                "treatment_events": mapping_row.get("treatment_events", ""),
                "control_events": mapping_row.get("control_events", ""),
                "treatment_n": mapping_row.get("treatment_n", ""),
                "control_n": mapping_row.get("control_n", ""),
                "source_text": extraction.get("source_text", ""),
                "source_id": mapping_row.get("source_id", "rct_extractor_v5"),
                "source_type": "rct_extractor_jsonl",
                "locator": locator,
                "confidence": extraction.get("calibrated_confidence", extraction.get("raw_confidence", "")),
                "source_file": entry.get("pdf_path", ""),
                "quote": extraction.get("source_text", ""),
                "parser_name": "rct_extractor_bridge",
                "study_id": study_id,
                "pdf_path": entry.get("pdf_path", ""),
                "automation_tier": extraction.get("automation_tier", ""),
                "page_number": page_number if page_number is not None else "",
                "se_method": extraction.get("se_method", ""),
            }
            writer.writerow(row)
            written_rows += 1

    return {
        "results_jsonl": str(results_jsonl),
        "mapping_csv": str(mapping_csv),
        "out_csv": str(output_path),
        "processed_rows": processed_rows,
        "written_rows": written_rows,
        "skipped_status": skipped_status,
        "skipped_unmapped": skipped_unmapped,
        "skipped_missing_effect": skipped_missing_effect,
        "skipped_type": skipped_type,
    }
