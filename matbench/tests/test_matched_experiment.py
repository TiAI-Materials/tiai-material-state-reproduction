import copy
import json
from pathlib import Path
import unittest

from tiai_matbench.matched_experiment import (
    MatchedExperimentError,
    validate_matched_protocol,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "experiments" / "matched_goal_driven_protocol_v0.8.json"


class MatchedExperimentTests(unittest.TestCase):
    def load_protocol(self):
        return json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_frozen_protocol_validates(self):
        report = validate_matched_protocol(self.load_protocol())
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["condition_count"], 6)
        self.assertEqual(report["pilot_stratum_count"], 3)
        self.assertEqual(report["pilot_task_count"], 12)
        self.assertEqual(report["pilot_run_count"], 192)
        self.assertEqual(report["confirmatory_adapter_count"], 5)

    def test_planned_run_count_is_derived_not_declared(self):
        protocol = self.load_protocol()
        protocol["phase_1_materials_pilot"]["planned_run_count"] = 191
        with self.assertRaises(MatchedExperimentError):
            validate_matched_protocol(protocol)

    def test_condition_ablation_cannot_be_silently_removed(self):
        protocol = self.load_protocol()
        protocol["system_conditions"].pop()
        with self.assertRaises(MatchedExperimentError):
            validate_matched_protocol(protocol)

    def test_native_verifier_receipt_is_mandatory(self):
        protocol = self.load_protocol()
        protocol["required_run_ledger"].remove("native_verifier_receipt")
        with self.assertRaises(MatchedExperimentError):
            validate_matched_protocol(protocol)

    def test_mother_machine_heavy_compute_stays_disabled(self):
        protocol = self.load_protocol()
        protocol["resource_policy"]["mother_machine_heavy_compute"] = True
        with self.assertRaises(MatchedExperimentError):
            validate_matched_protocol(protocol)

    def test_task_duplication_within_stratum_is_rejected(self):
        protocol = copy.deepcopy(self.load_protocol())
        tasks = protocol["phase_1_materials_pilot"]["strata"][0]["task_ids"]
        tasks.append(tasks[0])
        with self.assertRaises(MatchedExperimentError):
            validate_matched_protocol(protocol)


if __name__ == "__main__":
    unittest.main()
