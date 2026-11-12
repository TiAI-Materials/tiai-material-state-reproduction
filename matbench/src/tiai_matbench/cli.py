"""Command-line interface for TiAI-MatBench."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .grader import grade_submission, verify_assets
from .io import BenchmarkFormatError, read_json, read_jsonl, write_json
from .schema import (
    ValidationError,
    index_unique,
    validate_manifest,
    validate_reference,
    validate_task,
)


def _load_bundle(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    tasks = read_jsonl(args.tasks)
    references = read_jsonl(args.references)
    manifest = read_json(args.manifest)
    validate_manifest(manifest)
    for task in tasks:
        validate_task(task)
    for reference in references:
        validate_reference(reference)
    task_index = index_unique(tasks, "task_id", "tasks")
    reference_index = index_unique(references, "task_id", "references")
    if set(task_index) != set(reference_index):
        raise ValidationError(
            "task/reference task_id sets differ: "
            f"missing_refs={sorted(set(task_index) - set(reference_index))}, "
            f"extra_refs={sorted(set(reference_index) - set(task_index))}"
        )
    expected_total = int(manifest["task_counts"]["total"])
    expected_real = int(manifest["task_counts"]["real_released"])
    expected_synthetic = int(manifest["task_counts"]["synthetic_scorer_test"])
    observed_real = sum(task["data_kind"] == "REAL_RELEASED" for task in tasks)
    observed_synthetic = sum(
        task["data_kind"] == "SYNTHETIC_SCORER_TEST" for task in tasks
    )
    if (len(tasks), observed_real, observed_synthetic) != (
        expected_total,
        expected_real,
        expected_synthetic,
    ):
        raise ValidationError(
            "manifest task counts do not match task records: "
            f"observed={(len(tasks), observed_real, observed_synthetic)}, "
            f"expected={(expected_total, expected_real, expected_synthetic)}"
        )
    versions = {task["benchmark_version"] for task in tasks}
    commits = {task["release_commit"] for task in tasks}
    if versions != {manifest["benchmark_version"]}:
        raise ValidationError("task benchmark_version differs from manifest")
    if commits != {manifest["release_commit"]}:
        raise ValidationError("task release_commit differs from manifest")

    manifest_assets = {
        item["asset"]: item["git_blob_sha"] for item in manifest["assets"]
    }
    task_assets: dict[str, str] = {}
    for task in tasks:
        for item in task["inputs"]:
            previous = task_assets.setdefault(item["asset"], item["git_blob_sha"])
            if previous != item["git_blob_sha"]:
                raise ValidationError(
                    f"task assets disagree on blob identity for {item['asset']!r}"
                )
    if task_assets != manifest_assets:
        raise ValidationError(
            "manifest asset registry differs from task inputs: "
            f"task_only={sorted(set(task_assets) - set(manifest_assets))}, "
            f"manifest_only={sorted(set(manifest_assets) - set(task_assets))}, "
            "or a registered blob identity differs"
        )

    gate_policy = manifest["critical_gate_policy"]
    zero_score = set(gate_policy["zero_score"])
    caps = {key: float(value) for key, value in gate_policy["caps"].items()}
    for reference in references:
        for check in reference["checks"]:
            critical = check.get("critical")
            if not critical:
                continue
            violation = critical["violation"]
            if critical["action"] == "zero" and violation not in zero_score:
                raise ValidationError(
                    f"reference critical zero gate {violation!r} is absent from manifest"
                )
            if critical["action"] == "cap":
                expected_cap = caps.get(violation)
                observed_cap = float(critical["value"])
                if expected_cap is None or abs(expected_cap - observed_cap) > 1e-12:
                    raise ValidationError(
                        f"reference cap gate {violation!r} differs from manifest"
                    )
    return tasks, references, manifest


def command_validate(args: argparse.Namespace) -> int:
    tasks, references, manifest = _load_bundle(args)
    result = {
        "schema": "tiai.matbench.validation.v1",
        "status": "PASSED",
        "benchmark_version": manifest["benchmark_version"],
        "release_commit": manifest["release_commit"],
        "tasks": len(tasks),
        "references": len(references),
        "real_released": sum(task["data_kind"] == "REAL_RELEASED" for task in tasks),
        "synthetic_scorer_test": sum(
            task["data_kind"] == "SYNTHETIC_SCORER_TEST" for task in tasks
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_verify_assets(args: argparse.Namespace) -> int:
    tasks, _, _ = _load_bundle(args)
    result = verify_assets(tasks, args.repository_root)
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["all_match"] else 1


def command_grade(args: argparse.Namespace) -> int:
    tasks, references, manifest = _load_bundle(args)
    responses = read_jsonl(args.submission)
    report = grade_submission(
        tasks,
        references,
        responses,
        {key: float(value) for key, value in manifest["dimension_weights"].items()},
    )
    if args.output:
        write_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if (
        args.min_score is not None
        and (report["macro_score"] is None or report["macro_score"] + 1e-12 < args.min_score)
    ):
        return 1
    return 0


def _common_bundle_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tasks", required=True, help="task JSONL path")
    parser.add_argument("--references", required=True, help="reference JSONL path")
    parser.add_argument("--manifest", required=True, help="benchmark manifest JSON path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiai-matbench",
        description=(
            "Deterministic evaluation for source-aware, executable and trustworthy "
            "materials-research agents."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate benchmark records")
    _common_bundle_arguments(validate)
    validate.set_defaults(func=command_validate)

    verify = subparsers.add_parser(
        "verify-assets", help="verify frozen Git blob identities of source assets"
    )
    _common_bundle_arguments(verify)
    verify.add_argument("--repository-root", required=True)
    verify.add_argument("--output")
    verify.set_defaults(func=command_verify_assets)

    grade = subparsers.add_parser("grade", help="grade an agent submission")
    _common_bundle_arguments(grade)
    grade.add_argument("--submission", required=True)
    grade.add_argument("--output")
    grade.add_argument("--min-score", type=float)
    grade.set_defaults(func=command_grade)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (BenchmarkFormatError, ValidationError, OSError) as exc:
        print(f"TiAI-MatBench error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
