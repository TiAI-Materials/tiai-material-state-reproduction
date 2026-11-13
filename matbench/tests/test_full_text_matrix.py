"""Regression tests for the v0.10 full-text evidence audit."""
from __future__ import annotations

import base64
import copy
import gzip
import json
import unittest
from pathlib import Path

from tiai_matbench.full_text_matrix import FullTextMatrixError, validate_matrix

MATRIX_PATH = (
    Path(__file__).resolve().parents[1]
    / "literature"
    / "FULL_TEXT_EVIDENCE_MATRIX_V0.10.json.gz.b64"
)
MATRIX = json.loads(
    gzip.decompress(base64.b64decode(MATRIX_PATH.read_bytes().strip(), validate=True)).decode("utf-8")
)


class FullTextEvidenceMatrixTests(unittest.TestCase):
    def test_release_matrix_passes(self):
        report = validate_matrix(MATRIX)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["counted_full_texts"], 51)
        self.assertEqual(report["unique_titles"], 51)
        self.assertGreaterEqual(report["vertical_count"], 10)
        self.assertGreaterEqual(report["safety_related_count"], 5)
        self.assertIsNone(report["scientific_results"])

    def test_abstract_only_entry_is_rejected(self):
        data = copy.deepcopy(MATRIX)
        data["papers"][0]["abstract_only"] = True
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_unverified_entry_is_rejected(self):
        data = copy.deepcopy(MATRIX)
        data["papers"][0]["full_text_verified"] = False
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_duplicate_title_is_rejected(self):
        data = copy.deepcopy(MATRIX)
        data["papers"][1]["title"] = data["papers"][0]["title"].upper()
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_count_cannot_be_inflated_by_declaration(self):
        data = copy.deepcopy(MATRIX)
        data["audit_scope"]["counted_full_texts"] = 500
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_fewer_than_fifty_is_rejected(self):
        data = copy.deepcopy(MATRIX)
        data["papers"] = data["papers"][:49]
        data["audit_scope"]["counted_full_texts"] = 49
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_excluded_record_cannot_also_be_counted(self):
        data = copy.deepcopy(MATRIX)
        data["not_counted_in_this_release"][0]["title"] = data["papers"][0]["title"]
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)

    def test_claim_boundary_is_mandatory(self):
        data = copy.deepcopy(MATRIX)
        data["claim_boundary"]["not_supported"] = []
        with self.assertRaises(FullTextMatrixError):
            validate_matrix(data)


if __name__ == "__main__":
    unittest.main()
