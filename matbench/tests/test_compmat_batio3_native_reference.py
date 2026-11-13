"""Frozen *source-only* BaTiO3 official native-grader evidence, not Agent scores."""
import copy
import json
from pathlib import Path
import unittest

from tiai_matbench.compmat_source_identity import TASK_SHA, audit_source_identity
from tiai_matbench.pilot_ledger import PilotAuditError

ROOT = Path(__file__).resolve().parents[1]
TASK = "task_202603_034_step_batio3-dislocation-dipole-relaxed"
TRUE_TREE = "cc0f9a2fc727a9bdab09a6e6e8328b0a1358dafa"
BAD_AGENT_SUBTREE = "4d3b5a71cff0e4ceef5448c5336c9f01bc202c81"
RECEIPT = json.loads((ROOT / "experiments/COMPMAT_BATIO3_NATIVE_RECEIPT_V0.14.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((ROOT / "experiments/COMPMAT_SOURCE_IDENTITY_V0.11.json").read_text(encoding="utf-8"))
PROTOCOL = json.loads((ROOT / "experiments/matched_goal_driven_protocol_v0.8.json").read_text(encoding="utf-8"))


class BaTiO3NativeReferenceTests(unittest.TestCase):
    def test_corrected_source_pin_is_actual_task_root(self):
        self.assertEqual(TASK_SHA[TASK][0], TRUE_TREE)
        row = next(x for x in INVENTORY["public_tasks"] if x["task_id"] == TASK)
        self.assertEqual(row["task_tree_git_sha"], TRUE_TREE)
        self.assertEqual(audit_source_identity(INVENTORY, PROTOCOL)["blocked_slots"], 192)

    def test_agent_prompt_subtree_cannot_masquerade_as_task_root(self):
        bad = copy.deepcopy(INVENTORY)
        next(x for x in bad["public_tasks"] if x["task_id"] == TASK)["task_tree_git_sha"] = BAD_AGENT_SUBTREE
        with self.assertRaises(PilotAuditError):
            audit_source_identity(bad, PROTOCOL)

    def test_native_reference_and_coherent_global_swap_both_pass(self):
        results = RECEIPT["evaluations"]
        self.assertEqual(results["identity_reference"]["score"], 1)
        self.assertEqual(results["identity_reference"]["accepted_naming_convention"], "identity")
        self.assertEqual(results["coherent_global_swap"]["score"], 1)
        self.assertEqual(results["coherent_global_swap"]["accepted_naming_convention"], "BaO_TiO2_swapped")
        self.assertEqual(results["identity_reference"]["returncode"], 0)
        self.assertEqual(results["coherent_global_swap"]["returncode"], 0)

    def test_inconsistent_label_and_physical_spacing_mutation_both_fail(self):
        results = RECEIPT["evaluations"]
        for case in ("incoherent_label_only_swap", "corrupted_spacing"):
            with self.subTest(case=case):
                self.assertEqual(results[case]["score"], 0)
                self.assertIsNone(results[case]["accepted_naming_convention"])
                self.assertEqual(results[case]["returncode"], 0)

    def test_four_official_blobs_and_stdout_receipts_are_pinned(self):
        self.assertTrue(RECEIPT["git_blob_integrity"])
        self.assertEqual(RECEIPT["official_tree_sha"], TRUE_TREE)
        self.assertEqual(RECEIPT["upstream_commit"], "03fec439ca9c9b1b14ea914896886b74d3e739bc")
        self.assertEqual(
            {row["path"]: row["git_blob_sha"] for row in RECEIPT["files"]},
            {
                "grader/grader.py": "ac59c40b428472c9b50ce29c484309f9c64028c8",
                "grader/graderlib/grader_numeric.py": "9a451f81d09ad5f9e943fa0085c954c91303ebf1",
                "grader/ground_truth.json": "49e70a0ae8346153aa60938368db3b0522ae02d1",
                "grader/reference_submission/answer.json": "7dff3887037e109c60c45458472c4cb7c20f6211",
            })
        self.assertEqual(
            {k: v["stdout_sha256"] for k, v in RECEIPT["evaluations"].items()},
            {
                "identity_reference": "3747038d3572a298018401e989b0b47b9db2a003464d6454919291de77035f2b",
                "coherent_global_swap": "e16aa12e4106372eb2107ae0845d4459eb762e518fe54a9322b23e20f57b0695",
                "incoherent_label_only_swap": "a961039881afb696aa1e4bb01877ef5aac72b052dbb37e9817cbfc7235275872",
                "corrupted_spacing": "5f2c87fdfe81a770824fcf181332fbb45fd5600b90adf8872c55ab2dd3e4bd3c",
            })

    def test_source_only_smoke_never_unlocks_any_agent_trial(self):
        self.assertTrue(RECEIPT["selftest_pass"])
        self.assertFalse(RECEIPT["core_asset_sha256_verified"])
        self.assertFalse(RECEIPT["native_dispatch_allowed"])
        self.assertEqual(RECEIPT["real_tiai_agent_runs"], 0)
        self.assertEqual(RECEIPT["pilot_ready_slots"], 0)
        self.assertEqual(RECEIPT["source_mode"], "GIT_BLOBS_NOT_CORE_RELEASE")


if __name__ == "__main__":
    unittest.main()
