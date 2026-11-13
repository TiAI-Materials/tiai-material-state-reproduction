import copy
import json
from pathlib import Path
import unittest

from tiai_matbench.federation import FederationError, normalize_external_run, validate_federation_registry

ROOT = Path(__file__).resolve().parents[1]

def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

class FederationTests(unittest.TestCase):
    def setUp(self):
        self.registry = load("FEDERATED_BENCHMARK_REGISTRY.json")

    def test_registry_covers_all_twenty_industry_families(self):
        report = validate_federation_registry(self.registry)
        self.assertEqual(report["anchor_count"], 12)
        self.assertEqual(report["executable_anchor_count"], 4)
        self.assertEqual(report["industry_count"], 20)
        self.assertEqual(report["industry_coverage"]["materials_science"]["status"], "EXECUTABLE")

    def test_swe_bench_native_denominator_is_preserved(self):
        report = normalize_external_run(self.registry, "swe_bench", load("examples/federation_swebench_results_v2.json"))
        self.assertEqual(report["metrics"]["native_verified_success"], 0.25)
        self.assertEqual(report["metrics"]["execution_coverage"], 0.75)
        self.assertEqual(report["metrics"]["infrastructure_reliability"], 0.75)
        self.assertIsNone(report["metrics"]["trajectory_safety"])

    def test_osworld_unscored_error_stays_in_denominator(self):
        report = normalize_external_run(self.registry, "osworld", load("examples/federation_osworld_results_v1.json"))
        self.assertEqual(report["metrics"]["native_verified_success"], 0.5)
        self.assertEqual(report["metrics"]["execution_coverage"], 0.5)
        self.assertEqual(report["metrics"]["infrastructure_reliability"], 0.5)

    def test_calvin_reports_long_horizon_depth_without_inventing_safety(self):
        report = normalize_external_run(self.registry, "calvin", load("examples/federation_calvin_results_v1.json"))
        self.assertEqual(report["native_summary"]["selected_epoch"], "2")
        self.assertAlmostEqual(report["metrics"]["long_horizon_depth"], 0.6)
        self.assertAlmostEqual(report["metrics"]["native_verified_success"], 0.8)
        self.assertAlmostEqual(report["metrics"]["five_instruction_chain_success"], 0.5)
        self.assertIsNone(report["metrics"]["trajectory_safety"])

    def test_compmat_manifest_preserves_campaign_and_workflow_denominators(self):
        report = normalize_external_run(self.registry, "compmat_bench", load("examples/federation_compmat_manifest_v1.json"))
        self.assertEqual(report["task_count"], 8)
        self.assertEqual(report["metrics"]["native_verified_success"], 0.5)
        self.assertEqual(report["metrics"]["execution_coverage"], 1.0)
        self.assertAlmostEqual(report["metrics"]["workflow_native_success"], 1.0 / 3.0)
        self.assertAlmostEqual(report["metrics"]["reported_infrastructure_rerun_fraction"], 1.0 / 8.0)
        self.assertIsNone(report["metrics"]["infrastructure_reliability"])
        self.assertIn("INFRASTRUCTURE_FAILURE_DENOMINATOR_NOT_REPORTED", report["evidence_gaps"])

    def test_compmat_public_snapshot_matches_upstream_aggregate_counts(self):
        snapshot = load("COMPMAT_PUBLIC_RESULT_SNAPSHOT.json")
        self.assertEqual(snapshot["reported_rows"], 976)
        self.assertEqual(snapshot["reported_passes"], 771)
        self.assertAlmostEqual(snapshot["native_verified_success"], 771.0 / 976.0)
        self.assertEqual(sum(row["rows"] for row in snapshot["campaigns"].values()), snapshot["reported_rows"])
        self.assertEqual(sum(row["passes"] for row in snapshot["campaigns"].values()), snapshot["reported_passes"])
        self.assertEqual(snapshot["upstream"]["manifest_blob_sha"], "de6f82bc77a35b1a01d1d03a608c58e502e36516")

    def test_swe_bench_count_mismatch_is_rejected(self):
        payload = load("examples/federation_swebench_results_v2.json")
        payload["resolved_ids"] = []
        with self.assertRaises(FederationError):
            normalize_external_run(self.registry, "swe_bench", payload)

    def test_compmat_summary_row_mismatch_is_rejected(self):
        payload = load("examples/federation_compmat_manifest_v1.json")
        payload["summary"]["passes"]["workflow"]["model_alpha"] = 2
        with self.assertRaises(FederationError):
            normalize_external_run(self.registry, "compmat_bench", payload)

    def test_compmat_duplicate_record_path_is_rejected(self):
        payload = load("examples/federation_compmat_manifest_v1.json")
        payload["rows"][1]["record_path"] = payload["rows"][0]["record_path"]
        with self.assertRaises(FederationError):
            normalize_external_run(self.registry, "compmat_bench", payload)

    def test_catalog_only_anchor_cannot_be_normalized(self):
        with self.assertRaises(FederationError):
            normalize_external_run(self.registry, "openroad_flow", {})

    def test_unknown_adapter_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["anchors"][1]["result_adapter"] = "MADE_UP"
        with self.assertRaises(FederationError):
            validate_federation_registry(registry)

    def test_executable_coverage_without_executable_anchor_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["industry_coverage"][0]["benchmark_ids"] = ["science_agent_bench"]
        with self.assertRaises(FederationError):
            validate_federation_registry(registry)

    def test_missing_industry_row_is_rejected(self):
        registry = copy.deepcopy(self.registry)
        registry["industry_coverage"].pop()
        with self.assertRaises(FederationError):
            validate_federation_registry(registry)

if __name__ == "__main__":
    unittest.main()
