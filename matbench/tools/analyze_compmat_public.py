"""Reproduce the frozen CompMat-Bench public evidence artifact.

Usage:
    python matbench/tools/analyze_compmat_public.py \
        /path/to/trajectories/manifest.json \
        --output /path/to/evidence.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tiai_matbench.public_evidence import (
    analyze_compmat_manifest,
    validate_public_evidence,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a frozen CompMat-Bench trajectory manifest."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.manifest.read_bytes()
    payload = json.loads(raw)
    report = analyze_compmat_manifest(payload, raw_bytes=raw)
    validation = validate_public_evidence(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
