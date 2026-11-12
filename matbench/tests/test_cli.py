from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tiai_matbench.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def common(self) -> list[str]:
        return [
            "--tasks", str(ROOT / "tasks" / "dev.jsonl"),
            "--references", str(ROOT / "references" / "dev.jsonl"),
            "--manifest", str(ROOT / "MANIFEST.json"),
        ]

    def test_validate(self) -> None:
        with redirect_stdout(StringIO()):
            code = main(["validate", *self.common()])
        self.assertEqual(code, 0)

    def test_grade_oracle_and_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with redirect_stdout(StringIO()):
                code = main(
                    [
                        "grade", *self.common(),
                        "--submission", str(ROOT / "examples" / "oracle_submission.jsonl"),
                        "--output", str(output),
                        "--min-score", "1.0",
                    ]
                )
            self.assertEqual(code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["macro_score"], 1.0)

    def test_validate_full_stack_registry(self) -> None:
        with redirect_stdout(StringIO()):
            code = main([
                "validate-registry",
                "--registry", str(ROOT / "SUITE_REGISTRY.json"),
                "--roadmap", str(ROOT / "suites" / "roadmap_v0.2.jsonl"),
            ])
        self.assertEqual(code, 0)

    def test_list_suites_json(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "list-suites",
                "--registry", str(ROOT / "SUITE_REGISTRY.json"),
                "--json",
            ])
        self.assertEqual(code, 0)
        rows = json.loads(output.getvalue())
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["suite_id"], "S00_EVIDENCE")

    def test_validate_cross_industry_adapters(self) -> None:
        with redirect_stdout(StringIO()):
            code = main([
                "validate-adapters",
                "--adapters", str(ROOT / "DOMAIN_ADAPTER_REGISTRY.json"),
            ])
        self.assertEqual(code, 0)

    def test_validate_work_protocols(self) -> None:
        with redirect_stdout(StringIO()):
            code = main([
                "validate-protocols",
                "--protocols", str(ROOT / "protocols" / "protocols_v0.3.jsonl"),
                "--adapters", str(ROOT / "DOMAIN_ADAPTER_REGISTRY.json"),
                "--suites", str(ROOT / "SUITE_REGISTRY.json"),
            ])
        self.assertEqual(code, 0)

    def test_score_work_run_oracles(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "score-work-runs",
                "--protocols", str(ROOT / "protocols" / "protocols_v0.3.jsonl"),
                "--runs", str(ROOT / "examples" / "protocol_oracle_runs.jsonl"),
                "--require-vss", "1.0",
                "--require-wrc", "1.0",
            ])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["metrics"]["VSS"], 1.0)
        self.assertEqual(report["metrics"]["WRC"], 1.0)

    def test_validate_goal_driven_registry(self) -> None:
        with redirect_stdout(StringIO()):
            code = main([
                "validate-goal-registry",
                "--registry", str(ROOT / "GOAL_DRIVEN_REGISTRY.json"),
            ])
        self.assertEqual(code, 0)

    def test_validate_goal_protocols(self) -> None:
        with redirect_stdout(StringIO()):
            code = main([
                "validate-goal-protocols",
                "--protocols", str(ROOT / "goal_driven" / "protocols_v0.4.jsonl"),
                "--registry", str(ROOT / "GOAL_DRIVEN_REGISTRY.json"),
                "--adapters", str(ROOT / "DOMAIN_ADAPTER_REGISTRY.json"),
            ])
        self.assertEqual(code, 0)

    def test_score_goal_oracles(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "score-goal-runs",
                "--protocols", str(ROOT / "goal_driven" / "protocols_v0.4.jsonl"),
                "--runs", str(ROOT / "examples" / "goal_oracle_runs.jsonl"),
                "--require-gds", "1.0",
                "--require-vwr", "1.0",
                "--max-fcr", "0.0",
            ])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["metrics"]["GDS"], 1.0)


    def test_score_human_loop_fixture(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "score-goal-runs",
                "--protocols", str(ROOT / "goal_driven" / "protocols_v0.4.jsonl"),
                "--runs", str(ROOT / "examples" / "goal_human_loop_runs.jsonl"),
                "--require-gds", "1.0",
                "--max-fcr", "0.0",
            ])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertGreater(report["metrics"]["HLF"], 0.0)
        self.assertLess(report["metrics"]["VWR"], 1.0)

    def test_verify_reconstruction_cli(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = main([
                "verify-reconstruction",
                "--task-dir", str(ROOT / "reconstruction" / "fea1d"),
                "--submission", str(ROOT / "reconstruction" / "fea1d" / "oracle_solver.py"),
                "--require-signoff",
                "--min-pass-rate", "1.0",
            ])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report["functional_signoff"])


if __name__ == "__main__":
    unittest.main()
