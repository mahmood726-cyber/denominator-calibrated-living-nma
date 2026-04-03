from __future__ import annotations

import argparse
import json

from .data.builders import build_canonical_dataset
from .data.extractor_bridge import bridge_rct_extractor_jsonl
from .data.study_mapping import generate_study_mapping
from .pipeline import LivingNMAPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dclnma")
    subparsers = parser.add_subparsers(dest="command", required=True)

    describe_parser = subparsers.add_parser("describe-config", help="Print a config summary.")
    describe_parser.add_argument("--config", required=True)

    demo_parser = subparsers.add_parser("demo-capsule", help="Build a demo decision capsule.")
    demo_parser.add_argument("--effect", type=float, required=True)
    demo_parser.add_argument("--se", type=float, required=True)

    cardio_parser = subparsers.add_parser(
        "build-cardio-capsule",
        help="Load a cardio dataset from config, link records, and build a decision capsule.",
    )
    cardio_parser.add_argument("--config", required=True)

    ingest_parser = subparsers.add_parser(
        "build-canonical-dataset",
        help="Transform raw registry/publication/extraction CSV exports into canonical JSON files.",
    )
    ingest_parser.add_argument("--raw-dir", required=True)
    ingest_parser.add_argument("--out-dir", required=True)

    bridge_parser = subparsers.add_parser(
        "bridge-rct-extractor",
        help="Convert rct-extractor-v2 JSONL output into an extraction_export.csv file.",
    )
    bridge_parser.add_argument("--results-jsonl", required=True)
    bridge_parser.add_argument("--mapping-csv", required=True)
    bridge_parser.add_argument("--out-csv", required=True)
    bridge_parser.add_argument("--effect-types", default="HR,OR,RR")

    mapping_parser = subparsers.add_parser(
        "generate-study-mapping",
        help="Generate a study mapping CSV by matching extractor study_id PMIDs to canonical publication metadata.",
    )
    mapping_parser.add_argument("--results-jsonl", required=True)
    mapping_parser.add_argument("--data-root", required=True)
    mapping_parser.add_argument("--out-csv", required=True)
    mapping_parser.add_argument("--source-id", default="rct_extractor_v5")
    mapping_parser.add_argument("--status-filter", default="extracted")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "describe-config":
        pipeline = LivingNMAPipeline.from_config(args.config)
        print(json.dumps(pipeline.describe(), indent=2))
        return 0

    if args.command == "demo-capsule":
        pipeline = LivingNMAPipeline({"project": "dclnma"})
        capsule = pipeline.build_demo_capsule(observed_effect=args.effect, observed_se=args.se)
        print(json.dumps(pipeline.capsule_to_dict(capsule), indent=2))
        return 0

    if args.command == "build-cardio-capsule":
        pipeline = LivingNMAPipeline.from_config(args.config)
        capsule = pipeline.build_configured_capsule()
        print(json.dumps(pipeline.capsule_to_dict(capsule), indent=2))
        return 0

    if args.command == "build-canonical-dataset":
        result = build_canonical_dataset(raw_dir=args.raw_dir, out_dir=args.out_dir)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "bridge-rct-extractor":
        effect_types = {value.strip() for value in args.effect_types.split(",") if value.strip()}
        result = bridge_rct_extractor_jsonl(
            results_jsonl=args.results_jsonl,
            mapping_csv=args.mapping_csv,
            out_csv=args.out_csv,
            effect_types=effect_types,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "generate-study-mapping":
        status_filter = args.status_filter or None
        result = generate_study_mapping(
            results_jsonl=args.results_jsonl,
            data_root=args.data_root,
            out_csv=args.out_csv,
            source_id=args.source_id,
            status_filter=status_filter,
        )
        print(json.dumps(result, indent=2))
        return 0

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
