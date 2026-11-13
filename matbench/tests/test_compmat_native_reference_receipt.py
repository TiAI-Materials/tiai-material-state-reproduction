"""Receipt consistency regression, NOT a new native grader execution or Agent result."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "experiments" / "COMPMAT_ZNMGO_NATIVE_REFERENCE_RECEIPT_V0.13.json"
IDENTITY = ROOT / "experiments" / "COMPMAT_SOURCE_IDENTITY_V0.11.json"


class NativeReferenceReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        cls.identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
        cls.task = next(t for t in cls.identity["public_tasks"]
                        if t["task_id"] == cls.receipt["task_id"])

    def test_official_frozen_source_identity_is_unchanged(self):
        self.assertEqual(self.receipt["upstream_commit"],
                         self.identity["upstream"]["commit"])
        self.assertEqual(self.receipt["official_tree_sha"],
                         self.task["task_tree_git_sha"])
        self.assertEqual(self.receipt["source_mode"],
                         "GIT_BLOBS_NOT_CORE_RELEASE")

    def test_reference_and_corrupted_control_have_opposite_native_scores(self):
        r = self.receipt
        self.assertTrue(r["git_blob_integrity"])
        self.assertTrue(r["selftest_pass"])
        self.assertEqual(r["reference_native_evaluation"]["returncode"], 0)
        self.assertEqual(r["corrupt_native_evaluation"]["returncode"], 0)
        self.assertEqual((r["actual_reference_score"],
                          r["actual_corrupt_control_score"]), (1, 0))
        self.assertEqual(r["status"], "REFERENCE_NATIVE_GRADER_SELFTEST_PASS")

    def test_provenance_has_four_unique_verified_source_files(self):
        rows = self.receipt["files"]
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({r["path"] for r in rows}), 4)
        for row in rows:
            self.assertRegex(row["git_blob_sha"], r"^[0-9a-f]{40}$")
            self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(row["byte_size"], 0)
            self.assertTrue(row["path"].startswith("grader/"))

    def test_native_smoke_never_promotes_pilot_readiness(self):
        r = self.receipt
        self.assertFalse(r["core_asset_sha256_verified"])
        self.assertFalse(r["native_dispatch_allowed"])
        self.assertEqual(r["real_tiai_agent_runs"], 0)
        self.assertEqual(r["pilot_ready_slots"], 0)
        self.assertEqual(self.task["source_kind"], "GIT_METADATA_NOT_STAGED")
        self.assertIsNone(self.task["native_input_sha256"])
        self.assertIsNone(self.task["native_grader_reference_receipt"])


if __name__ == "__main__":
    unittest.main()
