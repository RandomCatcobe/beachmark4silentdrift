"""Python reproduction spec and result schemas."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field, replace
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
    package_path: Optional[str] = None


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
    build_exit_code: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReproductionRun":
        data = dict(data)
        data["environment"] = PythonEnvironmentDefinition(**data["environment"])
        return cls(**data)


@dataclass
class ReproductionDiff:
    stdout_changed: bool = False
    stderr_changed: bool = False
    exit_code_changed: bool = False
    summary: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def changed(self) -> bool:
        return self.stdout_changed or self.stderr_changed or self.exit_code_changed


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

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, default=_json_default)

    @classmethod
    def from_json(cls, text: str) -> "ReproductionResult":
        data = json.loads(text)
        data["old_run"] = ReproductionRun.from_dict(data["old_run"])
        data["new_run"] = ReproductionRun.from_dict(data["new_run"])
        data["diff"] = ReproductionDiff(**data["diff"])
        if data.get("drop_reason") is not None:
            data["drop_reason"] = DropReason(data["drop_reason"])
        return cls(**data)


def create_reproduction_spec(
    candidate_id: str,
    library: str,
    old_version: str,
    new_version: str,
    client_file: str | Path,
    old_package_path: str | Path | None = None,
    new_package_path: str | Path | None = None,
    old_python_executable: str = "python",
    new_python_executable: str = "python",
    extra_packages: list[str] | None = None,
    old_extra_packages: list[str] | None = None,
    new_extra_packages: list[str] | None = None,
) -> ReproductionSpec:
    shared_packages = list(extra_packages or [])
    old_packages = shared_packages + list(old_extra_packages or []) + [f"{library}=={old_version}"]
    new_packages = shared_packages + list(new_extra_packages or []) + [f"{library}=={new_version}"]
    old_environment = PythonEnvironmentDefinition(
        label="old",
        library=library,
        version=old_version,
        install_command=["python", "-m", "pip", "install", *old_packages],
        python_executable=old_python_executable,
        package_path=str(Path(old_package_path)) if old_package_path else None,
    )
    new_environment = PythonEnvironmentDefinition(
        label="new",
        library=library,
        version=new_version,
        install_command=["python", "-m", "pip", "install", *new_packages],
        python_executable=new_python_executable,
        package_path=str(Path(new_package_path)) if new_package_path else None,
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


def load_reproduction_result(path: Path) -> ReproductionResult:
    return ReproductionResult.from_json(path.read_text(encoding="utf-8"))


def run_reproduction_spec(
    spec: ReproductionSpec,
    out: Path,
    timeout_s: int = 30,
    install: bool = False,
    venv_root: Path | None = None,
    build_timeout_s: int = 300,
) -> ReproductionResult:
    attempt_dir = allocate_attempt_dir(out)
    attempt_dir.mkdir(parents=True, exist_ok=False)
    write_reproduction_spec(spec, attempt_dir / "spec.json")

    old_run = _run_one_side(
        spec,
        spec.old_environment,
        attempt_dir / "old",
        timeout_s,
        install=install,
        venv_root=venv_root,
        build_timeout_s=build_timeout_s,
    )
    new_run = _run_one_side(
        spec,
        spec.new_environment,
        attempt_dir / "new",
        timeout_s,
        install=install,
        venv_root=venv_root,
        build_timeout_s=build_timeout_s,
    )
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


def allocate_attempt_dir(out: Path) -> Path:
    out = Path(out)
    if re.fullmatch(r"attempt_\d{3}", out.name):
        root = out.parent
        if not out.exists():
            return out
    else:
        root = out

    root.mkdir(parents=True, exist_ok=True)
    for index in range(1, 1000):
        candidate = root / f"attempt_{index:03d}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"too many attempts under {root}")


def build_diff(old_run: ReproductionRun, new_run: ReproductionRun) -> ReproductionDiff:
    old_stdout = Path(old_run.stdout_path).read_text(encoding="utf-8")
    new_stdout = Path(new_run.stdout_path).read_text(encoding="utf-8")
    old_stderr = Path(old_run.stderr_path).read_text(encoding="utf-8")
    new_stderr = Path(new_run.stderr_path).read_text(encoding="utf-8")

    old_behavior_stdout = _normalize_stdout_for_behavior(old_stdout)
    new_behavior_stdout = _normalize_stdout_for_behavior(new_stdout)
    raw_stdout_changed = old_stdout != new_stdout
    stdout_changed = old_behavior_stdout != new_behavior_stdout
    stderr_changed = old_stderr != new_stderr
    exit_code_changed = old_run.exit_code != new_run.exit_code
    changed_bits = []
    if stdout_changed:
        changed_bits.append("stdout changed")
    if stderr_changed:
        changed_bits.append("stderr changed")
    if exit_code_changed:
        changed_bits.append("exit code changed")
    summary = ", ".join(changed_bits) if changed_bits else "no observed difference"
    return ReproductionDiff(
        stdout_changed=stdout_changed,
        stderr_changed=stderr_changed,
        exit_code_changed=exit_code_changed,
        summary=summary,
        details={
            "old_exit_code": old_run.exit_code,
            "new_exit_code": new_run.exit_code,
            "raw_stdout_changed": raw_stdout_changed,
            "stdout_compared_after_version_metadata": (
                old_behavior_stdout != old_stdout or new_behavior_stdout != new_stdout
            ),
        },
    )


def _normalize_stdout_for_behavior(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return text

    try:
        return json.dumps(_strip_version_metadata(json.loads(stripped)), ensure_ascii=False, sort_keys=True)
    except json.JSONDecodeError:
        pass

    normalized_lines: list[Any] = []
    for line in text.splitlines():
        if not line.strip():
            normalized_lines.append(line)
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            return text
        normalized_lines.append(_strip_version_metadata(parsed))
    return json.dumps(normalized_lines, ensure_ascii=False, sort_keys=True)


def _strip_version_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_version_metadata(item)
            for key, item in value.items()
            if key != "version" and not key.endswith("_version")
        }
    if isinstance(value, list):
        return [_strip_version_metadata(item) for item in value]
    return value


def _run_one_side(
    spec: ReproductionSpec,
    environment: PythonEnvironmentDefinition,
    out_dir: Path,
    timeout_s: int,
    install: bool = False,
    venv_root: Path | None = None,
    build_timeout_s: int = 300,
) -> ReproductionRun:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    exit_code_path = out_dir / "exit_code.txt"
    run_log_path = out_dir / "run.log"
    build_log_path = out_dir / "build.log"
    dockerfile_path = out_dir / "Dockerfile"

    build_exit_code: int | None = None
    build_log = _build_log(environment, install=install)
    run_environment = environment
    dockerfile_path.write_text(_dockerfile(spec, environment), encoding="utf-8")
    env = os.environ.copy()
    if environment.package_path:
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(Path(environment.package_path))
            if not existing
            else str(Path(environment.package_path)) + os.pathsep + existing
        )

    if install and not environment.package_path:
        build = _prepare_installed_environment(spec, environment, out_dir, venv_root, build_timeout_s)
        build_log += build["log"]
        build_exit_code = build["exit_code"]
        if build["python_executable"]:
            run_environment = replace(environment, python_executable=build["python_executable"])

    build_log_path.write_text(build_log, encoding="utf-8")
    command = [run_environment.python_executable, spec.client_file]
    run_log_path.write_text("command: " + " ".join(command) + "\n", encoding="utf-8")

    if build_exit_code not in (None, 0):
        stdout = ""
        stderr = f"client not run because build failed with exit code {build_exit_code}\n"
        exit_code = 1
    else:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_s}s\n"
            exit_code = 124

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_code_path.write_text(str(exit_code) + "\n", encoding="utf-8")
    return ReproductionRun(
        label=environment.label,
        environment=run_environment,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        exit_code_path=str(exit_code_path),
        run_log_path=str(run_log_path),
        build_log_path=str(build_log_path),
        exit_code=exit_code,
        build_exit_code=build_exit_code,
    )


def _build_log(environment: PythonEnvironmentDefinition, install: bool = False) -> str:
    if environment.package_path:
        return (
            "offline package path configured; using PYTHONPATH instead of pip install\n"
            f"package_path: {environment.package_path}\n"
        )
    if install:
        return "isolated install requested; creating a virtual environment\n"
    return "no build step configured; running client in current Python environment\n"


def _prepare_installed_environment(
    spec: ReproductionSpec,
    environment: PythonEnvironmentDefinition,
    out_dir: Path,
    venv_root: Path | None,
    build_timeout_s: int,
) -> dict[str, Any]:
    venv_dir = (
        _venv_dir(Path(venv_root), spec, environment)
        if venv_root
        else out_dir / ".venv"
    )
    python_path = _venv_python(venv_dir)
    lines = [
        f"venv_dir: {venv_dir}",
        f"base_python: {environment.python_executable}",
    ]

    try:
        create = subprocess.run(
            [environment.python_executable, "-m", "venv", str(venv_dir)],
            capture_output=True,
            text=True,
            timeout=build_timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        lines.extend(
            [
                "venv create timed out",
                exc.stdout or "",
                exc.stderr or "",
            ]
        )
        return {"python_executable": None, "exit_code": 124, "log": "\n".join(lines) + "\n"}

    lines.extend(
        [
            "venv create command: "
            + " ".join([environment.python_executable, "-m", "venv", str(venv_dir)]),
            f"venv create exit_code: {create.returncode}",
            create.stdout,
            create.stderr,
        ]
    )
    if create.returncode != 0:
        return {"python_executable": None, "exit_code": create.returncode, "log": "\n".join(lines) + "\n"}

    install_command = _venv_install_command(environment, python_path)
    try:
        install = subprocess.run(
            install_command,
            capture_output=True,
            text=True,
            timeout=build_timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        lines.extend(
            [
                "install command timed out",
                "install command: " + " ".join(install_command),
                exc.stdout or "",
                exc.stderr or "",
            ]
        )
        return {"python_executable": str(python_path), "exit_code": 124, "log": "\n".join(lines) + "\n"}

    lines.extend(
        [
            "install command: " + " ".join(install_command),
            f"install exit_code: {install.returncode}",
            install.stdout,
            install.stderr,
        ]
    )
    return {"python_executable": str(python_path), "exit_code": install.returncode, "log": "\n".join(lines) + "\n"}


def _venv_dir(root: Path, spec: ReproductionSpec, environment: PythonEnvironmentDefinition) -> Path:
    return root / _slug(spec.candidate_id) / f"{environment.label}-{_slug(environment.library)}-{_slug(environment.version)}"


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_install_command(environment: PythonEnvironmentDefinition, python_path: Path) -> list[str]:
    command = list(environment.install_command)
    if command:
        executable = Path(command[0]).name.lower()
        if executable in {"python", "python.exe", "python3", "python3.exe"}:
            command[0] = str(python_path)
            return command
    return [str(python_path), "-m", "pip", "install", f"{environment.library}=={environment.version}"]


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "value"


def _dockerfile(spec: ReproductionSpec, environment: PythonEnvironmentDefinition) -> str:
    lines = [
        "FROM python:3.12-slim",
        "WORKDIR /case",
        f"# Candidate: {spec.candidate_id}",
        f"# Side: {environment.label}",
        f"# Intended dependency: {environment.library}=={environment.version}",
    ]
    if environment.package_path:
        lines.append(f"# Offline package path used by local runner: {environment.package_path}")
    else:
        lines.append("RUN " + " ".join(environment.install_command))
    lines.extend(
        [
            "COPY client.py /case/client.py",
            "CMD [\"python\", \"/case/client.py\"]",
            "",
        ]
    )
    return "\n".join(lines)


def _drop_reason(
    old_run: ReproductionRun,
    new_run: ReproductionRun,
    diff: ReproductionDiff,
) -> Optional[DropReason]:
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
        if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
            return DropReason.IMPORT_FAILED
        if old_run.exit_code != new_run.exit_code:
            return DropReason.HARD_BREAK
        return DropReason.CLIENT_RUNTIME_ERROR
    if not diff.changed:
        return DropReason.NO_BEHAVIOR_DIFF
    return None


def _json_default(value):
    if isinstance(value, Enum):
        return value.value
    return str(value)
