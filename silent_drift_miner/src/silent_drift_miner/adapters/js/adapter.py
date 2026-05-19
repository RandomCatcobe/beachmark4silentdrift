"""Offline JavaScript/Node reproduction adapter."""
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
class JsEnvironmentDefinition:
    label: str
    library: str
    version: str
    package_path: str
    package_paths: list[str] = field(default_factory=list)
    node_executable: str = "node"
    module_paths: list[str] = field(default_factory=list)
    node_args: list[str] = field(default_factory=list)
    program_args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class JsReproductionSpec:
    candidate_id: str
    library: str
    old_version: str
    new_version: str
    client_file: str
    old_environment: JsEnvironmentDefinition
    new_environment: JsEnvironmentDefinition
    ecosystem: str = "js"
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "JsReproductionSpec":
        data = json.loads(text)
        if data.get("ecosystem") != "js":
            raise ValueError("JS reproduction spec requires ecosystem='js'")
        data["old_environment"] = JsEnvironmentDefinition(**data["old_environment"])
        data["new_environment"] = JsEnvironmentDefinition(**data["new_environment"])
        return cls(**data)


def create_js_reproduction_spec(
    candidate_id: str,
    library: str,
    old_version: str,
    new_version: str,
    client_file: str | Path,
    old_package_path: str | Path | list[str | Path],
    new_package_path: str | Path | list[str | Path],
    node_executable: str = "node",
    old_module_paths: list[str] | None = None,
    new_module_paths: list[str] | None = None,
    old_node_args: list[str] | None = None,
    new_node_args: list[str] | None = None,
    old_program_args: list[str] | None = None,
    new_program_args: list[str] | None = None,
    old_env: dict[str, str] | None = None,
    new_env: dict[str, str] | None = None,
) -> JsReproductionSpec:
    old_package_paths = _metadata_list(old_package_path)
    new_package_paths = _metadata_list(new_package_path)
    if not old_package_paths:
        raise ValueError("old JS package path is required")
    if not new_package_paths:
        raise ValueError("new JS package path is required")
    return JsReproductionSpec(
        candidate_id=candidate_id,
        library=library,
        old_version=old_version,
        new_version=new_version,
        client_file=str(Path(client_file)),
        old_environment=JsEnvironmentDefinition(
            label="old",
            library=library,
            version=old_version,
            package_path=str(Path(old_package_paths[0])),
            package_paths=[str(Path(path)) for path in old_package_paths],
            node_executable=node_executable,
            module_paths=list(old_module_paths or []),
            node_args=list(old_node_args or []),
            program_args=list(old_program_args or []),
            env=dict(old_env or {}),
        ),
        new_environment=JsEnvironmentDefinition(
            label="new",
            library=library,
            version=new_version,
            package_path=str(Path(new_package_paths[0])),
            package_paths=[str(Path(path)) for path in new_package_paths],
            node_executable=node_executable,
            module_paths=list(new_module_paths or []),
            node_args=list(new_node_args or []),
            program_args=list(new_program_args or []),
            env=dict(new_env or {}),
        ),
    )


def write_js_reproduction_spec(spec: JsReproductionSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(spec.to_json() + "\n", encoding="utf-8")


def load_js_reproduction_spec(path: Path) -> JsReproductionSpec:
    return JsReproductionSpec.from_json(path.read_text(encoding="utf-8"))


def run_js_reproduction_spec(
    spec: JsReproductionSpec,
    out: Path,
    timeout_s: int = 30,
) -> ReproductionResult:
    attempt_dir = allocate_attempt_dir(out)
    attempt_dir.mkdir(parents=True, exist_ok=False)
    write_js_reproduction_spec(spec, attempt_dir / "spec.json")

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


class JsAdapter:
    """Adapter facade matching the EcosystemAdapter protocol."""

    contract = get_adapter_contract("js")

    def plan(self, request: AdapterPlanRequest) -> Path:
        if request.ecosystem.lower() != "js":
            raise ValueError(f"JS adapter cannot plan ecosystem={request.ecosystem!r}")
        metadata = request.metadata
        old_package_paths = _metadata_paths(metadata, "old_package_paths", "old_package_path")
        new_package_paths = _metadata_paths(metadata, "new_package_paths", "new_package_path")
        _require_existing_path(Path(request.client_file), "JS client file")
        _require_existing_paths(old_package_paths, "old JS package path")
        _require_existing_paths(new_package_paths, "new JS package path")
        shared_module_paths = _metadata_list(metadata.get("module_paths"))
        old_module_paths = shared_module_paths + _metadata_list(metadata.get("old_module_paths"))
        new_module_paths = shared_module_paths + _metadata_list(metadata.get("new_module_paths"))
        _require_existing_paths(old_module_paths, "old JS module path")
        _require_existing_paths(new_module_paths, "new JS module path")
        shared_node_args = _metadata_list(metadata.get("node_args"))
        shared_program_args = _metadata_list(metadata.get("program_args"))
        shared_env = _metadata_env(metadata.get("env"))
        spec = create_js_reproduction_spec(
            candidate_id=request.candidate_id,
            library=request.library,
            old_version=request.old_version,
            new_version=request.new_version,
            client_file=request.client_file,
            old_package_path=old_package_paths,
            new_package_path=new_package_paths,
            node_executable=str(metadata.get("node_executable", "node")),
            old_module_paths=old_module_paths,
            new_module_paths=new_module_paths,
            old_node_args=shared_node_args + _metadata_list(metadata.get("old_node_args")),
            new_node_args=shared_node_args + _metadata_list(metadata.get("new_node_args")),
            old_program_args=shared_program_args + _metadata_list(metadata.get("old_program_args")),
            new_program_args=shared_program_args + _metadata_list(metadata.get("new_program_args")),
            old_env={**shared_env, **_metadata_env(metadata.get("old_env"))},
            new_env={**shared_env, **_metadata_env(metadata.get("new_env"))},
        )
        out_path = Path(request.out_path)
        write_js_reproduction_spec(spec, out_path)
        return out_path

    def run(self, request: AdapterRunRequest) -> Path:
        spec = load_js_reproduction_spec(Path(request.spec_path))
        result = run_js_reproduction_spec(spec, Path(request.out_dir), timeout_s=request.timeout_s)
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
    spec: JsReproductionSpec,
    environment: JsEnvironmentDefinition,
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


def _run_command_line(spec: JsReproductionSpec, environment: JsEnvironmentDefinition) -> list[str]:
    return [
        environment.node_executable,
        *environment.node_args,
        spec.client_file,
        *environment.program_args,
    ]


def _run_command(command: list[str], timeout_s: int, environment: JsEnvironmentDefinition) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(environment.env)
    node_path = os.pathsep.join([*environment.package_paths, *environment.module_paths])
    existing = env.get("NODE_PATH")
    if node_path:
        env["NODE_PATH"] = node_path if not existing else node_path + os.pathsep + existing
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


def _build_log(environment: JsEnvironmentDefinition) -> str:
    return (
        "offline JS package path configured; using NODE_PATH instead of npm install\n"
        f"package_paths: {os.pathsep.join(environment.package_paths)}\n"
        f"module_paths: {os.pathsep.join(environment.module_paths)}\n"
        f"node_args: {' '.join(environment.node_args)}\n"
        f"program_args: {' '.join(environment.program_args)}\n"
        f"library: {environment.library}\n"
        f"version: {environment.version}\n"
    )


def _result_environment(environment: JsEnvironmentDefinition, command: list[str]) -> PythonEnvironmentDefinition:
    return PythonEnvironmentDefinition(
        label=environment.label,
        library=environment.library,
        version=environment.version,
        install_command=command,
        python_executable=environment.node_executable,
        package_path=environment.package_path,
    )


def _dockerfile(spec: JsReproductionSpec, environment: JsEnvironmentDefinition) -> str:
    return "\n".join(
        [
            "FROM node:22-slim",
            "WORKDIR /case",
            f"# Candidate: {spec.candidate_id}",
            f"# Side: {environment.label}",
            f"# Intended dependency: {environment.library}@{environment.version}",
            f"# Offline package paths used by local runner: {os.pathsep.join(environment.package_paths)}",
            "# Run the configured client with NODE_PATH pointing at local package roots.",
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
        if "Cannot find module" in stderr or "ERR_MODULE_NOT_FOUND" in stderr:
            return DropReason.IMPORT_FAILED
        if old_run.exit_code != new_run.exit_code:
            return DropReason.HARD_BREAK
        return DropReason.CLIENT_RUNTIME_ERROR
    if not diff.changed:
        return DropReason.NO_BEHAVIOR_DIFF
    return None


def _metadata_paths(metadata: dict[str, Any], plural: str, singular: str) -> list[str]:
    value = metadata.get(plural)
    if value is None:
        value = metadata.get(singular)
    if not value:
        raise ValueError(f"JS adapter plan requires metadata[{singular!r}]")
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
        raise ValueError("JS env metadata must be a mapping")
    return {str(key): str(item) for key, item in value.items()}


def _require_existing_path(path: Path, label: str) -> None:
    if not path.exists():
        raise ValueError(f"{label} not found: {path}")


def _require_existing_paths(paths: list[str], label: str) -> None:
    for raw_path in paths:
        _require_existing_path(Path(raw_path), label)


def _nonzero_exit(run: dict[str, Any]) -> bool:
    value = run.get("exit_code")
    return value not in (None, 0)
