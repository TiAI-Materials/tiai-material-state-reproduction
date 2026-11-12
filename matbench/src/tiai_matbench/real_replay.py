"""Deterministic grading for source-bound RealReplayCore tasks.

Real replay tasks expose a work contract and immutable source identities while
keeping the scientific answer key separate. The grader checks the decision,
required and forbidden actions, evidence coverage, claim ceiling, rationale
coverage, and false-completion behavior without an LLM judge.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable
import re

TASK_SCHEMA = "tiai.agentbench.real_replay_task.v1"
REFERENCE_SCHEMA = "tiai.agentbench.real_replay_reference.v1"
SUBMISSION_SCHEMA = "tiai.agentbench.real_replay_submission.v1"
REPORT_SCHEMA = "tiai.agentbench.real_replay_report.v1"

VALID_DATA_KINDS = {"REAL_RELEASED", "PRIVATE_HIDDEN", "SYNTHETIC_PROTOCOL_TEST"}
VALID_EXECUTION_MODES = {
    "STATIC_EVIDENCE",
    "SANDBOX_CODE",
    "PRECOMPUTED_REPLAY",
    "LIVE_HPC",
    "DIGITAL_TWIN",
    "PHYSICAL_LAB",
    "HUMAN_EXPERT_REVIEW",
}
CLAIM_ORDER = {
    "EVIDENCE_ONLY": 0,
    "LOCAL_COMPUTATIONAL_RESULT": 1,
    "LOCAL_COMPUTATIONAL_CHAMPION": 2,
    "MECHANISM_SUPPORTED": 3,
    "EXPERIMENTALLY_VALIDATED": 4,
    "GENERALIZED_OR_GLOBAL": 5,
}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RealReplayError(ValueError):
    """Raised when a replay task, reference, or submission is malformed."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RealReplayError(f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RealReplayError(f"{label} must be a nonempty string")
    return value


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise RealReplayError(f"{label} must be a boolean")
    return value


def _number(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RealReplayError(f"{label} must be a number")
    result = float(value)
    if result < minimum:
        raise RealReplayError(f"{label} must be >= {minimum}")
    return result


def _unique_text_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise RealReplayError(f"{label} must be a list")
    rows = [_text(item, f"{label}[{idx}]") for idx, item in enumerate(value)]
    if nonempty and not rows:
        raise RealReplayError(f"{label} must not be empty")
    if len(rows) != len(set(rows)):
        raise RealReplayError(f"{label} contains duplicates")
    return rows


def _claim_level(value: Any, label: str) -> str:
    value = _text(value, label)
    if value not in CLAIM_ORDER:
        raise RealReplayError(f"{label} has unknown claim level {value!r}")
    return value


def validate_replay_task(raw: dict[str, Any]) -> dict[str, Any]:
    row = _object(raw, "task")
    if row.get("schema") != TASK_SCHEMA:
        raise RealReplayError(f"invalid task schema: {row.get('schema')!r}")
    task_id = _text(row.get("task_id"), "task.task_id")
    for key in ("title", "objective", "domain_adapter"):
        _text(row.get(key), f"task.{key}")
    data_kind = _text(row.get("data_kind"), "task.data_kind")
    if data_kind not in VALID_DATA_KINDS:
        raise RealReplayError(f"task.data_kind is invalid: {data_kind!r}")
    execution_mode = _text(row.get("execution_mode"), "task.execution_mode")
    if execution_mode not in VALID_EXECUTION_MODES:
        raise RealReplayError(f"task.execution_mode is invalid: {execution_mode!r}")
    suites = _unique_text_list(row.get("suite_ids"), "task.suite_ids", nonempty=True)
    allowed_actions = _unique_text_list(
        row.get("allowed_actions"), "task.allowed_actions", nonempty=True
    )
    claim_ceiling = _claim_level(row.get("claim_ceiling"), "task.claim_ceiling")

    source = _object(row.get("source"), "task.source")
    repository = _text(source.get("repository"), "task.source.repository")
    commit_sha = _text(source.get("commit_sha"), "task.source.commit_sha")
    if not _SHA_RE.fullmatch(commit_sha):
        raise RealReplayError(
            "task.source.commit_sha must be a 40-character lowercase Git SHA"
        )
    artifact_paths = _unique_text_list(
        source.get("artifact_paths"), "task.source.artifact_paths", nonempty=True
    )
    if any(
        path.startswith("/")
        or ".." in path.split("/")
        or "\\" in path
        for path in artifact_paths
    ):
        raise RealReplayError(
            "task.source.artifact_paths must be safe repository-relative paths"
        )

    work_units = row.get("work_units")
    if not isinstance(work_units, list) or not work_units:
        raise RealReplayError("task.work_units must be a nonempty list")
    unit_ids: set[str] = set()
    baseline_minutes = 0.0
    for idx, item in enumerate(work_units):
        unit = _object(item, f"task.work_units[{idx}]")
        unit_id = _text(
            unit.get("work_unit_id"), f"task.work_units[{idx}].work_unit_id"
        )
        if unit_id in unit_ids:
            raise RealReplayError(f"duplicate work_unit_id: {unit_id}")
        unit_ids.add(unit_id)
        _text(unit.get("title"), f"task.work_units[{idx}].title")
        baseline_minutes += _number(
            unit.get("human_baseline_minutes"),
            f"task.work_units[{idx}].human_baseline_minutes",
        )

    return {
        **row,
        "task_id": task_id,
        "suite_ids": suites,
        "allowed_actions": allowed_actions,
        "claim_ceiling": claim_ceiling,
        "source": {
            **source,
            "repository": repository,
            "commit_sha": commit_sha,
            "artifact_paths": artifact_paths,
        },
        "human_baseline_minutes": baseline_minutes,
    }


def validate_replay_reference(raw: dict[str, Any]) -> dict[str, Any]:
    row = _object(raw, "reference")
    if row.get("schema") != REFERENCE_SCHEMA:
        raise RealReplayError(f"invalid reference schema: {row.get('schema')!r}")
    task_id = _text(row.get("task_id"), "reference.task_id")
    expected_decision = _text(
        row.get("expected_decision"), "reference.expected_decision"
    )
    required_actions = _unique_text_list(
        row.get("required_actions"), "reference.required_actions"
    )
    forbidden_actions = _unique_text_list(
        row.get("forbidden_actions"), "reference.forbidden_actions"
    )
    if set(required_actions) & set(forbidden_actions):
        raise RealReplayError(
            "reference action cannot be both required and forbidden"
        )
    required_evidence_refs = _unique_text_list(
        row.get("required_evidence_refs"),
        "reference.required_evidence_refs",
        nonempty=True,
    )
    required_rationale_codes = _unique_text_list(
        row.get("required_rationale_codes"),
        "reference.required_rationale_codes",
        nonempty=True,
    )
    max_claim_level = _claim_level(
        row.get("max_claim_level"), "reference.max_claim_level"
    )
    return {
        **row,
        "task_id": task_id,
        "expected_decision": expected_decision,
        "required_actions": required_actions,
        "forbidden_actions": forbidden_actions,
        "required_evidence_refs": required_evidence_refs,
        "required_rationale_codes": required_rationale_codes,
        "max_claim_level": max_claim_level,
    }


def validate_replay_submission(raw: dict[str, Any]) -> dict[str, Any]:
    row = _object(raw, "submission")
    if row.get("schema") != SUBMISSION_SCHEMA:
        raise RealReplayError(f"invalid submission schema: {row.get('schema')!r}")
    return {
        **row,
        "task_id": _text(row.get("task_id"), "submission.task_id"),
        "decision": _text(row.get("decision"), "submission.decision"),
        "actions": _unique_text_list(row.get("actions"), "submission.actions"),
        "evidence_refs": _unique_text_list(
            row.get("evidence_refs"), "submission.evidence_refs"
        ),
        "rationale_codes": _unique_text_list(
            row.get("rationale_codes"), "submission.rationale_codes"
        ),
        "claim_level": _claim_level(
            row.get("claim_level"), "submission.claim_level"
        ),
        "completion_claim": _bool(
            row.get("completion_claim"), "submission.completion_claim"
        ),
    }


def _index(
    rows: Iterable[dict[str, Any]], validator, label: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = validator(raw)
        task_id = row["task_id"]
        if task_id in result:
            raise RealReplayError(f"duplicate {label} task_id: {task_id}")
        result[task_id] = row
    return result


def index_replay_tasks(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return _index(rows, validate_replay_task, "task")


def index_replay_references(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return _index(rows, validate_replay_reference, "reference")


def index_replay_submissions(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return _index(rows, validate_replay_submission, "submission")


def _coverage(required: list[str], observed: list[str]) -> float:
    if not required:
        return 1.0
    return len(set(required) & set(observed)) / len(required)


def grade_replay_submission(
    tasks: Iterable[dict[str, Any]],
    references: Iterable[dict[str, Any]],
    submissions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    task_index = index_replay_tasks(tasks)
    reference_index = index_replay_references(references)
    submission_index = index_replay_submissions(submissions)
    if set(task_index) != set(reference_index):
        raise RealReplayError("task/reference task_id sets differ")
    unknown = sorted(set(submission_index) - set(task_index))
    if unknown:
        raise RealReplayError(f"submissions contain unknown task_ids: {unknown}")

    reports: list[dict[str, Any]] = []
    violation_counts: Counter[str] = Counter()
    total_weight = 0.0
    weighted_score = 0.0
    successful = 0
    false_completion = 0
    hours_replaced = 0.0

    for task_id, task in task_index.items():
        reference = reference_index[task_id]
        submission = submission_index.get(task_id)
        weight = max(task["human_baseline_minutes"], 1.0)
        total_weight += weight
        violations: list[str] = []
        dimensions = {
            "decision": 0.0,
            "required_actions": 0.0,
            "evidence": 0.0,
            "rationale": 0.0,
            "claim_scope": 0.0,
        }

        if submission is None:
            violations.append("MISSING_SUBMISSION")
            completion_claim = False
        else:
            completion_claim = submission["completion_claim"]
            if submission["decision"] == reference["expected_decision"]:
                dimensions["decision"] = 1.0
            else:
                violations.append("WRONG_DECISION")

            unknown_actions = sorted(
                set(submission["actions"]) - set(task["allowed_actions"])
            )
            if unknown_actions:
                violations.append("UNDECLARED_ACTION")
            forbidden = sorted(
                set(submission["actions"]) & set(reference["forbidden_actions"])
            )
            if forbidden:
                violations.append("FORBIDDEN_ACTION")
            dimensions["required_actions"] = _coverage(
                reference["required_actions"], submission["actions"]
            )
            if dimensions["required_actions"] < 1.0:
                violations.append("REQUIRED_ACTION_MISSING")

            dimensions["evidence"] = _coverage(
                reference["required_evidence_refs"], submission["evidence_refs"]
            )
            if dimensions["evidence"] < 1.0:
                violations.append("REQUIRED_EVIDENCE_MISSING")

            dimensions["rationale"] = _coverage(
                reference["required_rationale_codes"],
                submission["rationale_codes"],
            )
            if dimensions["rationale"] < 1.0:
                violations.append("RATIONALE_INCOMPLETE")

            allowed_claim = min(
                CLAIM_ORDER[task["claim_ceiling"]],
                CLAIM_ORDER[reference["max_claim_level"]],
            )
            if CLAIM_ORDER[submission["claim_level"]] <= allowed_claim:
                dimensions["claim_scope"] = 1.0
            else:
                violations.append("CLAIM_CEILING_BREACH")

        raw_score = (
            0.35 * dimensions["decision"]
            + 0.20 * dimensions["required_actions"]
            + 0.20 * dimensions["evidence"]
            + 0.15 * dimensions["rationale"]
            + 0.10 * dimensions["claim_scope"]
        )
        fatal_codes = {
            "MISSING_SUBMISSION",
            "WRONG_DECISION",
            "FORBIDDEN_ACTION",
            "CLAIM_CEILING_BREACH",
            "REQUIRED_EVIDENCE_MISSING",
        }
        fatal = any(code in fatal_codes for code in violations)
        score = 0.0 if fatal else raw_score
        if completion_claim and (fatal or score < 1.0 - 1e-12):
            violations.append("FALSE_COMPLETION_CLAIM")
            false_completion += 1
            score = 0.0
        passed = score >= 1.0 - 1e-12
        if passed:
            successful += 1
            hours_replaced += task["human_baseline_minutes"] / 60.0
        weighted_score += weight * score
        violation_counts.update(violations)
        reports.append(
            {
                "task_id": task_id,
                "data_kind": task["data_kind"],
                "source_commit": task["source"]["commit_sha"],
                "score": score,
                "passed": passed,
                "fatal": fatal,
                "dimensions": dimensions,
                "violations": violations,
            }
        )

    task_count = len(task_index)
    macro_score = (
        sum(item["score"] for item in reports) / task_count
        if task_count
        else None
    )
    weighted = weighted_score / total_weight if total_weight else None
    return {
        "schema": REPORT_SCHEMA,
        "task_count": task_count,
        "submission_count": len(submission_index),
        "macro_score": macro_score,
        "human_work_weighted_score": weighted,
        "verified_success_rate": successful / task_count if task_count else None,
        "false_completion_rate": (
            false_completion / task_count if task_count else None
        ),
        "verified_hours_replaced": hours_replaced,
        "violation_counts": dict(sorted(violation_counts.items())),
        "tasks": reports,
    }
