"""Schema validation for case-bank metadata files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATUS_VALUES = {
    "idea_only",
    "verified_keep",
    "rejected_no_diff",
    "blocked_runtime",
    "blocked_dependency",
    "needs_source",
}

PRIMARY_SCENARIOS = {
    "validation-and-policy",
    "parsing-and-ingestion",
    "serialization-and-binding",
    "time-and-localization",
    "state-and-lifecycle",
    "routing-and-identity",
    "commerce-order-flow",
    "inventory-and-fulfillment",
    "observability-and-logging",
    "runtime-semantics",
}

APPLICATION_SCENARIOS = PRIMARY_SCENARIOS | {
    "identity-and-contact-data",
}

DRIFT_PATTERNS = {
    "default-changed",
    "field-semantics-changed",
    "field-removed-or-masked",
    "type-or-shape-changed",
    "parser-rule-changed",
    "ordering-changed",
    "bundled-data-changed",
    "runtime-locale-changed",
    "validation-relaxed",
    "validation-strictness-increased",
    "success-but-no-effect",
    "out-of-order-event",
    "old-state-overwrite",
}

FAILURE_MODES = {
    "silent-value-change",
    "silent-acceptance-change",
    "silent-rejection-change",
    "wrong-entity",
    "wrong-route",
    "stale-state",
    "missing-field",
    "wrong-type",
    "wrong-order",
    "wrong-timezone",
    "wrong-locale",
    "wrong-inventory",
    "wrong-fulfillment",
    "wrong-refund-or-payment-state",
}

DETERMINISM_VALUES = {
    "local-deterministic",
    "package-cache",
    "runtime-pair",
    "service-contract",
    "mockable-service",
    "requires-live-credential",
}

REQUIRED_FIELDS = {
    "case_id": str,
    "slug": str,
    "title": str,
    "status": str,
    "primary_scenario": str,
    "application_scenarios": list,
    "ecosystems": list,
    "languages": list,
    "api_surfaces": list,
    "drift_patterns": list,
    "failure_modes": list,
    "determinism": str,
    "external_dependencies": str,
    "old_version": str,
    "new_version": str,
    "source_urls": list,
    "provenance": dict,
}


def load_metadata(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_metadata(data, path)
    return data


def validate_metadata(data: dict[str, Any], path: Path | None = None) -> None:
    label = str(path) if path else "metadata"
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            raise ValueError(f"{label}: missing required field {field!r}")
        if not isinstance(data[field], expected_type):
            raise ValueError(f"{label}: field {field!r} must be {expected_type.__name__}")

    if data["status"] not in STATUS_VALUES:
        raise ValueError(f"{label}: unknown status {data['status']!r}")
    if data["primary_scenario"] not in PRIMARY_SCENARIOS:
        raise ValueError(f"{label}: unknown primary_scenario {data['primary_scenario']!r}")
    if data["primary_scenario"] not in data["application_scenarios"]:
        raise ValueError(f"{label}: primary_scenario must appear in application_scenarios")

    _validate_values(
        label,
        "application_scenarios",
        data["application_scenarios"],
        APPLICATION_SCENARIOS,
    )
    _validate_values(label, "drift_patterns", data["drift_patterns"], DRIFT_PATTERNS)
    _validate_values(label, "failure_modes", data["failure_modes"], FAILURE_MODES)
    if data["determinism"] not in DETERMINISM_VALUES:
        raise ValueError(f"{label}: unknown determinism {data['determinism']!r}")
    if data["external_dependencies"] not in DETERMINISM_VALUES:
        raise ValueError(f"{label}: unknown external_dependencies {data['external_dependencies']!r}")

    provenance = data["provenance"]
    if "reproduction_result" not in provenance or "verified_at" not in provenance:
        raise ValueError(f"{label}: provenance requires reproduction_result and verified_at")


def metadata_json_schema() -> dict[str, Any]:
    properties = {
        field: _json_schema_type(expected_type)
        for field, expected_type in REQUIRED_FIELDS.items()
    }
    properties["status"]["enum"] = sorted(STATUS_VALUES)
    properties["primary_scenario"]["enum"] = sorted(PRIMARY_SCENARIOS)
    properties["application_scenarios"]["items"] = {
        "type": "string",
        "enum": sorted(APPLICATION_SCENARIOS),
    }
    properties["drift_patterns"]["items"] = {"type": "string", "enum": sorted(DRIFT_PATTERNS)}
    properties["failure_modes"]["items"] = {"type": "string", "enum": sorted(FAILURE_MODES)}
    properties["determinism"]["enum"] = sorted(DETERMINISM_VALUES)
    properties["external_dependencies"]["enum"] = sorted(DETERMINISM_VALUES)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://silentdrift.local/case-bank/metadata.schema.json",
        "title": "SilentDrift Case Bank Metadata",
        "type": "object",
        "additionalProperties": True,
        "required": sorted(REQUIRED_FIELDS),
        "properties": properties,
    }


def write_metadata_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(metadata_json_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_values(label: str, field: str, values: list[Any], allowed: set[str]) -> None:
    _validate_string_list(label, field, values)
    for value in values:
        if value not in allowed:
            raise ValueError(f"{label}: unknown {field} value {value!r}")


def _validate_string_list(label: str, field: str, values: list[Any]) -> None:
    if not values:
        raise ValueError(f"{label}: {field} must not be empty")
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{label}: {field} values must be strings")


def _json_schema_type(expected_type: type) -> dict[str, Any]:
    if expected_type is str:
        return {"type": "string"}
    if expected_type is list:
        return {"type": "array", "items": {"type": "string"}}
    if expected_type is dict:
        return {"type": "object"}
    raise TypeError(f"unsupported schema type: {expected_type}")
