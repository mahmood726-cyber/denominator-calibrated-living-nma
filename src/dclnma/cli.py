from __future__ import annotations

import argparse
import json

from .data.builders import build_canonical_dataset
from .data.extractor_bridge import bridge_rct_extractor_jsonl
from .data.network import build_treatment_network, require_connected_network
from .data.study_mapping import generate_study_mapping
from .living import assert_living_equivalence, living_update, order_invariance_report
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

    network_parser = subparsers.add_parser(
        "describe-network",
        help="Build the treatment network for a config's outcome and report connectivity.",
    )
    network_parser.add_argument("--config", required=True)

    living_parser = subparsers.add_parser(
        "living-benchmark",
        help="Verify the living-update pool equals a from-scratch batch recompute for a config.",
    )
    living_parser.add_argument("--config", required=True)

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

    if args.command == "describe-network":
        pipeline = LivingNMAPipeline.from_config(args.config)
        bundle = pipeline.load_bundle()
        outcome_key = pipeline.config.get("outcome_key")
        if bundle is None or not outcome_key:
            parser.error("Config must define dataset_dir and outcome_key for describe-network.")
        network = build_treatment_network(bundle, outcome_key)
        # Surface connectivity but do not hard-fail here: describing a broken
        # network is a legitimate diagnostic use.
        print(json.dumps(network.summary(), indent=2))
        return 0 if network.is_connected else 1

    if args.command == "living-benchmark":
        pipeline = LivingNMAPipeline.from_config(args.config)
        bundle = pipeline.load_bundle()
        outcome_key = pipeline.config.get("outcome_key")
        if bundle is None or not outcome_key:
            parser.error("Config must define dataset_dir and outcome_key for living-benchmark.")
        # Refuse to benchmark a disconnected network — an NMA on one is undefined.
        require_connected_network(build_treatment_network(bundle, outcome_key))
        records = [r for r in bundle.extraction_records if r.endpoint_key == outcome_key]
        equivalence = assert_living_equivalence(records)
        order = order_invariance_report(records)
        result = {
            "equivalence": equivalence,
            "order_invariance": order,
            "trajectory": living_update(records),
        }
        print(json.dumps(result, indent=2))
        return 0 if equivalence["equivalent"] and order["order_invariant"] else 1

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
