from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tiai_matbench.goal_driven import (
    GoalDrivenError,
    aggregate_goal_runs,
    index_goal_protocols,
    score_goal_run,
    validate_goal_registry,
)
from tiai_matbench.io import read_json, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "GOAL_DRIVEN_REGISTRY.json"
PROTOCOLS = ROOT / "goal_driven" / "protocols_v0.4.jsonl"
ORACLE = ROOT / "examples" / "goal_oracle_runs.jsonl"
NEGATIVE = ROOT / "examples" / "goal_negative_runs.jsonl"
HUMAN_LOOP = ROOT / "examples" / "goal_human_loop_runs.jsonl"


class GoalDrivenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = read_json(REGISTRY)
        self.protocols = read_jsonl(PROTOCOLS)
        self.protocol_index = index_goal_protocols(self.protocols)
        self.oracle = read_jsonl(ORACLE)
        self.negative = read_jsonl(NEGATIVE)
        self.human_loop = read_jsonl(HUMAN_LOOP)

    def test_goal_registry_covers_industries_and_verifiability(self) -> None:
        result = validate_goal_registry(self.registry)
        self.assertGreaterEqual(result["industry_count"], 16)
        self.assertIn("materials_science", result["industries"])
        self.assertIn("eda_semiconductor", result["industries"])
        self.assertIn("scientific_robotics", result["industries"])
        self.assertEqual(len(result["verifiability_levels"]), 5)

    def test_goal_protocols_validate(self) -> None:
        self.assertEqual(len(self.protocol_index), 4)
        self.assertIn("GD-MAT-FULLSTACK-001", self.protocol_index)
        self.assertIn("GD-CAE-REBUILD-001", self.protocol_index)
        self.assertIn("GD-ROBOT-DT-001", self.protocol_index)
        self.assertIn("GD-HEALTH-HIL-001", self.protocol_index)

    def test_oracle_closes_goal_and_replaces_verified_work(self) -> None:
        report = aggregate_goal_runs(self.protocols, self.oracle)
        self.assertEqual(report["metrics"]["GDS"], 1.0)
        self.assertEqual(report["metrics"]["GA"], 1.0)
        self.assertEqual(report["metrics"]["CCR"], 1.0)
        self.assertEqual(report["metrics"]["VWR"], 1.0)
        self.assertEqual(report["metrics"]["HLF"], 0.0)
        self.assertEqual(report["metrics"]["PI"], 1.0)
        self.assertEqual(report["metrics"]["FCR"], 0.0)
        self.assertEqual(report["metrics"]["FSR"], 1.0)
        self.assertEqual(report["violation_counts"], {})


    def test_human_loop_success_is_not_mislabeled_as_full_replacement(self) -> None:
        report = aggregate_goal_runs(self.protocols, self.human_loop)
        self.assertEqual(report["metrics"]["GDS"], 1.0)
        self.assertGreater(report["metrics"]["HLF"], 0.0)
        self.assertGreater(report["metrics"]["VWR"], 0.0)
        self.assertLess(report["metrics"]["VWR"], 1.0)
        self.assertEqual(report["metrics"]["FCR"], 0.0)
        self.assertEqual(report["violation_counts"], {})

    def test_negative_control_detects_premature_completion(self) -> None:
        report = aggregate_goal_runs(self.protocols, self.negative)
        self.assertEqual(report["metrics"]["GDS"], 0.0)
        self.assertEqual(report["metrics"]["GA"], 0.0)
        self.assertEqual(report["metrics"]["FCR"], 1.0)
        self.assertIn("PREMATURE_COMPLETION_CLAIM", report["violation_counts"])
        self.assertTrue(
            any(key.startswith("REQUIRED_FAULT_NOT_RECOVERED") for key in report["violation_counts"])
        )
        self.assertTrue(
            any(key.startswith("RESOURCE_BUDGET_EXCEEDED") for key in report["violation_counts"])
        )

    def test_self_verification_does_not_close_required_criterion(self) -> None:
        run = copy.deepcopy(self.oracle[0])
        run["criterion_results"][0]["independent"] = False
        report = score_goal_run(self.protocol_index[run["goal_id"]], run)
        self.assertEqual(report["metrics"]["GDS"], 0.0)
        self.assertIn(
            "NONINDEPENDENT_VERIFIER:goal_contract", report["violations"]
        )

    def test_idle_episode_requires_restart(self) -> None:
        run = copy.deepcopy(self.oracle[2])
        run["episodes"] = [run["episodes"][0]]
        for fault in run["fault_results"]:
            fault["recovered"] = False
            fault["recovery_episode_id"] = None
        run["completion_claimed"] = False
        run["terminal_status"] = "FAILED"
        report = score_goal_run(self.protocol_index[run["goal_id"]], run)
        self.assertEqual(report["metrics"]["CRR"], 0.0)
        self.assertTrue(
            any(key.startswith("UNRECOVERED_AGENT_EPISODE") for key in report["violations"])
        )

    def test_work_unit_cycle_is_rejected(self) -> None:
        protocol = copy.deepcopy(self.protocols[0])
        protocol["work_units"][0]["depends_on"] = [protocol["work_units"][-1]["work_unit_id"]]
        with self.assertRaises(GoalDrivenError):
            index_goal_protocols([protocol])

    def test_duplicate_run_id_is_rejected(self) -> None:
        runs = [copy.deepcopy(self.oracle[0]), copy.deepcopy(self.oracle[0])]
        with self.assertRaises(GoalDrivenError):
            aggregate_goal_runs(self.protocols, runs)


if __name__ == "__main__":
    unittest.main()
