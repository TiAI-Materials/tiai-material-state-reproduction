from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tiai_matbench.adapters import AdapterValidationError, validate_adapter_registry
from tiai_matbench.io import read_json


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "DOMAIN_ADAPTER_REGISTRY.json"


class AdapterRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = read_json(ADAPTERS)

    def test_registry_validates(self) -> None:
        result = validate_adapter_registry(self.registry)
        self.assertEqual(result["adapter_count"], 8)
        self.assertIn("materials_science", result["adapters"])
        self.assertIn("scientific_robotics", result["adapters"])
        self.assertIn("software_engineering", result["adapters"])

    def test_unknown_work_class_is_rejected(self) -> None:
        broken = copy.deepcopy(self.registry)
        broken["adapters"][0]["work_classes"].append("UNKNOWN_CLASS")
        with self.assertRaises(AdapterValidationError):
            validate_adapter_registry(broken)

    def test_duplicate_adapter_is_rejected(self) -> None:
        broken = copy.deepcopy(self.registry)
        broken["adapters"].append(copy.deepcopy(broken["adapters"][0]))
        with self.assertRaises(AdapterValidationError):
            validate_adapter_registry(broken)


if __name__ == "__main__":
    unittest.main()
