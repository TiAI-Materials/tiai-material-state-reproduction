"""Goal-Driven work-replacement protocols and deterministic scoring.

The protocol operationalizes three linked ideas:

* professional work is decomposed into human work units;
* an agent must persist across episodes until explicit criteria are verified;
* completion is a verifier decision, not an agent self-declaration.

It is domain-neutral.  Materials science is the first active vertical, while
industry families can supply their own objects, tools, criteria and safety gates.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable
import re

from .io import BenchmarkFormatError

GOAL_REGISTRY_SCHEMA = "tiai.agentbench.goal_driven_registry.v1"
GOAL_PROTOCOL_SCHEMA = "tiai.agentbench.goal_protocol.v1"
GOAL_RUN_SCHEMA = "tiai.agentbench.goal_run.v1"
GOAL_REPORT_SCHEMA = "tiai.agentbench.goal_report.v1"

VALID_VERIFIABILITY_LEVELS = {
    "V0_LOCAL_DETERMINISTIC",
    "V1_COMPUTE_OR_REPLAY",
    "V2_DIGITAL_TWIN",
    "V3_PHYSICAL_INSTRUMENT",
    "V4_SOCIO_REGULATORY",
}
VALID_REPLACEMENT_SCOPES = {
    "TASK",
    "WORKFLOW",
    "ROLE",
    "TEAM",
    "ORGANIZATION",
    "INDUSTRY",
}
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
VALID_DATA_KINDS = {"REAL_RELEASED", "SYNTHETIC_PROTOCOL_TEST", "PRIVATE_HIDDEN"}
VALID_VERIFIER_TYPES = {
    "DETERMINISTIC",
    "DIFFERENTIAL",
    "SIMULATION",
    "PHYSICAL",
    "HUMAN_EXPERT",
}
VALID_TERMINAL_STATUSES = {"SUCCESS", "FAILED", "ABSTAINED", "BUDGET_EXHAUSTED"}
VALID_EPISODE_TERMINATIONS = {
    "CRITERIA_MET",
    "FAILED",
    "IDLE",
    "BUDGET_EXHAUSTED",
    "HUMAN_STOP",
    "SUPERSEDED",
}
VALID_WORK_STATUSES = {"COMPLETED", "PARTIAL", "FAILED", "SKIPPED"}
VALID_PERFORMERS = {"AGENT", "MIXED", "HUMAN"}
VALID_INTERVENTION_SEVERITIES = {
    "CLARIFICATION",
    "PARAMETER_CORRECTION",
    "CODE_REPAIR",
    "SCIENTIFIC_OVERRIDE",
    "SAFETY_INTERVENTION",
    "FULL_TAKEOVER",
}
INTERVENTION_WEIGHTS = {
    "CLARIFICATION": 0.05,
    "PARAMETER_CORRECTION": 0.15,
    "CODE_REPAIR": 0.25,
    "SCIENTIFIC_OVERRIDE": 0.50,
    "SAFETY_INTERVENTION": 0.75,
    "FULL_TAKEOVER": 1.00,
}
PERFORMER_AUTONOMY = {"AGENT": 1.0, "MIXED": 0.5, "HUMAN": 0.0}
RESOURCE_FIELDS = {
    "wall_time_s",
    "cpu_core_hours",
    "gpu_hours",
    "money_usd",
    "experiment_units",
    "robot_minutes",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GoalDrivenError(BenchmarkFormatError):
    """Raised when a Goal-Driven registry, protocol or run is malformed."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GoalDrivenError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise GoalDrivenError(f"{label} must be a list")
    if nonempty and not value:
        raise GoalDrivenError(f"{label} must not be empty")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GoalDrivenError(f"{label} must be a nonempty string")
    return value


def _bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise GoalDrivenError(f"{label} must be a boolean")
    return value


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GoalDrivenError(f"{label} must be an integer")
    if value < minimum:
        raise GoalDrivenError(f"{label} must be >= {minimum}")
    return value


def _number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GoalDrivenError(f"{label} must be a number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise GoalDrivenError(f"{label} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise GoalDrivenError(f"{label} must be <= {maximum}")
    return result


def _unique_text_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    rows = _list(value, label, nonempty=nonempty)
    result = [_text(row, f"{label}[{index}]") for index, row in enumerate(rows)]
    if len(result) != len(set(result)):
        raise GoalDrivenError(f"{label} contains duplicates")
    return result


def _resource_map(value: Any, label: str) -> dict[str, float]:
    row = _object(value, label)
    unknown = set(row) - RESOURCE_FIELDS
    if unknown:
        raise GoalDrivenError(f"{label} has unknown resource fields: {sorted(unknown)}")
    return {
        key: _number(raw, f"{label}.{key}", minimum=0.0)
        for key, raw in row.items()
    }


def _validate_dag(work_units: list[dict[str, Any]]) -> None:
    graph = {row["work_unit_id"]: list(row["depends_on"]) for row in work_units}
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        marker = state.get(node, 0)
        if marker == 1:
            raise GoalDrivenError(f"work-unit dependency cycle contains {node!r}")
        if marker == 2:
            return
        state[node] = 1
        for parent in graph[node]:
            visit(parent)
        state[node] = 2

    for node in graph:
        visit(node)


def validate_goal_registry(registry: dict[str, Any]) -> dict[str, Any]:
    """Validate the universal work-replacement and industry-family registry."""

    registry = _object(registry, "registry")
    if registry.get("schema") != GOAL_REGISTRY_SCHEMA:
        raise GoalDrivenError(f"invalid goal registry schema: {registry.get('schema')!r}")
    for key in ("benchmark", "version", "mission"):
        _text(registry.get(key), f"registry.{key}")
    principles = _unique_text_list(registry.get("principles"), "registry.principles", nonempty=True)

    levels = _list(registry.get("verifiability_levels"), "registry.verifiability_levels", nonempty=True)
    level_ids: set[str] = set()
    for index, raw in enumerate(levels):
        row = _object(raw, f"registry.verifiability_levels[{index}]")
        level_id = _text(row.get("id"), f"registry.verifiability_levels[{index}].id")
        if level_id not in VALID_VERIFIABILITY_LEVELS:
            raise GoalDrivenError(f"unknown verifiability level: {level_id}")
        if level_id in level_ids:
            raise GoalDrivenError(f"duplicate verifiability level: {level_id}")
        level_ids.add(level_id)
        _text(row.get("definition"), f"registry.verifiability_levels[{index}].definition")
    if level_ids != VALID_VERIFIABILITY_LEVELS:
        raise GoalDrivenError("registry must define all five verifiability levels")

    scopes = _unique_text_list(registry.get("replacement_scopes"), "registry.replacement_scopes", nonempty=True)
    if set(scopes) != VALID_REPLACEMENT_SCOPES:
        raise GoalDrivenError("registry must define TASK through INDUSTRY replacement scopes")

    families: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(registry.get("industry_families"), "registry.industry_families", nonempty=True)):
        row = _object(raw, f"registry.industry_families[{index}]")
        family_id = _text(row.get("industry_id"), f"registry.industry_families[{index}].industry_id")
        if family_id in families:
            raise GoalDrivenError(f"duplicate industry_id: {family_id}")
        for key in ("title", "scope", "readiness"):
            _text(row.get(key), f"registry.industry_families[{index}].{key}")
        _unique_text_list(row.get("example_roles"), f"registry.industry_families[{index}].example_roles", nonempty=True)
        _unique_text_list(row.get("verification_assets"), f"registry.industry_families[{index}].verification_assets", nonempty=True)
        _unique_text_list(row.get("human_loop_sources"), f"registry.industry_families[{index}].human_loop_sources", nonempty=True)
        supported_levels = set(
            _unique_text_list(
                row.get("verifiability_levels"),
                f"registry.industry_families[{index}].verifiability_levels",
                nonempty=True,
            )
        )
        unknown = supported_levels - VALID_VERIFIABILITY_LEVELS
        if unknown:
            raise GoalDrivenError(f"industry {family_id} has unknown verifiability levels: {sorted(unknown)}")
        families[family_id] = row

    required = {
        "materials_science",
        "software_engineering",
        "scientific_robotics",
        "eda_semiconductor",
        "cad_architecture_construction",
        "cae_simulation",
        "control_signal_electrical",
    }
    missing = required - set(families)
    if missing:
        raise GoalDrivenError(f"goal registry missing required industry families: {sorted(missing)}")
    if len(families) < 16:
        raise GoalDrivenError("goal registry must stage at least 16 industry families")

    return {
        "benchmark": registry["benchmark"],
        "version": registry["version"],
        "principle_count": len(principles),
        "industry_count": len(families),
        "industries": families,
        "verifiability_levels": level_ids,
        "replacement_scopes": set(scopes),
    }


def validate_goal_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    """Validate one Goal-Driven benchmark protocol."""

    protocol = _object(protocol, "protocol")
    if protocol.get("schema") != GOAL_PROTOCOL_SCHEMA:
        raise GoalDrivenError(f"invalid goal protocol schema: {protocol.get('schema')!r}")
    for key in (
        "goal_id",
        "title",
        "domain_adapter",
        "industry_family",
        "role",
        "objective",
    ):
        _text(protocol.get(key), f"protocol.{key}")
    if protocol.get("verifiability_level") not in VALID_VERIFIABILITY_LEVELS:
        raise GoalDrivenError("protocol.verifiability_level is invalid")
    if protocol.get("replacement_scope") not in VALID_REPLACEMENT_SCOPES:
        raise GoalDrivenError("protocol.replacement_scope is invalid")
    if protocol.get("horizon") not in VALID_HORIZONS:
        raise GoalDrivenError("protocol.horizon is invalid")
    if protocol.get("autonomy_target") not in VALID_AUTONOMY_LEVELS:
        raise GoalDrivenError("protocol.autonomy_target is invalid")
    if protocol.get("execution_mode") not in VALID_EXECUTION_MODES:
        raise GoalDrivenError("protocol.execution_mode is invalid")
    if protocol.get("data_kind") not in VALID_DATA_KINDS:
        raise GoalDrivenError("protocol.data_kind is invalid")

    contract = _object(protocol.get("goal_contract"), "protocol.goal_contract")
    _unique_text_list(contract.get("terminal_states"), "protocol.goal_contract.terminal_states", nonempty=True)
    _unique_text_list(contract.get("non_goals"), "protocol.goal_contract.non_goals")
    _number(contract.get("max_agent_hours"), "protocol.goal_contract.max_agent_hours", minimum=0.0)
    _integer(contract.get("heartbeat_interval_s"), "protocol.goal_contract.heartbeat_interval_s", minimum=1)
    _integer(contract.get("max_inactive_s"), "protocol.goal_contract.max_inactive_s", minimum=1)
    _integer(contract.get("max_restarts"), "protocol.goal_contract.max_restarts", minimum=0)
    _bool(contract.get("restart_inactive_agents"), "protocol.goal_contract.restart_inactive_agents")
    _bool(contract.get("all_required_criteria"), "protocol.goal_contract.all_required_criteria")
    _bool(contract.get("truthful_budget_exhaustion"), "protocol.goal_contract.truthful_budget_exhaustion")

    work_units: list[dict[str, Any]] = []
    work_index: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(protocol.get("work_units"), "protocol.work_units", nonempty=True)):
        row = _object(raw, f"protocol.work_units[{index}]")
        work_id = _text(row.get("work_unit_id"), f"protocol.work_units[{index}].work_unit_id")
        if work_id in work_index:
            raise GoalDrivenError(f"duplicate work_unit_id: {work_id}")
        _text(row.get("title"), f"protocol.work_units[{index}].title")
        _number(row.get("criticality"), f"protocol.work_units[{index}].criticality", minimum=0.000001)
        _number(row.get("human_baseline_minutes"), f"protocol.work_units[{index}].human_baseline_minutes", minimum=0.0)
        _bool(row.get("required"), f"protocol.work_units[{index}].required")
        row["depends_on"] = _unique_text_list(row.get("depends_on"), f"protocol.work_units[{index}].depends_on")
        row["criterion_ids"] = _unique_text_list(row.get("criterion_ids"), f"protocol.work_units[{index}].criterion_ids", nonempty=True)
        work_units.append(row)
        work_index[work_id] = row
    for row in work_units:
        unknown = set(row["depends_on"]) - set(work_index)
        if unknown:
            raise GoalDrivenError(f"work unit {row['work_unit_id']} has unknown dependencies: {sorted(unknown)}")
        if row["work_unit_id"] in row["depends_on"]:
            raise GoalDrivenError(f"work unit {row['work_unit_id']} depends on itself")
    _validate_dag(work_units)

    criteria: list[dict[str, Any]] = []
    criterion_index: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(protocol.get("criteria"), "protocol.criteria", nonempty=True)):
        row = _object(raw, f"protocol.criteria[{index}]")
        criterion_id = _text(row.get("criterion_id"), f"protocol.criteria[{index}].criterion_id")
        if criterion_id in criterion_index:
            raise GoalDrivenError(f"duplicate criterion_id: {criterion_id}")
        _text(row.get("title"), f"protocol.criteria[{index}].title")
        _number(row.get("weight"), f"protocol.criteria[{index}].weight", minimum=0.000001)
        _bool(row.get("required"), f"protocol.criteria[{index}].required")
        verifier_type = _text(row.get("verifier_type"), f"protocol.criteria[{index}].verifier_type")
        if verifier_type not in VALID_VERIFIER_TYPES:
            raise GoalDrivenError(f"invalid verifier_type: {verifier_type}")
        _bool(row.get("independent_required"), f"protocol.criteria[{index}].independent_required")
        row["artifact_types"] = _unique_text_list(
            row.get("artifact_types"), f"protocol.criteria[{index}].artifact_types", nonempty=True
        )
        row["work_unit_ids"] = _unique_text_list(
            row.get("work_unit_ids"), f"protocol.criteria[{index}].work_unit_ids", nonempty=True
        )
        unknown = set(row["work_unit_ids"]) - set(work_index)
        if unknown:
            raise GoalDrivenError(f"criterion {criterion_id} references unknown work units: {sorted(unknown)}")
        criteria.append(row)
        criterion_index[criterion_id] = row

    for row in work_units:
        unknown = set(row["criterion_ids"]) - set(criterion_index)
        if unknown:
            raise GoalDrivenError(f"work unit {row['work_unit_id']} references unknown criteria: {sorted(unknown)}")
    attached = {criterion_id for row in work_units for criterion_id in row["criterion_ids"]}
    missing = {row["criterion_id"] for row in criteria if row["required"]} - attached
    if missing:
        raise GoalDrivenError(f"required criteria are not attached to work units: {sorted(missing)}")

    resource_budget = _resource_map(protocol.get("resource_budget"), "protocol.resource_budget")
    faults: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(protocol.get("fault_injections"), "protocol.fault_injections")):
        row = _object(raw, f"protocol.fault_injections[{index}]")
        fault_id = _text(row.get("fault_id"), f"protocol.fault_injections[{index}].fault_id")
        if fault_id in faults:
            raise GoalDrivenError(f"duplicate fault_id: {fault_id}")
        _text(row.get("title"), f"protocol.fault_injections[{index}].title")
        _bool(row.get("required"), f"protocol.fault_injections[{index}].required")
        faults[fault_id] = row

    reconstruction = protocol.get("reconstruction_target")
    if reconstruction is not None:
        reconstruction = _object(reconstruction, "protocol.reconstruction_target")
        for key in ("target_type", "specification_artifact", "compatibility_reference"):
            _text(reconstruction.get(key), f"protocol.reconstruction_target.{key}")
        signoff_ids = set(
            _unique_text_list(
                reconstruction.get("signoff_criterion_ids"),
                "protocol.reconstruction_target.signoff_criterion_ids",
                nonempty=True,
            )
        )
        unknown = signoff_ids - set(criterion_index)
        if unknown:
            raise GoalDrivenError(f"reconstruction signoff references unknown criteria: {sorted(unknown)}")

    return {
        "protocol": protocol,
        "work_units": work_index,
        "criteria": criterion_index,
        "faults": faults,
        "resource_budget": resource_budget,
        "reconstruction": reconstruction,
    }


def validate_goal_run(run: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Validate one run against its Goal-Driven protocol."""

    indexes = validate_goal_protocol(protocol)
    run = _object(run, "run")
    if run.get("schema") != GOAL_RUN_SCHEMA:
        raise GoalDrivenError(f"invalid goal run schema: {run.get('schema')!r}")
    if run.get("goal_id") != protocol["goal_id"]:
        raise GoalDrivenError("run.goal_id does not match protocol.goal_id")
    _text(run.get("run_id"), "run.run_id")
    terminal_status = _text(run.get("terminal_status"), "run.terminal_status")
    if terminal_status not in VALID_TERMINAL_STATUSES:
        raise GoalDrivenError(f"invalid terminal_status: {terminal_status}")
    _bool(run.get("completion_claimed"), "run.completion_claimed")
    _bool(run.get("budget_exhausted"), "run.budget_exhausted")

    episodes: dict[str, dict[str, Any]] = {}
    episode_order: list[str] = []
    for index, raw in enumerate(_list(run.get("episodes"), "run.episodes", nonempty=True)):
        row = _object(raw, f"run.episodes[{index}]")
        episode_id = _text(row.get("episode_id"), f"run.episodes[{index}].episode_id")
        if episode_id in episodes:
            raise GoalDrivenError(f"duplicate episode_id: {episode_id}")
        _text(row.get("agent_id"), f"run.episodes[{index}].agent_id")
        start = _integer(row.get("start_step"), f"run.episodes[{index}].start_step")
        end = _integer(row.get("end_step"), f"run.episodes[{index}].end_step")
        if end < start:
            raise GoalDrivenError(f"episode {episode_id} ends before it starts")
        reason = _text(row.get("termination_reason"), f"run.episodes[{index}].termination_reason")
        if reason not in VALID_EPISODE_TERMINATIONS:
            raise GoalDrivenError(f"invalid episode termination_reason: {reason}")
        _integer(row.get("heartbeat_failures"), f"run.episodes[{index}].heartbeat_failures")
        _integer(row.get("subagents_created"), f"run.episodes[{index}].subagents_created")
        resumed_from = row.get("resumed_from")
        if resumed_from is not None:
            _text(resumed_from, f"run.episodes[{index}].resumed_from")
        checkpoint_id = row.get("checkpoint_id")
        if checkpoint_id is not None:
            _text(checkpoint_id, f"run.episodes[{index}].checkpoint_id")
        episodes[episode_id] = row
        episode_order.append(episode_id)
    for index, episode_id in enumerate(episode_order):
        resumed_from = episodes[episode_id].get("resumed_from")
        if resumed_from is not None:
            if resumed_from not in episodes:
                raise GoalDrivenError(f"episode {episode_id} resumes unknown episode {resumed_from}")
            if episode_order.index(resumed_from) >= index:
                raise GoalDrivenError(f"episode {episode_id} must resume an earlier episode")

    criterion_results: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(run.get("criterion_results"), "run.criterion_results")):
        row = _object(raw, f"run.criterion_results[{index}]")
        criterion_id = _text(row.get("criterion_id"), f"run.criterion_results[{index}].criterion_id")
        if criterion_id not in indexes["criteria"]:
            raise GoalDrivenError(f"run references unknown criterion: {criterion_id}")
        if criterion_id in criterion_results:
            raise GoalDrivenError(f"duplicate criterion result: {criterion_id}")
        _bool(row.get("passed"), f"run.criterion_results[{index}].passed")
        _text(row.get("verifier_id"), f"run.criterion_results[{index}].verifier_id")
        _bool(row.get("independent"), f"run.criterion_results[{index}].independent")
        _integer(row.get("evaluated_step"), f"run.criterion_results[{index}].evaluated_step")
        artifact_types = _unique_text_list(
            row.get("artifact_types"), f"run.criterion_results[{index}].artifact_types"
        )
        hashes = _unique_text_list(
            row.get("artifact_sha256"), f"run.criterion_results[{index}].artifact_sha256"
        )
        for digest in hashes:
            if not _SHA256_RE.fullmatch(digest):
                raise GoalDrivenError(f"invalid SHA-256 digest in criterion {criterion_id}: {digest!r}")
        row["artifact_types"] = artifact_types
        row["artifact_sha256"] = hashes
        criterion_results[criterion_id] = row

    work_results: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(run.get("work_unit_results"), "run.work_unit_results")):
        row = _object(raw, f"run.work_unit_results[{index}]")
        work_id = _text(row.get("work_unit_id"), f"run.work_unit_results[{index}].work_unit_id")
        if work_id not in indexes["work_units"]:
            raise GoalDrivenError(f"run references unknown work unit: {work_id}")
        if work_id in work_results:
            raise GoalDrivenError(f"duplicate work-unit result: {work_id}")
        status = _text(row.get("status"), f"run.work_unit_results[{index}].status")
        if status not in VALID_WORK_STATUSES:
            raise GoalDrivenError(f"invalid work status: {status}")
        performer = _text(row.get("performer"), f"run.work_unit_results[{index}].performer")
        if performer not in VALID_PERFORMERS:
            raise GoalDrivenError(f"invalid performer: {performer}")
        _number(row.get("human_minutes"), f"run.work_unit_results[{index}].human_minutes", minimum=0.0)
        _number(row.get("agent_minutes"), f"run.work_unit_results[{index}].agent_minutes", minimum=0.0)
        hashes = _unique_text_list(
            row.get("artifact_sha256"), f"run.work_unit_results[{index}].artifact_sha256"
        )
        for digest in hashes:
            if not _SHA256_RE.fullmatch(digest):
                raise GoalDrivenError(f"invalid SHA-256 digest in work unit {work_id}: {digest!r}")
        row["artifact_sha256"] = hashes
        work_results[work_id] = row

    faults: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(run.get("fault_results"), "run.fault_results")):
        row = _object(raw, f"run.fault_results[{index}]")
        fault_id = _text(row.get("fault_id"), f"run.fault_results[{index}].fault_id")
        if fault_id not in indexes["faults"]:
            raise GoalDrivenError(f"run references unknown fault: {fault_id}")
        if fault_id in faults:
            raise GoalDrivenError(f"duplicate fault result: {fault_id}")
        _bool(row.get("injected"), f"run.fault_results[{index}].injected")
        _bool(row.get("recovered"), f"run.fault_results[{index}].recovered")
        recovery_episode_id = row.get("recovery_episode_id")
        if recovery_episode_id is not None:
            _text(recovery_episode_id, f"run.fault_results[{index}].recovery_episode_id")
            if recovery_episode_id not in episodes:
                raise GoalDrivenError(f"fault {fault_id} cites unknown recovery episode")
        faults[fault_id] = row

    interventions: list[dict[str, Any]] = []
    for index, raw in enumerate(_list(run.get("interventions"), "run.interventions")):
        row = _object(raw, f"run.interventions[{index}]")
        severity = _text(row.get("severity"), f"run.interventions[{index}].severity")
        if severity not in VALID_INTERVENTION_SEVERITIES:
            raise GoalDrivenError(f"invalid intervention severity: {severity}")
        _text(row.get("description"), f"run.interventions[{index}].description")
        work_unit_id = row.get("work_unit_id")
        if work_unit_id is not None:
            _text(work_unit_id, f"run.interventions[{index}].work_unit_id")
            if work_unit_id not in indexes["work_units"]:
                raise GoalDrivenError(f"intervention references unknown work unit: {work_unit_id}")
        interventions.append(row)

    resources = _resource_map(run.get("resources"), "run.resources")
    return {
        **indexes,
        "run": run,
        "episodes": episodes,
        "episode_order": episode_order,
        "criterion_results": criterion_results,
        "work_results": work_results,
        "fault_results": faults,
        "interventions": interventions,
        "resources": resources,
    }


def _criterion_pass(indexes: dict[str, Any], criterion_id: str) -> tuple[bool, list[str]]:
    criterion = indexes["criteria"][criterion_id]
    result = indexes["criterion_results"].get(criterion_id)
    violations: list[str] = []
    if result is None:
        return False, [f"MISSING_CRITERION_RESULT:{criterion_id}"]
    if not result["passed"]:
        violations.append(f"CRITERION_FAILED:{criterion_id}")
    if criterion["independent_required"] and not result["independent"]:
        violations.append(f"NONINDEPENDENT_VERIFIER:{criterion_id}")
    missing_types = set(criterion["artifact_types"]) - set(result["artifact_types"])
    if missing_types:
        violations.append(
            f"MISSING_CRITERION_ARTIFACT_TYPE:{criterion_id}:{','.join(sorted(missing_types))}"
        )
    if criterion["artifact_types"] and not result["artifact_sha256"]:
        violations.append(f"MISSING_CRITERION_ARTIFACT_HASH:{criterion_id}")
    return not violations, violations


def score_goal_run(protocol: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Score one Goal-Driven run as verified work replacement."""

    indexes = validate_goal_run(run, protocol)
    violations: list[str] = []

    criterion_pass: dict[str, bool] = {}
    total_criterion_weight = 0.0
    passed_criterion_weight = 0.0
    required_pass = True
    for criterion_id, criterion in indexes["criteria"].items():
        passed, local = _criterion_pass(indexes, criterion_id)
        criterion_pass[criterion_id] = passed
        violations.extend(local)
        weight = float(criterion["weight"])
        total_criterion_weight += weight
        if passed:
            passed_criterion_weight += weight
        if criterion["required"] and not passed:
            required_pass = False
    ccr = passed_criterion_weight / total_criterion_weight

    work_total_weight = 0.0
    verified_autonomous_weight = 0.0
    human_loop_weight = 0.0
    human_baseline_total = 0.0
    human_minutes_observed = 0.0
    agent_minutes_observed = 0.0
    work_rows: list[dict[str, Any]] = []
    for work_id, work in indexes["work_units"].items():
        weight = float(work["criticality"])
        work_total_weight += weight
        human_baseline_total += float(work["human_baseline_minutes"])
        result = indexes["work_results"].get(work_id)
        verified = all(criterion_pass[criterion_id] for criterion_id in work["criterion_ids"])
        if result is None:
            violations.append(f"MISSING_WORK_UNIT_RESULT:{work_id}")
            status = "MISSING"
            performer = "HUMAN"
            autonomy_credit = 0.0
            human_minutes = float(work["human_baseline_minutes"])
            agent_minutes = 0.0
        else:
            status = result["status"]
            performer = result["performer"]
            autonomy_credit = PERFORMER_AUTONOMY[performer]
            human_minutes = float(result["human_minutes"])
            agent_minutes = float(result["agent_minutes"])
            if status != "COMPLETED":
                autonomy_credit = 0.0
                if work["required"]:
                    violations.append(f"REQUIRED_WORK_NOT_COMPLETED:{work_id}:{status}")
            if not verified:
                autonomy_credit = 0.0
                violations.append(f"WORK_UNIT_UNVERIFIED:{work_id}")
            if status == "COMPLETED" and not result["artifact_sha256"]:
                autonomy_credit = 0.0
                violations.append(f"WORK_UNIT_ARTIFACT_MISSING:{work_id}")
        verified_autonomous_weight += weight * autonomy_credit
        human_loop_weight += weight * (1.0 - autonomy_credit)
        human_minutes_observed += human_minutes
        agent_minutes_observed += agent_minutes
        work_rows.append(
            {
                "work_unit_id": work_id,
                "status": status,
                "performer": performer,
                "verified": verified,
                "autonomy_credit": autonomy_credit,
            }
        )

    intervention_penalty = sum(
        INTERVENTION_WEIGHTS[row["severity"]] for row in indexes["interventions"]
    )
    normalized_intervention = min(1.0, intervention_penalty / max(1.0, len(indexes["work_units"])))
    base_hlf = human_loop_weight / work_total_weight
    human_loop_fraction = min(1.0, base_hlf + normalized_intervention)
    autonomous_replacement = max(0.0, 1.0 - human_loop_fraction)
    vwr = verified_autonomous_weight / work_total_weight

    recovery_needed = 0
    recovery_completed = 0
    for episode_id in indexes["episode_order"]:
        episode = indexes["episodes"][episode_id]
        if episode["termination_reason"] in {"FAILED", "IDLE"}:
            recovery_needed += 1
            successors = [
                candidate
                for candidate in indexes["episodes"].values()
                if candidate.get("resumed_from") == episode_id
            ]
            if successors:
                recovery_completed += 1
            else:
                violations.append(f"UNRECOVERED_AGENT_EPISODE:{episode_id}")
    continuity_recovery_rate = (
        recovery_completed / recovery_needed if recovery_needed else 1.0
    )

    required_faults = [
        fault_id for fault_id, fault in indexes["faults"].items() if fault["required"]
    ]
    fault_recovered = 0
    for fault_id in required_faults:
        result = indexes["fault_results"].get(fault_id)
        if result is None or not result["injected"]:
            violations.append(f"REQUIRED_FAULT_NOT_INJECTED:{fault_id}")
        elif not result["recovered"]:
            violations.append(f"REQUIRED_FAULT_NOT_RECOVERED:{fault_id}")
        else:
            fault_recovered += 1
    fault_recovery_rate = fault_recovered / len(required_faults) if required_faults else 1.0

    heartbeat_failures = sum(
        int(row["heartbeat_failures"]) for row in indexes["episodes"].values()
    )
    heartbeat_integrity = 1.0 / (1.0 + heartbeat_failures)

    final_episode = indexes["episodes"][indexes["episode_order"][-1]]
    premature_completion = bool(run["completion_claimed"] and not required_pass)
    if final_episode["termination_reason"] == "CRITERIA_MET" and not required_pass:
        premature_completion = True
    if run["terminal_status"] == "SUCCESS" and not required_pass:
        premature_completion = True
    if premature_completion:
        violations.append("PREMATURE_COMPLETION_CLAIM")
    if required_pass and not run["completion_claimed"] and run["terminal_status"] == "SUCCESS":
        violations.append("SUCCESS_WITHOUT_COMPLETION_CLAIM")

    budget_exceeded = False
    for field, budget in indexes["resource_budget"].items():
        observed = indexes["resources"].get(field, 0.0)
        if observed > budget + 1e-12:
            budget_exceeded = True
            violations.append(f"RESOURCE_BUDGET_EXCEEDED:{field}")
    if bool(run["budget_exhausted"]) != budget_exceeded and run["terminal_status"] == "BUDGET_EXHAUSTED":
        violations.append("BUDGET_EXHAUSTION_FLAG_INCONSISTENT")

    persistence_integrity = 0.0 if premature_completion else min(
        continuity_recovery_rate,
        fault_recovery_rate,
        heartbeat_integrity,
    )
    goal_attainment = float(
        required_pass
        and run["terminal_status"] == "SUCCESS"
        and run["completion_claimed"]
        and not premature_completion
    )
    goal_driven_success = float(
        goal_attainment == 1.0
        and not budget_exceeded
        and continuity_recovery_rate == 1.0
        and fault_recovery_rate == 1.0
    )

    functional_signoff: float | None = None
    if indexes["reconstruction"] is not None:
        signoff_ids = indexes["reconstruction"]["signoff_criterion_ids"]
        functional_signoff = float(all(criterion_pass[criterion_id] for criterion_id in signoff_ids))

    human_hours_replaced = (human_baseline_total * vwr) / 60.0
    resource_efficiency = 0.0
    if goal_driven_success:
        budget_ratios = []
        for field, budget in indexes["resource_budget"].items():
            if budget > 0:
                budget_ratios.append(min(1.0, indexes["resources"].get(field, 0.0) / budget))
        utilization = sum(budget_ratios) / len(budget_ratios) if budget_ratios else 0.0
        resource_efficiency = max(0.0, 1.0 - utilization) * vwr

    return {
        "schema": GOAL_REPORT_SCHEMA,
        "goal_id": protocol["goal_id"],
        "run_id": run["run_id"],
        "domain_adapter": protocol["domain_adapter"],
        "industry_family": protocol["industry_family"],
        "role": protocol["role"],
        "replacement_scope": protocol["replacement_scope"],
        "verifiability_level": protocol["verifiability_level"],
        "execution_mode": protocol["execution_mode"],
        "data_kind": protocol["data_kind"],
        "metrics": {
            "GDS": goal_driven_success,
            "GA": goal_attainment,
            "CCR": ccr,
            "VWR": vwr,
            "HLF": human_loop_fraction,
            "ARP": autonomous_replacement,
            "PI": persistence_integrity,
            "CRR": continuity_recovery_rate,
            "FRR": fault_recovery_rate,
            "FCR": float(premature_completion),
            "FSR": functional_signoff,
            "HOURS_REPLACED": human_hours_replaced,
            "RNU": resource_efficiency,
        },
        "required_criteria_passed": required_pass,
        "budget_exceeded": budget_exceeded,
        "work_units": work_rows,
        "human_baseline_minutes": human_baseline_total,
        "human_minutes_observed": human_minutes_observed,
        "agent_minutes_observed": agent_minutes_observed,
        "episodes": len(indexes["episodes"]),
        "heartbeat_failures": heartbeat_failures,
        "violations": sorted(set(violations)),
    }


def index_goal_protocols(protocols: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for protocol in protocols:
        validate_goal_protocol(protocol)
        goal_id = protocol["goal_id"]
        if goal_id in result:
            raise GoalDrivenError(f"duplicate goal_id: {goal_id}")
        result[goal_id] = protocol
    if not result:
        raise GoalDrivenError("at least one goal protocol is required")
    return result


def aggregate_goal_runs(
    protocols: Iterable[dict[str, Any]],
    runs: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate Goal-Driven runs without hiding domain or scope failures."""

    protocol_index = index_goal_protocols(protocols)
    reports: list[dict[str, Any]] = []
    seen_run_ids: set[str] = set()
    for run in runs:
        goal_id = run.get("goal_id")
        if goal_id not in protocol_index:
            raise GoalDrivenError(f"run references unknown goal_id: {goal_id!r}")
        run_id = run.get("run_id")
        if run_id in seen_run_ids:
            raise GoalDrivenError(f"duplicate run_id: {run_id!r}")
        seen_run_ids.add(run_id)
        reports.append(score_goal_run(protocol_index[goal_id], run))
    if not reports:
        raise GoalDrivenError("at least one goal run is required")

    metric_names = ["GDS", "GA", "CCR", "VWR", "HLF", "ARP", "PI", "CRR", "FRR", "FCR", "FSR", "HOURS_REPLACED", "RNU"]

    def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
        metrics: dict[str, float | None] = {}
        for name in metric_names:
            values = [row["metrics"][name] for row in rows if row["metrics"][name] is not None]
            metrics[name] = sum(values) / len(values) if values else None
        return {
            "run_count": len(rows),
            "metrics": metrics,
            "violation_counts": dict(
                sorted(Counter(v for row in rows for v in row["violations"]).items())
            ),
        }

    breakdowns: dict[str, dict[str, Any]] = {}
    for field in ("industry_family", "domain_adapter", "replacement_scope", "verifiability_level", "execution_mode", "data_kind"):
        groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in reports:
            groups[row[field]].append(row)
        breakdowns[field] = {key: summarize(value) for key, value in sorted(groups.items())}

    return {
        "schema": "tiai.agentbench.goal_aggregate.v1",
        "run_count": len(reports),
        "goal_count": len({row["goal_id"] for row in reports}),
        "metrics": summarize(reports)["metrics"],
        "violation_counts": summarize(reports)["violation_counts"],
        "breakdowns": breakdowns,
        "runs": reports,
    }
