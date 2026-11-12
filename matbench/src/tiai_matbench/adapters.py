"""Validation for cross-industry domain adapters."""

from __future__ import annotations

from typing import Any

from .io import BenchmarkFormatError

ADAPTER_REGISTRY_SCHEMA = "tiai.agentbench.domain_adapter_registry.v1"
VALID_READINESS = {
    "MATERIALS_ACTIVE",
    "DESIGN_ONLY",
    "EXTERNAL_CALIBRATION",
    "REQUIRES_DOMAIN_PARTNER",
    "REQUIRES_REGULATORY_GOVERNANCE",
}


class AdapterValidationError(BenchmarkFormatError):
    """Raised when the cross-industry adapter registry is malformed."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterValidationError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise AdapterValidationError(f"{label} must be a list")
    if nonempty and not value:
        raise AdapterValidationError(f"{label} must not be empty")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdapterValidationError(f"{label} must be a nonempty string")
    return value


def _unique_text_list(value: Any, label: str) -> list[str]:
    rows = _list(value, label, nonempty=True)
    result = [_text(row, f"{label}[{index}]") for index, row in enumerate(rows)]
    if len(result) != len(set(result)):
        raise AdapterValidationError(f"{label} contains duplicates")
    return result


def validate_adapter_registry(registry: dict[str, Any]) -> dict[str, Any]:
    registry = _object(registry, "registry")
    if registry.get("schema") != ADAPTER_REGISTRY_SCHEMA:
        raise AdapterValidationError(
            f"invalid adapter registry schema: {registry.get('schema')!r}"
        )
    for key in ("benchmark", "version", "core_protocol"):
        _text(registry.get(key), f"registry.{key}")
    core_work_classes = set(
        _unique_text_list(registry.get("core_work_classes"), "registry.core_work_classes")
    )
    adapters: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(_list(registry.get("adapters"), "registry.adapters", nonempty=True)):
        row = _object(raw, f"registry.adapters[{index}]")
        adapter_id = _text(row.get("adapter_id"), f"registry.adapters[{index}].adapter_id")
        if adapter_id in adapters:
            raise AdapterValidationError(f"duplicate adapter_id: {adapter_id}")
        for key in ("title", "scope"):
            _text(row.get(key), f"registry.adapters[{index}].{key}")
        readiness = _text(row.get("readiness"), f"registry.adapters[{index}].readiness")
        if readiness not in VALID_READINESS:
            raise AdapterValidationError(f"invalid adapter readiness: {readiness}")
        objects = _unique_text_list(row.get("domain_objects"), f"registry.adapters[{index}].domain_objects")
        tools = _unique_text_list(row.get("tool_families"), f"registry.adapters[{index}].tool_families")
        gates = _unique_text_list(row.get("critical_gates"), f"registry.adapters[{index}].critical_gates")
        classes = set(
            _unique_text_list(row.get("work_classes"), f"registry.adapters[{index}].work_classes")
        )
        unknown = classes - core_work_classes
        if unknown:
            raise AdapterValidationError(
                f"adapter {adapter_id} references unknown work classes: {sorted(unknown)}"
            )
        if not objects or not tools or not gates:
            raise AdapterValidationError(f"adapter {adapter_id} is incomplete")
        adapters[adapter_id] = row
    if "materials_science" not in adapters:
        raise AdapterValidationError("materials_science adapter is required")
    return {
        "adapter_count": len(adapters),
        "adapters": adapters,
        "core_work_classes": core_work_classes,
    }
