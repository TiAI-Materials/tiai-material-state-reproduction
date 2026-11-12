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


if __name__ == "__main__":
    unittest.main()
