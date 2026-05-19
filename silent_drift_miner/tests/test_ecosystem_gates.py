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
    assert report.required_tools == [{"name": "java", "found": False, "path": None}]


def test_ecosystem_env_check_cli_writes_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}" if tool == "java" else None,
    )
    out = tmp_path / "jvm_env.json"

    assert main(["ecosystem", "env-check", "--target", "jvm", "--out", str(out)]) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pass"] is True
    assert payload["required_tools"][0]["name"] == "java"


def test_adapter_contracts_reserve_future_ecosystems() -> None:
    contracts = {contract.ecosystem: contract for contract in list_adapter_contracts()}

    assert contracts["python"].status == AdapterStatus.ACTIVE
    assert contracts["jvm"].status == AdapterStatus.RESERVED
    assert contracts["go"].status == AdapterStatus.RESERVED
    assert contracts["js"].status == AdapterStatus.RESERVED
    assert contracts["php"].status == AdapterStatus.RESERVED
    assert contracts["ruby"].status == AdapterStatus.RESERVED
    assert contracts["rust"].status == AdapterStatus.RESERVED
    assert contracts["dotnet"].status == AdapterStatus.RESERVED
    assert get_adapter_contract("JVM").required_tools == ["java"]
    assert get_adapter_contract("php").required_tools == ["php", "composer"]


def test_ecosystem_adapters_cli_reports_reserved_contracts(tmp_path, capsys) -> None:
    out = tmp_path / "adapters.json"

    assert main(["ecosystem", "adapters", "--target", "jvm", "--out", str(out)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["contracts"][0]["ecosystem"] == "jvm"
    assert payload["contracts"][0]["status"] == "reserved"
    assert "explicit user command" in payload["handoff_rule"]
    assert json.loads(out.read_text(encoding="utf-8")) == payload


def test_ecosystem_env_check_supports_php_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "silent_drift_miner.ecosystems.shutil.which",
        lambda tool: f"/fake/bin/{tool}",
    )

    report = check_ecosystem_environment("php")

    assert report.pass_ is True
    assert [tool["name"] for tool in report.required_tools] == ["php", "composer"]


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
