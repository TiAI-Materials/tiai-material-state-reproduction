"""Synthetic-only adversarial tests for externally authenticated pilot receipts."""
from __future__ import annotations

import copy
import hashlib
import hmac
import unittest

from tiai_matbench.attested_pilot import AUTH_SCHEMA, audit_attested_pilot, signable_payload
from tiai_matbench.pilot_ledger import PilotAuditError, build_plan, digest
from test_pilot_ledger import P, complete_bindings, native_fixture

TEST_KEY = b"TEST-ONLY-NEVER-USE-FOR-RESEARCH-" * 2
KEY_ID = "synthetic-adversarial-tests-only"


def seal(plan, records, receipts, key=TEST_KEY):
    authority = {
        "schema": AUTH_SCHEMA,
        "issuer_id": "MOCK_ISOLATED_VERIFIER_FOR_TESTS_ONLY",
        "key_id": KEY_ID,
        "protocol_sha256": digest(P),
        "slot_set_digest": plan["slot_set_digest"],
        "native_receipt_index": receipts,
        "run_ledger_sha256": {r["run_id"]: digest(r) for r in records},
        "artifact_sha256_by_run": {r["run_id"]: r["artifact_hashes"] for r in records},
    }
    authority["hmac_sha256"] = hmac.new(
        key, signable_payload(authority), hashlib.sha256
    ).hexdigest()
    return authority


class AttestedPilotTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_plan(P, complete_bindings())
        self.record, self.trusted = native_fixture(self.plan["slots"][0])
        self.records = [self.record]
        self.auth = seal(self.plan, self.records, self.trusted)

    def audit(self, records=None, authority=None, key=TEST_KEY, key_id=KEY_ID):
        return audit_attested_pilot(
            P, self.plan,
            self.records if records is None else records,
            self.auth if authority is None else authority,
            key, expected_key_id=key_id,
        )

    def test_signed_one_run_valid_but_not_a_leaderboard(self):
        report = self.audit()
        self.assertTrue(report["independent_verifier_authenticated"])
        self.assertEqual(report["valid_native_records"], 1)
        self.assertEqual(report["not_submitted"], 191)
        self.assertFalse(report["matched_effect_analysis_eligible"])

    def test_unsigned_authority_rejected(self):
        bad = copy.deepcopy(self.auth)
        del bad["hmac_sha256"]
        with self.assertRaises(PilotAuditError):
            self.audit(authority=bad)

    def test_attacker_minted_digest_index_without_key_rejected(self):
        forged = copy.deepcopy(self.auth)
        forged["hmac_sha256"] = "0" * 64
        with self.assertRaisesRegex(PilotAuditError, "signature mismatch"):
            self.audit(authority=forged)

    def test_wrong_key_and_key_id_rejected(self):
        with self.assertRaises(PilotAuditError):
            self.audit(key=b"X" * 32)
        with self.assertRaises(PilotAuditError):
            self.audit(key_id="unapproved-issuer")

    def test_missing_external_key_rejected(self):
        with self.assertRaisesRegex(PilotAuditError, "out of band"):
            self.audit(key=b"")

    def test_modified_ledger_rejected_even_if_native_receipt_unchanged(self):
        changed = copy.deepcopy(self.records)
        changed[0]["monetary_cost"] = 123
        with self.assertRaisesRegex(PilotAuditError, "not sealed"):
            self.audit(records=changed)

    def test_modified_artifact_hash_rejected(self):
        changed = copy.deepcopy(self.records)
        changed[0]["artifact_hashes"]["output"] = "0" * 64
        with self.assertRaisesRegex(PilotAuditError, "not sealed"):
            self.audit(records=changed)

    def test_plan_mutation_rejected(self):
        self.plan["slots"][0]["budget"] = {"token_limit": 99}
        with self.assertRaises(PilotAuditError):
            self.audit()

    def test_signed_incomplete_cost_cannot_enter_effect_analysis(self):
        self.assertIn("MISSING_INDEPENDENT_RESOURCE_TELEMETRY:monetary_cost",
                      self.audit()["evidence_gaps"])

    def test_complete_synthetic_bundle_is_harness_selftest_only(self):
        records, receipts = [], {}
        for slot in self.plan["slots"]:
            record, index = native_fixture(slot)
            record.update(
                input_tokens=17, output_tokens=3, cpu_core_seconds=0,
                gpu_seconds=0, monetary_cost=0.05,
                GDS=1.0, VWR=1.0, HLF=0.0, FCR=0.0,
            )
            records.append(record)
            receipts.update(index)
        authority = seal(self.plan, records, receipts)
        report = self.audit(records=records, authority=authority)
        self.assertEqual(report["valid_native_records"], 192)
        self.assertTrue(report["matched_effect_analysis_eligible"])
        # Entire fixture is mock; NEVER publish a synthetic score as empirical.


if __name__ == "__main__":
    unittest.main()
