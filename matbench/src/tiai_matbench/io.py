"""Strict JSON and JSONL utilities used by TiAI-MatBench.

The benchmark deliberately rejects duplicate object keys, NaN and infinity so
that different runtimes cannot silently interpret a submission differently.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable


class BenchmarkFormatError(ValueError):
    """Raised when benchmark or submission data is not deterministic JSON."""


def _reject_constant(value: str) -> None:
    raise BenchmarkFormatError(f"non-finite JSON number is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BenchmarkFormatError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def strict_loads(text: str, *, source: str = "<string>") -> Any:
    """Parse strict JSON with stable rejection of ambiguous constructs."""

    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, BenchmarkFormatError) as exc:
        raise BenchmarkFormatError(f"{source}: {exc}") from exc
    _assert_finite(value, source=source)
    return value


def _assert_finite(value: Any, *, source: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise BenchmarkFormatError(f"{source}: non-finite float is not allowed")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_finite(nested, source=source)
    elif isinstance(value, list):
        for nested in value:
            _assert_finite(nested, source=source)


def read_json(path: str | Path) -> Any:
    path = Path(path)
    return strict_loads(path.read_text(encoding="utf-8"), source=str(path))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        value = strict_loads(raw_line, source=f"{path}:{line_number}")
        if not isinstance(value, dict):
            raise BenchmarkFormatError(
                f"{path}:{line_number}: each JSONL record must be an object"
            )
        records.append(value)
    return records


def write_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
