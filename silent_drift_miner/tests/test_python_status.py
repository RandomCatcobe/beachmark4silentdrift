from __future__ import annotations

import json
from pathlib import Path

from silent_drift_miner.cli import main
from silent_drift_miner.python_status import build_python_status_report


def test_python_status_passes_with_three_complete_cases(tmp_path) -> None:
    for name in ["case_one", "case_two", "case_three"]:
        _write_complete_case(tmp_path, name)

    report = build_python_status_report(
        cases_root=tmp_path / "cases",
        packages_root=tmp_path / "packages",
        min_audited_cases=3,
    )

    assert report.pass_ is True
    assert report.audited_case_count == 3
    assert not report.findings


def test_python_status_fails_when_client_is_missing(tmp_path) -> None:
    _write_complete_case(tmp_path, "case_one", write_client=False)

    report = build_python_status_report(
        cases_root=tmp_path / "cases",
        packages_root=tmp_path / "packages",
        min_audited_cases=1,
    )

    assert report.pass_ is False
    assert any(finding["check"] == "client_compiles" for finding in report.findings)


def test_python_status_cli_writes_report(tmp_path) -> None:
    for name in ["case_one", "case_two", "case_three"]:
        _write_complete_case(tmp_path, name)
    out = tmp_path / "reports" / "python_status.json"

    assert main(
        [
            "python",
            "status",
            "--cases",
            str(tmp_path / "cases"),
            "--packages",
            str(tmp_path / "packages"),
            "--min-cases",
            "3",
            "--out",
            str(out),
        ]
    ) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pass"] is True
    assert payload["audited_case_count"] == 3


def _write_complete_case(tmp_path: Path, case_id: str, write_client: bool = True) -> None:
    cases_root = tmp_path / "cases" / case_id
    package_dir = tmp_path / "packages" / case_id
    public_dir = package_dir / "public"
    cases_root.mkdir(parents=True)
    public_dir.mkdir(parents=True)

    (cases_root / "README.md").write_text(f"# {case_id}\n", encoding="utf-8")
    if write_client:
        (cases_root / "client.py").write_text("print('ok')\n", encoding="utf-8")
    (cases_root / "candidate.json").write_text(
        json.dumps(
            {
                "case_id": case_id,
                "candidate_id": f"{case_id}-candidate",
                "library": "example",
                "version_old": "1.0.0",
                "version_new": "2.0.0",
                "source_url": "https://example.com/release-notes",
                "client_file": "client.py",
            }
        ),
        encoding="utf-8",
    )
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
    (package_dir / "oracle_spec.yaml").write_text(
        "\n".join(
            [
                f'case_id: "{case_id}"',
                f'candidate_id: "{case_id}-candidate"',
                "case_path: " + json.dumps(str(package_dir / "case.yaml")),
                'template: "pytest"',
                'hidden_test_path: ""',
                'expected_path: ""',
                "public_readme_path: " + json.dumps(str(public_dir / "README.md")),
                "starter_client_path: " + json.dumps(str(public_dir / "starter_client.py")),
                'schema_version: "1"',
                'created_at: "2026-01-01T00:00:00"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "task_id": case_id,
                "case_id": case_id,
                "candidate_id": f"{case_id}-candidate",
                "levels": ["L1", "L2", "L3"],
                "public_dir": "public",
                "reproduction_result": "reproduction_result.json",
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "reproduction_result.json").write_text('{"keep": true}\n', encoding="utf-8")
    (public_dir / "README.md").write_text("# public\n", encoding="utf-8")
    (public_dir / "starter_client.py").write_text("print('starter')\n", encoding="utf-8")
