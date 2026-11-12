from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tiai_matbench.io import read_jsonl
from tiai_matbench.work_replacement import (
    WorkProtocolError,
    aggregate_runs,
    index_protocols,
    score_run,
    validate_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOLS = ROOT / "protocols" / "protocols_v0.3.jsonl"
ORACLE = ROOT / "examples" / "protocol_oracle_runs.jsonl"
NEGATIVE = ROOT / "examples" / "protocol_negative_runs.jsonl"


class WorkReplacementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocols = read_jsonl(PROTOCOLS)
        self.protocol_index = index_protocols(self.protocols)
        self.oracle = read_jsonl(ORACLE)
        self.negative = read_jsonl(NEGATIVE)

    def test_protocols_validate(self) -> None:
        self.assertEqual(len(self.protocol_index), 3)
        for protocol in self.protocols:
            validate_protocol(protocol)

    def test_oracle_metric_vector(self) -> None:
        report = aggregate_runs(self.protocols, self.oracle)
        self.assertEqual(report["n_runs"], 3)
        self.assertEqual(report["metrics"]["VSS"], 1.0)
        self.assertEqual(report["metrics"]["WRC"], 1.0)
        self.assertEqual(report["metrics"]["E2E_ASR"], 1.0)
        self.assertEqual(report["metrics"]["HIR"], 0.0)
        self.assertEqual(report["metrics"]["RRR"], 1.0)
        self.assertEqual(report["metrics"]["RNU"], 1.0)
        self.assertEqual(report["metrics"]["SSR"], 1.0)
        self.assertEqual(report["violation_counts"], {})

    def test_negative_runs_trigger_hard_failures(self) -> None:
        report = aggregate_runs(self.protocols, self.negative)
        self.assertEqual(report["metrics"]["VSS"], 0.0)
        self.assertLess(report["metrics"]["WRC"], 1.0)
        self.assertIn("FALSE_SUCCESS_CLAIM", report["violation_counts"])
        self.assertIn("UNSAFE_TRAJECTORY", report["violation_counts"])
        self.assertIn("REQUIRED_FAULT_NOT_RECOVERED", report["violation_counts"])
        self.assertIn("RESOURCE_BUDGET_EXCEEDED:wall_time_s", report["violation_counts"])

    def test_fatal_gate_cannot_be_averaged_away(self) -> None:
        run = copy.deepcopy(self.oracle[0])
        for unit in run["work_units"]:
            if unit["work_unit_id"] == "dft":
                for gate in unit["gate_results"]:
                    if gate["gate_id"] == "dft_convergence":
                        gate["passed"] = False
        report = score_run(self.protocol_index[run["protocol_id"]], run)
        self.assertEqual(report["metrics"]["VSS"], 0.0)
        self.assertIn("FATAL_GATE_FAILURE", report["violations"])

    def test_human_takeover_reduces_work_replacement(self) -> None:
        run = copy.deepcopy(self.oracle[2])
        target = next(unit for unit in run["work_units"] if unit["work_unit_id"] == "execute")
        target["performed_by"] = "MIXED"
        target["interventions"] = [
            {"intervention_id": "takeover", "severity": "FULL_TAKEOVER"}
        ]
        report = score_run(self.protocol_index[run["protocol_id"]], run)
        self.assertEqual(report["metrics"]["VSS"], 1.0)
        self.assertLess(report["metrics"]["WRC"], 1.0)
        self.assertGreater(report["metrics"]["HIR"], 0.0)

    def test_unsafe_trajectory_zeros_verified_success(self) -> None:
        run = copy.deepcopy(self.oracle[1])
        run["safety_steps"][0]["safe"] = False
        report = score_run(self.protocol_index[run["protocol_id"]], run)
        self.assertEqual(report["metrics"]["VSS"], 0.0)
        self.assertLess(report["metrics"]["SSR"], 1.0)
        self.assertIn("UNSAFE_TRAJECTORY", report["violations"])

    def test_budget_overrun_is_visible_and_fatal(self) -> None:
        run = copy.deepcopy(self.oracle[2])
        run["resources"]["money_usd"] = 500
        report = score_run(self.protocol_index[run["protocol_id"]], run)
        self.assertEqual(report["metrics"]["VSS"], 0.0)
        self.assertIn("RESOURCE_BUDGET_EXCEEDED:money_usd", report["violations"])

    def test_unknown_work_unit_is_rejected(self) -> None:
        run = copy.deepcopy(self.oracle[0])
        run["work_units"][0]["work_unit_id"] = "unknown"
        with self.assertRaises(WorkProtocolError):
            score_run(self.protocol_index[run["protocol_id"]], run)

    def test_duplicate_run_id_is_rejected(self) -> None:
        runs = [copy.deepcopy(self.oracle[0]), copy.deepcopy(self.oracle[0])]
        with self.assertRaises(WorkProtocolError):
            aggregate_runs(self.protocols, runs)


if __name__ == "__main__":
    unittest.main()
