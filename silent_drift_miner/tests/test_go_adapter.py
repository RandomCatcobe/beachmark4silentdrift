from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from silent_drift_miner.adapter_contracts import AdapterPlanRequest, AdapterRunRequest
from silent_drift_miner.adapters.go import GoAdapter
from silent_drift_miner.audit import audit_package
from silent_drift_miner.bench import create_benchmark_package
from silent_drift_miner.cli import main
from silent_drift_miner.curation import create_curated_case, write_curated_case
from silent_drift_miner.oracle import generate_pytest_oracle


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "cases" / "go_toy_drift"


def test_go_adapter_plans_and_runs_offline_toy_case(tmp_path) -> None:
    go = _fake_go(tmp_path)
    adapter = GoAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="go-toy-drift",
            ecosystem="go",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "go_executable": str(go),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "go-toy-drift"
    assert payload["keep"] is True
    assert payload["drop_reason"] is None
    assert payload["diff"]["summary"] == "stdout changed"
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"
    assert payload["old_run"]["environment"]["library"] == "toy-drift"


def test_go_adapter_result_flows_through_oracle_package_and_audit(tmp_path) -> None:
    go = _fake_go(tmp_path)
    adapter = GoAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="go-toy-drift",
            ecosystem="go",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "go_executable": str(go),
            },
        )
    )
    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    case = create_curated_case(
        result_path,
        "accept",
        "go_toy_drift",
        source_url="https://example.com/go-toy-release-notes",
        source_excerpt="Default behavior changed.",
        retrieved_at="2026-05-19",
        ecosystem="go",
        version_old="1.0.0",
        version_new="2.0.0",
        api_surface=["ToyDrift.Value"],
        review_notes="Synthetic Go fixture for adapter lifecycle coverage.",
    )
    case_path = tmp_path / "case.yaml"
    oracle_dir = tmp_path / "oracle"
    packages_dir = tmp_path / "packages"
    write_curated_case(case, case_path)
    oracle = generate_pytest_oracle(case_path, oracle_dir)
    package_dir = create_benchmark_package(case_path, Path(oracle_dir / "oracle_spec.yaml"), ["L1"], packages_dir)

    audit = audit_package(package_dir)

    assert oracle.case_id == "go_toy_drift"
    assert audit["pass"] is True
    assert (package_dir / "reproduction_result.json").exists()
    assert not (package_dir / "hidden").exists()


def test_go_adapter_records_go_inputs(tmp_path) -> None:
    go = _fake_go(tmp_path)
    module_path = tmp_path / "shared_module"
    module_path.mkdir()
    adapter = GoAdapter()

    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="go-inputs",
            ecosystem="go",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "module_paths": [str(module_path)],
                "go_args": ["-tags", "toy"],
                "program_args": ["--format", "plain"],
                "go_executable": str(go),
                "no_network": False,
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    old_run_log = Path(result["old_run"]["run_log_path"]).read_text(encoding="utf-8")
    old_build_log = Path(result["old_run"]["build_log_path"]).read_text(encoding="utf-8")
    assert spec_payload["old_environment"]["module_paths"] == [str(module_path)]
    assert spec_payload["old_environment"]["go_args"] == ["-tags", "toy"]
    assert spec_payload["old_environment"]["program_args"] == ["--format", "plain"]
    assert spec_payload["old_environment"]["no_network"] is False
    assert "-tags toy" in old_run_log
    assert "--format plain" in old_run_log
    assert str(module_path) in old_build_log
    assert result["keep"] is True


def test_go_reproduce_cli_plans_and_runs_go_spec(tmp_path) -> None:
    go = _fake_go(tmp_path)
    spec_path = tmp_path / "spec.json"
    out_dir = tmp_path / "repro"

    assert main(
        [
            "reproduce",
            "plan",
            "--ecosystem",
            "go",
            "--candidate-id",
            "go-cli-toy",
            "--library",
            "toy-drift",
            "--old-version",
            "1.0.0",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(FIXTURE_ROOT / "client"),
            "--old-package-path",
            str(FIXTURE_ROOT / "old"),
            "--new-package-path",
            str(FIXTURE_ROOT / "new"),
            "--go-executable",
            str(go),
            "--out",
            str(spec_path),
        ]
    ) == 0

    assert main(["reproduce", "run", "--spec", str(spec_path), "--out", str(out_dir)]) == 0

    result = json.loads((out_dir / "attempt_001" / "result.json").read_text(encoding="utf-8"))
    assert result["candidate_id"] == "go-cli-toy"
    assert result["keep"] is True
    assert result["drop_reason"] is None


def test_go_adapter_classifies_missing_tool_as_install_failed(tmp_path) -> None:
    adapter = GoAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="go-missing-tool",
            ecosystem="go",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "go_executable": "definitely-missing-go",
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is False
    assert payload["drop_reason"] == "install_failed"
    assert adapter.classify_failure(payload) == "install_failed"


def test_go_adapter_rejects_non_go_plan(tmp_path) -> None:
    adapter = GoAdapter()

    with pytest.raises(ValueError, match="ecosystem"):
        adapter.plan(
            AdapterPlanRequest(
                candidate_id="wrong-ecosystem",
                ecosystem="python",
                library="toy-drift",
                old_version="1.0.0",
                new_version="2.0.0",
                client_file=str(FIXTURE_ROOT / "client"),
                out_path=str(tmp_path / "spec.json"),
                metadata={
                    "old_package_path": str(FIXTURE_ROOT / "old"),
                    "new_package_path": str(FIXTURE_ROOT / "new"),
                },
            )
        )


@pytest.mark.skipif(shutil.which("go") is None, reason="real Go smoke test requires go in PATH")
def test_go_adapter_runs_toy_case_with_real_go(tmp_path) -> None:
    adapter = GoAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="go-real-toy",
            ecosystem="go",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_package_path": str(FIXTURE_ROOT / "old"),
                "new_package_path": str(FIXTURE_ROOT / "new"),
                "go_executable": shutil.which("go"),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is True
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"


def _fake_go(tmp_path: Path) -> Path:
    if sys.platform == "win32":
        go = tmp_path / "go.cmd"
        go.write_text(
            "\r\n".join(
                [
                    "@echo off",
                    "echo %GO_ADAPTER_PACKAGE_PATHS% | findstr /i \"old\" >NUL",
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
        return go

    go = tmp_path / "go"
    go.write_text(
        "#!/usr/bin/env sh\n"
        "case \"$GO_ADAPTER_PACKAGE_PATHS\" in\n"
        "  *old*) echo old ;;\n"
        "  *) echo new ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    os.chmod(go, 0o755)
    return go
