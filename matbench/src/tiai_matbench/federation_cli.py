"""CLI for FederationCore native-result validation and normalization."""
from __future__ import annotations

import argparse
import json
import sys

from .federation import normalize_external_run, validate_federation_registry
from .io import BenchmarkFormatError, read_json, write_json


def command_validate(args: argparse.Namespace) -> int:
    report = validate_federation_registry(read_json(args.registry))
    output = {
        "schema": "tiai.agentbench.federation_validation.v1",
        "status": "PASSED",
        "benchmark": report["benchmark"],
        "version": report["version"],
        "anchor_count": report["anchor_count"],
        "executable_anchor_count": report["executable_anchor_count"],
        "industry_count": report["industry_count"],
        "executable_industries": sorted(
            family for family, row in report["industry_coverage"].items()
            if row["status"] == "EXECUTABLE"
        ),
    }
    if args.output:
        write_json(args.output, output)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_executable_anchors is not None and output["executable_anchor_count"] < args.require_executable_anchors:
        return 1
    return 0


def command_normalize(args: argparse.Namespace) -> int:
    report = normalize_external_run(
        read_json(args.registry), args.benchmark_id, read_json(args.input)
    )
    if args.output:
        write_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.min_native_success is not None:
        observed = report["metrics"]["native_verified_success"]
        if observed is None or observed + 1e-12 < args.min_native_success:
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tiai_matbench.federation_cli",
        description="Validate FederationCore and normalize native upstream result artifacts without redefining success semantics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--registry", required=True)
    validate.add_argument("--output")
    validate.add_argument("--require-executable-anchors", type=int)
    validate.set_defaults(func=command_validate)
    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("--registry", required=True)
    normalize.add_argument("--benchmark-id", required=True)
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--output")
    normalize.add_argument("--min-native-success", type=float)
    normalize.set_defaults(func=command_normalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (BenchmarkFormatError, OSError) as exc:
        print(f"TiAI-AgentBench federation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
