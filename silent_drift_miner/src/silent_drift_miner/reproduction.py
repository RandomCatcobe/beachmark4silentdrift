"""Python reproduction spec and result schemas."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


class DropReason(str, Enum):
    INSTALL_FAILED = "install_failed"
    IMPORT_FAILED = "import_failed"
    CLIENT_GENERATION_FAILED = "client_generation_failed"
    CLIENT_RUNTIME_ERROR = "client_runtime_error"
    NO_BEHAVIOR_DIFF = "no_behavior_diff"
    HARD_BREAK = "hard_break"
    FLAKY_OUTPUT = "flaky_output"
    TIMEOUT = "timeout"


@dataclass
class PythonEnvironmentDefinition:
    label: str
    library: str
    version: str
    install_command: list[str]
    python_executable: str = "python"


@dataclass
class ReproductionSpec:
    candidate_id: str
    library: str
    old_version: str
    new_version: str
    client_file: str
    old_environment: PythonEnvironmentDefinition
    new_environment: PythonEnvironmentDefinition
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "ReproductionSpec":
        data = json.loads(text)
        data["old_environment"] = PythonEnvironmentDefinition(**data["old_environment"])
        data["new_environment"] = PythonEnvironmentDefinition(**data["new_environment"])
        return cls(**data)


@dataclass
class ReproductionRun:
    label: str
    environment: PythonEnvironmentDefinition
    stdout_path: str
    stderr_path: str
    exit_code_path: str
    run_log_path: str
    build_log_path: str
    exit_code: Optional[int] = None


@dataclass
class ReproductionDiff:
    stdout_changed: bool = False
    stderr_changed: bool = False
    exit_code_changed: bool = False
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReproductionResult:
    candidate_id: str
    spec_path: str
    attempt_dir: str
    old_run: ReproductionRun
    new_run: ReproductionRun
    diff: ReproductionDiff
    keep: bool
    drop_reason: Optional[DropReason] = None
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)


def create_reproduction_spec(
    candidate_id: str,
    library: str,
    old_version: str,
    new_version: str,
    client_file: str | Path,
) -> ReproductionSpec:
    old_environment = PythonEnvironmentDefinition(
        label="old",
        library=library,
        version=old_version,
        install_command=["python", "-m", "pip", "install", f"{library}=={old_version}"],
    )
    new_environment = PythonEnvironmentDefinition(
        label="new",
        library=library,
        version=new_version,
        install_command=["python", "-m", "pip", "install", f"{library}=={new_version}"],
    )
    return ReproductionSpec(
        candidate_id=candidate_id,
        library=library,
        old_version=old_version,
        new_version=new_version,
        client_file=str(Path(client_file)),
        old_environment=old_environment,
        new_environment=new_environment,
    )


def write_reproduction_spec(spec: ReproductionSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(spec.to_json() + "\n", encoding="utf-8")


def load_reproduction_spec(path: Path) -> ReproductionSpec:
    return ReproductionSpec.from_json(path.read_text(encoding="utf-8"))
