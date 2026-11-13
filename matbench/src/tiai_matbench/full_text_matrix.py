"""Validation for the TiAI-AgentBench full-text evidence matrix v0.10."""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "tiai-agentbench.full-text-evidence-matrix.v0.10"
REQUIRED_PAPER_FIELDS = {
    "paper_id",
    "title",
    "vertical",
    "task_horizon",
    "primary_source_locator",
    "verifier_pattern",
    "method_axes",
    "transferable_rule",
    "claim_boundary",
    "full_text_verified",
    "verification_date_utc",
    "verification_basis",
    "abstract_only",
}
FORBIDDEN_COUNTING_PHRASES = {
    "abstract only",
    "metadata only",
    "abstract/metadata only",
}


class FullTextMatrixError(ValueError):
    """Raised when the matrix violates an auditable counting rule."""


def _norm_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _require_nonempty_text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FullTextMatrixError(f"{label} must be non-empty text")


def validate_matrix(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise FullTextMatrixError("matrix root must be an object")
    if data.get("schema") != SCHEMA:
        raise FullTextMatrixError(f"unexpected schema: {data.get('schema')!r}")

    scope = data.get("audit_scope")
    if not isinstance(scope, dict):
        raise FullTextMatrixError("audit_scope must be an object")
    minimum = scope.get("minimum_count")
    if not isinstance(minimum, int) or minimum < 50:
        raise FullTextMatrixError("minimum_count must be an integer >= 50")

    papers = data.get("papers")
    if not isinstance(papers, list):
        raise FullTextMatrixError("papers must be a list")
    if len(papers) < minimum:
        raise FullTextMatrixError(
            f"only {len(papers)} counted full texts; at least {minimum} are required"
        )
    declared = scope.get("counted_full_texts")
    if declared != len(papers):
        raise FullTextMatrixError(
            f"declared counted_full_texts={declared!r} but observed {len(papers)}"
        )

    ids: list[str] = []
    titles: list[str] = []
    verticals: Counter[str] = Counter()
    safety_count = 0
    for index, paper in enumerate(papers):
        label = f"papers[{index}]"
        if not isinstance(paper, dict):
            raise FullTextMatrixError(f"{label} must be an object")
        missing = sorted(REQUIRED_PAPER_FIELDS - set(paper))
        if missing:
            raise FullTextMatrixError(f"{label} missing fields: {missing}")

        for key in (
            "paper_id", "title", "vertical", "task_horizon",
            "primary_source_locator", "verifier_pattern",
            "transferable_rule", "claim_boundary",
            "verification_date_utc", "verification_basis",
        ):
            _require_nonempty_text(paper[key], f"{label}.{key}")

        if paper["full_text_verified"] is not True:
            raise FullTextMatrixError(f"{label} is counted without full_text_verified=true")
        if paper["abstract_only"] is not False:
            raise FullTextMatrixError(f"{label} is abstract-only but counted")
        basis = paper["verification_basis"].casefold()
        if any(phrase in basis for phrase in FORBIDDEN_COUNTING_PHRASES):
            raise FullTextMatrixError(f"{label} verification_basis indicates an abstract-only record")

        axes = paper["method_axes"]
        if not isinstance(axes, list) or not axes or any(
            not isinstance(axis, str) or not axis.strip() for axis in axes
        ):
            raise FullTextMatrixError(f"{label}.method_axes must be a non-empty text list")

        ids.append(paper["paper_id"])
        titles.append(_norm_title(paper["title"]))
        verticals[paper["vertical"]] += 1
        if "safety" in paper["vertical"] or any("safety" in axis for axis in axes):
            safety_count += 1

    duplicate_ids = [key for key, count in Counter(ids).items() if count > 1]
    duplicate_titles = [key for key, count in Counter(titles).items() if count > 1]
    if duplicate_ids:
        raise FullTextMatrixError(f"duplicate paper_id values: {duplicate_ids}")
    if duplicate_titles:
        raise FullTextMatrixError(f"duplicate normalized titles: {duplicate_titles}")

    excluded = data.get("not_counted_in_this_release")
    if not isinstance(excluded, list):
        raise FullTextMatrixError("not_counted_in_this_release must be a list")
    for index, record in enumerate(excluded):
        if not isinstance(record, dict):
            raise FullTextMatrixError(f"excluded[{index}] must be an object")
        _require_nonempty_text(record.get("title"), f"excluded[{index}].title")
        _require_nonempty_text(record.get("reason"), f"excluded[{index}].reason")
        if _norm_title(record["title"]) in set(titles):
            raise FullTextMatrixError(
                f"excluded record is also counted: {record['title']}"
            )

    findings = data.get("cross_paper_findings")
    if not isinstance(findings, list) or len(findings) < 5:
        raise FullTextMatrixError("at least five cross-paper findings are required")
    finding_ids: list[str] = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise FullTextMatrixError(f"finding[{index}] must be an object")
        for key in ("finding_id", "finding", "implication"):
            _require_nonempty_text(finding.get(key), f"finding[{index}].{key}")
        finding_ids.append(finding["finding_id"])
    if len(finding_ids) != len(set(finding_ids)):
        raise FullTextMatrixError("finding_id values must be unique")

    boundary = data.get("claim_boundary")
    if not isinstance(boundary, dict):
        raise FullTextMatrixError("claim_boundary must be an object")
    for key in ("supported", "not_supported"):
        values = boundary.get(key)
        if not isinstance(values, list) or not values:
            raise FullTextMatrixError(f"claim_boundary.{key} must be a non-empty list")
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise FullTextMatrixError(f"claim_boundary.{key} must contain non-empty text")

    return {
        "schema": SCHEMA,
        "counted_full_texts": len(papers),
        "minimum_count": minimum,
        "unique_paper_ids": len(set(ids)),
        "unique_titles": len(set(titles)),
        "vertical_count": len(verticals),
        "verticals": dict(sorted(verticals.items())),
        "safety_related_count": safety_count,
        "excluded_not_counted": len(excluded),
        "cross_paper_findings": len(findings),
        "status": "PASS",
        "scientific_results": None,
        "claim_boundary": "METHOD_EVIDENCE_ONLY_NOT_SYSTEM_ADVANTAGE",
    }


def load_and_validate(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    payload = source.read_bytes()
    if source.name.endswith(".json.gz.b64"):
        raw = gzip.decompress(base64.b64decode(payload.strip(), validate=True))
    elif source.suffix == ".gz":
        raw = gzip.decompress(payload)
    else:
        raw = payload
    data = json.loads(raw.decode("utf-8"))
    return validate_matrix(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = load_and_validate(args.matrix)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
