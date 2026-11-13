"""FederationCore public API with executable CompMat-Bench support."""
from __future__ import annotations

from typing import Any

from . import federation_base as _base
from .compmat_federation import normalize_compmat_bench

FEDERATION_REGISTRY_SCHEMA = _base.FEDERATION_REGISTRY_SCHEMA
FEDERATED_REPORT_SCHEMA = _base.FEDERATED_REPORT_SCHEMA
FederationError = _base.FederationError
ADAPTER_STATUSES = _base.ADAPTER_STATUSES
COVERAGE_STATUSES = _base.COVERAGE_STATUSES
EXECUTION_MODES = _base.EXECUTION_MODES
VERIFIABILITY_LEVELS = _base.VERIFIABILITY_LEVELS
REPLACEMENT_SCOPES = _base.REPLACEMENT_SCOPES

normalize_swe_bench = _base.normalize_swe_bench
normalize_osworld = _base.normalize_osworld
normalize_calvin = _base.normalize_calvin

COMPMAT_ADAPTER = "COMPMAT_TRAJECTORY_MANIFEST_V1"
_base.SUPPORTED_ADAPTERS.add(COMPMAT_ADAPTER)
_base._NORMALIZERS[COMPMAT_ADAPTER] = normalize_compmat_bench
SUPPORTED_ADAPTERS = _base.SUPPORTED_ADAPTERS


def validate_federation_registry(registry: dict[str, Any]) -> dict[str, Any]:
    """Validate the registry and enforce truthful executable coverage."""
    result = _base.validate_federation_registry(registry)
    anchors = result["anchors"]
    for family, coverage in result["industry_coverage"].items():
        if coverage["status"] != "EXECUTABLE":
            continue
        if not any(
            anchors[benchmark_id]["adapter_status"] == "EXECUTABLE"
            for benchmark_id in coverage["benchmark_ids"]
        ):
            raise FederationError(
                f"industry {family} is marked EXECUTABLE without an "
                "executable native-result adapter"
            )
    return result


def normalize_external_run(
    registry: dict[str, Any],
    benchmark_id: str,
    payload: Any,
) -> dict[str, Any]:
    """Normalize one native upstream result while preserving its semantics."""
    validated = validate_federation_registry(registry)
    try:
        anchor = validated["anchors"][benchmark_id]
    except KeyError as exc:
        raise FederationError(f"unknown benchmark_id: {benchmark_id}") from exc
    if anchor["adapter_status"] != "EXECUTABLE":
        raise FederationError(
            f"benchmark {benchmark_id} does not have an executable adapter"
        )
    return _base._NORMALIZERS[anchor["result_adapter"]](anchor, payload)
