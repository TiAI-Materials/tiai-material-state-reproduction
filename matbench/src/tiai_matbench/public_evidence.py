"""Deterministic analysis of published CompMat-Bench trajectory manifests.

The module preserves upstream fixed-rule pass/fail semantics.  It extracts
same-task guidance contrasts, repeated-trial reliability, and complete-workflow
stability without inferring missing human-loop, cost, safety, or false-completion
metrics.
"""
from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from typing import Any

from .io import BenchmarkFormatError

PUBLIC_EVIDENCE_SCHEMA = "tiai.agentbench.compmat_public_evidence.v0.8"
EXPECTED_COMPMAT_COMMIT = "03fec439ca9c9b1b14ea914896886b74d3e739bc"
EXPECTED_MANIFEST_BLOB = "de6f82bc77a35b1a01d1d03a608c58e502e36516"
EXPECTED_MODELS = (
    "deepseek_v4_1_flash",
    "gemini_3_8_flash",
    "gpt_5_6_sol",
)


class PublicEvidenceError(BenchmarkFormatError):
    """Raised when a published evidence artifact is malformed or inconsistent."""


def exact_mcnemar_p(full_only: int, reduced_only: int) -> float:
    """Return the exact two-sided McNemar/binomial p-value."""
    if min(full_only, reduced_only) < 0:
        raise PublicEvidenceError("discordant counts must be non-negative")
    n = full_only + reduced_only
    if n == 0:
        return 1.0
    tail = sum(
        math.comb(n, i) for i in range(min(full_only, reduced_only) + 1)
    ) / (2**n)
    return min(1.0, 2.0 * tail)


def pairwise_agreement(successes: int, trials: int) -> float:
    """Agreement probability over all unordered trial pairs for one task."""
    if trials < 1 or successes < 0 or successes > trials:
        raise PublicEvidenceError("invalid successes/trials")
    if trials == 1:
        return 1.0
    return (
        math.comb(successes, 2) + math.comb(trials - successes, 2)
    ) / math.comb(trials, 2)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PublicEvidenceError(f"{label} must be an object")
    return value


def _rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise PublicEvidenceError(f"{label} must be a list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        rows.append(_mapping(row, f"{label}[{index}]"))
    return rows


def _score(row: dict[str, Any], label: str) -> int:
    value = row.get("score")
    if value not in (0, 1):
        raise PublicEvidenceError(f"{label}.score must be 0 or 1")
    return int(value)


def _unique(values: list[str], label: str) -> list[str]:
    if len(values) != len(set(values)):
        raise PublicEvidenceError(f"{label} contains duplicates")
    return values


def _model_summary(rows: list[dict[str, Any]]) -> tuple[dict, dict, Counter]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    passes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    reruns: Counter[str] = Counter()
    for index, row in enumerate(rows):
        campaign = row.get("campaign")
        model = row.get("model")
        if not isinstance(campaign, str) or not campaign:
            raise PublicEvidenceError(f"rows[{index}].campaign must be text")
        if not isinstance(model, str) or not model:
            raise PublicEvidenceError(f"rows[{index}].model must be text")
        counts[campaign][model] += 1
        passes[campaign][model] += _score(row, f"rows[{index}]")
        if row.get("rerun_after_infrastructure_failure") is True:
            reruns[f"{campaign}/{model}"] += 1
    return (
        {key: dict(value) for key, value in counts.items()},
        {key: dict(value) for key, value in passes.items()},
        reruns,
    )


def analyze_compmat_manifest(
    payload: dict[str, Any],
    *,
    raw_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Analyze the public CompMat-Bench v1 trajectory manifest.

    The returned evidence artifact uses all reduced52, repeat20x5, and workflow
    rows.  Reduced-guidance rows are paired only with the same task and model in
    full94, preventing outcome-based selection.
    """
    payload = _mapping(payload, "manifest")
    summary = _mapping(payload.get("summary"), "manifest.summary")
    rows = _rows(payload.get("rows"), "manifest.rows")
    if summary.get("total") != len(rows):
        raise PublicEvidenceError("summary.total does not match row count")

    record_paths = []
    for index, row in enumerate(rows):
        record_path = row.get("record_path")
        if not isinstance(record_path, str) or not record_path:
            raise PublicEvidenceError(f"rows[{index}].record_path must be text")
        record_paths.append(record_path)
    _unique(record_paths, "record_path")

    counts, passes, reruns = _model_summary(rows)
    if counts != summary.get("counts"):
        raise PublicEvidenceError("published count summary does not reconcile")
    if passes != summary.get("passes"):
        raise PublicEvidenceError("published pass summary does not reconcile")
    if dict(reruns) != summary.get("reruns_after_infrastructure_failure"):
        raise PublicEvidenceError("published rerun summary does not reconcile")

    guidance_models: dict[str, Any] = {}
    shared_tasks: list[str] | None = None
    for model in EXPECTED_MODELS:
        full = {
            row["task_or_chain"]: _score(row, "full94")
            for row in rows
            if row.get("campaign") == "full94" and row.get("model") == model
        }
        reduced = {
            row["task_or_chain"]: _score(row, "reduced52")
            for row in rows
            if row.get("campaign") == "reduced52" and row.get("model") == model
        }
        task_ids = sorted(set(full) & set(reduced))
        if not task_ids:
            raise PublicEvidenceError(f"no paired guidance tasks for {model}")
        if shared_tasks is None:
            shared_tasks = task_ids
        elif task_ids != shared_tasks:
            raise PublicEvidenceError("paired guidance task sets differ by model")
        full_passes = sum(full[task] for task in task_ids)
        reduced_passes = sum(reduced[task] for task in task_ids)
        full_only = sum(full[t] == 1 and reduced[t] == 0 for t in task_ids)
        reduced_only = sum(full[t] == 0 and reduced[t] == 1 for t in task_ids)
        guidance_models[model] = {
            "paired_task_count": len(task_ids),
            "full_passes": full_passes,
            "reduced_passes": reduced_passes,
            "full_pass_rate": full_passes / len(task_ids),
            "reduced_pass_rate": reduced_passes / len(task_ids),
            "reduced_minus_full": (reduced_passes - full_passes) / len(task_ids),
            "both_pass": sum(full[t] == 1 and reduced[t] == 1 for t in task_ids),
            "full_only": full_only,
            "reduced_only": reduced_only,
            "both_fail": sum(full[t] == 0 and reduced[t] == 0 for t in task_ids),
            "mcnemar_exact_two_sided_p": exact_mcnemar_p(full_only, reduced_only),
        }

    repeat_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in rows:
        if row.get("campaign") == "repeat20x5":
            repeat_groups[(row["model"], row["task_or_chain"])].append(
                _score(row, "repeat20x5")
            )
    repeat_task_ids = sorted({task for _, task in repeat_groups})
    if not repeat_task_ids:
        raise PublicEvidenceError("repeat20x5 rows are missing")
    repeat_models: dict[str, Any] = {}
    per_task_passes: dict[str, dict[str, int]] = {
        task: {} for task in repeat_task_ids
    }
    for model in EXPECTED_MODELS:
        pass_counts: list[int] = []
        agreements: list[float] = []
        trials_per_task: int | None = None
        for task in repeat_task_ids:
            scores = repeat_groups[(model, task)]
            if not scores:
                raise PublicEvidenceError(f"missing repeat rows for {model}/{task}")
            if trials_per_task is None:
                trials_per_task = len(scores)
            elif len(scores) != trials_per_task:
                raise PublicEvidenceError("repeat trial counts are inconsistent")
            successes = sum(scores)
            pass_counts.append(successes)
            agreements.append(pairwise_agreement(successes, len(scores)))
            per_task_passes[task][model] = successes
        assert trials_per_task is not None
        distribution = Counter(pass_counts)
        attempts = len(repeat_task_ids) * trials_per_task
        repeat_models[model] = {
            "attempts": attempts,
            "passes": sum(pass_counts),
            "pass_rate": sum(pass_counts) / attempts,
            "unanimous_pass_tasks": distribution[trials_per_task],
            "unanimous_fail_tasks": distribution[0],
            "mixed_outcome_tasks": (
                len(repeat_task_ids)
                - distribution[trials_per_task]
                - distribution[0]
            ),
            "mean_pairwise_agreement": sum(agreements) / len(agreements),
            "pass_count_distribution": {
                str(value): distribution[value]
                for value in range(trials_per_task + 1)
            },
        }

    workflow_groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        if row.get("campaign") == "workflow":
            workflow_groups[
                (row["model"], row["guidance"], row["task_or_chain"])
            ].append(_score(row, "workflow"))
    workflow_ids = sorted({chain for _, _, chain in workflow_groups})
    if not workflow_ids:
        raise PublicEvidenceError("workflow rows are missing")
    workflow_models: dict[str, Any] = {}
    workflow_trials: int | None = None
    for model in EXPECTED_MODELS:
        model_report: dict[str, Any] = {}
        per_workflow: dict[str, dict[str, int]] = {
            chain: {} for chain in workflow_ids
        }
        for guidance in ("LG", "LA"):
            successes_by_chain: list[int] = []
            agreements: list[float] = []
            for chain in workflow_ids:
                scores = workflow_groups[(model, guidance, chain)]
                if not scores:
                    raise PublicEvidenceError(
                        f"missing workflow rows for {model}/{guidance}/{chain}"
                    )
                if workflow_trials is None:
                    workflow_trials = len(scores)
                elif len(scores) != workflow_trials:
                    raise PublicEvidenceError("workflow trial counts are inconsistent")
                successes = sum(scores)
                successes_by_chain.append(successes)
                agreements.append(pairwise_agreement(successes, len(scores)))
                per_workflow[chain][guidance] = successes
            assert workflow_trials is not None
            attempts = len(workflow_ids) * workflow_trials
            model_report[guidance] = {
                "attempts": attempts,
                "passes": sum(successes_by_chain),
                "pass_rate": sum(successes_by_chain) / attempts,
                "mean_pairwise_agreement": sum(agreements) / len(agreements),
            }
        model_report["LA_minus_LG"] = (
            model_report["LA"]["pass_rate"] - model_report["LG"]["pass_rate"]
        )
        model_report["per_workflow_passes"] = per_workflow
        workflow_models[model] = model_report

    all_passes = sum(_score(row, "rows") for row in rows)
    workflow_rows = [row for row in rows if row.get("campaign") == "workflow"]
    shared_tasks = shared_tasks or []
    manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest() if raw_bytes else None
    return {
        "schema": PUBLIC_EVIDENCE_SCHEMA,
        "source": {
            "repository": "cz2014/CompMat-Bench",
            "release": "v1.0.0",
            "commit": EXPECTED_COMPMAT_COMMIT,
            "manifest_blob_sha": EXPECTED_MANIFEST_BLOB,
            "manifest_sha256": manifest_sha256,
        },
        "global": {
            "attempts": len(rows),
            "passes": all_passes,
            "native_pass_rate": all_passes / len(rows),
            "reported_infrastructure_reruns": sum(reruns.values()),
            "workflow_attempts": len(workflow_rows),
            "workflow_passes": sum(_score(row, "workflow") for row in workflow_rows),
        },
        "guidance_paired": {
            "task_count": len(shared_tasks),
            "task_ids": shared_tasks,
            "models": guidance_models,
            "interpretation": (
                "Same-model, same-task published contrast. Treat as descriptive "
                "sensitivity, not a definitive causal estimate from a single "
                "stochastic draw per condition."
            ),
        },
        "repeatability": {
            "task_count": len(repeat_task_ids),
            "trials_per_task_model": (
                next(iter(repeat_models.values()))["attempts"] // len(repeat_task_ids)
            ),
            "task_ids": repeat_task_ids,
            "models": repeat_models,
            "per_task_passes": per_task_passes,
        },
        "workflow": {
            "workflow_count": len(workflow_ids),
            "workflow_ids": workflow_ids,
            "trials_per_model_guidance_workflow": workflow_trials,
            "models": workflow_models,
            "interpretation": (
                "Three-trial published workflow evidence. Guidance contrasts remain "
                "descriptive; model, task, and stochastic interactions are retained."
            ),
        },
        "frozen_matched_protocol": {
            "published_attempts_used": (
                2 * len(shared_tasks) * len(EXPECTED_MODELS)
                + sum(row["attempts"] for row in repeat_models.values())
                + sum(
                    report[guidance]["attempts"]
                    for report in workflow_models.values()
                    for guidance in ("LG", "LA")
                )
            ),
            "paired_single_step_tasks": len(shared_tasks),
            "paired_single_step_models": list(EXPECTED_MODELS),
            "paired_single_step_attempts": 2 * len(shared_tasks) * len(EXPECTED_MODELS),
            "repeat_tasks": repeat_task_ids,
            "repeat_trials_per_task_model": (
                next(iter(repeat_models.values()))["attempts"] // len(repeat_task_ids)
            ),
            "repeat_attempts": sum(row["attempts"] for row in repeat_models.values()),
            "workflow_ids": workflow_ids,
            "workflow_guidance_conditions": ["LG", "LA"],
            "workflow_trials_per_chain_model_guidance": workflow_trials,
            "workflow_attempts": sum(
                report[guidance]["attempts"]
                for report in workflow_models.values()
                for guidance in ("LG", "LA")
            ),
            "selection_rule": (
                "Use every public row in reduced52, repeat20x5, and workflow; "
                "pair reduced52 only to the same model and task in full94. "
                "No outcome-based task selection."
            ),
        },
        "claim_boundary": {
            "allowed": [
                "descriptive native pass rates",
                "same-task paired full-versus-reduced published contrasts",
                "five-trial task-level repeatability",
                "three-trial workflow stability and long-horizon pass rates",
            ],
            "forbidden": [
                "claiming TiAI-AgentBench or Goal-Driven improvement from upstream results",
                "treating reported reruns as a complete infrastructure-failure denominator",
                "inferring human-loop, cost, safety, or false-completion metrics",
                "calling one published stochastic contrast a definitive causal effect",
            ],
        },
    }


def validate_public_evidence(report: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen CompMat-Bench public evidence artifact."""
    report = _mapping(report, "report")
    if report.get("schema") != PUBLIC_EVIDENCE_SCHEMA:
        raise PublicEvidenceError("invalid public evidence schema")
    source = _mapping(report.get("source"), "report.source")
    if source.get("commit") != EXPECTED_COMPMAT_COMMIT:
        raise PublicEvidenceError("unexpected CompMat-Bench commit")
    if source.get("manifest_blob_sha") != EXPECTED_MANIFEST_BLOB:
        raise PublicEvidenceError("unexpected trajectory manifest blob")
    global_row = _mapping(report.get("global"), "report.global")
    if (global_row.get("attempts"), global_row.get("passes")) != (976, 771):
        raise PublicEvidenceError("global public counts changed")
    if (global_row.get("workflow_attempts"), global_row.get("workflow_passes")) != (144, 94):
        raise PublicEvidenceError("workflow public counts changed")
    guidance = _mapping(report.get("guidance_paired"), "report.guidance_paired")
    repeat = _mapping(report.get("repeatability"), "report.repeatability")
    workflow = _mapping(report.get("workflow"), "report.workflow")
    if guidance.get("task_count") != 52:
        raise PublicEvidenceError("expected 52 paired guidance tasks")
    if repeat.get("task_count") != 20 or repeat.get("trials_per_task_model") != 5:
        raise PublicEvidenceError("expected 20 tasks with five repeat trials")
    if workflow.get("workflow_count") != 8 or workflow.get("trials_per_model_guidance_workflow") != 3:
        raise PublicEvidenceError("expected eight workflows with three trials")
    protocol = _mapping(report.get("frozen_matched_protocol"), "report.frozen_matched_protocol")
    if protocol.get("published_attempts_used") != 756:
        raise PublicEvidenceError("matched public protocol must use 756 attempts")
    if set(_mapping(guidance.get("models"), "guidance.models")) != set(EXPECTED_MODELS):
        raise PublicEvidenceError("guidance model set changed")
    return {
        "schema": report["schema"],
        "status": "PASSED",
        "attempts": global_row["attempts"],
        "passes": global_row["passes"],
        "matched_attempts": protocol["published_attempts_used"],
        "paired_tasks": guidance["task_count"],
        "repeat_tasks": repeat["task_count"],
        "workflows": workflow["workflow_count"],
    }
