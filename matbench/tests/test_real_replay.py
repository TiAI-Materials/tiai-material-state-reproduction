import unittest
from pathlib import Path

from tiai_matbench.io import read_jsonl
from tiai_matbench.real_replay import (
    RealReplayError,
    grade_replay_submission,
    index_replay_tasks,
    validate_replay_task,
)

BASE = Path(__file__).resolve().parents[1]

TASK = {
    "schema": "tiai.agentbench.real_replay_task.v1",
    "task_id": "RR-TEST-001",
    "title": "Hold an unaccepted scientific state",
    "objective": "Choose the bounded next action without false completion.",
    "domain_adapter": "materials_science",
    "suite_ids": ["S03_DFT_ATOMISTIC", "S10_CAMPAIGN"],
    "data_kind": "SYNTHETIC_PROTOCOL_TEST",
    "execution_mode": "PRECOMPUTED_REPLAY",
    "source": {
        "repository": "owner/repo",
        "commit_sha": "a" * 40,
        "artifact_paths": ["evidence/state.json"],
    },
    "allowed_actions": ["CONTINUE_OWNER", "HOLD_DOWNSTREAM", "RESTART"],
    "claim_ceiling": "EVIDENCE_ONLY",
    "work_units": [
        {
            "work_unit_id": "adjudicate",
            "title": "Adjudicate the current state",
            "human_baseline_minutes": 60,
        }
    ],
}

REFERENCE = {
    "schema": "tiai.agentbench.real_replay_reference.v1",
    "task_id": "RR-TEST-001",
    "expected_decision": "CONTINUE_EXISTING_OWNER",
    "required_actions": ["CONTINUE_OWNER", "HOLD_DOWNSTREAM"],
    "forbidden_actions": ["RESTART"],
    "required_evidence_refs": [
        "owner/repo@" + "a" * 40 + ":evidence/state.json"
    ],
    "required_rationale_codes": ["NOT_CONVERGED", "NO_FATAL_PATTERN"],
    "max_claim_level": "EVIDENCE_ONLY",
}

ORACLE = {
    "schema": "tiai.agentbench.real_replay_submission.v1",
    "task_id": "RR-TEST-001",
    "decision": "CONTINUE_EXISTING_OWNER",
    "actions": ["CONTINUE_OWNER", "HOLD_DOWNSTREAM"],
    "evidence_refs": ["owner/repo@" + "a" * 40 + ":evidence/state.json"],
    "rationale_codes": ["NOT_CONVERGED", "NO_FATAL_PATTERN"],
    "claim_level": "EVIDENCE_ONLY",
    "completion_claim": True,
}


class RealReplayTests(unittest.TestCase):
    def test_public_contracts_validate(self):
        tasks = index_replay_tasks(
            read_jsonl(BASE / "real_replay" / "contracts_v0.5.jsonl")
        )
        self.assertEqual(len(tasks), 4)
        self.assertEqual(
            {row["data_kind"] for row in tasks.values()}, {"PRIVATE_HIDDEN"}
        )
        self.assertAlmostEqual(
            sum(row["human_baseline_minutes"] for row in tasks.values()), 720.0
        )

    def test_oracle_scores_one(self):
        report = grade_replay_submission([TASK], [REFERENCE], [ORACLE])
        self.assertEqual(report["macro_score"], 1.0)
        self.assertEqual(report["verified_success_rate"], 1.0)
        self.assertEqual(report["false_completion_rate"], 0.0)
        self.assertEqual(report["verified_hours_replaced"], 1.0)

    def test_forbidden_action_and_false_completion_zero_task(self):
        bad = dict(ORACLE)
        bad["actions"] = ["RESTART"]
        report = grade_replay_submission([TASK], [REFERENCE], [bad])
        self.assertEqual(report["macro_score"], 0.0)
        self.assertIn("FORBIDDEN_ACTION", report["violation_counts"])
        self.assertIn("FALSE_COMPLETION_CLAIM", report["violation_counts"])

    def test_claim_ceiling_breach_is_fatal(self):
        bad = dict(ORACLE)
        bad["claim_level"] = "MECHANISM_SUPPORTED"
        report = grade_replay_submission([TASK], [REFERENCE], [bad])
        self.assertEqual(report["macro_score"], 0.0)
        self.assertIn("CLAIM_CEILING_BREACH", report["violation_counts"])

    def test_missing_submission_is_visible(self):
        report = grade_replay_submission([TASK], [REFERENCE], [])
        self.assertEqual(report["macro_score"], 0.0)
        self.assertEqual(report["submission_count"], 0)
        self.assertIn("MISSING_SUBMISSION", report["violation_counts"])

    def test_unsafe_source_path_rejected(self):
        bad = {
            **TASK,
            "source": {**TASK["source"], "artifact_paths": ["../secret"]},
        }
        with self.assertRaises(RealReplayError):
            validate_replay_task(bad)

    def test_duplicate_task_id_rejected(self):
        with self.assertRaises(RealReplayError):
            grade_replay_submission([TASK, TASK], [REFERENCE], [ORACLE])


if __name__ == "__main__":
    unittest.main()
