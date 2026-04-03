from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .io import load_publication_records


PMID_STUDY_ID_PATTERN = re.compile(r"rct_trial__(\d+)__")


def _extract_pmid(study_id: str) -> str | None:
    match = PMID_STUDY_ID_PATTERN.search(study_id)
    if not match:
        return None
    return match.group(1)


def _scan_publication_index(data_root: str | Path) -> dict[str, dict[str, str]]:
    root = Path(data_root)
    index: dict[str, dict[str, str]] = {}
    for publication_file in root.glob("*/publication_records.json"):
        dataset_dir = publication_file.parent
        dataset_name = dataset_dir.name
        for record in load_publication_records(publication_file):
            if record.pmid in index:
                raise ValueError(f"Duplicate PMID in publication index: {record.pmid}")
            index[record.pmid] = {
                "dataset_name": dataset_name,
                "publication_id": record.publication_id,
                "trial_id": record.trial_id,
                "endpoint_key": record.endpoint_key,
                "pmid": record.pmid,
                "title": record.title,
                "journal": record.journal,
                "publication_date": record.publication_date,
            }
    return index


def generate_study_mapping(
    results_jsonl: str | Path,
    data_root: str | Path,
    out_csv: str | Path,
    source_id: str = "rct_extractor_v5",
    status_filter: str | None = None,
) -> dict:
    publication_index = _scan_publication_index(data_root)
    output_path = Path(out_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "study_id",
        "trial_id",
        "publication_id",
        "endpoint_key",
        "source_id",
        "extraction_id",
        "pmid",
        "dataset_name",
        "title",
        "journal",
        "publication_date",
    ]

    processed_rows = 0
    mapped_rows = 0
    skipped_status = 0
    skipped_no_pmid = 0
    unmatched_pmids: list[str] = []
    seen_study_ids: set[str] = set()

    with Path(results_jsonl).open("r", encoding="utf-8") as handle, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=fieldnames)
        writer.writeheader()

        for line in handle:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            study_id = entry.get("study_id")
            if not study_id or study_id in seen_study_ids:
                continue
            seen_study_ids.add(study_id)
            processed_rows += 1

            status = entry.get("status")
            if status_filter and status != status_filter:
                skipped_status += 1
                continue

            pmid = _extract_pmid(study_id)
            if pmid is None:
                skipped_no_pmid += 1
                continue

            publication = publication_index.get(pmid)
            if publication is None:
                unmatched_pmids.append(pmid)
                continue

            writer.writerow(
                {
                    "study_id": study_id,
                    "trial_id": publication["trial_id"],
                    "publication_id": publication["publication_id"],
                    "endpoint_key": publication["endpoint_key"],
                    "source_id": source_id,
                    "extraction_id": f"auto_{publication['trial_id']}_{pmid}",
                    "pmid": pmid,
                    "dataset_name": publication["dataset_name"],
                    "title": publication["title"],
                    "journal": publication["journal"],
                    "publication_date": publication["publication_date"],
                }
            )
            mapped_rows += 1

    return {
        "results_jsonl": str(results_jsonl),
        "data_root": str(data_root),
        "out_csv": str(output_path),
        "processed_rows": processed_rows,
        "mapped_rows": mapped_rows,
        "skipped_status": skipped_status,
        "skipped_no_pmid": skipped_no_pmid,
        "unmatched_count": len(unmatched_pmids),
        "unmatched_pmids": unmatched_pmids[:20],
    }
