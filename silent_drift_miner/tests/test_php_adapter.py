from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from silent_drift_miner.adapter_contracts import AdapterPlanRequest, AdapterRunRequest
from silent_drift_miner.adapters.php import PhpAdapter
from silent_drift_miner.audit import audit_package
from silent_drift_miner.bench import create_benchmark_package
from silent_drift_miner.cli import main
from silent_drift_miner.curation import create_curated_case, write_curated_case
from silent_drift_miner.oracle import generate_pytest_oracle


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "cases" / "php_toy_drift"


def test_php_adapter_plans_and_runs_offline_toy_case(tmp_path) -> None:
    php = _fake_php(tmp_path)
    adapter = PhpAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-toy-drift",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "php_executable": str(php),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "php-toy-drift"
    assert payload["keep"] is True
    assert payload["drop_reason"] is None
    assert payload["diff"]["summary"] == "stdout changed"
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"
    assert payload["old_run"]["environment"]["library"] == "toy-drift"


def test_php_adapter_result_flows_through_oracle_package_and_audit(tmp_path) -> None:
    php = _fake_php(tmp_path)
    adapter = PhpAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-toy-drift",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "php_executable": str(php),
            },
        )
    )
    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    case = create_curated_case(
        result_path,
        "accept",
        "php_toy_drift",
        source_url="https://example.com/php-toy-release-notes",
        source_excerpt="Default behavior changed.",
        retrieved_at="2026-05-19",
        ecosystem="php",
        version_old="1.0.0",
        version_new="2.0.0",
        api_surface=["ToyDrift\\value"],
        review_notes="Synthetic PHP fixture for adapter lifecycle coverage.",
    )
    case_path = tmp_path / "case.yaml"
    oracle_dir = tmp_path / "oracle"
    packages_dir = tmp_path / "packages"
    write_curated_case(case, case_path)
    oracle = generate_pytest_oracle(case_path, oracle_dir)
    package_dir = create_benchmark_package(case_path, Path(oracle_dir / "oracle_spec.yaml"), ["L1"], packages_dir)

    audit = audit_package(package_dir)

    assert oracle.case_id == "php_toy_drift"
    assert audit["pass"] is True
    assert (package_dir / "reproduction_result.json").exists()
    assert not (package_dir / "hidden").exists()


def test_php_adapter_records_php_inputs(tmp_path) -> None:
    php = _fake_php(tmp_path)
    include_path = tmp_path / "shared_include"
    include_path.mkdir()
    adapter = PhpAdapter()

    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-inputs",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "include_paths": [str(include_path)],
                "php_args": ["-d", "display_errors=1"],
                "program_args": ["--format", "plain"],
                "php_executable": str(php),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    old_run_log = Path(result["old_run"]["run_log_path"]).read_text(encoding="utf-8")
    old_build_log = Path(result["old_run"]["build_log_path"]).read_text(encoding="utf-8")
    assert spec_payload["old_environment"]["include_paths"] == [str(include_path)]
    assert spec_payload["old_environment"]["php_args"] == ["-d", "display_errors=1"]
    assert spec_payload["old_environment"]["program_args"] == ["--format", "plain"]
    assert "display_errors=1" in old_run_log
    assert "--format plain" in old_run_log
    assert str(include_path) in old_build_log
    assert result["keep"] is True


def test_php_adapter_supports_side_specific_php_executables(tmp_path) -> None:
    old_php = _fake_php_with_output(tmp_path, "old-php", "old")
    new_php = _fake_php_with_output(tmp_path, "new-php", "new")
    adapter = PhpAdapter()

    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-side-specific-executables",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "php_executable": "unused-shared-php",
                "old_php_executable": str(old_php),
                "new_php_executable": str(new_php),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert spec_payload["old_environment"]["php_executable"] == str(old_php)
    assert spec_payload["new_environment"]["php_executable"] == str(new_php)
    assert Path(result["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(result["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"
    assert result["keep"] is True


def test_php_reproduce_cli_plans_and_runs_php_spec(tmp_path) -> None:
    php = _fake_php(tmp_path)
    spec_path = tmp_path / "spec.json"
    out_dir = tmp_path / "repro"

    assert main(
        [
            "reproduce",
            "plan",
            "--ecosystem",
            "php",
            "--candidate-id",
            "php-cli-toy",
            "--library",
            "toy-drift",
            "--old-version",
            "1.0.0",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(FIXTURE_ROOT / "client.php"),
            "--old-package-path",
            str(FIXTURE_ROOT / "old"),
            "--new-package-path",
            str(FIXTURE_ROOT / "new"),
            "--php-executable",
            str(php),
            "--out",
            str(spec_path),
        ]
    ) == 0

    assert main(["reproduce", "run", "--spec", str(spec_path), "--out", str(out_dir)]) == 0

    result = json.loads((out_dir / "attempt_001" / "result.json").read_text(encoding="utf-8"))
    assert result["candidate_id"] == "php-cli-toy"
    assert result["keep"] is True
    assert result["drop_reason"] is None


def test_php_adapter_classifies_missing_tool_as_install_failed(tmp_path) -> None:
    adapter = PhpAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-missing-tool",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "php_executable": "definitely-missing-php",
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is False
    assert payload["drop_reason"] == "install_failed"
    assert adapter.classify_failure(payload) == "install_failed"


def test_php_adapter_rejects_non_php_plan(tmp_path) -> None:
    adapter = PhpAdapter()

    with pytest.raises(ValueError, match="ecosystem"):
        adapter.plan(
            AdapterPlanRequest(
                candidate_id="wrong-ecosystem",
                ecosystem="python",
                library="toy-drift",
                old_version="1.0.0",
                new_version="2.0.0",
                client_file=str(FIXTURE_ROOT / "client.php"),
                out_path=str(tmp_path / "spec.json"),
                metadata={
                    "old_package_path": str(FIXTURE_ROOT / "old"),
                    "new_package_path": str(FIXTURE_ROOT / "new"),
                },
            )
        )


@pytest.mark.skipif(shutil.which("php") is None, reason="real PHP smoke test requires php in PATH")
def test_php_adapter_runs_toy_case_with_real_php(tmp_path) -> None:
    adapter = PhpAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="php-real-toy",
            ecosystem="php",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client.php"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "php_executable": shutil.which("php"),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is True
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"


def _fake_php(tmp_path: Path) -> Path:
    if sys.platform == "win32":
        php = tmp_path / "php.cmd"
        php.write_text(
            "\r\n".join(
                [
                    "@echo off",
                    "echo %PHP_INCLUDE_PATH% | findstr /i \"old\" >NUL",
                    "if %ERRORLEVEL%==0 (",
                    "  echo old",
                    ") else (",
                    "  echo new",
                    ")",
                    "exit /b 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return php

    php = tmp_path / "php"
    php.write_text(
        "#!/usr/bin/env sh\n"
        "case \"$PHP_INCLUDE_PATH\" in\n"
        "  *old*) echo old ;;\n"
        "  *) echo new ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    os.chmod(php, 0o755)
    return php


def _fake_php_with_output(tmp_path: Path, name: str, output: str) -> Path:
    if sys.platform == "win32":
        php = tmp_path / f"{name}.cmd"
        php.write_text(f"@echo off\r\necho {output}\r\nexit /b 0\r\n", encoding="utf-8")
        return php

    php = tmp_path / name
    php.write_text(f"#!/usr/bin/env sh\necho {output}\n", encoding="utf-8")
    os.chmod(php, 0o755)
    return php
