"""Validation for matched cross-condition Goal-Driven experiments."""
from __future__ import annotations

from typing import Any

from .io import BenchmarkFormatError

MATCHED_PROTOCOL_SCHEMA = "tiai.agentbench.matched_goal_driven_protocol.v0.8"
EXPECTED_CONDITIONS = {
    "single_agent",
    "ordinary_multi_agent",
    "goal_driven_no_independent_verifier",
    "goal_driven_no_recovery",
    "goal_driven_no_provenance_claim_gate",
    "full_goal_driven",
}
REQUIRED_LEDGER_FIELDS = {
    "run_id",
    "domain_id",
    "benchmark_id",
    "task_id",
    "condition_id",
    "model_id",
    "trial",
    "input_commit_or_blob",
    "budget",
    "wall_time_seconds",
    "human_interventions",
    "faults_observed",
    "faults_recovered",
    "artifact_hashes",
    "native_verifier_receipt",
    "native_success",
    "claimed_success",
    "false_completion",
    "GDS",
    "VWR",
    "HLF",
    "FCR",
    "FRR",
    "RNU",
}


class MatchedExperimentError(BenchmarkFormatError):
    """Raised when a matched experiment contract is malformed."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MatchedExperimentError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise MatchedExperimentError(f"{label} must be a list")
    if nonempty and not value:
        raise MatchedExperimentError(f"{label} must not be empty")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MatchedExperimentError(f"{label} must be nonempty text")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MatchedExperimentError(f"{label} must be a positive integer")
    return value


def _unique_texts(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    rows = [
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(_list(value, label, nonempty=nonempty))
    ]
    if len(rows) != len(set(rows)):
        raise MatchedExperimentError(f"{label} contains duplicates")
    return rows


def validate_matched_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    """Validate the v0.8 staged matched-baseline protocol."""
    protocol = _object(protocol, "protocol")
    if protocol.get("schema") != MATCHED_PROTOCOL_SCHEMA:
        raise MatchedExperimentError("invalid matched experiment schema")
    for key in ("experiment_id", "version", "objective", "primary_hypothesis"):
        _text(protocol.get(key), f"protocol.{key}")

    conditions = _list(
        protocol.get("system_conditions"),
        "protocol.system_conditions",
        nonempty=True,
    )
    condition_ids = []
    for index, raw in enumerate(conditions):
        row = _object(raw, f"protocol.system_conditions[{index}]")
        condition_ids.append(
            _text(row.get("condition_id"), f"conditions[{index}].condition_id")
        )
        _text(row.get("description"), f"conditions[{index}].description")
    if len(condition_ids) != len(set(condition_ids)):
        raise MatchedExperimentError("system condition IDs must be unique")
    if set(condition_ids) != EXPECTED_CONDITIONS:
        raise MatchedExperimentError(
            "system conditions differ from the pre-registered six-condition ablation"
        )

    phase0 = _object(protocol.get("phase_0_public_evidence"), "protocol.phase_0")
    if phase0.get("status") != "COMPLETED" or phase0.get("attempts") != 756:
        raise MatchedExperimentError("Phase 0 must bind the 756-attempt public evidence")
    _text(phase0.get("artifact"), "protocol.phase_0.artifact")

    phase1 = _object(protocol.get("phase_1_materials_pilot"), "protocol.phase_1")
    strata = _list(phase1.get("strata"), "protocol.phase_1.strata", nonempty=True)
    stratum_ids: list[str] = []
    planned = 0
    all_task_keys: set[tuple[str, str]] = set()
    for index, raw in enumerate(strata):
        row = _object(raw, f"protocol.phase_1.strata[{index}]")
        stratum_id = _text(row.get("stratum_id"), f"strata[{index}].stratum_id")
        stratum_ids.append(stratum_id)
        _text(row.get("execution_mode"), f"strata[{index}].execution_mode")
        _text(row.get("native_verifier"), f"strata[{index}].native_verifier")
        tasks = _unique_texts(
            row.get("task_ids"),
            f"strata[{index}].task_ids",
            nonempty=True,
        )
        repeats = _positive_int(
            row.get("repeats_per_condition_task"),
            f"strata[{index}].repeats_per_condition_task",
        )
        for task in tasks:
            key = (stratum_id, task)
            if key in all_task_keys:
                raise MatchedExperimentError(f"duplicate pilot task key: {key}")
            all_task_keys.add(key)
        planned += len(tasks) * repeats * len(EXPECTED_CONDITIONS)
    if len(stratum_ids) != len(set(stratum_ids)):
        raise MatchedExperimentError("pilot stratum IDs must be unique")
    if phase1.get("planned_run_count") != planned:
        raise MatchedExperimentError(
            f"planned_run_count={phase1.get('planned_run_count')} but contract requires {planned}"
        )

    quality = _object(phase1.get("data_quality_gate"), "protocol.phase_1.data_quality_gate")
    for key in (
        "minimum_valid_run_fraction",
        "required_fields_complete_fraction",
        "native_verifier_receipt_fraction",
    ):
        value = quality.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MatchedExperimentError(f"data_quality_gate.{key} must be numeric")
        if not 0.0 <= float(value) <= 1.0:
            raise MatchedExperimentError(f"data_quality_gate.{key} must be in [0,1]")
    if quality.get("task_or_budget_changes_after_first_outcome") != 0:
        raise MatchedExperimentError("task or budget changes after outcomes are forbidden")

    phase2 = _object(
        protocol.get("phase_2_cross_domain_confirmatory"),
        "protocol.phase_2",
    )
    adapters = _unique_texts(
        phase2.get("benchmark_adapters"),
        "protocol.phase_2.benchmark_adapters",
        nonempty=True,
    )
    required_adapters = {
        "TIIAI_HIDDEN_REAL_REPLAY",
        "COMPMAT_TRAJECTORY_MANIFEST_V1",
        "SWE_BENCH_RESULTS_V2",
        "OSWORLD_RESULTS_V1",
        "CALVIN_RESULTS_V1",
    }
    if set(adapters) != required_adapters:
        raise MatchedExperimentError("confirmatory adapter set changed")

    ledger = set(
        _unique_texts(
            protocol.get("required_run_ledger"),
            "protocol.required_run_ledger",
            nonempty=True,
        )
    )
    missing = sorted(REQUIRED_LEDGER_FIELDS - ledger)
    if missing:
        raise MatchedExperimentError(f"required run ledger fields missing: {missing}")

    resource = _object(protocol.get("resource_policy"), "protocol.resource_policy")
    if resource.get("mother_machine_heavy_compute") is not False:
        raise MatchedExperimentError("mother-machine heavy compute must remain disabled")

    return {
        "schema": protocol["schema"],
        "status": "PASSED",
        "experiment_id": protocol["experiment_id"],
        "condition_count": len(condition_ids),
        "pilot_stratum_count": len(strata),
        "pilot_task_count": len(all_task_keys),
        "pilot_run_count": planned,
        "confirmatory_adapter_count": len(adapters),
        "ledger_field_count": len(ledger),
    }
