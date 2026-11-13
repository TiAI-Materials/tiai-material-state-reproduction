import json
from pathlib import Path
import tempfile
import unittest

from tiai_matbench.federation_cli import main

ROOT = Path(__file__).resolve().parents[1]

class FederationCliTests(unittest.TestCase):
    def test_validate_registry_threshold(self):
        registry = ROOT / "FEDERATED_BENCHMARK_REGISTRY.json"
        self.assertEqual(main(["validate", "--registry", str(registry), "--require-executable-anchors", "4"]), 0)
        self.assertEqual(main(["validate", "--registry", str(registry), "--require-executable-anchors", "5"]), 1)

    def test_normalize_compmat_writes_report_and_applies_threshold(self):
        registry = ROOT / "FEDERATED_BENCHMARK_REGISTRY.json"
        payload = ROOT / "examples/federation_compmat_manifest_v1.json"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            self.assertEqual(main(["normalize", "--registry", str(registry), "--benchmark-id", "compmat_bench", "--input", str(payload), "--output", str(output), "--min-native-success", "0.5"]), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["benchmark_id"], "compmat_bench")
            self.assertEqual(report["task_count"], 8)
            self.assertEqual(main(["normalize", "--registry", str(registry), "--benchmark-id", "compmat_bench", "--input", str(payload), "--min-native-success", "0.6"]), 1)

if __name__ == "__main__":
    unittest.main()
