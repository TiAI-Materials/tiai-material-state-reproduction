"""Identity-only CompMat preflight tests, not model or native grader runs."""
import copy
import json
import unittest
from pathlib import Path

from tiai_matbench.compmat_source_identity import audit_source_identity
from tiai_matbench.pilot_ledger import PilotAuditError

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / "experiments/COMPMAT_SOURCE_IDENTITY_V0.11.json").read_text(encoding="utf-8"))
PROTOCOL = json.loads((ROOT / "experiments/matched_goal_driven_protocol_v0.8.json").read_text(encoding="utf-8"))


class CompMatSourceIdentityTests(unittest.TestCase):
    def audit(self, payload=None):
        return audit_source_identity(INVENTORY if payload is None else payload, PROTOCOL)

    def test_eight_frozen_public_source_pins_are_not_native_runs(self):
        report = self.audit()
        self.assertEqual(report["public_task_git_identities"], 6)
        self.assertEqual(report["public_workflow_git_identities"], 2)
        self.assertEqual(report["hidden_tasks_unbound"], 4)
        self.assertEqual(report["real_model_runs"], 0)
        self.assertEqual(report["blocked_slots"], 192)
        self.assertFalse(report["dispatch_allowed"])

    def test_upstream_commit_tampering_fails(self):
        x = copy.deepcopy(INVENTORY)
        x["upstream"]["commit"] = "0" * 40
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_replaced_source_tree_sha_fails(self):
        x = copy.deepcopy(INVENTORY)
        x["public_tasks"][0]["task_tree_git_sha"] = "0" * 40
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_unfrozen_public_task_or_order_fails(self):
        x = copy.deepcopy(INVENTORY)
        x["public_tasks"][0], x["public_tasks"][1] = x["public_tasks"][1], x["public_tasks"][0]
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_published_core_checksum_mutation_fails(self):
        x = copy.deepcopy(INVENTORY)
        x["upstream"]["published_core_release"]["expected_sha256"] = "a" * 64
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_claiming_archive_bytes_downloaded_without_verification_fails(self):
        x = copy.deepcopy(INVENTORY)
        x["upstream"]["published_core_release"]["downloaded_actual_sha256"] = x["upstream"]["published_core_release"]["expected_sha256"]
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_git_metadata_cannot_be_native_input_hash(self):
        x = copy.deepcopy(INVENTORY)
        x["public_tasks"][0]["native_input_sha256"] = "f" * 64
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_licensed_c07_potcar_is_not_assumed_present(self):
        x = copy.deepcopy(INVENTORY)
        x["public_workflows"][1]["licensed_potcar_verified"] = "YES"
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_private_hidden_tasks_cannot_be_silent_omissions(self):
        x = copy.deepcopy(INVENTORY)
        x["hidden_real_replay"].pop()
        with self.assertRaises(PilotAuditError):
            self.audit(x)

    def test_placeholder_provider_binding_cannot_unlock_dispatch(self):
        x = copy.deepcopy(INVENTORY)
        x["execution_bindings"]["model_id"] = "MOCK_MODEL_FOR_TESTS_ONLY"
        x["native_dispatch_allowed"] = True
        with self.assertRaises(PilotAuditError):
            self.audit(x)


if __name__ == "__main__":
    unittest.main()
