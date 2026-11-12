"""Validation and reporting for the TiAI-AgentBench full-stack suite registry."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .io import BenchmarkFormatError

REGISTRY_SCHEMA = "tiai.agentbench.suite_registry.v1"
TASK_SPEC_SCHEMA = "tiai.agentbench.task_spec.v1"

VALID_HORIZONS = {"UNIT", "WORKFLOW", "CAMPAIGN", "CLOSED_LOOP"}
VALID_AUTONOMY_LEVELS = {"A0", "A1", "A2", "A3", "A4", "A5"}
VALID_EXECUTION_MODES = {
    "STATIC_EVIDENCE",
    "SANDBOX_CODE",
    "PRECOMPUTED_REPLAY",
    "LIVE_HPC",
    "DIGITAL_TWIN",
    "PHYSICAL_LAB",
    "HUMAN_EXPERT_REVIEW",
}
VALID_READINESS = {
    "EXECUTABLE_PUBLIC_DEV",
    "EXECUTABLE_PRIVATE_REPLAY",
    "DESIGN_READY",
    "REQUIRES_SANITIZED_ASSETS",
    "REQUIRES_LIVE_HPC",
    "REQUIRES_DIGITAL_TWIN",
    "REQUIRES_PHYSICAL_LAB",
}
VALID_RESOURCE_CLASSES = {"LIGHT", "MEDIUM", "HEAVY", "PHYSICAL"}
REQUIRED_METRICS = {"VSS", "WRC", "E2E_ASR", "HIR", "RRR", "RNU", "SSR"}


class SuiteValidationError(BenchmarkFormatError):
    """Raised when the full-stack suite registry or roadmap is inconsistent."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SuiteValidationError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise SuiteValidationError(f"{label} must be a list")
    if nonempty and not value:
        raise SuiteValidationError(f"{label} must not be empty")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SuiteValidationError(f"{label} must be a nonempty string")
    return value


def _unique_text_list(value: Any, label: str, *, allowed: set[str] | None = None) -> list[str]:
    items = _list(value, label, nonempty=True)
    result: list[str] = []
    for index, item in enumerate(items):
        text = _text(item, f"{label}[{index}]")
        if allowed is not None and text not in allowed:
            raise SuiteValidationError(f"{label}[{index}] has unsupported value: {text!r}")
        result.append(text)
    if len(result) != len(set(result)):
        raise SuiteValidationError(f"{label} contains duplicates")
    return result


def _validate_named_map(value: Any, label: str, required: set[str]) -> set[str]:
    rows = _object(value, label)
    keys = set(rows)
    if keys != required:
        raise SuiteValidationError(f"{label} must contain exactly {sorted(required)}")
    for key, raw in rows.items():
        if isinstance(raw, str):
            _text(raw, f"{label}.{key}")
        else:
            item = _object(raw, f"{label}.{key}")
            for field in ("name", "definition"):
                _text(item.get(field), f"{label}.{key}.{field}")
    return keys


def validate_suite_registry(registry: dict[str, Any]) -> dict[str, Any]:
    """Validate the umbrella benchmark registry and return useful indexes."""

    registry = _object(registry, "registry")
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise SuiteValidationError(f"invalid registry schema: {registry.get('schema')!r}")
    for key in ("umbrella_benchmark", "working_package", "version", "mission"):
        _text(registry.get(key), f"registry.{key}")
    _unique_text_list(registry.get("principles"), "registry.principles")
    horizon_ids = _validate_named_map(registry.get("horizons"), "registry.horizons", VALID_HORIZONS)
    autonomy_ids = _validate_named_map(
        registry.get("autonomy_levels"), "registry.autonomy_levels", VALID_AUTONOMY_LEVELS
    )
    execution_modes = set(
        _unique_text_list(
            registry.get("execution_modes"), "registry.execution_modes", allowed=VALID_EXECUTION_MODES
        )
    )
    if execution_modes != VALID_EXECUTION_MODES:
        raise SuiteValidationError("registry.execution_modes must declare the complete vocabulary")
    readiness_states = set(
        _unique_text_list(
            registry.get("readiness_states"), "registry.readiness_states", allowed=VALID_READINESS
        )
    )
    if readiness_states != VALID_READINESS:
        raise SuiteValidationError("registry.readiness_states must declare the complete vocabulary")

    metrics = _object(registry.get("global_metrics"), "registry.global_metrics")
    if not REQUIRED_METRICS <= set(metrics):
        raise SuiteValidationError(
            f"registry.global_metrics missing {sorted(REQUIRED_METRICS - set(metrics))}"
        )
    for metric_id, raw in metrics.items():
        _text(metric_id, "registry.global_metrics key")
        item = _object(raw, f"registry.global_metrics.{metric_id}")
        for field in ("name", "definition"):
            _text(item.get(field), f"registry.global_metrics.{metric_id}.{field}")

    suites: dict[str, dict[str, Any]] = {}
    slugs: set[str] = set()
    for index, raw in enumerate(_list(registry.get("suites"), "registry.suites", nonempty=True)):
        row = _object(raw, f"registry.suites[{index}]")
        suite_id = _text(row.get("id"), f"registry.suites[{index}].id")
        if suite_id in suites:
            raise SuiteValidationError(f"duplicate suite id: {suite_id}")
        slug = _text(row.get("slug"), f"registry.suites[{index}].slug")
        if slug in slugs:
            raise SuiteValidationError(f"duplicate suite slug: {slug}")
        slugs.add(slug)
        for key in ("title", "objective"):
            _text(row.get(key), f"registry.suites[{index}].{key}")
        readiness = _text(row.get("readiness"), f"registry.suites[{index}].readiness")
        if readiness not in VALID_READINESS:
            raise SuiteValidationError(f"unsupported suite readiness: {readiness}")
        _unique_text_list(row.get("modes"), f"registry.suites[{index}].modes", allowed=VALID_EXECUTION_MODES)
        _unique_text_list(row.get("autonomy"), f"registry.suites[{index}].autonomy", allowed=VALID_AUTONOMY_LEVELS)
        _unique_text_list(row.get("horizons"), f"registry.suites[{index}].horizons", allowed=VALID_HORIZONS)
        pack = row.get("pack")
        if pack is not None:
            _text(pack, f"registry.suites[{index}].pack")
        for key in ("artifacts", "gates", "examples"):
            _unique_text_list(row.get(key), f"registry.suites[{index}].{key}")
        suites[suite_id] = row

    if len(suites) != 12:
        raise SuiteValidationError(f"registry must declare 12 suites, observed {len(suites)}")
    return {
        "suites": suites,
        "metric_ids": set(metrics),
        "autonomy_ids": autonomy_ids,
        "horizon_ids": horizon_ids,
    }


def validate_task_roadmap(
    records: Iterable[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    """Validate staged task specifications against the suite registry."""

    indexes = validate_suite_registry(registry)
    suites = indexes["suites"]
    seen: set[str] = set()
    by_suite: Counter[str] = Counter()
    by_readiness: Counter[str] = Counter()
    by_mode: Counter[str] = Counter()
    by_horizon: Counter[str] = Counter()
    total = 0
    for index, raw in enumerate(records):
        row = _object(raw, f"roadmap[{index}]")
        if row.get("schema") != TASK_SPEC_SCHEMA:
            raise SuiteValidationError(f"roadmap[{index}] has invalid schema")
        task_id = _text(row.get("id"), f"roadmap[{index}].id")
        if task_id in seen:
            raise SuiteValidationError(f"duplicate task id: {task_id}")
        seen.add(task_id)
        suite_id = _text(row.get("suite"), f"roadmap[{index}].suite")
        if suite_id not in suites:
            raise SuiteValidationError(f"roadmap[{index}] references unknown suite: {suite_id}")
        _text(row.get("title"), f"roadmap[{index}].title")
        horizon = _text(row.get("horizon"), f"roadmap[{index}].horizon")
        autonomy = _text(row.get("autonomy"), f"roadmap[{index}].autonomy")
        mode = _text(row.get("mode"), f"roadmap[{index}].mode")
        readiness = _text(row.get("readiness"), f"roadmap[{index}].readiness")
        resource = _text(row.get("resource"), f"roadmap[{index}].resource")
        if horizon not in VALID_HORIZONS or autonomy not in VALID_AUTONOMY_LEVELS:
            raise SuiteValidationError(f"roadmap[{index}] has invalid horizon/autonomy")
        if mode not in VALID_EXECUTION_MODES or readiness not in VALID_READINESS:
            raise SuiteValidationError(f"roadmap[{index}] has invalid mode/readiness")
        if resource not in VALID_RESOURCE_CLASSES:
            raise SuiteValidationError(f"roadmap[{index}] has invalid resource class")
        suite = suites[suite_id]
        if horizon not in suite["horizons"]:
            raise SuiteValidationError(f"roadmap[{index}] horizon not declared by {suite_id}")
        if autonomy not in suite["autonomy"]:
            raise SuiteValidationError(f"roadmap[{index}] autonomy not declared by {suite_id}")
        if mode not in suite["modes"]:
            raise SuiteValidationError(f"roadmap[{index}] mode not declared by {suite_id}")
        total += 1
        by_suite[suite_id] += 1
        by_readiness[readiness] += 1
        by_mode[mode] += 1
        by_horizon[horizon] += 1

    if not total:
        raise SuiteValidationError("roadmap must contain at least one task")
    missing = sorted(set(suites) - set(by_suite))
    if missing:
        raise SuiteValidationError(f"roadmap has no task for suites: {missing}")
    return {
        "schema": "tiai.agentbench.registry_validation.v1",
        "status": "PASSED",
        "umbrella_benchmark": registry["umbrella_benchmark"],
        "version": registry["version"],
        "suite_count": len(suites),
        "task_spec_count": total,
        "tasks_by_suite": dict(sorted(by_suite.items())),
        "tasks_by_readiness": dict(sorted(by_readiness.items())),
        "tasks_by_execution_mode": dict(sorted(by_mode.items())),
        "tasks_by_horizon": dict(sorted(by_horizon.items())),
    }


def suite_rows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a compact, stable suite summary for CLI and downstream UIs."""

    validate_suite_registry(registry)
    return [
        {
            "suite_id": suite["id"],
            "title": suite["title"],
            "readiness": suite["readiness"],
            "execution_modes": suite["modes"],
            "autonomy_levels": suite["autonomy"],
            "horizons": suite["horizons"],
            "current_pack": suite["pack"],
        }
        for suite in registry["suites"]
    ]
