from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tiai_matbench.io import read_json, read_jsonl
from tiai_matbench.suites import (
    SuiteValidationError,
    suite_rows,
    validate_suite_registry,
    validate_task_roadmap,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "SUITE_REGISTRY.json"
ROADMAP = ROOT / "suites" / "roadmap_v0.2.jsonl"


class SuiteRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = read_json(REGISTRY)
        self.roadmap = read_jsonl(ROADMAP)

    def test_registry_and_roadmap_validate(self) -> None:
        report = validate_task_roadmap(self.roadmap, self.registry)
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["suite_count"], 12)
        self.assertEqual(report["task_spec_count"], 39)
        self.assertEqual(set(report["tasks_by_suite"]), {
            suite["id"] for suite in self.registry["suites"]
        })

    def test_duplicate_suite_rejected(self) -> None:
        broken = copy.deepcopy(self.registry)
        broken["suites"].append(copy.deepcopy(broken["suites"][0]))
        with self.assertRaises(SuiteValidationError):
            validate_suite_registry(broken)

    def test_unknown_suite_in_roadmap_rejected(self) -> None:
        broken = copy.deepcopy(self.roadmap)
        broken[0]["suite"] = "S99_UNKNOWN"
        with self.assertRaises(SuiteValidationError):
            validate_task_roadmap(broken, self.registry)

    def test_execution_mode_must_be_declared_by_suite(self) -> None:
        broken = copy.deepcopy(self.roadmap)
        broken[0]["mode"] = "PHYSICAL_LAB"
        with self.assertRaises(SuiteValidationError):
            validate_task_roadmap(broken, self.registry)

    def test_compact_suite_rows_are_stable(self) -> None:
        rows = suite_rows(self.registry)
        self.assertEqual(rows[0]["suite_id"], "S00_EVIDENCE")
        self.assertEqual(rows[-1]["suite_id"], "S11_COMMUNICATION")
        self.assertEqual(rows[0]["current_pack"], "tasks/dev.jsonl")


if __name__ == "__main__":
    unittest.main()
