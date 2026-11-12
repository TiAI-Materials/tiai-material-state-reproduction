from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tiai_matbench.grader import git_blob_sha_bytes, grade_submission, verify_assets
from tiai_matbench.io import BenchmarkFormatError, read_json, read_jsonl, strict_loads


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks" / "dev.jsonl"
REFERENCES = ROOT / "references" / "dev.jsonl"
MANIFEST = ROOT / "MANIFEST.json"
ORACLE = ROOT / "examples" / "oracle_submission.jsonl"
NAIVE = ROOT / "examples" / "naive_submission.jsonl"


class StrictJsonTests(unittest.TestCase):
    def test_duplicate_keys_are_rejected(self) -> None:
        with self.assertRaises(BenchmarkFormatError):
            strict_loads('{"a":1,"a":2}')

    def test_nonfinite_numbers_are_rejected(self) -> None:
        with self.assertRaises(BenchmarkFormatError):
            strict_loads('{"a":NaN}')


class GraderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = read_jsonl(TASKS)
        cls.references = read_jsonl(REFERENCES)
        cls.manifest = read_json(MANIFEST)
        cls.weights = cls.manifest["dimension_weights"]
        cls.oracle = read_jsonl(ORACLE)

    def test_oracle_scores_one(self) -> None:
        report = grade_submission(
            self.tasks, self.references, self.oracle, self.weights
        )
        self.assertEqual(report["macro_score"], 1.0)
        self.assertEqual(report["real_released_macro_score"], 1.0)
        self.assertEqual(report["synthetic_scorer_macro_score"], 1.0)
        self.assertEqual(report["violation_counts"], {})

    def test_synthetic_fixture_does_not_change_primary_score(self) -> None:
        responses = [
            response
            for response in self.oracle
            if response["task_id"] != "TMB-EXECUTION-001"
        ]
        report = grade_submission(
            self.tasks, self.references, responses, self.weights
        )
        self.assertEqual(report["macro_score"], 1.0)
        self.assertEqual(report["synthetic_scorer_macro_score"], 0.0)
        self.assertLess(report["all_task_macro_score"], 1.0)

    def test_naive_pooled_only_baseline_is_penalized(self) -> None:
        report = grade_submission(
            self.tasks, self.references, read_jsonl(NAIVE), self.weights
        )
        self.assertLess(report["macro_score"], 0.2)
        self.assertIn("UNSUPPORTED_CAUSAL_CLAIM", report["violation_counts"])
        self.assertIn("MISSING_RESPONSE", report["violation_counts"])

    def test_unregistered_evidence_zeros_task(self) -> None:
        responses = copy.deepcopy(self.oracle)
        responses[0]["evidence"].append(
            {
                "asset": "invented/results.json",
                "git_blob_sha": "0" * 40,
                "locator": "/made/up",
            }
        )
        report = grade_submission(
            self.tasks, self.references, responses, self.weights
        )
        task_report = report["task_reports"][0]
        self.assertEqual(task_report["score"], 0.0)
        self.assertTrue(
            any(
                item["violation"] == "UNREGISTERED_EVIDENCE_ASSET"
                for item in task_report["violations"]
            )
        )

    def test_source_leakage_permission_zeros_split_task(self) -> None:
        responses = copy.deepcopy(self.oracle)
        split_response = next(
            item for item in responses if item["task_id"] == "TMB-SPLIT-INTEGRITY-001"
        )
        split_response["answer"]["source_cross_fold_allowed"] = True
        report = grade_submission(
            self.tasks, self.references, responses, self.weights
        )
        split_report = next(
            item
            for item in report["task_reports"]
            if item["task_id"] == "TMB-SPLIT-INTEGRITY-001"
        )
        self.assertEqual(split_report["score"], 0.0)
        self.assertTrue(
            any(
                item["violation"] == "SOURCE_LEAKAGE_ALLOWED"
                for item in split_report["violations"]
            )
        )

    def test_temperature_mixing_zeros_state_task(self) -> None:
        responses = copy.deepcopy(self.oracle)
        state_response = next(
            item for item in responses if item["task_id"] == "TMB-STATE-BOUNDARY-001"
        )
        state_response["answer"]["pooled_across_temperature_regimes"] = True
        report = grade_submission(
            self.tasks, self.references, responses, self.weights
        )
        state_report = next(
            item
            for item in report["task_reports"]
            if item["task_id"] == "TMB-STATE-BOUNDARY-001"
        )
        self.assertEqual(state_report["score"], 0.0)
        self.assertTrue(
            any(
                item["violation"] == "STATE_CONDITION_MIXING"
                for item in state_report["violations"]
            )
        )

    def test_git_blob_identity_verification(self) -> None:
        content = b"frozen evidence\n"
        sha = git_blob_sha_bytes(content)
        task = copy.deepcopy(self.tasks[0])
        task["inputs"] = [
            {
                "asset": "fixture.txt",
                "git_blob_sha": sha,
                "allowed_locators": ["line:1"],
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture.txt").write_bytes(content)
            report = verify_assets([task], root)
        self.assertTrue(report["all_match"])
        self.assertEqual(report["assets"][0]["status"], "MATCH")


if __name__ == "__main__":
    unittest.main()
