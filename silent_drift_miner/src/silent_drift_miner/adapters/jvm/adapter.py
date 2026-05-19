"""Offline JVM reproduction adapter.

This module stays inside the JVM adapter boundary: it plans and runs local JVM
old/new inputs against one shared client and writes the existing
ReproductionResult-compatible JSON shape. JVM-specific special cases are
represented in the spec as source roots, classpath entries, resource
directories, JVM arguments, and program arguments.
"""
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
class JvmEnvironmentDefinition:
    label: str
    library: str
    version: str
    source_path: str
    source_paths: list[str] = field(default_factory=list)
    java_executable: str = "java"
    javac_executable: str = "javac"
    classpath: list[str] = field(default_factory=list)
    resource_paths: list[str] = field(default_factory=list)
    jvm_args: list[str] = field(default_factory=list)
    program_args: list[str] = field(default_factory=list)


@dataclass
class JvmReproductionSpec:
    candidate_id: str
    library: str
    old_version: str
    new_version: str
    client_file: str
    old_environment: JvmEnvironmentDefinition
    new_environment: JvmEnvironmentDefinition
    main_class: str = "DriftClient"
    ecosystem: str = "jvm"
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "JvmReproductionSpec":
        data = json.loads(text)
        if data.get("ecosystem") != "jvm":
            raise ValueError("JVM reproduction spec requires ecosystem='jvm'")
        data["old_environment"] = JvmEnvironmentDefinition(**data["old_environment"])
        data["new_environment"] = JvmEnvironmentDefinition(**data["new_environment"])
        return cls(**data)


def create_jvm_reproduction_spec(
    candidate_id: str,
    library: str,
    old_version: str,
    new_version: str,
    client_file: str | Path,
    old_source_path: str | Path | list[str | Path],
    new_source_path: str | Path | list[str | Path],
    main_class: str = "DriftClient",
    java_executable: str = "java",
    javac_executable: str = "javac",
    old_classpath: list[str] | None = None,
    new_classpath: list[str] | None = None,
    old_resource_paths: list[str] | None = None,
    new_resource_paths: list[str] | None = None,
    old_jvm_args: list[str] | None = None,
    new_jvm_args: list[str] | None = None,
    old_program_args: list[str] | None = None,
    new_program_args: list[str] | None = None,
) -> JvmReproductionSpec:
    old_source_paths = _metadata_list(old_source_path)
    new_source_paths = _metadata_list(new_source_path)
    if not old_source_paths:
        raise ValueError("old JVM source path is required")
    if not new_source_paths:
        raise ValueError("new JVM source path is required")
    return JvmReproductionSpec(
        candidate_id=candidate_id,
        library=library,
        old_version=old_version,
        new_version=new_version,
        client_file=str(Path(client_file)),
        main_class=main_class,
        old_environment=JvmEnvironmentDefinition(
            label="old",
            library=library,
            version=old_version,
            source_path=str(Path(old_source_paths[0])),
            source_paths=[str(Path(path)) for path in old_source_paths],
            java_executable=java_executable,
            javac_executable=javac_executable,
            classpath=list(old_classpath or []),
            resource_paths=list(old_resource_paths or []),
            jvm_args=list(old_jvm_args or []),
            program_args=list(old_program_args or []),
        ),
        new_environment=JvmEnvironmentDefinition(
            label="new",
            library=library,
            version=new_version,
            source_path=str(Path(new_source_paths[0])),
            source_paths=[str(Path(path)) for path in new_source_paths],
            java_executable=java_executable,
            javac_executable=javac_executable,
            classpath=list(new_classpath or []),
            resource_paths=list(new_resource_paths or []),
            jvm_args=list(new_jvm_args or []),
            program_args=list(new_program_args or []),
        ),
    )


def write_jvm_reproduction_spec(spec: JvmReproductionSpec, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(spec.to_json() + "\n", encoding="utf-8")


def load_jvm_reproduction_spec(path: Path) -> JvmReproductionSpec:
    return JvmReproductionSpec.from_json(path.read_text(encoding="utf-8"))


def run_jvm_reproduction_spec(
    spec: JvmReproductionSpec,
    out: Path,
    timeout_s: int = 30,
    build_timeout_s: int = 120,
) -> ReproductionResult:
    attempt_dir = allocate_attempt_dir(out)
    attempt_dir.mkdir(parents=True, exist_ok=False)
    write_jvm_reproduction_spec(spec, attempt_dir / "spec.json")

    old_run = _run_one_side(spec, spec.old_environment, attempt_dir / "old", timeout_s, build_timeout_s)
    new_run = _run_one_side(spec, spec.new_environment, attempt_dir / "new", timeout_s, build_timeout_s)
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


class JvmAdapter:
    """Adapter facade matching the EcosystemAdapter protocol."""

    contract = get_adapter_contract("jvm")

    def plan(self, request: AdapterPlanRequest) -> Path:
        if request.ecosystem.lower() != "jvm":
            raise ValueError(f"JVM adapter cannot plan ecosystem={request.ecosystem!r}")
        metadata = request.metadata
        old_source_paths = _metadata_paths(metadata, "old_source_paths", "old_source_path", "old_package_path")
        new_source_paths = _metadata_paths(metadata, "new_source_paths", "new_source_path", "new_package_path")
        _require_existing_path(Path(request.client_file), "JVM client file")
        _require_existing_paths(old_source_paths, "old JVM source path")
        _require_existing_paths(new_source_paths, "new JVM source path")
        shared_classpath = _metadata_list(metadata.get("classpath"))
        shared_resource_paths = _metadata_list(metadata.get("resource_paths"))
        old_resource_paths = shared_resource_paths + _metadata_list(metadata.get("old_resource_paths"))
        new_resource_paths = shared_resource_paths + _metadata_list(metadata.get("new_resource_paths"))
        _require_existing_paths(old_resource_paths, "old JVM resource path")
        _require_existing_paths(new_resource_paths, "new JVM resource path")
        shared_jvm_args = _metadata_list(metadata.get("jvm_args"))
        shared_program_args = _metadata_list(metadata.get("program_args"))
        spec = create_jvm_reproduction_spec(
            candidate_id=request.candidate_id,
            library=request.library,
            old_version=request.old_version,
            new_version=request.new_version,
            client_file=request.client_file,
            old_source_path=old_source_paths,
            new_source_path=new_source_paths,
            main_class=str(metadata.get("main_class", "DriftClient")),
            java_executable=str(metadata.get("java_executable", "java")),
            javac_executable=str(metadata.get("javac_executable", "javac")),
            old_classpath=shared_classpath + _metadata_list(metadata.get("old_classpath")),
            new_classpath=shared_classpath + _metadata_list(metadata.get("new_classpath")),
            old_resource_paths=old_resource_paths,
            new_resource_paths=new_resource_paths,
            old_jvm_args=shared_jvm_args + _metadata_list(metadata.get("old_jvm_args")),
            new_jvm_args=shared_jvm_args + _metadata_list(metadata.get("new_jvm_args")),
            old_program_args=shared_program_args + _metadata_list(metadata.get("old_program_args")),
            new_program_args=shared_program_args + _metadata_list(metadata.get("new_program_args")),
        )
        out_path = Path(request.out_path)
        write_jvm_reproduction_spec(spec, out_path)
        return out_path

    def run(self, request: AdapterRunRequest) -> Path:
        spec = load_jvm_reproduction_spec(Path(request.spec_path))
        result = run_jvm_reproduction_spec(
            spec,
            Path(request.out_dir),
            timeout_s=request.timeout_s,
            build_timeout_s=int(request.metadata.get("build_timeout_s", 120)),
        )
        return Path(result.attempt_dir) / "result.json"

    def classify_failure(self, run_payload: dict[str, Any]) -> str | None:
        existing = run_payload.get("drop_reason")
        if existing:
            return str(existing)
        old_run = run_payload.get("old_run") or {}
        new_run = run_payload.get("new_run") or {}
        if _nonzero_build(old_run) or _nonzero_build(new_run):
            return DropReason.INSTALL_FAILED.value
        if old_run.get("exit_code") == 124 or new_run.get("exit_code") == 124:
            return DropReason.TIMEOUT.value
        if _nonzero_exit(old_run) or _nonzero_exit(new_run):
            return DropReason.CLIENT_RUNTIME_ERROR.value
        diff = run_payload.get("diff") or {}
        if not any(diff.get(key) for key in ("stdout_changed", "stderr_changed", "exit_code_changed")):
            return DropReason.NO_BEHAVIOR_DIFF.value
        return None


def _run_one_side(
    spec: JvmReproductionSpec,
    environment: JvmEnvironmentDefinition,
    out_dir: Path,
    timeout_s: int,
    build_timeout_s: int,
) -> ReproductionRun:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    exit_code_path = out_dir / "exit_code.txt"
    run_log_path = out_dir / "run.log"
    build_log_path = out_dir / "build.log"
    dockerfile_path = out_dir / "Dockerfile"
    classes_dir = out_dir / "classes"
    classes_dir.mkdir()

    compile_command, source_error = _compile_command(spec, environment, classes_dir)
    build_exit_code: int | None
    build_log_parts = [_build_header(environment)]
    if source_error:
        build_exit_code = 1
        build_log_parts.append(source_error)
    else:
        build = _run_command(compile_command, build_timeout_s)
        build_exit_code = build["exit_code"]
        build_log_parts.extend(_command_log("compile", compile_command, build))

    dockerfile_path.write_text(_dockerfile(spec, environment), encoding="utf-8")
    build_log_path.write_text("\n".join(build_log_parts).rstrip() + "\n", encoding="utf-8")

    run_command = _run_command_line(spec, environment, classes_dir)
    run_log_path.write_text("command: " + " ".join(run_command) + "\n", encoding="utf-8")
    if build_exit_code not in (None, 0):
        stdout = ""
        stderr = f"client not run because build failed with exit code {build_exit_code}\n"
        exit_code = 1
    else:
        run = _run_command(run_command, timeout_s)
        stdout = run["stdout"]
        stderr = run["stderr"]
        exit_code = run["exit_code"]

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_code_path.write_text(str(exit_code) + "\n", encoding="utf-8")
    return ReproductionRun(
        label=environment.label,
        environment=_result_environment(environment, compile_command),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        exit_code_path=str(exit_code_path),
        run_log_path=str(run_log_path),
        build_log_path=str(build_log_path),
        exit_code=exit_code,
        build_exit_code=build_exit_code,
    )


def _compile_command(
    spec: JvmReproductionSpec,
    environment: JvmEnvironmentDefinition,
    classes_dir: Path,
) -> tuple[list[str], str | None]:
    try:
        sources = _java_sources(_source_paths(environment), Path(spec.client_file))
    except FileNotFoundError as exc:
        return [environment.javac_executable, "-d", str(classes_dir)], str(exc)
    command = [environment.javac_executable, "-d", str(classes_dir)]
    compile_classpath = [*environment.classpath, *environment.resource_paths]
    if compile_classpath:
        command.extend(["-cp", os.pathsep.join(compile_classpath)])
    command.extend(str(path) for path in sources)
    return command, None


def _java_sources(source_paths: list[Path], client_file: Path) -> list[Path]:
    if not client_file.exists():
        raise FileNotFoundError(f"JVM client file not found: {client_file}")
    sources = [client_file]
    for source_path in source_paths:
        if not source_path.exists():
            raise FileNotFoundError(f"JVM source path not found: {source_path}")
        if source_path.is_file():
            sources.append(source_path)
        else:
            sources.extend(path for path in source_path.rglob("*.java") if path.is_file())
    return sorted(set(sources), key=lambda path: str(path).lower())


def _run_command_line(
    spec: JvmReproductionSpec,
    environment: JvmEnvironmentDefinition,
    classes_dir: Path,
) -> list[str]:
    return [
        environment.java_executable,
        *environment.jvm_args,
        "-cp",
        os.pathsep.join(_runtime_classpath(environment, classes_dir)),
        spec.main_class,
        *environment.program_args,
    ]


def _run_command(command: list[str], timeout_s: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_code": completed.returncode,
        }
    except FileNotFoundError as exc:
        return {"stdout": "", "stderr": f"{exc}\n", "exit_code": 127}
    except subprocess.TimeoutExpired as exc:
        return {
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + f"\nTIMEOUT after {timeout_s}s\n",
            "exit_code": 124,
        }


def _command_log(label: str, command: list[str], result: dict[str, Any]) -> list[str]:
    return [
        f"{label} command: " + " ".join(command),
        f"{label} exit_code: {result['exit_code']}",
        "=== stdout ===",
        result["stdout"],
        "=== stderr ===",
        result["stderr"],
    ]


def _build_header(environment: JvmEnvironmentDefinition) -> str:
    return (
        "offline JVM source path configured; compiling with javac\n"
        f"source_paths: {', '.join(str(path) for path in _source_paths(environment))}\n"
        f"classpath: {os.pathsep.join(environment.classpath)}\n"
        f"resource_paths: {os.pathsep.join(environment.resource_paths)}\n"
        f"jvm_args: {' '.join(environment.jvm_args)}\n"
        f"program_args: {' '.join(environment.program_args)}\n"
        f"library: {environment.library}\n"
        f"version: {environment.version}"
    )


def _result_environment(
    environment: JvmEnvironmentDefinition,
    compile_command: list[str],
) -> PythonEnvironmentDefinition:
    return PythonEnvironmentDefinition(
        label=environment.label,
        library=environment.library,
        version=environment.version,
        install_command=compile_command,
        python_executable=environment.java_executable,
        package_path=environment.source_path,
    )


def _dockerfile(spec: JvmReproductionSpec, environment: JvmEnvironmentDefinition) -> str:
    return "\n".join(
        [
            "FROM eclipse-temurin:21",
            "WORKDIR /case",
            f"# Candidate: {spec.candidate_id}",
            f"# Side: {environment.label}",
            f"# Intended dependency: {environment.library}:{environment.version}",
            f"# Offline source paths used by local runner: {', '.join(str(path) for path in _source_paths(environment))}",
            f"# Runtime classpath extras: {os.pathsep.join(environment.classpath)}",
            f"# Runtime resource paths: {os.pathsep.join(environment.resource_paths)}",
            "# Compile source and client with javac, then run the configured main class.",
            "",
        ]
    )


def _drop_reason(
    old_run: ReproductionRun,
    new_run: ReproductionRun,
    diff: ReproductionDiff,
) -> DropReason | None:
    if (old_run.build_exit_code not in (None, 0)) or (new_run.build_exit_code not in (None, 0)):
        return DropReason.INSTALL_FAILED
    if old_run.exit_code == 124 or new_run.exit_code == 124:
        return DropReason.TIMEOUT
    if old_run.exit_code != 0 or new_run.exit_code != 0:
        stderr = (
            Path(old_run.stderr_path).read_text(encoding="utf-8")
            + "\n"
            + Path(new_run.stderr_path).read_text(encoding="utf-8")
        )
        if "ClassNotFoundException" in stderr or "NoClassDefFoundError" in stderr:
            return DropReason.IMPORT_FAILED
        if old_run.exit_code != new_run.exit_code:
            return DropReason.HARD_BREAK
        return DropReason.CLIENT_RUNTIME_ERROR
    if not diff.changed:
        return DropReason.NO_BEHAVIOR_DIFF
    return None


def _metadata_paths(metadata: dict[str, Any], plural: str, singular: str, fallback: str) -> list[str]:
    value = metadata.get(plural)
    if value is None:
        value = metadata.get(singular) or metadata.get(fallback)
    if not value:
        raise ValueError(f"JVM adapter plan requires metadata[{singular!r}]")
    return _metadata_list(value)


def _metadata_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    return [str(item) for item in value]


def _require_existing_path(path: Path, label: str) -> None:
    if not path.exists():
        raise ValueError(f"{label} not found: {path}")


def _require_existing_paths(paths: list[str], label: str) -> None:
    for raw_path in paths:
        _require_existing_path(Path(raw_path), label)


def _source_paths(environment: JvmEnvironmentDefinition) -> list[Path]:
    raw_paths = environment.source_paths or [environment.source_path]
    return [Path(path) for path in raw_paths]


def _runtime_classpath(environment: JvmEnvironmentDefinition, classes_dir: Path) -> list[str]:
    return [str(classes_dir), *environment.resource_paths, *environment.classpath]


def _nonzero_build(run: dict[str, Any]) -> bool:
    value = run.get("build_exit_code")
    return value not in (None, 0)


def _nonzero_exit(run: dict[str, Any]) -> bool:
    value = run.get("exit_code")
    return value not in (None, 0)
