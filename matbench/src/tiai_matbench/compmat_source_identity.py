"""Fail-closed audit of the eight frozen public CompMat-Bench source identities.

This is a source inventory, NOT an execution runner or native task receipt.
The git tree SHA identifies only published repository bytes; release-staged
inputs and licensed packages must be verified independently before dispatch.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .pilot_ledger import PilotAuditError, digest, load_json

SOURCE_SCHEMA = "tiai.agentbench.compmat_source_identity.v0.11"
REPO = "cz2014/CompMat-Bench"
UPSTREAM_COMMIT = "03fec439ca9c9b1b14ea914896886b74d3e739bc"
PROTOCOL_SHA = "6d2673a95e1b6f731d1d83673ed42782efb0b3305bafd6ae7f58b113958b9001"
CORE_SHA256 = "6be09447536a8d3e23aa9e21e3cea3864380ad1a7c841fb9970930b008f067bb"
CORE_BYTES = 516859324
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
# Directly read from the frozen upstream git-tree and task.yaml identities.
TASK_SHA = {
    "task_202602_015_step_ws2-wse2-moire-lammps-inputs": ("532960a2ceea6b18379fe0238885c49a11183a9f", "c212bb1597a2c2fc9dd6f73128a1663be7108971", "gen_input"),
    "task_202601_009_step_snte-110-surface-dirac-cones": ("944b5485f695709e9b51512c1850e11f19dd19a0", "9048fb5888f5060b7dc76864b809f5b39c851708", "analyze"),
    "task_202603_007_step_znmgo-strain-composition-phase-map": ("f261454f7a57999e50186a906da9c747d16c1066", "bbd3bd278f168f85f386a4a86f54dd3b949d2330", "analyze"),
    "task_202603_034_step_batio3-dislocation-dipole-relaxed": ("cc0f9a2fc727a9bdab09a6e6e8328b0a1358dafa", "8b4cf6899b5e7ba19ee1daccd8615b36ee909727", "analyze"),
    "task_202603_024_step_si-ge-slab-thermal-conductivity": ("9c494f1a607e0dfdf4ca139ee5a56712e578e623", "57fad0e15bc9f476a82f2294fd77fbda61fd7209", "analyze"),
    "task_202603_031_step_batio3-hysteresis-lammps-inputs": ("a4b6898d42ea31e4398b87f322bb8ab4119ccfea", "cc0644630229f883f2ab97aca45c4da6063233e9", "gen_input"),
}
WORKFLOW_SHA = {
    "C03": ("b184b7ac82f53e046581e45beffda9a3407f8fe7", "f97c64314b32fde4c29d89266651d0cb885ff39c", "e763c37007ce47e1e66b219e9355a4efbc7690b6", False),
    "C07": ("61cbb16abbf174e421a0c1c222b3a076b8a8de9a", "328279472348d0d1477109ee1079981747c33317", "9586a5aafff52243f03dcf041f1cc8074bdcdc6b", True),
}


def _require(test: bool, message: str) -> None:
    if not test:
        raise PilotAuditError("CompMat source preflight: " + message)


def audit_source_identity(doc: dict, protocol: dict) -> dict:
    """Check source pins without transforming them into a native-ready claim."""
    _require(isinstance(doc, dict) and doc.get("schema") == SOURCE_SCHEMA,
             "wrong schema")
    _require(digest(protocol) == doc.get("protocol_sha256") == PROTOCOL_SHA,
             "frozen protocol drift")
    strata = protocol["phase_1_materials_pilot"]["strata"]
    step_ids = strata[1]["task_ids"]
    flow_ids = strata[2]["task_ids"]
    hidden_ids = strata[0]["task_ids"]
    _require(step_ids == list(TASK_SHA) and flow_ids == list(WORKFLOW_SHA),
             "task list/order changed")
    upstream = doc.get("upstream", {})
    _require(upstream.get("repo") == REPO and
             upstream.get("commit") == UPSTREAM_COMMIT and
             upstream.get("release") == "v1.0.0",
             "unrecognized upstream version")
    core = upstream.get("published_core_release", {})
    _require(core.get("filename") == "compmat_bench_core.zip" and
             core.get("byte_size") == CORE_BYTES and
             core.get("expected_sha256") == CORE_SHA256,
             "published core archive metadata changed")
    _require(core.get("downloaded_actual_sha256") is None,
             "unstaged snapshot must not claim archive was verified")
    steps = doc.get("public_tasks", [])
    _require(isinstance(steps, list) and [r.get("task_id") for r in steps] == step_ids,
             "public step identity/order mismatch")
    for row in steps:
        task_id = row["task_id"]
        tree, meta, role = TASK_SHA[task_id]
        _require(row.get("source_path") == "tasks/" + task_id and
                 row.get("task_tree_git_sha") == tree and
                 row.get("task_yaml_git_sha") == meta and
                 row.get("role") == role,
                 "task Git source drift: " + task_id)
        _require(row.get("source_kind") == "GIT_METADATA_NOT_STAGED" and
                 row.get("native_input_sha256") is None and
                 row.get("native_grader_reference_receipt") is None,
                 "task native staging cannot be inferred: " + task_id)
    flows = doc.get("public_workflows", [])
    _require(isinstance(flows, list) and [r.get("task_id") for r in flows] == flow_ids,
             "workflow identity/order mismatch")
    for row in flows:
        task_id = row["task_id"]
        tree, agent, grader, potcar = WORKFLOW_SHA[task_id]
        _require(row.get("source_path") == "workflows/" + task_id and
                 row.get("workflow_tree_git_sha") == tree and
                 row.get("agent_full_guidance_tree_git_sha") == agent and
                 row.get("grader_tree_git_sha") == grader and
                 row.get("requires_licensed_vasp_potcar") is potcar,
                 "workflow source/license drift: " + task_id)
        _require(row.get("source_kind") == "GIT_METADATA_NOT_STAGED" and
                 row.get("native_input_sha256") is None and
                 row.get("native_grader_reference_receipt") is None,
                 "workflow not natively staged: " + task_id)
        _require(row.get("licensed_potcar_verified") ==
                 (None if potcar else "NOT_REQUIRED"),
                 "licensed POTCAR was improperly inferred: " + task_id)
    hidden = doc.get("hidden_real_replay", [])
    _require(isinstance(hidden, list) and
             [r.get("task_id") for r in hidden] == hidden_ids,
             "four frozen hidden tasks must remain in denominator")
    for row in hidden:
        _require(row.get("private_input_digest") is None and
                 row.get("independent_hidden_verifier_attestation") is None,
                 "cannot assert private hidden input/answer binding")
    bindings = doc.get("execution_bindings")
    _require(isinstance(bindings, dict) and
             set(bindings) == {"model_id", "provider_route", "allowed_tools",
                              "budgets_by_stratum", "independent_verifier_key_id"} and
             all(x is None for x in bindings.values()),
             "no authorized model/provider/verifier binding recorded")
    _require(doc.get("selected_public_are_core_only") is True,
             "selected public tasks unexpectedly require heavy-input archives")
    _require(doc.get("status") == "SOURCE_IDENTIFIED_NOT_NATIVE_STAGED" and
             doc.get("native_dispatch_allowed") is False,
             "source inventory must not authorize execution")
    _require(isinstance(doc.get("claim_boundary"), str) and
             "not" in doc["claim_boundary"].lower(), "missing claim boundary")
    return {
        "schema": SOURCE_SCHEMA, "status": "SOURCE_PINS_VALIDATED_NOT_READY",
        "frozen_protocol_sha256": PROTOCOL_SHA,
        "public_task_git_identities": len(steps),
        "public_workflow_git_identities": len(flows),
        "hidden_tasks_unbound": len(hidden),
        "verified_release_archive_bytes": 0,
        "verified_native_input_workspaces": 0,
        "verified_native_grader_runs": 0,
        "real_model_runs": 0,
        "legitimate_ready_slots": 0,
        "blocked_slots": 192,
        "dispatch_allowed": False,
        "blockers": [
            "CORE_ARCHIVE_BYTES_NOT_DOWNLOADED_OR_HASH_VERIFIED",
            "EIGHT_STAGED_AGENT_INPUTS_NOT_HASHED",
            "EIGHT_NATIVE_GRADER_REFERENCE_CHECKS_NOT_EXECUTED",
            "C07_LICENSED_POTCAR_NOT_VERIFIED",
            "FOUR_HIDDEN_REAL_REPLAY_INPUTS_NOT_BOUND",
            "SAME_MODEL_PROVIDER_TOOLS_AND_BUDGET_NOT_AUTHORIZED",
            "INDEPENDENT_VERIFIER_TRUST_ROOT_NOT_BOUND",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Source identity preflight; never an Agent run")
    p.add_argument("--inventory", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    report = audit_source_identity(load_json(a.inventory), load_json(a.protocol))
    Path(a.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
