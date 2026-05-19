"""Ecosystem adapter contracts.

This module defines the handoff surface for non-Python adapters. Python remains
the mature production path; JVM, JS, PHP, Ruby, .NET, and Go are active behind
their adapter boundaries.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


LIFECYCLE_STEPS = (
    "candidate",
    "triage",
    "reproduction",
    "curation",
    "oracle",
    "package",
    "audit",
)


class AdapterStatus(str, Enum):
    """Implementation status for an ecosystem adapter."""

    ACTIVE = "active"
    RESERVED = "reserved"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AdapterContract:
    """Static contract exposed to future adapter implementations."""

    ecosystem: str
    status: AdapterStatus
    owner_model: str
    implementation_module: str | None = None
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)
    lifecycle_steps: tuple[str, ...] = LIFECYCLE_STEPS
    result_schema: str = "ReproductionResult-compatible JSON"
    oracle_contract: str = "public/hidden split, no expected-output leakage"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["lifecycle_steps"] = list(self.lifecycle_steps)
        return payload


@dataclass(frozen=True)
class AdapterPlanRequest:
    """Future adapter planning request.

    All adapters should be able to turn this request into a deterministic plan
    artifact before any environment-specific execution happens.
    """

    candidate_id: str
    ecosystem: str
    library: str
    old_version: str
    new_version: str
    client_file: str
    out_path: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterRunRequest:
    """Future adapter execution request."""

    spec_path: str
    out_dir: str
    timeout_s: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)


class EcosystemAdapter(Protocol):
    """Protocol future ecosystem adapters must satisfy."""

    contract: AdapterContract

    def plan(self, request: AdapterPlanRequest) -> Path:
        """Write a deterministic reproduction plan and return its path."""

    def run(self, request: AdapterRunRequest) -> Path:
        """Run old/new environments and return a ReproductionResult-compatible path."""

    def classify_failure(self, run_payload: dict[str, Any]) -> str | None:
        """Map ecosystem-specific failures to shared drop reasons."""


class ReservedAdapter:
    """Non-executing placeholder used for handoff and discovery."""

    def __init__(self, contract: AdapterContract):
        self.contract = contract

    def plan(self, _request: AdapterPlanRequest) -> Path:
        raise NotImplementedError(f"{self.contract.ecosystem} adapter is reserved, not implemented")

    def run(self, _request: AdapterRunRequest) -> Path:
        raise NotImplementedError(f"{self.contract.ecosystem} adapter is reserved, not implemented")

    def classify_failure(self, _run_payload: dict[str, Any]) -> str | None:
        raise NotImplementedError(f"{self.contract.ecosystem} adapter is reserved, not implemented")


ADAPTER_CONTRACTS: dict[str, AdapterContract] = {
    "python": AdapterContract(
        ecosystem="python",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.reproduction",
        required_tools=["python", "pip"],
        notes="Existing stable package old/new pipeline; do not rewrite while reserving other interfaces.",
    ),
    "jvm": AdapterContract(
        ecosystem="jvm",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.jvm",
        required_tools=["java", "javac"],
        optional_tools=["mvn", "gradle"],
        notes=(
            "Active first non-Python adapter. JVM-specific special cases are allowed "
            "inside the JVM adapter boundary when they remain local and deterministic."
        ),
    ),
    "go": AdapterContract(
        ecosystem="go",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.go",
        required_tools=["go"],
        notes=(
            "Active Go adapter for local deterministic package-root reproductions. "
            "Network module downloads remain optional future work."
        ),
    ),
    "js": AdapterContract(
        ecosystem="js",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.js",
        required_tools=["node"],
        optional_tools=["npm", "pnpm", "yarn"],
        notes=(
            "Active Node adapter for local deterministic package-root reproductions. "
            "Package-manager installs remain optional future work."
        ),
    ),
    "php": AdapterContract(
        ecosystem="php",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.php",
        required_tools=["php"],
        optional_tools=["composer"],
        notes=(
            "Active PHP adapter for local deterministic include-path reproductions. "
            "Composer installs remain optional future work."
        ),
    ),
    "ruby": AdapterContract(
        ecosystem="ruby",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.ruby",
        required_tools=["ruby"],
        optional_tools=["bundle"],
        notes=(
            "Active Ruby adapter for local deterministic load-path reproductions. "
            "Bundler installs remain optional future work."
        ),
    ),
    "rust": AdapterContract(
        ecosystem="rust",
        status=AdapterStatus.RESERVED,
        owner_model="handoff",
        implementation_module=None,
        required_tools=["cargo", "rustc"],
        notes="Reserved for future crate-based old/new reproductions.",
    ),
    "dotnet": AdapterContract(
        ecosystem="dotnet",
        status=AdapterStatus.ACTIVE,
        owner_model="current",
        implementation_module="silent_drift_miner.adapters.dotnet",
        required_tools=["dotnet"],
        optional_tools=["nuget"],
        notes=(
            "Active .NET adapter for local deterministic project-root reproductions. "
            "NuGet restores remain optional future work."
        ),
    ),
}


def list_adapter_contracts() -> list[AdapterContract]:
    return [ADAPTER_CONTRACTS[name] for name in sorted(ADAPTER_CONTRACTS)]


def get_adapter_contract(ecosystem: str) -> AdapterContract:
    key = ecosystem.lower()
    if key not in ADAPTER_CONTRACTS:
        raise KeyError(f"unknown ecosystem adapter: {ecosystem}")
    return ADAPTER_CONTRACTS[key]


def build_adapter_contract_report(target: str | None = None) -> dict[str, Any]:
    contracts = [get_adapter_contract(target)] if target else list_adapter_contracts()
    return {
        "schema_version": "1",
        "contracts": [contract.to_dict() for contract in contracts],
        "handoff_rule": (
            "Active adapters may execute inside their ecosystem boundary; reserved "
            "adapters expose contracts only until explicitly opened."
        ),
    }


def adapter_contract_report_json(target: str | None = None) -> str:
    return json.dumps(build_adapter_contract_report(target), indent=2, ensure_ascii=False)
