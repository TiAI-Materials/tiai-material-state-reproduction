"""Deterministic pilot-slot expansion and native-verifier receipt audit.

This is NOT an agent/model runner. It binds the frozen v0.8 experiment to an
immutable 192-slot launch ledger, rejects unmatched runs, and only admits
external verifier receipts through an independently supplied trusted index.
No synthetic fixture may be reported as empirical Agent performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

CONDITIONS = (
    "single_agent",
    "ordinary_multi_agent",
    "goal_driven_no_independent_verifier",
    "goal_driven_no_recovery",
    "goal_driven_no_provenance_claim_gate",
    "full_goal_driven",
)
PLAN_SCHEMA = "tiai.agentbench.pilot_plan.v0.9"
BINDINGS_SCHEMA = "tiai.agentbench.pilot_bindings.v0.9"
RUN_SCHEMA = "tiai.agentbench.pilot_native_run.v0.9"
RECEIPT_SCHEMA = "tiai.agentbench.native_receipt.v0.9"
REQUIRED_COSTS = ("wall_time_seconds", "input_tokens", "output_tokens",
                  "cpu_core_seconds", "gpu_seconds", "monetary_cost")
SCORES = ("GDS", "VWR", "HLF", "FCR", "FRR", "RNU")


class PilotAuditError(ValueError):
    pass


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=False).encode("utf-8")


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def _finite_nonnegative(value: Any, field: str, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PilotAuditError(f"{field}: expected nonnegative finite number")
    if not math.isfinite(value) or value < 0:
        raise PilotAuditError(f"{field}: expected nonnegative finite number")


def protocol_slots(protocol: dict) -> list[dict]:
    if protocol.get("schema") != "tiai.agentbench.matched_goal_driven_protocol.v0.8":
        raise PilotAuditError("not the frozen v0.8 protocol")
    conds = [row["condition_id"] for row in protocol["system_conditions"]]
    if len(conds) != 6 or set(conds) != set(CONDITIONS):
        raise PilotAuditError("ablation conditions have changed")
    strata = protocol["phase_1_materials_pilot"]["strata"]
    if len(strata) != 3:
        raise PilotAuditError("pilot strata changed")
    slots = []
    for stratum in strata:
        tasks = stratum["task_ids"]
        if len(tasks) != len(set(tasks)):
            raise PilotAuditError("duplicate task")
        for task in tasks:
            for trial in range(1, stratum["repeats_per_condition_task"] + 1):
                # Same pairing index for all six conditions. Never outcome-selected.
                pair_id = digest([protocol["experiment_id"], stratum["stratum_id"], task, trial])[:20]
                for cond in CONDITIONS:
                    slot = dict(
                        experiment_id=protocol["experiment_id"],
                        stratum_id=stratum["stratum_id"],
                        execution_mode=stratum["execution_mode"],
                        task_id=task,
                        condition_id=cond,
                        trial=trial,
                        pair_id=pair_id,
                        native_verifier=stratum["native_verifier"],
                    )
                    slot["run_id"] = digest(slot)[:24]
                    slots.append(slot)
    if len(slots) != 192 or len(set(x["run_id"] for x in slots)) != 192:
        raise PilotAuditError("pilot no longer matches frozen 192-slot design")
    return slots


def build_plan(protocol: dict, bindings: dict | None = None) -> dict:
    slots = protocol_slots(protocol)
    protocol_sha = digest(protocol)
    bindings = bindings or {}
    model_id = bindings.get("model_id")
    provider_route = bindings.get("provider_route")
    tools = bindings.get("tool_allowlist")
    budgets = bindings.get("budgets_by_stratum", {})
    tasks = bindings.get("tasks", {})
    if bindings:
        if bindings.get("schema") != BINDINGS_SCHEMA:
            raise PilotAuditError("invalid bindings schema")
        if bindings.get("protocol_sha256") != protocol_sha:
            raise PilotAuditError("protocol digest mismatch")
    for slot in slots:
        task = tasks.get(slot["task_id"], {})
        budget = budgets.get(slot["stratum_id"])
        reasons = []
        if not isinstance(model_id, str) or not model_id.strip():
            reasons.append("MODEL_UNBOUND")
        if not isinstance(provider_route, str) or not provider_route.strip():
            reasons.append("PROVIDER_UNBOUND")
        if not isinstance(tools, list) or not tools or not all(
            isinstance(t, str) and t.strip() for t in tools
        ):
            reasons.append("TOOLS_UNBOUND")
        if not isinstance(budget, dict) or not budget:
            reasons.append("BUDGET_UNBOUND")
        else:
            for name, value in budget.items():
                _finite_nonnegative(value, "budget." + name)
        if not isinstance(task, dict) or not task.get("input_commit_or_blob"):
            reasons.append("INPUT_UNBOUND")
        if task.get("native_verifier") != slot["native_verifier"]:
            reasons.append("VERIFIER_UNBOUND_OR_MISMATCHED")
        if task.get("execution_mode") != slot["execution_mode"]:
            reasons.append("MODE_UNBOUND_OR_MISMATCHED")
        slot.update(
            model_id=model_id,
            provider_route=provider_route,
            tool_allowlist=tools,
            budget=budget,
            input_commit_or_blob=task.get("input_commit_or_blob"),
            binding_status="BLOCKED" if reasons else "READY_TO_DISPATCH",
            blocking_reasons=reasons,
            data_kind="PRE_REGISTERED_SLOT_NOT_EXECUTED",
        )
    return {
        "schema": PLAN_SCHEMA,
        "protocol_sha256": protocol_sha,
        "run_count": len(slots),
        "ready": sum(s["binding_status"] == "READY_TO_DISPATCH" for s in slots),
        "blocked": sum(s["binding_status"] == "BLOCKED" for s in slots),
        "dispatch_allowed": all(s["binding_status"] == "READY_TO_DISPATCH" for s in slots),
        "slots": slots,
        "slot_set_digest": digest(slots),
        "scientific_results": None,
    }


def _trusted_receipt(record: dict, trusted_index: dict, slot: dict) -> bool:
    receipt = record.get("native_verifier_receipt")
    if not isinstance(receipt, dict):
        raise PilotAuditError("independent native receipt required")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise PilotAuditError("wrong native receipt schema")
    if receipt.get("run_id") != slot["run_id"] or receipt.get("task_id") != slot["task_id"]:
        raise PilotAuditError("receipt belongs to another run/task")
    if receipt.get("verifier_id") != slot["native_verifier"]:
        raise PilotAuditError("native verifier changed")
    if type(receipt.get("native_success")) is not bool:
        raise PilotAuditError("native success must be boolean")
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        raise PilotAuditError("receipt identity missing")
    if not isinstance(trusted_index, dict):
        raise PilotAuditError("separate trusted native receipt index required")
    # Only evidence imported independently from the native scorer can populate
    # this index. Checking equality cannot itself prove the index's authority.
    if trusted_index.get(receipt_id) != digest(receipt):
        raise PilotAuditError("native receipt absent/mismatched in trusted index")
    if record.get("native_success") is not receipt["native_success"]:
        raise PilotAuditError("self-reported native success contradicts verifier")
    return receipt["native_success"]


def audit_pilot(protocol: dict, plan: dict, records: list[dict],
                trusted_receipts: dict) -> dict:
    if plan.get("schema") != PLAN_SCHEMA or plan.get("protocol_sha256") != digest(protocol):
        raise PilotAuditError("plan/protocol mismatch")
    if plan.get("slot_set_digest") != digest(plan.get("slots", [])):
        raise PilotAuditError("plan bindings changed after pre-registration")
    expected = {row["run_id"]: row for row in protocol_slots(protocol)}
    if set(x["run_id"] for x in plan.get("slots", [])) != set(expected):
        raise PilotAuditError("missing or altered pre-registered slots")
    plan_slots = {row["run_id"]: row for row in plan["slots"]}
    if len(plan_slots) != 192 or len(records) != len(set(r.get("run_id") for r in records)):
        raise PilotAuditError("duplicate or invalid run identity")
    errors = []
    accepted = []
    for record in records:
        run_id = record.get("run_id")
        if run_id not in plan_slots:
            raise PilotAuditError("unregistered run identity: " + str(run_id))
        slot = plan_slots[run_id]
        try:
            if slot.get("binding_status") != "READY_TO_DISPATCH":
                raise PilotAuditError("run executed without complete frozen bindings")
            if record.get("schema") != RUN_SCHEMA:
                raise PilotAuditError("wrong run ledger schema")
            missing_fields = set(protocol["required_run_ledger"]) - set(record)
            if missing_fields:
                raise PilotAuditError("missing required ledger keys: " + ",".join(sorted(missing_fields)))
            if record.get("data_kind") != "REAL_AGENT_RUN":
                raise PilotAuditError("synthetic/replay fixture is not a real agent result")
            for k in ("experiment_id", "stratum_id", "task_id", "trial",
                      "condition_id", "model_id", "provider_route", "execution_mode",
                      "native_verifier", "input_commit_or_blob", "tool_allowlist", "budget"):
                if record.get(k) != slot[k]:
                    raise PilotAuditError("frozen matching field changed: " + k)
            for k in REQUIRED_COSTS:
                _finite_nonnegative(record.get(k), k, allow_null=True)
            if record.get("wall_time_seconds") is None:
                raise PilotAuditError("wall time is required")
            for k in ("human_interventions", "faults_observed", "faults_recovered"):
                if not isinstance(record.get(k), list):
                    raise PilotAuditError("missing list: " + k)
            if not isinstance(record.get("human_takeover"), bool):
                raise PilotAuditError("human takeover must be boolean")
            if not isinstance(record.get("artifact_hashes"), dict):
                raise PilotAuditError("artifact SHA-256 map missing")
            if not isinstance(record.get("claimed_success"), bool):
                raise PilotAuditError("claimed_success must be boolean")
            if not isinstance(record.get("restart_count"), int) or isinstance(
                record.get("restart_count"), bool
            ) or record["restart_count"] < 0:
                raise PilotAuditError("restart count malformed")
            if len(record["faults_recovered"]) > len(record["faults_observed"]):
                raise PilotAuditError("cannot recover more faults than observed")
            if not set(record["faults_recovered"]).issubset(
                set(record["faults_observed"])
            ):
                raise PilotAuditError("recovered fault not observed")
            success = _trusted_receipt(record, trusted_receipts, slot)
            false_completion = record["claimed_success"] and not success
            if record.get("false_completion") is not false_completion:
                raise PilotAuditError("false completion contradicts native receipt")
            if success and not record["artifact_hashes"]:
                raise PilotAuditError("verified success requires artifact identity")
            for k in SCORES + ("safety_evidence_coverage",):
                value = record.get(k)
                _finite_nonnegative(value, k, allow_null=True)
                if value is not None and value > 1:
                    raise PilotAuditError(k + " > 1")
            if record.get("trajectory_safety") not in (None, True, False):
                raise PilotAuditError("invalid trajectory safety")
            if record.get("trajectory_safety") is True and not record.get("safety_receipt"):
                raise PilotAuditError("safety cannot be asserted without safety receipt")
            if not success and (record.get("GDS") not in (None, 0, 0.0) or
                                record.get("VWR") not in (None, 0, 0.0)):
                raise PilotAuditError("failed native task cannot claim verified Goal or Work Replacement")
            if record.get("FCR") is not None and record["FCR"] != int(false_completion):
                raise PilotAuditError("FCR contradicts verified false completion")
            if record.get("FRR") is not None and not record["faults_observed"]:
                raise PilotAuditError("fault recovery rate requires observed faults")
            if record.get("RNU") is not None and record.get("monetary_cost") is None:
                raise PilotAuditError("cost-normalized utility requires cost evidence")
            accepted.append({"run_id": run_id, "native_success": success,
                             "false_completion": false_completion,
                             "human_takeover": record["human_takeover"]})
        except (PilotAuditError, TypeError, ValueError) as exc:
            errors.append({"run_id": run_id, "error": str(exc)})
    missing = len(expected) - len(records)
    if missing < 0:
        raise PilotAuditError("too many runs")
    return {
        "schema": "tiai.agentbench.pilot_audit.v0.9",
        "protocol_sha256": digest(protocol),
        "planned": 192,
        "received": len(records),
        "accepted_native_receipts": len(accepted),
        "invalid_records": errors,
        "not_submitted": missing,
        "verified_native_passes": sum(x["native_success"] for x in accepted),
        "false_completions": sum(x["false_completion"] for x in accepted),
        "matched_complete": missing == 0 and not errors,
        # A digest index is not an independent verifier signature. This
        # legacy structural audit never grants permission for effect analysis.
        # Use attested_pilot.audit_attested_pilot with an out-of-band key.
        "real_agent_effect_estimate": None,
        "claim_boundary": "STRUCTURAL AUDIT ONLY: supplied digest index can be forged. Require externally authenticated native receipts and independently sealed run/artifact telemetry before any system-effect estimate.",
    }


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          PilotAuditError("nonfinite JSON")))


def main() -> None:
    p = argparse.ArgumentParser(description="v0.8 frozen pilot plan and native receipt audit")
    p.add_argument("command", choices=["plan", "audit"])
    p.add_argument("--protocol", required=True)
    p.add_argument("--bindings")
    p.add_argument("--plan")
    p.add_argument("--ledger")
    p.add_argument("--trusted-receipts")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    protocol = load_json(args.protocol)
    if args.command == "plan":
        report = build_plan(protocol, load_json(args.bindings) if args.bindings else None)
    else:
        if not args.plan or not args.ledger or not args.trusted_receipts:
            p.error("audit requires --plan, --ledger and --trusted-receipts")
        with open(args.ledger, encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream if line.strip()]
        report = audit_pilot(protocol, load_json(args.plan), records,
                             load_json(args.trusted_receipts))
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                             allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "slots"},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()