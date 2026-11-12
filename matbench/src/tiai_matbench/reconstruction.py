"""Deterministic verification for specification-driven tool reconstruction tasks."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from types import ModuleType
from typing import Any

from .io import BenchmarkFormatError, read_json, read_jsonl

RECONSTRUCTION_SPEC_SCHEMA = "tiai.agentbench.reconstruction_spec.v1"


class ReconstructionError(BenchmarkFormatError):
    """Raised when a reconstruction task or submission is malformed."""


def _load_module(path: Path) -> ModuleType:
    if not path.is_file():
        raise ReconstructionError(f"submission module does not exist: {path}")
    spec = importlib.util.spec_from_file_location("tiai_reconstruction_submission", path)
    if spec is None or spec.loader is None:
        raise ReconstructionError(f"cannot import submission module: {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # execution failure is a benchmark result
        raise ReconstructionError(f"submission import failed: {exc}") from exc
    return module


def _close(observed: float, expected: float, abs_tol: float, rel_tol: float) -> bool:
    return math.isclose(float(observed), float(expected), abs_tol=abs_tol, rel_tol=rel_tol)


def _validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict) or spec.get("schema") != RECONSTRUCTION_SPEC_SCHEMA:
        raise ReconstructionError("invalid reconstruction spec schema")
    for key in ("task_id", "title", "entrypoint", "cases_file"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ReconstructionError(f"spec.{key} must be a nonempty string")
    for key in ("absolute_tolerance", "relative_tolerance"):
        value = spec.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ReconstructionError(f"spec.{key} must be a nonnegative number")
    required = spec.get("required_output_keys")
    if not isinstance(required, list) or not required or not all(isinstance(x, str) and x for x in required):
        raise ReconstructionError("spec.required_output_keys must be a nonempty string list")
    if len(required) != len(set(required)):
        raise ReconstructionError("spec.required_output_keys contains duplicates")
    return spec


def _numeric_vector(value: Any, label: str) -> list[float]:
    if not isinstance(value, list):
        raise ReconstructionError(f"{label} must be a list")
    result: list[float] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ReconstructionError(f"{label}[{index}] must be numeric")
        result.append(float(item))
    return result


def verify_reconstruction(task_dir: str | Path, submission: str | Path) -> dict[str, Any]:
    """Execute and grade a reconstruction submission against frozen differential cases."""

    task_dir = Path(task_dir)
    spec = _validate_spec(read_json(task_dir / "spec.json"))
    cases_path = task_dir / spec["cases_file"]
    cases = read_jsonl(cases_path)
    if not cases:
        raise ReconstructionError("reconstruction task contains no cases")

    module = _load_module(Path(submission))
    entrypoint = getattr(module, spec["entrypoint"], None)
    if not callable(entrypoint):
        raise ReconstructionError(
            f"submission must expose callable {spec['entrypoint']!r}"
        )

    abs_tol = float(spec["absolute_tolerance"])
    rel_tol = float(spec["relative_tolerance"])
    rows: list[dict[str, Any]] = []
    passed = 0
    fatal_violations: list[str] = []
    for index, case in enumerate(cases):
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ReconstructionError(f"case {index} has invalid case_id")
        input_payload = case.get("input")
        if not isinstance(input_payload, dict):
            raise ReconstructionError(f"case {case_id} input must be an object")
        expected_error = case.get("expected_error")
        expected = case.get("expected")
        case_violations: list[str] = []
        output: Any = None
        raised: Exception | None = None
        try:
            output = entrypoint(input_payload)
        except Exception as exc:  # expected for invalid-input cases
            raised = exc

        if expected_error is not None:
            if not isinstance(expected_error, str) or not expected_error:
                raise ReconstructionError(f"case {case_id} expected_error must be a string")
            if raised is None:
                case_violations.append("EXPECTED_ERROR_NOT_RAISED")
            elif raised.__class__.__name__ != expected_error:
                case_violations.append(
                    f"WRONG_ERROR_TYPE:{raised.__class__.__name__}"
                )
        else:
            if raised is not None:
                case_violations.append(f"UNEXPECTED_EXCEPTION:{raised.__class__.__name__}")
            elif not isinstance(output, dict):
                case_violations.append("OUTPUT_NOT_OBJECT")
            elif not isinstance(expected, dict):
                raise ReconstructionError(f"case {case_id} expected must be an object")
            else:
                missing_keys = set(spec["required_output_keys"]) - set(output)
                if missing_keys:
                    case_violations.append(
                        "MISSING_OUTPUT_KEYS:" + ",".join(sorted(missing_keys))
                    )
                for key in spec["required_output_keys"]:
                    if key not in output or key not in expected:
                        continue
                    try:
                        observed_vector = _numeric_vector(output[key], f"{case_id}.{key}")
                        expected_vector = _numeric_vector(expected[key], f"{case_id}.expected.{key}")
                    except ReconstructionError as exc:
                        case_violations.append(f"MALFORMED_OUTPUT:{key}:{exc}")
                        continue
                    if len(observed_vector) != len(expected_vector):
                        case_violations.append(
                            f"LENGTH_MISMATCH:{key}:{len(observed_vector)}!={len(expected_vector)}"
                        )
                        continue
                    for item_index, (observed, target) in enumerate(
                        zip(observed_vector, expected_vector)
                    ):
                        if not _close(observed, target, abs_tol, rel_tol):
                            case_violations.append(
                                f"NUMERIC_MISMATCH:{key}[{item_index}]:{observed}!={target}"
                            )

                if not case_violations:
                    loads = input_payload.get("loads", {})
                    if isinstance(loads, dict):
                        applied = sum(float(value) for value in loads.values())
                        reactions = _numeric_vector(output["reactions"], f"{case_id}.reactions")
                        if not _close(sum(reactions) + applied, 0.0, abs_tol * 10, rel_tol * 10):
                            case_violations.append("GLOBAL_EQUILIBRIUM_FAILED")
                    fixed = input_payload.get("fixed_dofs", [])
                    displacements = _numeric_vector(output["displacements"], f"{case_id}.displacements")
                    if isinstance(fixed, list):
                        for dof in fixed:
                            if not isinstance(dof, int) or dof < 0 or dof >= len(displacements):
                                case_violations.append("INVALID_FIXED_DOF_IN_CASE")
                            elif not _close(displacements[dof], 0.0, abs_tol * 10, rel_tol * 10):
                                case_violations.append(f"FIXED_DOF_MOVED:{dof}")

        case_passed = not case_violations
        passed += int(case_passed)
        rows.append(
            {
                "case_id": case_id,
                "passed": case_passed,
                "violations": case_violations,
            }
        )
        if case.get("fatal", True) and not case_passed:
            fatal_violations.append(case_id)

    pass_rate = passed / len(cases)
    functional_signoff = not fatal_violations and pass_rate >= float(
        spec.get("minimum_pass_rate", 1.0)
    )
    return {
        "schema": "tiai.agentbench.reconstruction_report.v1",
        "task_id": spec["task_id"],
        "title": spec["title"],
        "case_count": len(cases),
        "passed_cases": passed,
        "pass_rate": pass_rate,
        "functional_signoff": functional_signoff,
        "fatal_failed_cases": fatal_violations,
        "cases": rows,
    }
