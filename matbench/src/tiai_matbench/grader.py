"""Deterministic, non-LLM grading engine for TiAI-MatBench."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .schema import (
    REPORT_SCHEMA,
    ValidationError,
    index_unique,
    validate_reference,
    validate_response,
    validate_task,
)

_MISSING = object()


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    dimension: str
    kind: str
    passed: bool
    weight: float
    observed: Any
    expected: Any
    message: str
    critical: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "dimension": self.dimension,
            "kind": self.kind,
            "passed": self.passed,
            "weight": self.weight,
            "observed": None if self.observed is _MISSING else self.observed,
            "expected": self.expected,
            "message": self.message,
            "critical": self.critical,
        }


def get_path(value: Any, dotted_path: str) -> Any:
    """Resolve a conservative dotted path with integer list indices."""

    current = value
    if dotted_path == "":
        return current
    for part in dotted_path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return _MISSING
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return _MISSING
            current = current[index]
        else:
            return _MISSING
    return current


def _matches_locator(locator: str, allowed: str) -> bool:
    if locator == allowed:
        return True
    if allowed.endswith("/"):
        return locator.startswith(allowed)
    return locator.startswith(allowed + "/")


def _check_evidence(
    response: dict[str, Any], expected: dict[str, Any]
) -> tuple[bool, Any, str]:
    for item in response.get("evidence", []):
        if (
            item.get("asset") == expected.get("asset")
            and item.get("git_blob_sha") == expected.get("git_blob_sha")
            and _matches_locator(str(item.get("locator", "")), expected.get("locator", ""))
        ):
            return True, item, "registered evidence identity and locator matched"
    return False, response.get("evidence", []), "required registered evidence was not cited"


def evaluate_check(check: dict[str, Any], response: dict[str, Any]) -> CheckResult:
    kind = check["kind"]
    expected: Any
    if kind == "evidence":
        expected = check["expected"]
        passed, observed, message = _check_evidence(response, expected)
    else:
        observed = get_path(response, check["path"])
        if kind == "exact":
            expected = check.get("expected")
            passed = observed is not _MISSING and observed == expected
            message = "exact match" if passed else "exact value mismatch"
        elif kind == "numeric":
            expected = check["expected"]
            atol = float(check.get("atol", 0.0))
            rtol = float(check.get("rtol", 0.0))
            passed = (
                observed is not _MISSING
                and not isinstance(observed, bool)
                and isinstance(observed, (int, float))
                and math.isfinite(float(observed))
                and math.isclose(float(observed), float(expected), abs_tol=atol, rel_tol=rtol)
            )
            message = (
                f"numeric match within atol={atol}, rtol={rtol}"
                if passed
                else f"numeric mismatch (atol={atol}, rtol={rtol})"
            )
        elif kind == "one_of":
            expected = check["allowed"]
            passed = observed is not _MISSING and observed in expected
            message = "allowed value" if passed else "value is outside the allowed set"
        elif kind == "contains_all":
            expected = check["required"]
            if isinstance(observed, list):
                passed = all(required in observed for required in expected)
            elif isinstance(observed, str):
                passed = all(str(required) in observed for required in expected)
            else:
                passed = False
            message = "all required values present" if passed else "required values missing"
        else:  # guarded by schema validation
            raise ValidationError(f"unsupported check kind: {kind}")

    return CheckResult(
        check_id=check["check_id"],
        dimension=check["dimension"],
        kind=kind,
        passed=passed,
        weight=float(check.get("weight", 1.0)),
        observed=observed,
        expected=expected,
        message=message,
        critical=check.get("critical"),
    )


def _allowed_evidence(task: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["asset"]: item for item in task["inputs"]}


def audit_evidence_whitelist(
    task: dict[str, Any], response: dict[str, Any]
) -> list[dict[str, Any]]:
    """Reject evidence identities not registered by the closed released-asset task."""

    violations: list[dict[str, Any]] = []
    allowed = _allowed_evidence(task)
    for index, item in enumerate(response.get("evidence", [])):
        asset = item.get("asset")
        registered = allowed.get(asset)
        if registered is None:
            violations.append(
                {
                    "violation": "UNREGISTERED_EVIDENCE_ASSET",
                    "action": "zero",
                    "detail": f"evidence[{index}] cites unregistered asset {asset!r}",
                }
            )
            continue
        if item.get("git_blob_sha") != registered["git_blob_sha"]:
            violations.append(
                {
                    "violation": "EVIDENCE_IDENTITY_MISMATCH",
                    "action": "zero",
                    "detail": f"evidence[{index}] blob identity does not match the frozen asset",
                }
            )
        locator = str(item.get("locator", ""))
        if not any(
            _matches_locator(locator, allowed_locator)
            for allowed_locator in registered["allowed_locators"]
        ):
            violations.append(
                {
                    "violation": "EVIDENCE_LOCATOR_OUT_OF_SCOPE",
                    "action": "zero",
                    "detail": f"evidence[{index}] locator is outside the task evidence scope",
                }
            )
    return violations


def _dimension_scores(checks: Iterable[CheckResult]) -> dict[str, float]:
    numerators: dict[str, float] = {}
    denominators: dict[str, float] = {}
    for check in checks:
        numerators[check.dimension] = numerators.get(check.dimension, 0.0) + (
            check.weight if check.passed else 0.0
        )
        denominators[check.dimension] = denominators.get(check.dimension, 0.0) + check.weight
    return {
        dimension: (numerators.get(dimension, 0.0) / denominator if denominator else 0.0)
        for dimension, denominator in denominators.items()
    }


def _weighted_task_score(
    dimension_scores: dict[str, float], dimension_weights: dict[str, float]
) -> float:
    active_weights = {
        dimension: dimension_weights.get(dimension, 0.0)
        for dimension in dimension_scores
    }
    weight_sum = sum(active_weights.values())
    if weight_sum <= 0.0:
        return 0.0
    return sum(
        dimension_scores[dimension] * weight / weight_sum
        for dimension, weight in active_weights.items()
    )


def grade_task(
    task: dict[str, Any],
    reference: dict[str, Any],
    response: dict[str, Any] | None,
    dimension_weights: dict[str, float],
) -> dict[str, Any]:
    if response is None:
        return {
            "task_id": task["task_id"],
            "track": task["track"],
            "data_kind": task["data_kind"],
            "raw_score": 0.0,
            "score": 0.0,
            "dimension_scores": {},
            "checks": [],
            "violations": [
                {
                    "violation": "MISSING_RESPONSE",
                    "action": "zero",
                    "detail": "no response was submitted for this task",
                }
            ],
        }

    validate_response(response)
    allowed_statuses = task["required_output"]["allowed_statuses"]
    pre_violations = audit_evidence_whitelist(task, response)
    if response["status"] not in allowed_statuses:
        pre_violations.append(
            {
                "violation": "DISALLOWED_RESPONSE_STATUS",
                "action": "zero",
                "detail": (
                    f"status {response['status']!r} not in task allowed statuses "
                    f"{allowed_statuses!r}"
                ),
            }
        )

    checks = [evaluate_check(check, response) for check in reference["checks"]]
    dimension_scores = _dimension_scores(checks)
    raw_score = _weighted_task_score(dimension_scores, dimension_weights)

    violations = list(pre_violations)
    for check in checks:
        if not check.passed and check.critical:
            violations.append(
                {
                    "violation": check.critical["violation"],
                    "action": check.critical["action"],
                    "value": check.critical.get("value"),
                    "detail": f"critical check failed: {check.check_id}",
                }
            )

    score = raw_score
    for violation in violations:
        if violation["action"] == "zero":
            score = 0.0
        elif violation["action"] == "cap":
            score = min(score, float(violation["value"]))
    return {
        "task_id": task["task_id"],
        "track": task["track"],
        "data_kind": task["data_kind"],
        "raw_score": raw_score,
        "score": score,
        "dimension_scores": dimension_scores,
        "checks": [check.as_dict() for check in checks],
        "violations": violations,
    }


def grade_submission(
    tasks: list[dict[str, Any]],
    references: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    dimension_weights: dict[str, float],
) -> dict[str, Any]:
    for task in tasks:
        validate_task(task)
    for reference in references:
        validate_reference(reference)
    for response in responses:
        validate_response(response)

    task_index = index_unique(tasks, "task_id", "tasks")
    reference_index = index_unique(references, "task_id", "references")
    response_index = index_unique(responses, "task_id", "responses")

    missing_references = sorted(set(task_index) - set(reference_index))
    extra_references = sorted(set(reference_index) - set(task_index))
    unknown_responses = sorted(set(response_index) - set(task_index))
    if missing_references:
        raise ValidationError(f"tasks without references: {missing_references}")
    if extra_references:
        raise ValidationError(f"references without tasks: {extra_references}")
    if unknown_responses:
        raise ValidationError(f"responses for unknown tasks: {unknown_responses}")

    task_reports = [
        grade_task(
            task,
            reference_index[task_id],
            response_index.get(task_id),
            dimension_weights,
        )
        for task_id, task in task_index.items()
    ]

    real_reports = [
        report for report in task_reports if report["data_kind"] == "REAL_RELEASED"
    ]
    synthetic_reports = [
        report
        for report in task_reports
        if report["data_kind"] == "SYNTHETIC_SCORER_TEST"
    ]

    def macro(reports: list[dict[str, Any]], field: str) -> float | None:
        if not reports:
            return None
        return sum(float(report[field]) for report in reports) / len(reports)

    # The primary scientific score excludes scorer-only synthetic fixtures.
    macro_score = macro(real_reports, "score")
    raw_macro_score = macro(real_reports, "raw_score")
    all_task_macro_score = macro(task_reports, "score")
    all_task_raw_macro_score = macro(task_reports, "raw_score")
    synthetic_macro_score = macro(synthetic_reports, "score")

    track_values: dict[str, list[float]] = {}
    dimension_values: dict[str, list[float]] = {}
    violation_counts: dict[str, int] = {}
    for report in task_reports:
        track_values.setdefault(report["track"], []).append(report["score"])
        for dimension, score in report["dimension_scores"].items():
            dimension_values.setdefault(dimension, []).append(score)
        for violation in report["violations"]:
            code = violation["violation"]
            violation_counts[code] = violation_counts.get(code, 0) + 1

    return {
        "schema": REPORT_SCHEMA,
        "benchmark": "TiAI-MatBench",
        "benchmark_version": tasks[0]["benchmark_version"] if tasks else None,
        "release_commit": tasks[0]["release_commit"] if tasks else None,
        "n_tasks": len(tasks),
        "n_responses": len(responses),
        "n_real_released_tasks": len(real_reports),
        "n_synthetic_scorer_tasks": len(synthetic_reports),
        "macro_score": macro_score,
        "real_released_macro_score": macro_score,
        "raw_macro_score_before_critical_gates": raw_macro_score,
        "all_task_macro_score": all_task_macro_score,
        "all_task_raw_macro_score_before_critical_gates": all_task_raw_macro_score,
        "synthetic_scorer_macro_score": synthetic_macro_score,
        "track_macro": {
            track: sum(values) / len(values) for track, values in track_values.items()
        },
        "dimension_macro": {
            dimension: sum(values) / len(values)
            for dimension, values in dimension_values.items()
        },
        "violation_counts": dict(sorted(violation_counts.items())),
        "task_reports": task_reports,
    }


def git_blob_sha_bytes(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def verify_assets(tasks: list[dict[str, Any]], repository_root: str | Path) -> dict[str, Any]:
    """Verify registered source assets against their frozen Git blob identities."""

    root = Path(repository_root)
    expected: dict[str, str] = {}
    for task in tasks:
        validate_task(task)
        for item in task["inputs"]:
            previous = expected.setdefault(item["asset"], item["git_blob_sha"])
            if previous != item["git_blob_sha"]:
                raise ValidationError(
                    f"conflicting blob identities for asset {item['asset']!r}"
                )

    results: list[dict[str, Any]] = []
    for relative_path, expected_sha in sorted(expected.items()):
        path = root / relative_path
        if not path.is_file():
            results.append(
                {
                    "asset": relative_path,
                    "expected_git_blob_sha": expected_sha,
                    "observed_git_blob_sha": None,
                    "status": "MISSING",
                }
            )
            continue
        observed_sha = git_blob_sha_bytes(path.read_bytes())
        results.append(
            {
                "asset": relative_path,
                "expected_git_blob_sha": expected_sha,
                "observed_git_blob_sha": observed_sha,
                "status": "MATCH" if observed_sha == expected_sha else "MISMATCH",
            }
        )
    return {
        "schema": "tiai.matbench.asset_verification.v1",
        "repository_root": str(root.resolve()),
        "all_match": all(result["status"] == "MATCH" for result in results),
        "assets": results,
    }
