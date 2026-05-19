from __future__ import annotations

import json
from pathlib import Path

from silent_drift_miner.cli import main
from silent_drift_miner.adapter_contracts import AdapterStatus, get_adapter_contract, list_adapter_contracts
from silent_drift_miner.ecosystems import check_ecosystem_environment, evaluate_adapter_gates


def test_ecosystem_gates_block_jvm_until_python_case_budget_met(tmp_path) -> None:
    _write_case_package(tmp_path, "case_one")

    report = evaluate_adapter_gates(
        packages_root=tmp_path / "packages",
        audit_root=tmp_path / "audit",
        target_ecosystem="jvm",
        required_python_cases=3,
    )

    assert report.pass_ is False
    assert report.audited_python_cases == 1


def test_ecosystem_gates_allow_target_when_budget_met(tmp_path) -> None:
    for name in ["case_one", "case_two", "case_three"]:
        _write_case_package(tmp_path, name)

    report = evaluate_adapter_gates(
        packages_root=tmp_path / "packages",
        audit_root=tmp_path / "audit",
        target_ecosystem="jvm",
        required_python_cases=3,
    )

    assert report.pass_ is True
    assert report.audited_python_cases == 3


def test_ecosystem_gates_cli_returns_nonzero_when_blocked(tmp_path, capsys) -> None:
    _write_case_package(tmp_path, "case_one")

    assert main(
        [
            "ecosystem",
            "gates",
            "--target",
            "jvm",
            "--packages",
            str(tmp_path / "packages"),
            "--audit",
            str(tmp_path / "audit"),
            "--min-python-cases",
            "3",
        ]
    ) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["pass"] is False
    assert payload["audited_python_cases"] == 1


def test_ecosystem_env_check_reports_missing_required_tool(monkeypatch) -> None:
    monkeypatch.setattr("silent_drift_miner.ecosystems.shutil.which", lambda _tool: None)

    report = check_ecosystem_environment("jvm")

    assert report.pass_ is False
    assert report.required_tools == [
        {"name": "java", "found": False, "path": None},
        {"name": "javac", "found": False, "path": None},
    ]


def test_ecosystem_env_check_cli_writes_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool in {"java", "javac"} else None,
    )
    out = tmp_path / "jvm_env.json"

    assert main(["ecosystem", "env-check", "--target", "jvm", "--out", str(out)]) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pass"] is True
    assert [tool["name"] for tool in payload["required_tools"]] == ["java", "javac"]


def test_adapter_contracts_reserve_future_ecosystems() -> None:
    contracts = {contract.ecosystem: contract for contract in list_adapter_contracts()}

    assert contracts["python"].status == AdapterStatus.ACTIVE
    assert contracts["jvm"].status == AdapterStatus.ACTIVE
    assert contracts["go"].status == AdapterStatus.ACTIVE
    assert contracts["js"].status == AdapterStatus.ACTIVE
    assert contracts["php"].status == AdapterStatus.ACTIVE
    assert contracts["ruby"].status == AdapterStatus.ACTIVE
    assert contracts["rust"].status == AdapterStatus.RESERVED
    assert contracts["dotnet"].status == AdapterStatus.ACTIVE
    assert get_adapter_contract("JVM").required_tools == ["java", "javac"]
    assert get_adapter_contract("JS").required_tools == ["node"]
    assert get_adapter_contract("php").required_tools == ["php"]
    assert get_adapter_contract("ruby").required_tools == ["ruby"]
    assert get_adapter_contract("dotnet").required_tools == ["dotnet"]
    assert get_adapter_contract("go").required_tools == ["go"]


def test_ecosystem_adapters_cli_reports_jvm_active_contract(tmp_path, capsys) -> None:
    out = tmp_path / "adapters.json"

    assert main(["ecosystem", "adapters", "--target", "jvm", "--out", str(out)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["contracts"][0]["ecosystem"] == "jvm"
    assert payload["contracts"][0]["status"] == "active"
    assert payload["contracts"][0]["implementation_module"] == "silent_drift_miner.adapters.jvm"
    assert "reserved adapters expose contracts only" in payload["handoff_rule"]
    assert json.loads(out.read_text(encoding="utf-8")) == payload


def test_ecosystem_env_check_supports_php_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "php" else None,
    )

    report = check_ecosystem_environment("php")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["php"]
    assert [tool["name"] for tool in report.optional_tools] == ["composer"]


def test_ecosystem_env_check_supports_ruby_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "ruby" else None,
    )

    report = check_ecosystem_environment("ruby")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["ruby"]
    assert [tool["name"] for tool in report.optional_tools] == ["bundle"]


def test_ecosystem_env_check_supports_dotnet_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "dotnet" else None,
    )

    report = check_ecosystem_environment("dotnet")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["dotnet"]
    assert [tool["name"] for tool in report.optional_tools] == ["nuget"]


def test_ecosystem_env_check_supports_go_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "go" else None,
    )

    report = check_ecosystem_environment("go")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["go"]
    assert report.optional_tools == []


def test_ecosystem_env_check_supports_js_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "node" else None,
    )

    report = check_ecosystem_environment("js")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["node"]
    assert [tool["name"] for tool in report.optional_tools] == ["npm", "pnpm", "yarn"]


def _write_case_package(tmp_path: Path, case_id: str) -> None:
    package_dir = tmp_path / "packages" / case_id
    audit_dir = tmp_path / "audit"
    package_dir.mkdir(parents=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "case.yaml").write_text(
        "\n".join(
            [
                f'case_id: "{case_id}"',
                'decision: "accept"',
                f'candidate_id: "{case_id}-candidate"',
                'reproduction_result: "reproduction_result.json"',
                "keep: true",
                "drop_reason: null",
                'source_url: "https://example.com/release-notes"',
                'source_excerpt: "Default behavior changed."',
                'retrieved_at: "2026-01-01"',
                'ecosystem: "python"',
                'version_old: "1.0.0"',
                'version_new: "2.0.0"',
                'api_surface: ["example.api"]',
                'review_notes: "audited fixture"',
                'schema_version: "1"',
                'created_at: "2026-01-01T00:00:00"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (audit_dir / f"{case_id}.json").write_text(
        json.dumps({"package": str(package_dir), "pass": True, "findings": []}) + "\n",
        encoding="utf-8",
    )
