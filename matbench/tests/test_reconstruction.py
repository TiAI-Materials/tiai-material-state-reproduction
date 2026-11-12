from __future__ import annotations

import unittest
from pathlib import Path

from tiai_matbench.reconstruction import verify_reconstruction


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "reconstruction" / "fea1d"


class ReconstructionTests(unittest.TestCase):
    def test_reference_solver_receives_functional_signoff(self) -> None:
        report = verify_reconstruction(TASK, TASK / "oracle_solver.py")
        self.assertEqual(report["case_count"], 12)
        self.assertEqual(report["pass_rate"], 1.0)
        self.assertTrue(report["functional_signoff"])
        self.assertEqual(report["fatal_failed_cases"], [])

    def test_naive_solver_is_rejected(self) -> None:
        report = verify_reconstruction(TASK, TASK / "naive_solver.py")
        self.assertLess(report["pass_rate"], 1.0)
        self.assertFalse(report["functional_signoff"])
        self.assertGreater(len(report["fatal_failed_cases"]), 0)


if __name__ == "__main__":
    unittest.main()
