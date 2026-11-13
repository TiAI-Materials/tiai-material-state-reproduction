"""Synthetic harness regression tests; NEVER real agent benchmark scores."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from tiai_matbench.pilot_ledger import (
    BINDINGS_SCHEMA, RECEIPT_SCHEMA, RUN_SCHEMA, PilotAuditError,
    audit_pilot, build_plan, digest, protocol_slots,
)

PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "experiments" / "matched_goal_driven_protocol_v0.8.json"
P = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def complete_bindings():
    strata = P["phase_1_materials_pilot"]["strata"]
    tasks = {}
    for s in strata:
        for task in s["task_ids"]:
            tasks[task] = {
                "input_commit_or_blob": hashlib.sha256(task.encode()).hexdigest(),
                "native_verifier": s["native_verifier"],
                "execution_mode": s["execution_mode"],
            }
    return {
        "schema": BINDINGS_SCHEMA,
        "protocol_sha256": digest(P),
        "model_id": "MOCK_MODEL_FOR_TESTS_ONLY",
        "provider_route": "MOCK_PROVIDER_FOR_TESTS_ONLY",
        "tool_allowlist": ["MOCK_TOOL"],
        "budgets_by_stratum": {
            s["stratum_id"]: {"wall_time_seconds": 3600, "token_limit": 2000}
            for s in strata
        },
        "tasks": tasks,
    }


def native_fixture(slot, success=True, claimed=True):
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": "MOCK-RECEIPT-" + slot["run_id"],
        "run_id": slot["run_id"],
        "task_id": slot["task_id"],
        "verifier_id": slot["native_verifier"],
        "native_success": success,
    }
    record = {k: slot[k] for k in (
        "run_id", "experiment_id", "stratum_id", "task_id", "trial",
        "condition_id", "model_id", "provider_route", "execution_mode",
        "native_verifier", "input_commit_or_blob", "tool_allowlist", "budget",
    )}
    record.update(
        schema=RUN_SCHEMA,
        domain_id="materials_science",
        benchmark_id="MOCK_BENCHMARK_FOR_TESTS_ONLY",
        start_time="2026-11-13T00:00:00Z",
        end_time="2026-11-13T00:00:05Z",
        data_kind="REAL_AGENT_RUN",  # Unit-test fixture ONLY, never published as result.
        wall_time_seconds=5.0,
        input_tokens=None,
        output_tokens=None,
        cpu_core_seconds=None,
        gpu_seconds=None,
        monetary_cost=None,
        human_interventions=[],
        human_takeover=False,
        faults_observed=[],
        faults_recovered=[],
        restart_count=0,
        artifact_hashes={"output": "f" * 64} if success else {},
        native_verifier_receipt=receipt,
        native_success=success,
        claimed_success=claimed,
        false_completion=claimed and not success,
        GDS=None, VWR=None, HLF=None, FCR=None, FRR=None, RNU=None,
        safety_evidence_coverage=None, trajectory_safety=None,
    )
    return record, {receipt["receipt_id"]: digest(receipt)}


class PilotLedgerTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_plan(P, complete_bindings())
        self.slot = self.plan["slots"][0]

    def test_frozen_192_plan_has_six_matched_arms(self):
        slots = protocol_slots(P)
        self.assertEqual(len(slots), 192)
        groups = {}
        for s in slots:
            groups.setdefault(s["pair_id"], set()).add(s["condition_id"])
        self.assertEqual(len(groups), 32)
        self.assertTrue(all(len(x) == 6 for x in groups.values()))

    def test_all_unbound_by_default(self):
        plan = build_plan(P)
        self.assertEqual((plan["blocked"], plan["ready"]), (192, 0))
        self.assertIsNone(plan["scientific_results"])
        report = audit_pilot(P, plan, [], {})
        self.assertEqual(report["not_submitted"], 192)
        self.assertIsNone(report["real_agent_effect_estimate"])

    def test_mock_binding_is_complete_but_not_executed(self):
        self.assertEqual(self.plan["ready"], 192)
        self.assertEqual(self.plan["blocked"], 0)
        self.assertTrue(all(s["data_kind"] == "PRE_REGISTERED_SLOT_NOT_EXECUTED"
                            for s in self.plan["slots"]))

    def test_no_drift_in_ablation(self):
        p = copy.deepcopy(P)
        p["system_conditions"].pop()
        with self.assertRaises(PilotAuditError):
            protocol_slots(p)

    def test_missing_native_receipt_rejected(self):
        record, trusted = native_fixture(self.slot)
        record.pop("native_verifier_receipt")
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)
        self.assertEqual(len(report["invalid_records"]), 1)

    def test_forged_receipt_not_in_trusted_index_rejected(self):
        record, _ = native_fixture(self.slot)
        report = audit_pilot(P, self.plan, [record], {})
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_independently_indexed_mock_receipt_is_structurally_accepted(self):
        record, trusted = native_fixture(self.slot)
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 1)
        self.assertEqual(report["not_submitted"], 191)
        self.assertIsNone(report["real_agent_effect_estimate"])

    def test_false_completion_disagreement_rejected(self):
        record, trusted = native_fixture(self.slot, success=False, claimed=True)
        record["false_completion"] = False
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertIn("false completion", report["invalid_records"][0]["error"])

    def test_native_failure_claimed_success_detected(self):
        record, trusted = native_fixture(self.slot, success=False, claimed=True)
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["false_completions"], 1)
        self.assertEqual(report["verified_native_passes"], 0)

    def test_binding_budget_mutation_rejected(self):
        record, trusted = native_fixture(self.slot)
        record["budget"]["wall_time_seconds"] = 4000
        with self.assertRaises(PilotAuditError):
            audit_pilot(P, self.plan, [record], trusted)

    def test_synthetic_fixture_not_empirical_score(self):
        record, trusted = native_fixture(self.slot)
        record["data_kind"] = "SIMULATED_HARNESS_FIXTURE"
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_no_safety_from_missing_receipt(self):
        record, trusted = native_fixture(self.slot)
        record["trajectory_safety"] = True
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_unregistered_run_fails(self):
        record, trusted = native_fixture(self.slot)
        record["run_id"] = "unregistered"
        with self.assertRaises(PilotAuditError):
            audit_pilot(P, self.plan, [record], trusted)

    def test_duplicate_run_fails(self):
        record, trusted = native_fixture(self.slot)
        with self.assertRaises(PilotAuditError):
            audit_pilot(P, self.plan, [record, record], trusted)

    def test_nonfinite_cost_rejected(self):
        record, trusted = native_fixture(self.slot)
        record["monetary_cost"] = float("inf")
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_overreported_recovery_rejected(self):
        record, trusted = native_fixture(self.slot)
        record["faults_recovered"] = ["fault-not-observed"]
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_required_field_missing_rejected(self):
        record, trusted = native_fixture(self.slot)
        record.pop("start_time")
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertIn("missing required ledger keys", report["invalid_records"][0]["error"])

    def test_native_failure_cannot_claim_vwr(self):
        record, trusted = native_fixture(self.slot, success=False, claimed=False)
        record["VWR"] = 1.0
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_cost_score_requires_cost(self):
        record, trusted = native_fixture(self.slot)
        record["RNU"] = 1.0
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)

    def test_no_recovery_rate_without_faults(self):
        record, trusted = native_fixture(self.slot)
        record["FRR"] = 1.0
        report = audit_pilot(P, self.plan, [record], trusted)
        self.assertEqual(report["accepted_native_receipts"], 0)


if __name__ == "__main__":
    unittest.main()