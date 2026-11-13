"""CompMat-Bench trajectory-manifest adapter for FederationCore."""
from __future__ import annotations

from typing import Any

from .federation_base import (
    FederationError,
    _base_report,
    _integer,
    _list,
    _object,
    _ratio,
    _text,
)


def _nested_count_table(value: Any, label: str) -> dict[str, dict[str, int]]:
    table = _object(value, label)
    if not table:
        raise FederationError(f"{label} must not be empty")
    result: dict[str, dict[str, int]] = {}
    for raw_campaign, raw_models in table.items():
        campaign = _text(raw_campaign, f"{label}.campaign")
        models = _object(raw_models, f"{label}[{campaign!r}]")
        if not models:
            raise FederationError(f"{label}[{campaign!r}] must not be empty")
        result[campaign] = {}
        for raw_model, raw_count in models.items():
            model = _text(raw_model, f"{label}[{campaign!r}].model")
            result[campaign][model] = _integer(
                raw_count,
                f"{label}[{campaign!r}][{model!r}]",
            )
    return result


def normalize_compmat_bench(
    anchor: dict[str, Any],
    payload: Any,
) -> dict[str, Any]:
    """Normalize the published CompMat-Bench trajectory manifest.

    Native fixed-rule pass/fail remains authoritative. Rows marked as reruns
    after infrastructure failure remain reported, but the excluded failed-run
    denominator is unavailable, so infrastructure reliability stays unknown.
    """
    root = _object(payload, "CompMat-Bench trajectory manifest")
    summary = _object(root.get("summary"), "CompMat-Bench.summary")
    rows = _list(root.get("rows"), "CompMat-Bench.rows", nonempty=True)

    total = _integer(summary.get("total"), "CompMat-Bench.summary.total")
    counts = _nested_count_table(
        summary.get("counts"),
        "CompMat-Bench.summary.counts",
    )
    passes = _nested_count_table(
        summary.get("passes"),
        "CompMat-Bench.summary.passes",
    )

    if set(counts) != set(passes):
        raise FederationError("CompMat-Bench count/pass campaign sets differ")
    for campaign, model_counts in counts.items():
        if set(model_counts) != set(passes[campaign]):
            raise FederationError(
                f"CompMat-Bench count/pass model sets differ for {campaign}"
            )
        for model, count in model_counts.items():
            if passes[campaign][model] > count:
                raise FederationError("CompMat-Bench passes cannot exceed counts")

    if sum(sum(models.values()) for models in counts.values()) != total:
        raise FederationError("CompMat-Bench summary counts do not sum to total")

    raw_reruns = _object(
        summary.get("reruns_after_infrastructure_failure", {}),
        "CompMat-Bench.summary.reruns_after_infrastructure_failure",
    )
    reruns: dict[str, int] = {}
    for raw_key, raw_count in raw_reruns.items():
        key = _text(raw_key, "CompMat-Bench.summary.rerun key")
        if "/" not in key:
            raise FederationError(
                "CompMat-Bench rerun keys must be campaign/model"
            )
        campaign, model = key.split("/", 1)
        if campaign not in counts or model not in counts[campaign]:
            raise FederationError(
                f"CompMat-Bench rerun key references unknown group: {key}"
            )
        count = _integer(
            raw_count,
            f"CompMat-Bench.summary.reruns[{key!r}]",
        )
        if count > counts[campaign][model]:
            raise FederationError(
                f"CompMat-Bench reruns exceed reported rows for {key}"
            )
        reruns[key] = count

    observed_counts: dict[str, dict[str, int]] = {}
    observed_passes: dict[str, dict[str, int]] = {}
    observed_reruns: dict[str, int] = {}
    seen_paths: set[str] = set()
    campaigns: set[str] = set()
    models: set[str] = set()
    workflow_rows = 0
    workflow_passes = 0

    for i, raw in enumerate(rows):
        row = _object(raw, f"CompMat-Bench.rows[{i}]")
        campaign = _text(
            row.get("campaign"), f"CompMat-Bench.rows[{i}].campaign"
        )
        model = _text(row.get("model"), f"CompMat-Bench.rows[{i}].model")
        _text(
            row.get("provider_route"),
            f"CompMat-Bench.rows[{i}].provider_route",
        )
        _text(
            row.get("task_or_chain"),
            f"CompMat-Bench.rows[{i}].task_or_chain",
        )
        _text(row.get("guidance"), f"CompMat-Bench.rows[{i}].guidance")
        _integer(
            row.get("trial"),
            f"CompMat-Bench.rows[{i}].trial",
            minimum=1,
        )
        _text(row.get("attempt_id"), f"CompMat-Bench.rows[{i}].attempt_id")
        session_id = row.get("session_id")
        if session_id is not None:
            _text(session_id, f"CompMat-Bench.rows[{i}].session_id")
        _text(row.get("host"), f"CompMat-Bench.rows[{i}].host")
        score = _integer(row.get("score"), f"CompMat-Bench.rows[{i}].score")
        if score not in {0, 1}:
            raise FederationError("CompMat-Bench score must be 0 or 1")
        rerun = row.get("rerun_after_infrastructure_failure")
        if not isinstance(rerun, bool):
            raise FederationError("CompMat-Bench rerun flag must be boolean")
        record_path = _text(
            row.get("record_path"),
            f"CompMat-Bench.rows[{i}].record_path",
        )
        if record_path in seen_paths:
            raise FederationError(
                f"duplicate CompMat-Bench record_path: {record_path}"
            )
        seen_paths.add(record_path)

        observed_counts.setdefault(campaign, {}).setdefault(model, 0)
        observed_counts[campaign][model] += 1
        observed_passes.setdefault(campaign, {}).setdefault(model, 0)
        observed_passes[campaign][model] += score
        if rerun:
            key = f"{campaign}/{model}"
            observed_reruns[key] = observed_reruns.get(key, 0) + 1
        campaigns.add(campaign)
        models.add(model)
        if campaign == "workflow":
            workflow_rows += 1
            workflow_passes += score

    if len(rows) != total:
        raise FederationError(
            "CompMat-Bench row count differs from summary total"
        )
    if observed_counts != counts:
        raise FederationError("CompMat-Bench row counts differ from summary")
    if observed_passes != passes:
        raise FederationError("CompMat-Bench row passes differ from summary")
    observed_reruns = {
        key: value for key, value in observed_reruns.items() if value
    }
    if observed_reruns != reruns:
        raise FederationError("CompMat-Bench rerun counts differ from summary")

    total_passes = sum(
        sum(models_passed.values()) for models_passed in passes.values()
    )
    total_reruns = sum(reruns.values())
    campaign_rates = {
        campaign: _ratio(
            sum(passes[campaign].values()),
            sum(counts[campaign].values()),
        )
        for campaign in sorted(counts)
    }

    model_counts: dict[str, int] = {}
    model_passes: dict[str, int] = {}
    for campaign, campaign_counts in counts.items():
        for model, count in campaign_counts.items():
            model_counts[model] = model_counts.get(model, 0) + count
            model_passes[model] = (
                model_passes.get(model, 0) + passes[campaign][model]
            )
    model_rates = {
        model: _ratio(model_passes[model], model_counts[model])
        for model in sorted(model_counts)
    }

    metrics = {
        "native_verified_success": _ratio(total_passes, total),
        "execution_coverage": 1.0 if total else None,
        "infrastructure_reliability": None,
        "reported_infrastructure_rerun_fraction": _ratio(
            total_reruns, total
        ),
        "workflow_native_success": _ratio(
            workflow_passes, workflow_rows
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
            "INFRASTRUCTURE_FAILURE_DENOMINATOR_NOT_REPORTED",
            "ARTIFACT_HASHES_NOT_REPORTED",
        ],
        {
            "campaigns": sorted(campaigns),
            "models": sorted(models),
            "passes": total_passes,
            "reported_rows": total,
            "campaign_pass_rates": campaign_rates,
            "model_pass_rates": model_rates,
            "reported_rerun_count": total_reruns,
            "rerun_semantics": (
                "Rows flagged rerun_after_infrastructure_failure replace "
                "excluded infrastructure-failed attempts; the original "
                "failed-launch denominator is not present."
            ),
            "workflow_rows": workflow_rows,
            "workflow_passes": workflow_passes,
        },
    )
