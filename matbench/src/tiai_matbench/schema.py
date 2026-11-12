"""Schema validation for benchmark tasks, references and agent responses."""

from __future__ import annotations

from typing import Any, Iterable

from .io import BenchmarkFormatError

TASK_SCHEMA = "tiai.matbench.task.v1"
REFERENCE_SCHEMA = "tiai.matbench.reference.v1"
RESPONSE_SCHEMA = "tiai.matbench.response.v1"
MANIFEST_SCHEMA = "tiai.matbench.manifest.v1"
REPORT_SCHEMA = "tiai.matbench.report.v1"

VALID_DATA_KINDS = {"REAL_RELEASED", "SYNTHETIC_SCORER_TEST"}
VALID_STATUSES = {"ANSWERED", "ABSTAINED", "FAILED"}
VALID_CHECK_KINDS = {
    "exact",
    "numeric",
    "one_of",
    "contains_all",
    "evidence",
}
VALID_DIMENSIONS = {
    "outcome_correctness",
    "evidence_fidelity",
    "state_condition_fidelity",
    "split_integrity",
    "claim_calibration",
    "execution_integrity",
}
VALID_CRITICAL_ACTIONS = {"zero", "cap"}


class ValidationError(BenchmarkFormatError):
    """Raised when a record does not satisfy the benchmark schema."""


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list")
    return value


def _require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string")
    if nonempty and not value.strip():
        raise ValidationError(f"{label} must not be empty")
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{label} must be a boolean")
    return value


def _require_number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} must be a number")
    number = float(value)
    if minimum is not None and number < minimum:
        raise ValidationError(f"{label} must be >= {minimum}")
    return number


def validate_task(task: dict[str, Any]) -> None:
    _require_object(task, "task")
    if task.get("schema") != TASK_SCHEMA:
        raise ValidationError(f"invalid task schema: {task.get('schema')!r}")
    _require_string(task.get("task_id"), "task.task_id")
    _require_string(task.get("benchmark_version"), "task.benchmark_version")
    _require_string(task.get("track"), "task.track")
    if task.get("data_kind") not in VALID_DATA_KINDS:
        raise ValidationError(f"invalid task.data_kind: {task.get('data_kind')!r}")
    _require_string(task.get("prompt"), "task.prompt")
    _require_string(task.get("release_commit"), "task.release_commit")

    inputs = _require_list(task.get("inputs"), "task.inputs")
    if not inputs:
        raise ValidationError("task.inputs must contain at least one asset")
    seen_assets: set[str] = set()
    for index, raw_input in enumerate(inputs):
        item = _require_object(raw_input, f"task.inputs[{index}]")
        asset = _require_string(item.get("asset"), f"task.inputs[{index}].asset")
        if asset in seen_assets:
            raise ValidationError(f"task has duplicate input asset: {asset}")
        seen_assets.add(asset)
        git_sha = _require_string(
            item.get("git_blob_sha"), f"task.inputs[{index}].git_blob_sha"
        )
        if len(git_sha) != 40 or any(ch not in "0123456789abcdef" for ch in git_sha):
            raise ValidationError(
                f"task.inputs[{index}].git_blob_sha must be a lowercase SHA-1"
            )
        locators = _require_list(
            item.get("allowed_locators"),
            f"task.inputs[{index}].allowed_locators",
        )
        if not locators:
            raise ValidationError(
                f"task.inputs[{index}].allowed_locators must not be empty"
            )
        for locator_index, locator in enumerate(locators):
            _require_string(
                locator,
                f"task.inputs[{index}].allowed_locators[{locator_index}]",
            )

    required_output = _require_object(
        task.get("required_output"), "task.required_output"
    )
    statuses = _require_list(
        required_output.get("allowed_statuses"),
        "task.required_output.allowed_statuses",
    )
    if not statuses or any(status not in VALID_STATUSES for status in statuses):
        raise ValidationError(
            "task.required_output.allowed_statuses contains an invalid status"
        )


def validate_reference(reference: dict[str, Any]) -> None:
    _require_object(reference, "reference")
    if reference.get("schema") != REFERENCE_SCHEMA:
        raise ValidationError(
            f"invalid reference schema: {reference.get('schema')!r}"
        )
    _require_string(reference.get("task_id"), "reference.task_id")
    checks = _require_list(reference.get("checks"), "reference.checks")
    if not checks:
        raise ValidationError("reference.checks must not be empty")
    seen_check_ids: set[str] = set()
    for index, raw_check in enumerate(checks):
        check = _require_object(raw_check, f"reference.checks[{index}]")
        check_id = _require_string(
            check.get("check_id"), f"reference.checks[{index}].check_id"
        )
        if check_id in seen_check_ids:
            raise ValidationError(f"duplicate check_id: {check_id}")
        seen_check_ids.add(check_id)
        kind = check.get("kind")
        if kind not in VALID_CHECK_KINDS:
            raise ValidationError(f"invalid check kind: {kind!r}")
        dimension = check.get("dimension")
        if dimension not in VALID_DIMENSIONS:
            raise ValidationError(f"invalid check dimension: {dimension!r}")
        _require_number(
            check.get("weight", 1.0),
            f"reference.checks[{index}].weight",
            minimum=0.0,
        )
        if kind != "evidence":
            _require_string(check.get("path"), f"reference.checks[{index}].path")
        if kind == "numeric":
            _require_number(
                check.get("expected"), f"reference.checks[{index}].expected"
            )
            _require_number(
                check.get("atol", 0.0),
                f"reference.checks[{index}].atol",
                minimum=0.0,
            )
            _require_number(
                check.get("rtol", 0.0),
                f"reference.checks[{index}].rtol",
                minimum=0.0,
            )
        elif kind == "one_of":
            allowed = _require_list(
                check.get("allowed"), f"reference.checks[{index}].allowed"
            )
            if not allowed:
                raise ValidationError("one_of check must define allowed values")
        elif kind == "contains_all":
            required = _require_list(
                check.get("required"), f"reference.checks[{index}].required"
            )
            if not required:
                raise ValidationError("contains_all check must define required values")
        elif kind == "evidence":
            expected = _require_object(
                check.get("expected"), f"reference.checks[{index}].expected"
            )
            _require_string(expected.get("asset"), "evidence expected.asset")
            _require_string(expected.get("git_blob_sha"), "evidence expected.git_blob_sha")
            _require_string(expected.get("locator"), "evidence expected.locator")

        critical = check.get("critical")
        if critical is not None:
            critical = _require_object(
                critical, f"reference.checks[{index}].critical"
            )
            _require_string(critical.get("violation"), "critical.violation")
            action = critical.get("action")
            if action not in VALID_CRITICAL_ACTIONS:
                raise ValidationError(f"invalid critical action: {action!r}")
            if action == "cap":
                cap = _require_number(critical.get("value"), "critical.value")
                if not 0.0 <= cap <= 1.0:
                    raise ValidationError("critical cap value must be in [0, 1]")


def validate_response(response: dict[str, Any]) -> None:
    _require_object(response, "response")
    if response.get("schema") != RESPONSE_SCHEMA:
        raise ValidationError(f"invalid response schema: {response.get('schema')!r}")
    _require_string(response.get("task_id"), "response.task_id")
    if response.get("status") not in VALID_STATUSES:
        raise ValidationError(f"invalid response.status: {response.get('status')!r}")
    _require_object(response.get("answer"), "response.answer")
    evidence = _require_list(response.get("evidence"), "response.evidence")
    for index, raw_evidence in enumerate(evidence):
        item = _require_object(raw_evidence, f"response.evidence[{index}]")
        _require_string(item.get("asset"), f"response.evidence[{index}].asset")
        _require_string(
            item.get("git_blob_sha"),
            f"response.evidence[{index}].git_blob_sha",
        )
        _require_string(item.get("locator"), f"response.evidence[{index}].locator")
    claims = _require_list(response.get("claims"), "response.claims")
    for index, raw_claim in enumerate(claims):
        claim = _require_object(raw_claim, f"response.claims[{index}]")
        _require_string(claim.get("claim_id"), f"response.claims[{index}].claim_id")
        _require_string(claim.get("scope"), f"response.claims[{index}].scope")
        _require_string(claim.get("support"), f"response.claims[{index}].support")
    execution = _require_object(response.get("execution"), "response.execution")
    _require_bool(execution.get("success"), "response.execution.success")
    artifacts = _require_list(
        execution.get("artifacts"), "response.execution.artifacts"
    )
    for index, artifact in enumerate(artifacts):
        _require_string(artifact, f"response.execution.artifacts[{index}]")
    warnings = _require_list(execution.get("warnings"), "response.execution.warnings")
    for index, warning in enumerate(warnings):
        _require_string(warning, f"response.execution.warnings[{index}]")


def validate_manifest(manifest: dict[str, Any]) -> None:
    _require_object(manifest, "manifest")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValidationError(f"invalid manifest schema: {manifest.get('schema')!r}")
    _require_string(manifest.get("benchmark_version"), "manifest.benchmark_version")
    _require_string(manifest.get("release_commit"), "manifest.release_commit")
    weights = _require_object(manifest.get("dimension_weights"), "manifest.dimension_weights")
    unknown = set(weights) - VALID_DIMENSIONS
    if unknown:
        raise ValidationError(f"unknown manifest dimensions: {sorted(unknown)}")
    total = 0.0
    for name, value in weights.items():
        total += _require_number(value, f"manifest.dimension_weights.{name}", minimum=0.0)
    if abs(total - 1.0) > 1e-12:
        raise ValidationError("manifest.dimension_weights must sum to 1")
    counts = _require_object(manifest.get("task_counts"), "manifest.task_counts")
    _require_number(counts.get("total"), "manifest.task_counts.total", minimum=0)
    _require_number(
        counts.get("real_released"), "manifest.task_counts.real_released", minimum=0
    )
    _require_number(
        counts.get("synthetic_scorer_test"),
        "manifest.task_counts.synthetic_scorer_test",
        minimum=0,
    )


def index_unique(records: Iterable[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        value = _require_string(record.get(key), f"{label}[{index}].{key}")
        if value in result:
            raise ValidationError(f"duplicate {label} {key}: {value}")
        result[value] = record
    return result
