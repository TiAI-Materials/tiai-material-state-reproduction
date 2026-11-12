"""Federate native benchmark results without redefining upstream success.

The federation layer accepts result artifacts emitted by mature external
benchmarks and maps only observable quantities into a shared report. Missing
human-loop, cost, provenance or safety evidence remains missing; it is never
silently imputed as success.
"""
from __future__ import annotations

from typing import Any, Callable

from .io import BenchmarkFormatError

FEDERATION_REGISTRY_SCHEMA = "tiai.agentbench.federation_registry.v1"
FEDERATED_REPORT_SCHEMA = "tiai.agentbench.federated_report.v1"

SUPPORTED_ADAPTERS = {
    "SWE_BENCH_RESULTS_V2",
    "OSWORLD_RESULTS_V1",
    "CALVIN_RESULTS_V1",
}
ADAPTER_STATUSES = {"EXECUTABLE", "CATALOG_ONLY", "GAP"}
COVERAGE_STATUSES = {"EXECUTABLE", "ANCHORED", "GAP", "REQUIRES_PARTNER"}
EXECUTION_MODES = {
    "SANDBOX_CODE",
    "REAL_COMPUTER",
    "DIGITAL_TWIN",
    "PRECOMPUTED_REPLAY",
    "LIVE_HPC",
    "PHYSICAL_LAB",
    "HUMAN_EXPERT_REVIEW",
}
VERIFIABILITY_LEVELS = {
    "V0_LOCAL_DETERMINISTIC",
    "V1_COMPUTE_OR_REPLAY",
    "V2_DIGITAL_TWIN",
    "V3_PHYSICAL_INSTRUMENT",
    "V4_SOCIO_REGULATORY",
}
REPLACEMENT_SCOPES = {
    "TASK",
    "WORKFLOW",
    "ROLE",
    "TEAM",
    "ORGANIZATION",
    "INDUSTRY",
}


class FederationError(BenchmarkFormatError):
    """Raised when a federation registry or upstream result is malformed."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FederationError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise FederationError(f"{label} must be a list")
    if nonempty and not value:
        raise FederationError(f"{label} must not be empty")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FederationError(f"{label} must be a nonempty string")
    return value


def _number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FederationError(f"{label} must be a number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise FederationError(f"{label} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise FederationError(f"{label} must be <= {maximum}")
    return result


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FederationError(f"{label} must be an integer")
    if value < minimum:
        raise FederationError(f"{label} must be >= {minimum}")
    return value


def _unique_texts(
    value: Any,
    label: str,
    *,
    nonempty: bool = False,
) -> list[str]:
    rows = [
        _text(item, f"{label}[{i}]")
        for i, item in enumerate(_list(value, label, nonempty=nonempty))
    ]
    if len(rows) != len(set(rows)):
        raise FederationError(f"{label} contains duplicates")
    return rows


def validate_federation_registry(registry: dict[str, Any]) -> dict[str, Any]:
    registry = _object(registry, "registry")
    if registry.get("schema") != FEDERATION_REGISTRY_SCHEMA:
        raise FederationError(
            f"invalid federation registry schema: {registry.get('schema')!r}"
        )
    for key in ("benchmark", "version", "policy"):
        _text(registry.get(key), f"registry.{key}")

    expected_families = set(
        _unique_texts(
            registry.get("expected_industry_families"),
            "registry.expected_industry_families",
            nonempty=True,
        )
    )

    anchors: dict[str, dict[str, Any]] = {}
    for i, raw in enumerate(
        _list(registry.get("anchors"), "registry.anchors", nonempty=True)
    ):
        row = _object(raw, f"registry.anchors[{i}]")
        benchmark_id = _text(
            row.get("benchmark_id"),
            f"registry.anchors[{i}].benchmark_id",
        )
        if benchmark_id in anchors:
            raise FederationError(f"duplicate benchmark_id: {benchmark_id}")
        for key in (
            "title",
            "industry_family",
            "official_repository",
            "native_success_semantics",
        ):
            _text(row.get(key), f"registry.anchors[{i}].{key}")
        if row["industry_family"] not in expected_families:
            raise FederationError(
                f"anchor {benchmark_id} references unknown industry family "
                f"{row['industry_family']!r}"
            )
        if not row["official_repository"].startswith("https://github.com/"):
            raise FederationError(
                f"anchor {benchmark_id} official_repository must be a GitHub URL"
            )
        status = _text(
            row.get("adapter_status"),
            f"registry.anchors[{i}].adapter_status",
        )
        if status not in ADAPTER_STATUSES:
            raise FederationError(
                f"anchor {benchmark_id} has unknown adapter_status {status!r}"
            )
        adapter = row.get("result_adapter")
        if status == "EXECUTABLE":
            if adapter not in SUPPORTED_ADAPTERS:
                raise FederationError(
                    f"anchor {benchmark_id} has unsupported executable adapter "
                    f"{adapter!r}"
                )
        elif adapter not in (None, "NONE"):
            raise FederationError(
                f"anchor {benchmark_id} must use result_adapter NONE when not "
                "executable"
            )
        mode = _text(
            row.get("execution_mode"),
            f"registry.anchors[{i}].execution_mode",
        )
        level = _text(
            row.get("verifiability_level"),
            f"registry.anchors[{i}].verifiability_level",
        )
        scope = _text(
            row.get("replacement_scope"),
            f"registry.anchors[{i}].replacement_scope",
        )
        if mode not in EXECUTION_MODES:
            raise FederationError(
                f"anchor {benchmark_id} has unknown execution_mode {mode!r}"
            )
        if level not in VERIFIABILITY_LEVELS:
            raise FederationError(
                f"anchor {benchmark_id} has unknown verifiability_level {level!r}"
            )
        if scope not in REPLACEMENT_SCOPES:
            raise FederationError(
                f"anchor {benchmark_id} has unknown replacement_scope {scope!r}"
            )
        _unique_texts(
            row.get("source_files"),
            f"registry.anchors[{i}].source_files",
            nonempty=True,
        )
        anchors[benchmark_id] = row

    coverage: dict[str, dict[str, Any]] = {}
    for i, raw in enumerate(
        _list(
            registry.get("industry_coverage"),
            "registry.industry_coverage",
            nonempty=True,
        )
    ):
        row = _object(raw, f"registry.industry_coverage[{i}]")
        family = _text(
            row.get("industry_family"),
            f"registry.industry_coverage[{i}].industry_family",
        )
        if family in coverage:
            raise FederationError(f"duplicate industry coverage row: {family}")
        status = _text(
            row.get("status"),
            f"registry.industry_coverage[{i}].status",
        )
        if status not in COVERAGE_STATUSES:
            raise FederationError(
                f"industry {family} has unknown coverage status {status!r}"
            )
        benchmark_ids = _unique_texts(
            row.get("benchmark_ids", []),
            f"registry.industry_coverage[{i}].benchmark_ids",
        )
        unknown = sorted(set(benchmark_ids) - set(anchors))
        if unknown:
            raise FederationError(
                f"industry {family} references unknown benchmarks: {unknown}"
            )
        if status in {"EXECUTABLE", "ANCHORED"} and not benchmark_ids:
            raise FederationError(
                f"industry {family} status {status} requires benchmark_ids"
            )
        _text(
            row.get("next_minimum_task"),
            f"registry.industry_coverage[{i}].next_minimum_task",
        )
        coverage[family] = row

    if set(coverage) != expected_families:
        raise FederationError(
            "industry_coverage must contain every expected family exactly once: "
            f"missing={sorted(expected_families - set(coverage))}, "
            f"extra={sorted(set(coverage) - expected_families)}"
        )

    return {
        "benchmark": registry["benchmark"],
        "version": registry["version"],
        "anchor_count": len(anchors),
        "executable_anchor_count": sum(
            row["adapter_status"] == "EXECUTABLE"
            for row in anchors.values()
        ),
        "industry_count": len(coverage),
        "anchors": anchors,
        "industry_coverage": coverage,
    }


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _base_report(
    anchor: dict[str, Any],
    task_count: int,
    metrics: dict[str, float | None],
    gaps: list[str],
    native_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": FEDERATED_REPORT_SCHEMA,
        "benchmark_id": anchor["benchmark_id"],
        "title": anchor["title"],
        "industry_family": anchor["industry_family"],
        "result_adapter": anchor["result_adapter"],
        "task_count": task_count,
        "metrics": metrics,
        "evidence_gaps": sorted(set(gaps)),
        "native_summary": native_summary,
        "claim_boundary": (
            "Only native upstream outcomes are normalized. Missing safety, "
            "human-intervention, cost, provenance or false-completion evidence "
            "remains unknown and cannot be counted as success."
        ),
    }


def normalize_swe_bench(
    anchor: dict[str, Any],
    payload: Any,
) -> dict[str, Any]:
    row = _object(payload, "SWE-bench results")
    if row.get("schema_version") != 2:
        raise FederationError("SWE-bench results schema_version must be 2")
    count_fields = [
        "total_instances",
        "submitted_instances",
        "completed_instances",
        "resolved_instances",
        "unresolved_instances",
        "infra_failure_instances",
        "ambiguous_failure_instances",
        "empty_patch_instances",
        "error_instances",
    ]
    counts = {
        key: _integer(row.get(key), f"SWE-bench.{key}")
        for key in count_fields
    }
    total = counts["total_instances"]
    if (
        counts["resolved_instances"] + counts["unresolved_instances"]
        > counts["completed_instances"]
    ):
        raise FederationError(
            "SWE-bench resolved+unresolved cannot exceed completed_instances"
        )
    if any(value > total for value in counts.values()):
        raise FederationError("SWE-bench count cannot exceed total_instances")
    for key in (
        "resolved_ids",
        "unresolved_ids",
        "infra_failure_ids",
        "error_ids",
    ):
        ids = _unique_texts(row.get(key), f"SWE-bench.{key}")
        expected = counts[key.replace("_ids", "_instances")]
        if len(ids) != expected:
            raise FederationError(
                f"SWE-bench {key} length differs from count"
            )
    metrics = {
        "native_verified_success": _ratio(
            counts["resolved_instances"], total
        ),
        "execution_coverage": _ratio(
            counts["completed_instances"], total
        ),
        "infrastructure_reliability": (
            None
            if total == 0
            else 1.0 - counts["infra_failure_instances"] / total
        ),
        "long_horizon_depth": None,
        "trajectory_safety": None,
        "human_loop_fraction": None,
        "false_completion_rate": None,
        "resource_normalized_utility": None,
    }
    return _base_report(
        anchor,
        total,
        metrics,
        [
            "TRAJECTORY_SAFETY_NOT_REPORTED",
            "HUMAN_INTERVENTION_NOT_REPORTED",
            "COST_NOT_REPORTED",
            "FALSE_COMPLETION_NOT_REPORTED",
        ],
        counts,
    )


def normalize_osworld(
    anchor: dict[str, Any],
    payload: Any,
) -> dict[str, Any]:
    rows = _list(payload, "OSWorld results", nonempty=True)
    seen: set[tuple[str, str]] = set()
    total_score = 0.0
    scored = 0
    errors = 0
    applications: set[str] = set()
    for i, raw in enumerate(rows):
        row = _object(raw, f"OSWorld[{i}]")
        application = _text(
            row.get("application"),
            f"OSWorld[{i}].application",
        )
        task_id = _text(row.get("task_id"), f"OSWorld[{i}].task_id")
        key = (application, task_id)
        if key in seen:
            raise FederationError(f"duplicate OSWorld task result: {key}")
        seen.add(key)
        applications.add(application)
        status = _text(row.get("status"), f"OSWorld[{i}].status")
        if status not in {"success", "error"}:
            raise FederationError(
                f"OSWorld[{i}].status must be success or error"
            )
        if status == "error":
            errors += 1
        score = row.get("score")
        if score is not None:
            score_value = _number(
                score,
                f"OSWorld[{i}].score",
                minimum=0.0,
                maximum=1.0,
            )
            total_score += score_value
            scored += 1
        # An unscored/error attempt remains in the denominator and contributes zero.
    total = len(rows)
    metrics = {
        "native_verified_success": total_score / total,
        "execution_coverage": scored / total,
        "infrastructure_reliability": 1.0 - errors / total,
        "long_horizon_depth": None,
        "trajectory_safety": None,
        "human_loop_fraction": None,
        "false_completion_rate": None,
        "resource_normalized_utility": None,
    }
    return _base_report(
        anchor,
        total,
        metrics,
        [
            "TRAJECTORY_SAFETY_NOT_REPORTED",
            "HUMAN_INTERVENTION_NOT_REPORTED",
            "COST_NOT_REPORTED",
            "FALSE_COMPLETION_NOT_REPORTED",
        ],
        {
            "applications": sorted(applications),
            "scored_tasks": scored,
            "error_tasks": errors,
        },
    )


def normalize_calvin(
    anchor: dict[str, Any],
    payload: Any,
) -> dict[str, Any]:
    rows = _object(payload, "CALVIN results")
    if not rows:
        raise FederationError("CALVIN results must not be empty")
    epochs: list[tuple[str, dict[str, Any], float]] = []
    for epoch, raw in rows.items():
        data = _object(raw, f"CALVIN[{epoch!r}]")
        avg_seq_len = _number(
            data.get("avg_seq_len"),
            f"CALVIN[{epoch!r}].avg_seq_len",
            minimum=0.0,
            maximum=5.0,
        )
        chain_sr = _object(
            data.get("chain_sr"),
            f"CALVIN[{epoch!r}].chain_sr",
        )
        for step in range(1, 6):
            key = str(step) if str(step) in chain_sr else step
            _number(
                chain_sr.get(key),
                f"CALVIN[{epoch!r}].chain_sr[{step}]",
                minimum=0.0,
                maximum=1.0,
            )
        task_info = _object(
            data.get("task_info"),
            f"CALVIN[{epoch!r}].task_info",
        )
        for task, raw_counts in task_info.items():
            counts = _object(
                raw_counts,
                f"CALVIN[{epoch!r}].task_info[{task!r}]",
            )
            success = _integer(
                counts.get("success"),
                f"CALVIN[{epoch!r}].task_info[{task!r}].success",
            )
            total = _integer(
                counts.get("total"),
                f"CALVIN[{epoch!r}].task_info[{task!r}].total",
            )
            if success > total:
                raise FederationError(
                    "CALVIN task success cannot exceed total"
                )
        epochs.append((str(epoch), data, avg_seq_len))
    selected_epoch, selected, avg_seq_len = max(
        epochs,
        key=lambda item: item[2],
    )
    task_success = sum(
        int(value["success"])
        for value in selected["task_info"].values()
    )
    task_total = sum(
        int(value["total"])
        for value in selected["task_info"].values()
    )
    chain_sr = selected["chain_sr"]
    chain5_key = "5" if "5" in chain_sr else 5
    metrics = {
        "native_verified_success": _ratio(task_success, task_total),
        "execution_coverage": None,
        "infrastructure_reliability": None,
        "long_horizon_depth": avg_seq_len / 5.0,
        "five_instruction_chain_success": float(chain_sr[chain5_key]),
        "trajectory_safety": None,
        "human_loop_fraction": None,
        "false_completion_rate": None,
        "resource_normalized_utility": None,
    }
    return _base_report(
        anchor,
        task_total,
        metrics,
        [
            "TRAJECTORY_SAFETY_NOT_REPORTED",
            "INFRASTRUCTURE_FAILURES_NOT_REPORTED",
            "HUMAN_INTERVENTION_NOT_REPORTED",
            "COST_NOT_REPORTED",
            "FALSE_COMPLETION_NOT_REPORTED",
        ],
        {
            "selected_epoch": selected_epoch,
            "selection_rule": "MAX_AVG_SEQ_LEN",
            "avg_seq_len": avg_seq_len,
            "task_success": task_success,
            "task_total": task_total,
        },
    )


_NORMALIZERS: dict[
    str,
    Callable[[dict[str, Any], Any], dict[str, Any]],
] = {
    "SWE_BENCH_RESULTS_V2": normalize_swe_bench,
    "OSWORLD_RESULTS_V1": normalize_osworld,
    "CALVIN_RESULTS_V1": normalize_calvin,
}


def normalize_external_run(
    registry: dict[str, Any],
    benchmark_id: str,
    payload: Any,
) -> dict[str, Any]:
    validated = validate_federation_registry(registry)
    try:
        anchor = validated["anchors"][benchmark_id]
    except KeyError as exc:
        raise FederationError(f"unknown benchmark_id: {benchmark_id}") from exc
    if anchor["adapter_status"] != "EXECUTABLE":
        raise FederationError(
            f"benchmark {benchmark_id} does not have an executable adapter"
        )
    return _NORMALIZERS[anchor["result_adapter"]](anchor, payload)
