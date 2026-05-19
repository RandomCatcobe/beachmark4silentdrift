from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from silent_drift_miner.adapter_contracts import AdapterPlanRequest, AdapterRunRequest
from silent_drift_miner.adapters.jvm import JvmAdapter
from silent_drift_miner.audit import audit_package
from silent_drift_miner.bench import create_benchmark_package
from silent_drift_miner.cli import main
from silent_drift_miner.curation import create_curated_case, write_curated_case
from silent_drift_miner.oracle import generate_pytest_oracle


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "cases" / "jvm_toy_drift"


def test_jvm_adapter_plans_and_runs_offline_toy_case(tmp_path) -> None:
    java, javac = _fake_toolchain(tmp_path)
    adapter = JvmAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="jvm-toy-drift",
            ecosystem="jvm",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_source_path": str(FIXTURE_ROOT / "old"),
                "new_source_path": str(FIXTURE_ROOT / "new"),
                "java_executable": str(java),
                "javac_executable": str(javac),
                "main_class": "DriftClient",
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["candidate_id"] == "jvm-toy-drift"
    assert payload["keep"] is True
    assert payload["drop_reason"] is None
    assert payload["diff"]["summary"] == "stdout changed"
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"
    assert payload["old_run"]["environment"]["library"] == "toy-drift"


def test_jvm_adapter_result_flows_through_oracle_package_and_audit(tmp_path) -> None:
    java, javac = _fake_toolchain(tmp_path)
    adapter = JvmAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="jvm-toy-drift",
            ecosystem="jvm",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_source_path": str(FIXTURE_ROOT / "old"),
                "new_source_path": str(FIXTURE_ROOT / "new"),
                "java_executable": str(java),
                "javac_executable": str(javac),
            },
        )
    )
    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    case = create_curated_case(
        result_path,
        "accept",
        "jvm_toy_drift",
        source_url="https://example.com/jvm-toy-release-notes",
        source_excerpt="Default behavior changed.",
        retrieved_at="2026-05-19",
        ecosystem="jvm",
        version_old="1.0.0",
        version_new="2.0.0",
        api_surface=["example.toy.ToyDrift.value"],
        review_notes="Synthetic JVM fixture for adapter lifecycle coverage.",
    )
    case_path = tmp_path / "case.yaml"
    oracle_dir = tmp_path / "oracle"
    packages_dir = tmp_path / "packages"
    write_curated_case(case, case_path)
    oracle = generate_pytest_oracle(case_path, oracle_dir)
    package_dir = create_benchmark_package(case_path, Path(oracle_dir / "oracle_spec.yaml"), ["L1"], packages_dir)

    audit = audit_package(package_dir)

    assert oracle.case_id == "jvm_toy_drift"
    assert audit["pass"] is True
    assert (package_dir / "reproduction_result.json").exists()
    assert not (package_dir / "hidden").exists()


def test_jvm_adapter_records_jvm_special_case_inputs(tmp_path) -> None:
    java, javac = _fake_toolchain(tmp_path)
    extra_source = tmp_path / "extra_src"
    resources = tmp_path / "resources"
    extra_source.mkdir()
    resources.mkdir()
    (extra_source / "ExtraMarker.java").write_text(
        "public final class ExtraMarker { private ExtraMarker() {} }\n",
        encoding="utf-8",
    )
    (resources / "drift.properties").write_text("mode=toy\n", encoding="utf-8")
    adapter = JvmAdapter()

    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="jvm-special-inputs",
            ecosystem="jvm",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_source_paths": [str(FIXTURE_ROOT / "old"), str(extra_source)],
                "new_source_paths": [str(FIXTURE_ROOT / "new"), str(extra_source)],
                "resource_paths": [str(resources)],
                "jvm_args": ["-Ddrift.mode=toy"],
                "program_args": ["--format", "plain"],
                "java_executable": str(java),
                "javac_executable": str(javac),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    old_run_log = Path(result["old_run"]["run_log_path"]).read_text(encoding="utf-8")
    old_build_log = Path(result["old_run"]["build_log_path"]).read_text(encoding="utf-8")
    assert spec_payload["old_environment"]["source_paths"] == [str(FIXTURE_ROOT / "old"), str(extra_source)]
    assert spec_payload["old_environment"]["resource_paths"] == [str(resources)]
    assert spec_payload["old_environment"]["jvm_args"] == ["-Ddrift.mode=toy"]
    assert spec_payload["old_environment"]["program_args"] == ["--format", "plain"]
    assert "-Ddrift.mode=toy" in old_run_log
    assert "--format plain" in old_run_log
    assert str(resources) in old_build_log
    assert result["keep"] is True


def test_jvm_reproduce_cli_plans_and_runs_jvm_spec(tmp_path) -> None:
    java, javac = _fake_toolchain(tmp_path)
    spec_path = tmp_path / "spec.json"
    out_dir = tmp_path / "repro"

    assert main(
        [
            "reproduce",
            "plan",
            "--ecosystem",
            "jvm",
            "--candidate-id",
            "jvm-cli-toy",
            "--library",
            "toy-drift",
            "--old-version",
            "1.0.0",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            "--old-source-path",
            str(FIXTURE_ROOT / "old"),
            "--new-source-path",
            str(FIXTURE_ROOT / "new"),
            "--java-executable",
            str(java),
            "--javac-executable",
            str(javac),
            "--out",
            str(spec_path),
        ]
    ) == 0

    assert main(["reproduce", "run", "--spec", str(spec_path), "--out", str(out_dir)]) == 0

    result = json.loads((out_dir / "attempt_001" / "result.json").read_text(encoding="utf-8"))
    assert result["candidate_id"] == "jvm-cli-toy"
    assert result["keep"] is True
    assert result["drop_reason"] is None


def test_jvm_adapter_classifies_missing_tool_as_install_failed(tmp_path) -> None:
    adapter = JvmAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="jvm-missing-tool",
            ecosystem="jvm",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_source_path": str(FIXTURE_ROOT / "old"),
                "new_source_path": str(FIXTURE_ROOT / "new"),
                "java_executable": "definitely-missing-java",
                "javac_executable": "definitely-missing-javac",
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is False
    assert payload["drop_reason"] == "install_failed"
    assert adapter.classify_failure(payload) == "install_failed"


def test_jvm_adapter_rejects_non_jvm_plan(tmp_path) -> None:
    adapter = JvmAdapter()

    with pytest.raises(ValueError, match="ecosystem"):
        adapter.plan(
            AdapterPlanRequest(
                candidate_id="wrong-ecosystem",
                ecosystem="python",
                library="toy-drift",
                old_version="1.0.0",
                new_version="2.0.0",
                client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
                out_path=str(tmp_path / "spec.json"),
                metadata={
                    "old_source_path": str(FIXTURE_ROOT / "old"),
                    "new_source_path": str(FIXTURE_ROOT / "new"),
                },
            )
        )


@pytest.mark.skipif(
    shutil.which("java") is None or shutil.which("javac") is None,
    reason="real JDK smoke test requires java and javac in PATH",
)
def test_jvm_adapter_runs_toy_case_with_real_jdk(tmp_path) -> None:
    adapter = JvmAdapter()
    spec_path = adapter.plan(
        AdapterPlanRequest(
            candidate_id="jvm-real-jdk-toy",
            ecosystem="jvm",
            library="toy-drift",
            old_version="1.0.0",
            new_version="2.0.0",
            client_file=str(FIXTURE_ROOT / "client" / "DriftClient.java"),
            out_path=str(tmp_path / "spec.json"),
            metadata={
                "old_source_path": str(FIXTURE_ROOT / "old"),
                "new_source_path": str(FIXTURE_ROOT / "new"),
                "java_executable": shutil.which("java"),
                "javac_executable": shutil.which("javac"),
            },
        )
    )

    result_path = adapter.run(AdapterRunRequest(spec_path=str(spec_path), out_dir=str(tmp_path / "repro")))

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["keep"] is True
    assert Path(payload["old_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "old"
    assert Path(payload["new_run"]["stdout_path"]).read_text(encoding="utf-8").strip() == "new"


def _fake_toolchain(tmp_path: Path) -> tuple[Path, Path]:
    if sys.platform == "win32":
        javac = tmp_path / "javac.cmd"
        java = tmp_path / "java.cmd"
        javac.write_text(
            "\r\n".join(
                [
                    "@echo off",
                    "set out=",
                    ":loop",
                    "if \"%1\"==\"\" goto done",
                    "if \"%1\"==\"-d\" (",
                    "  set out=%2",
                    "  shift",
                    "  shift",
                    "  goto loop",
                    ")",
                    "shift",
                    "goto loop",
                    ":done",
                    "if not \"%out%\"==\"\" mkdir \"%out%\" 2>NUL",
                    "exit /b 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        java.write_text(
            "\r\n".join(
                [
                    "@echo off",
                    "echo %* | findstr /i \"old\" >NUL",
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
        return java, javac

    javac = tmp_path / "javac"
    java = tmp_path / "java"
    javac.write_text(
        "#!/usr/bin/env sh\n"
        "out=\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = \"-d\" ]; then out=\"$2\"; shift 2; continue; fi\n"
        "  shift\n"
        "done\n"
        "[ -n \"$out\" ] && mkdir -p \"$out\"\n",
        encoding="utf-8",
    )
    java.write_text(
        "#!/usr/bin/env sh\n"
        "case \"$*\" in\n"
        "  *old*) echo old ;;\n"
        "  *) echo new ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    os.chmod(javac, 0o755)
    os.chmod(java, 0o755)
    return java, javac
