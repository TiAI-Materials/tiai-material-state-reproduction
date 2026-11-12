import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FederationCoverageGateTests(unittest.TestCase):
    def test_executable_industries_have_executable_result_adapters(self):
        registry = json.loads(
            (ROOT / "FEDERATED_BENCHMARK_REGISTRY.json").read_text(encoding="utf-8")
        )
        anchors = {row["benchmark_id"]: row for row in registry["anchors"]}

        for coverage in registry["industry_coverage"]:
            if coverage["status"] != "EXECUTABLE":
                continue
            self.assertTrue(
                any(
                    anchors[benchmark_id]["adapter_status"] == "EXECUTABLE"
                    for benchmark_id in coverage["benchmark_ids"]
                ),
                msg=(
                    f"industry {coverage['industry_family']} is marked EXECUTABLE "
                    "without an executable result adapter"
                ),
            )


if __name__ == "__main__":
    unittest.main()
