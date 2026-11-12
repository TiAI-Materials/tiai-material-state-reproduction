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


if __name__ == "__main__":
    unittest.main()
