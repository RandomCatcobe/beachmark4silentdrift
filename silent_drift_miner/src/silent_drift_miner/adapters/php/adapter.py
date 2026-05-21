"""Offline PHP reproduction adapter."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ...adapter_contracts import AdapterPlanRequest, AdapterRunRequest, get_adapter_contract
from ...reproduction import (
    DropReason,
    PythonEnvironmentDefinition,
    ReproductionDiff,
    ReproductionResult,
    ReproductionRun,
    allocate_attempt_dir,
    build_diff,
)
from ...schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


@dataclass
class PhpEnvironmentDefinition:
    label: str
    library: str
    version: str
    package_path: str
    package_paths: list[str] = field(default_factory=list)
    php_executable: str = "php"
    include_paths: list[str] = field(default_factory=list)
    php_args: list[str] = field(default_factory=list)
    program_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class PhpReproductionSpec:
    candidate_id: str
    library: str
    old_version: str
    new_version: str
    client_file: str
    old_environment: PhpEnvironmentDefinition
    new_environment: PhpEnvironmentDefinition
    ecosystem: str = "php"
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "PhpReproductionSpec":
        data = json.loads(text)
        if data.get("ecosystem") != "php":
            raise ValueError("PHP reproduction spec requires ecosystem='php'")
        data["old_environment"] = PhpEnvironmentDefinition(**data["old_environment"])
        data["new_environment"] = PhpEnvironmentDefinition(**data["new_environment"])
        return cls(**data)


def create_php_reproduction_spec(
    candidate_id: str,
    library: str,
    old_version: str,
    new_version: str,
    client_file: str | Path,
    old_package_path: str | Path | list[str | Path],
    new_package_path: str | Path | list[str | Path],
    php_executable: str = "php",
    old_include_paths: list[str] | None = None,
    new_include_paths: list[str] | None = None,
    old_php_args: list[str] | None = None,
    new_php_args: list[str] | None = None,
    old_program_args: list[str] | None = None,
    new_program_args: list[str] | None = None,
    old_env: dict[str, str] | None = None,
    new_env: dict[str, str] | None = None,
    old_php_executable: str | None = None,
    new_php_executable: str | None = None,
) -> PhpReproductionSpec:
    old_package_paths = _metadata_list(old_package_path)
    new_package_paths = _metadata_list(new_package_path)
    if not old_package_paths:
        raise ValueError("old PHP package path is required")
    if not new_package_paths:
        raise ValueError("new PHP package path is required")
    return PhpReproductionSpec(
        candidate_id=candidate_id,
        library=library,
        old_version=old_version,
        new_version=new_version,
        client_file=str(Path(client_file)),
        old_environment=PhpEnvironmentDefinition(
            label="old",
            library=library,
            version=old_version,
            package_path=str(Path(old_package_paths[0])),
            package_paths=[str(Path(path)) for path in old_package_paths],
            php_executable=old_php_executable or php_executable,
            include_paths=list(old_include_paths or []),
            php_args=list(old_php_args or []),
            program_args=list(old_program_args or []),
            env=dict(old_env or {}),
        ),
        new_environment=PhpEnvironmentDefinition(
            label="new",
            library=library,
            version=new_version,
            package_path=str(Path(new_package_paths[0])),
            package_paths=[str(Path(path)) for path in new_package_paths],
            php_executable=new_php_executable or php_executable,
            include_paths=list(new_include_paths or []),
            php_args=list(new_php_args or []),
            program_args=list(new_program_args or []),
            env=dict(new_env or {}),
        ),
    )


def write_php_reproduction_spec(spec: PhpReproductionSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(spec.to_json() + "\n", encoding="utf-8")


def load_php_reproduction_spec(path: Path) -> PhpReproductionSpec:
    return PhpReproductionSpec.from_json(path.read_text(encoding="utf-8"))


def run_php_reproduction_spec(
    spec: PhpReproductionSpec,
    out: Path,
    timeout_s: int = 30,
) -> ReproductionResult:
    attempt_dir = allocate_attempt_dir(out)
    attempt_dir.mkdir(parents=True, exist_ok=False)
    write_php_reproduction_spec(spec, attempt_dir / "spec.json")

    old_run = _run_one_side(spec, spec.old_environment, attempt_dir / "old", timeout_s)
    new_run = _run_one_side(spec, spec.new_environment, attempt_dir / "new", timeout_s)
    diff = build_diff(old_run, new_run)
    drop_reason = _drop_reason(old_run, new_run, diff)
    result = ReproductionResult(
        candidate_id=spec.candidate_id,
        spec_path=str(attempt_dir / "spec.json"),
        attempt_dir=str(attempt_dir),
        old_run=old_run,
        new_run=new_run,
        diff=diff,
        keep=drop_reason is None,
        drop_reason=drop_reason,
    )
    (attempt_dir / "diff.json").write_text(
        json.dumps(asdict(diff), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (attempt_dir / "result.json").write_text(result.to_json() + "\n", encoding="utf-8")
    return result


class PhpAdapter:
    """Adapter facade matching the EcosystemAdapter protocol."""

    contract = get_adapter_contract("php")

    def plan(self, request: AdapterPlanRequest) -> Path:
        if request.ecosystem.lower() != "php":
            raise ValueError(f"PHP adapter cannot plan ecosystem={request.ecosystem!r}")
        metadata = request.metadata
        old_package_paths = _metadata_paths(metadata, "old_package_paths", "old_package_path")
        new_package_paths = _metadata_paths(metadata, "new_package_paths", "new_package_path")
        _require_existing_path(Path(request.client_file), "PHP client file")
        _require_existing_paths(old_package_paths, "old PHP package path")
        _require_existing_paths(new_package_paths, "new PHP package path")
        shared_include_paths = _metadata_list(metadata.get("include_paths"))
        old_include_paths = shared_include_paths + _metadata_list(metadata.get("old_include_paths"))
        new_include_paths = shared_include_paths + _metadata_list(metadata.get("new_include_paths"))
        _require_existing_paths(old_include_paths, "old PHP include path")
        _require_existing_paths(new_include_paths, "new PHP include path")
        shared_php_args = _metadata_list(metadata.get("php_args"))
        shared_program_args = _metadata_list(metadata.get("program_args"))
        shared_env = _metadata_env(metadata.get("env"))
        spec = create_php_reproduction_spec(
            candidate_id=request.candidate_id,
            library=request.library,
            old_version=request.old_version,
            new_version=request.new_version,
            client_file=request.client_file,
            old_package_path=old_package_paths,
            new_package_path=new_package_paths,
            php_executable=str(metadata.get("php_executable", "php")),
            old_include_paths=old_include_paths,
            new_include_paths=new_include_paths,
            old_php_args=shared_php_args + _metadata_list(metadata.get("old_php_args")),
            new_php_args=shared_php_args + _metadata_list(metadata.get("new_php_args")),
            old_program_args=shared_program_args + _metadata_list(metadata.get("old_program_args")),
            new_program_args=shared_program_args + _metadata_list(metadata.get("new_program_args")),
            old_env={**shared_env, **_metadata_env(metadata.get("old_env"))},
            new_env={**shared_env, **_metadata_env(metadata.get("new_env"))},
            old_php_executable=_metadata_optional_str(metadata.get("old_php_executable")),
            new_php_executable=_metadata_optional_str(metadata.get("new_php_executable")),
        )
        out_path = Path(request.out_path)
        write_php_reproduction_spec(spec, out_path)
        return out_path

    def run(self, request: AdapterRunRequest) -> Path:
        spec = load_php_reproduction_spec(Path(request.spec_path))
        result = run_php_reproduction_spec(spec, Path(request.out_dir), timeout_s=request.timeout_s)
        return Path(result.attempt_dir) / "result.json"

    def classify_failure(self, run_payload: dict[str, Any]) -> str | None:
        existing = run_payload.get("drop_reason")
        if existing:
            return str(existing)
        old_run = run_payload.get("old_run") or {}
        new_run = run_payload.get("new_run") or {}
        if old_run.get("exit_code") == 124 or new_run.get("exit_code") == 124:
            return DropReason.TIMEOUT.value
        if old_run.get("exit_code") == 127 or new_run.get("exit_code") == 127:
            return DropReason.INSTALL_FAILED.value
        if _nonzero_exit(old_run) or _nonzero_exit(new_run):
            return DropReason.CLIENT_RUNTIME_ERROR.value
        diff = run_payload.get("diff") or {}
        if not any(diff.get(key) for key in ("stdout_changed", "stderr_changed", "exit_code_changed")):
            return DropReason.NO_BEHAVIOR_DIFF.value
        return None


def _run_one_side(
    spec: PhpReproductionSpec,
    environment: PhpEnvironmentDefinition,
    out_dir: Path,
    timeout_s: int,
) -> ReproductionRun:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    exit_code_path = out_dir / "exit_code.txt"
    run_log_path = out_dir / "run.log"
    build_log_path = out_dir / "build.log"
    dockerfile_path = out_dir / "Dockerfile"

    build_log_path.write_text(_build_log(environment), encoding="utf-8")
    dockerfile_path.write_text(_dockerfile(spec, environment), encoding="utf-8")
    command = _run_command_line(spec, environment)
    run_log_path.write_text("command: " + " ".join(command) + "\n", encoding="utf-8")
    run = _run_command(command, timeout_s, environment)
    stdout_path.write_text(run["stdout"], encoding="utf-8")
    stderr_path.write_text(run["stderr"], encoding="utf-8")
    exit_code_path.write_text(str(run["exit_code"]) + "\n", encoding="utf-8")
    return ReproductionRun(
        label=environment.label,
        environment=_result_environment(environment, command),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        exit_code_path=str(exit_code_path),
        run_log_path=str(run_log_path),
        build_log_path=str(build_log_path),
        exit_code=run["exit_code"],
        build_exit_code=0,
    )


def _run_command_line(spec: PhpReproductionSpec, environment: PhpEnvironmentDefinition) -> list[str]:
    include_path = os.pathsep.join(_include_paths(environment))
    return [
        environment.php_executable,
        *environment.php_args,
        "-d",
        f"include_path={include_path}",
        spec.client_file,
        *environment.program_args,
    ]


def _run_command(command: list[str], timeout_s: int, environment: PhpEnvironmentDefinition) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(environment.env)
    env["PHP_INCLUDE_PATH"] = os.pathsep.join(_include_paths(environment))
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
        return {"stdout": completed.stdout, "stderr": completed.stderr, "exit_code": completed.returncode}
    except FileNotFoundError as exc:
        return {"stdout": "", "stderr": f"{exc}\n", "exit_code": 127}
    except subprocess.TimeoutExpired as exc:
        return {
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTIMEOUT after {timeout_s}s\n",
            "exit_code": 124,
        }


def _build_log(environment: PhpEnvironmentDefinition) -> str:
    package_paths = os.pathsep.join(environment.package_paths) or "<none>"
    include_paths = os.pathsep.join(environment.include_paths) or "<none>"
    php_args = " ".join(environment.php_args) or "<none>"
    program_args = " ".join(environment.program_args) or "<none>"
    return (
        "offline PHP package path configured; using include_path instead of composer install\n"
        f"package_paths: {package_paths}\n"
        f"include_paths: {include_paths}\n"
        f"php_args: {php_args}\n"
        f"program_args: {program_args}\n"
        f"library: {environment.library}\n"
        f"version: {environment.version}\n"
    )


def _result_environment(environment: PhpEnvironmentDefinition, command: list[str]) -> PythonEnvironmentDefinition:
    return PythonEnvironmentDefinition(
        label=environment.label,
        library=environment.library,
        version=environment.version,
        install_command=command,
        python_executable=environment.php_executable,
        package_path=environment.package_path,
    )


def _dockerfile(spec: PhpReproductionSpec, environment: PhpEnvironmentDefinition) -> str:
    return "\n".join(
        [
            "FROM php:8.3-cli",
            "WORKDIR /case",
            f"# Candidate: {spec.candidate_id}",
            f"# Side: {environment.label}",
            f"# Intended dependency: {environment.library}:{environment.version}",
            f"# Offline package paths used by local runner: {os.pathsep.join(environment.package_paths)}",
            "# Run the configured client with include_path pointing at local package roots.",
            "",
        ]
    )


def _drop_reason(
    old_run: ReproductionRun,
    new_run: ReproductionRun,
    diff: ReproductionDiff,
) -> DropReason | None:
    if old_run.exit_code == 124 or new_run.exit_code == 124:
        return DropReason.TIMEOUT
    if old_run.exit_code == 127 or new_run.exit_code == 127:
        return DropReason.INSTALL_FAILED
    if old_run.exit_code != 0 or new_run.exit_code != 0:
        stderr = (
            Path(old_run.stderr_path).read_text(encoding="utf-8")
            + "\n"
            + Path(new_run.stderr_path).read_text(encoding="utf-8")
        )
        if "Failed opening required" in stderr or "Failed to open stream" in stderr:
            return DropReason.IMPORT_FAILED
        if old_run.exit_code != new_run.exit_code:
            return DropReason.HARD_BREAK
        return DropReason.CLIENT_RUNTIME_ERROR
    if not diff.changed:
        return DropReason.NO_BEHAVIOR_DIFF
    return None


def _include_paths(environment: PhpEnvironmentDefinition) -> list[str]:
    return [*environment.package_paths, *environment.include_paths]


def _metadata_paths(metadata: dict[str, Any], plural: str, singular: str) -> list[str]:
    value = metadata.get(plural)
    if value is None:
        value = metadata.get(singular)
    if not value:
        raise ValueError(f"PHP adapter plan requires metadata[{singular!r}]")
    return _metadata_list(value)


def _metadata_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    return [str(item) for item in value]


def _metadata_env(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("PHP env metadata must be a mapping")
    return {str(key): str(item) for key, item in value.items()}


def _metadata_optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _require_existing_path(path: Path, label: str) -> None:
    if not path.exists():
        raise ValueError(f"{label} not found: {path}")


def _require_existing_paths(paths: list[str], label: str) -> None:
    for raw_path in paths:
        _require_existing_path(Path(raw_path), label)


def _nonzero_exit(run: dict[str, Any]) -> bool:
    value = run.get("exit_code")
    return value not in (None, 0)
