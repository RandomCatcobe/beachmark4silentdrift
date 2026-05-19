"""Oracle generation for curated Python cases."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .curation import CurationDecision, load_curated_case
from .reproduction import load_reproduction_result
from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


@dataclass
class OracleSpec:
    case_id: str
    candidate_id: str
    case_path: str
    template: str = "pytest"
    hidden_test_path: str = ""
    expected_path: str = ""
    public_readme_path: str = ""
    starter_client_path: str = ""
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_yaml(self) -> str:
        data = asdict(self)
        return "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in data.items()) + "\n"


@dataclass
class OracleValidationResult:
    case_id: str
    mode: str
    pass_: bool
    exit_code: int
    log_path: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "case_id": self.case_id,
                "mode": self.mode,
                "pass": self.pass_,
                "exit_code": self.exit_code,
                "log_path": self.log_path,
            },
            ensure_ascii=False,
        )


def generate_pytest_oracle(case_path: Path, out_dir: Path) -> OracleSpec:
    case = load_curated_case(case_path)
    if case.decision != CurationDecision.ACCEPT:
        raise ValueError("oracle generation requires an accepted curated case")

    hidden_dir = out_dir / "hidden"
    public_dir = out_dir / "public"
    validation_dir = out_dir / "validation"
    hidden_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    spec = OracleSpec(
        case_id=case.case_id,
        candidate_id=case.candidate_id,
        case_path=str(case_path),
        hidden_test_path=str(hidden_dir / "test_behavior.py"),
        expected_path=str(hidden_dir / "expected.json"),
        public_readme_path=str(public_dir / "README.md"),
        starter_client_path=str(public_dir / "starter_client.py"),
    )
    expected_payload = _expected_payload(case_path, case)
    (out_dir / "oracle_spec.yaml").write_text(spec.to_yaml(), encoding="utf-8")
    (hidden_dir / "expected.json").write_text(
        json.dumps(expected_payload, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    (hidden_dir / "test_behavior.py").write_text(_hidden_test_template(), encoding="utf-8")
    (public_dir / "README.md").write_text(_public_readme(case.case_id), encoding="utf-8")
    (public_dir / "starter_client.py").write_text(_starter_client_template(), encoding="utf-8")
    return spec


def load_oracle_spec(path: Path) -> OracleSpec:
    data = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = json.loads(value.strip())
    return OracleSpec(**data)


def validate_pytest_oracle(oracle_spec_path: Path, mode: str) -> OracleValidationResult:
    if mode not in {"old", "new", "fixed"}:
        raise ValueError("mode must be one of: old, new, fixed")
    spec = load_oracle_spec(oracle_spec_path)
    hidden_test = Path(spec.hidden_test_path).resolve()
    if not hidden_test.exists():
        raise ValueError(f"hidden test not found: {hidden_test}")

    command = [sys.executable, "-m", "pytest", str(hidden_test)]
    completed = subprocess.run(
        command,
        cwd=str(hidden_test.parent),
        capture_output=True,
        text=True,
        check=False,
    )
    passed = completed.returncode == 0
    validation_dir = oracle_spec_path.parent / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    log_path = validation_dir / f"{mode}_{'pass' if passed else 'fail'}.log"
    log_path.write_text(
        "\n".join(
            [
                f"case_id: {spec.case_id}",
                f"mode: {mode}",
                f"exit_code: {completed.returncode}",
                "command: " + " ".join(command),
                "",
                "=== stdout ===",
                completed.stdout,
                "=== stderr ===",
                completed.stderr,
            ]
        ),
        encoding="utf-8",
    )
    return OracleValidationResult(
        case_id=spec.case_id,
        mode=mode,
        pass_=passed,
        exit_code=completed.returncode,
        log_path=str(log_path),
    )


def _hidden_test_template() -> str:
    return '''"""Hidden pytest oracle.

Verifies that the curated reproduction captured a real old/new behavior diff.
"""

import json
from pathlib import Path


def test_behavior_matches_expected():
    expected = json.loads((Path(__file__).parent / "expected.json").read_text())
    assert expected["keep"] is True
    assert expected["old_stdout"] != expected["new_stdout"]
    assert expected["diff_summary"]
'''


def _public_readme(case_id: str) -> str:
    return (
        f"# {case_id}\n\n"
        "Implement or adapt `starter_client.py` to reproduce the documented behavior.\n"
        "Public files intentionally omit oracle expectations.\n"
    )


def _starter_client_template() -> str:
    return (
        '"""Public starter client for the reproduced case."""\n\n'
        "def main():\n"
        "    raise NotImplementedError('fill in the public client entrypoint')\n\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )


def _resolve_link(base_file: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_file.parent / path


def _expected_payload(case_path: Path, case) -> dict:
    base = {
        "case_id": case.case_id,
        "candidate_id": case.candidate_id,
        "keep": case.keep,
        "diff_summary": "",
        "old_stdout": "",
        "new_stdout": "",
    }
    try:
        result = load_reproduction_result(_resolve_link(case_path, case.reproduction_result))
    except Exception:
        return base
    base.update(
        {
            "keep": result.keep,
            "diff_summary": result.diff.summary,
            "old_stdout": Path(result.old_run.stdout_path).read_text(encoding="utf-8"),
            "new_stdout": Path(result.new_run.stdout_path).read_text(encoding="utf-8"),
        }
    )
    return base
