"""Externally authenticated publication gate for the frozen v0.8 materials pilot.

PilotLedger v0.9 is a structural checker: a digest index alone does not
authenticate an independent native scorer. This module requires an out-of-band
HMAC key owned by an isolated verifier, sealing native receipts, run ledgers
and artifact hashes. It cannot generate native scores or launch a model.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any

from .pilot_ledger import PilotAuditError, audit_pilot, canonical, digest, load_json

AUTH_SCHEMA = "tiai.agentbench.external_native_authority.v0.10"
AUDIT_SCHEMA = "tiai.agentbench.attested_pilot_audit.v0.10"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PUBLISH_COST_FIELDS = (
    "wall_time_seconds", "input_tokens", "output_tokens",
    "cpu_core_seconds", "gpu_seconds", "monetary_cost",
)
PUBLISH_SCORE_FIELDS = ("GDS", "VWR", "HLF", "FCR")


def _sha(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _key_check(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < 32:
        raise PilotAuditError("independent verifier key must be >=32 bytes, supplied out of band")


def signable_payload(authority: dict[str, Any]) -> bytes:
    """Serialize all authority fields except the HMAC itself."""
    if not isinstance(authority, dict):
        raise PilotAuditError("authority must be a JSON object")
    return canonical({k: v for k, v in authority.items() if k != "hmac_sha256"})


def audit_attested_pilot(protocol: dict, plan: dict, records: list[dict],
                         authority: dict, verifier_key: bytes,
                         *, expected_key_id: str) -> dict:
    """Verify an isolated scorer's signed evidence, not agent assertions.

    This requires an auditor/verifier account inaccessible to tested agents.
    A valid HMAC authenticates the issuer of the bundle, not the underlying
    scientific truth; the issuer must actually run the native verifier.
    """
    _key_check(verifier_key)
    if not isinstance(expected_key_id, str) or not expected_key_id:
        raise PilotAuditError("expected verifier key ID must be explicit")
    if not isinstance(authority, dict) or authority.get("schema") != AUTH_SCHEMA:
        raise PilotAuditError("externally authenticated authority bundle required")
    if authority.get("key_id") != expected_key_id:
        raise PilotAuditError("unrecognized external verifier key ID")
    if not isinstance(authority.get("issuer_id"), str) or not authority["issuer_id"].strip():
        raise PilotAuditError("independent issuer identity required")
    if authority.get("protocol_sha256") != digest(protocol):
        raise PilotAuditError("authority protocol SHA mismatch")
    if authority.get("slot_set_digest") != plan.get("slot_set_digest"):
        raise PilotAuditError("authority frozen plan digest mismatch")
    if not _sha(authority.get("hmac_sha256")):
        raise PilotAuditError("authority HMAC missing or malformed")
    expected_mac = hmac.new(verifier_key, signable_payload(authority),
                            hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_mac, authority["hmac_sha256"]):
        raise PilotAuditError("native verifier authority signature mismatch")

    receipts = authority.get("native_receipt_index")
    ledgers = authority.get("run_ledger_sha256")
    artifacts = authority.get("artifact_sha256_by_run")
    if not all(isinstance(x, dict) for x in (receipts, ledgers, artifacts)):
        raise PilotAuditError("signed receipt/ledger/artifact indices required")
    ids = [r.get("run_id") for r in records]
    if len(ids) != len(set(ids)):
        raise PilotAuditError("duplicate run identity in attested ledger")
    if set(ledgers) != set(ids) or set(artifacts) != set(ids):
        raise PilotAuditError("signed ledgers and artifacts must cover exact submitted runs")
    for record in records:
        run_id = record["run_id"]
        if not _sha(ledgers[run_id]) or ledgers[run_id] != digest(record):
            raise PilotAuditError("run ledger not sealed by independent issuer: " + run_id)
        hashes = record.get("artifact_hashes")
        if not isinstance(hashes, dict) or hashes != artifacts[run_id]:
            raise PilotAuditError("artifact index differs from sealed export: " + run_id)
        if not all(isinstance(name, str) and name and _sha(value)
                   for name, value in hashes.items()):
            raise PilotAuditError("artifact hashes must be SHA-256 hex: " + run_id)

    structural = audit_pilot(protocol, plan, records, receipts)
    gaps = []
    if structural["not_submitted"]:
        gaps.append("MISSING_PRE_REGISTERED_RUNS")
    if structural["invalid_records"]:
        gaps.append("INVALID_NATIVE_RUN_RECORDS")
    for record in records:
        for field in PUBLISH_COST_FIELDS:
            if record.get(field) is None:
                gaps.append("MISSING_INDEPENDENT_RESOURCE_TELEMETRY:" + field)
        for field in PUBLISH_SCORE_FIELDS:
            if record.get(field) is None:
                gaps.append("MISSING_VERIFIED_WORK_SCORE:" + field)
    eligible = structural["matched_complete"] and not gaps
    return {
        "schema": AUDIT_SCHEMA,
        "protocol_sha256": digest(protocol),
        "slot_set_digest": plan["slot_set_digest"],
        "independent_verifier_authenticated": True,
        "external_issuer_id": authority["issuer_id"],
        "external_key_id": expected_key_id,
        "planned": structural["planned"],
        "received": structural["received"],
        "valid_native_records": structural["accepted_native_receipts"],
        "invalid_records": structural["invalid_records"],
        "not_submitted": structural["not_submitted"],
        "verified_native_passes": structural["verified_native_passes"],
        "false_completions": structural["false_completions"],
        "evidence_gaps": sorted(set(gaps)),
        "matched_effect_analysis_eligible": eligible,
        "claim_boundary": (
            "A signed receipt is not a scientific or system-performance result. "
            "Only 192 valid matched runs with independent native verification and "
            "complete telemetry enter separate stratum-wise effect analysis. "
            "Never give the tested agent access to the verifier key."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Attested audit; NOT an agent/model runner")
    for flag in ("protocol", "plan", "ledger", "authority",
                 "verifier-key-file", "expected-key-id", "output"):
        p.add_argument("--" + flag, required=True)
    args = p.parse_args()
    with open(args.ledger, encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream if line.strip()]
    report = audit_attested_pilot(
        load_json(args.protocol), load_json(args.plan), records,
        load_json(args.authority), Path(args.verifier_key_file).read_bytes(),
        expected_key_id=args.expected_key_id,
    )
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                            allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
