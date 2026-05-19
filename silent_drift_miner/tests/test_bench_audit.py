from __future__ import annotations

import json
from pathlib import Path

from silent_drift_miner.cli import main


def test_bench_package_copies_public_only_and_audit_passes(tmp_path) -> None:
    case, oracle_spec = _case_and_oracle(tmp_path)
    packages = tmp_path / "packages"
    audit = tmp_path / "audit" / "toy_case_001.json"

    assert main(
        [
            "bench",
            "package",
            "--case",
            str(case),
            "--oracle",
            str(oracle_spec),
            "--levels",
            "L1,L2,L3",
            "--out",
            str(packages),
        ]
    ) == 0
    package_dir = packages / "toy_case_001"
    assert (package_dir / "public" / "README.md").exists()
    assert not (package_dir / "hidden").exists()

    assert main(["audit", "case", "--package", str(package_dir), "--out", str(audit)]) == 0
    report = json.loads(audit.read_text(encoding="utf-8"))
    assert report["pass"] is True


def test_audit_fails_when_public_mentions_hidden_path(tmp_path) -> None:
    case, oracle_spec = _case_and_oracle(tmp_path)
    packages = tmp_path / "packages"
    audit = tmp_path / "audit.json"
    assert main(["bench", "package", "--case", str(case), "--oracle", str(oracle_spec), "--out", str(packages)]) == 0
    package_dir = packages / "toy_case_001"
    (package_dir / "public" / "README.md").write_text("see hidden expected.json\n", encoding="utf-8")

    assert main(["audit", "case", "--package", str(package_dir), "--out", str(audit)]) == 1
    report = json.loads(audit.read_text(encoding="utf-8"))
    assert report["pass"] is False
    assert report["findings"]


def test_audit_fails_when_reproduction_result_missing(tmp_path) -> None:
    case, oracle_spec = _case_and_oracle(tmp_path, create_result=False)
    packages = tmp_path / "packages"
    audit = tmp_path / "audit.json"
    assert main(["bench", "package", "--case", str(case), "--oracle", str(oracle_spec), "--out", str(packages)]) == 0

    assert main(["audit", "case", "--package", str(packages / "toy_case_001"), "--out", str(audit)]) == 1
    report = json.loads(audit.read_text(encoding="utf-8"))
    assert any(finding["check"] == "reproducibility_status" for finding in report["findings"])


def _case_and_oracle(tmp_path: Path, create_result: bool = True) -> tuple[Path, Path]:
    case = tmp_path / "case.yaml"
    oracle = tmp_path / "oracle"
    if create_result:
        (tmp_path / "result.json").write_text('{"candidate_id": "cand-1", "keep": true}\n', encoding="utf-8")
    case.write_text(
        "\n".join(
            [
                'case_id: "toy_case_001"',
                'decision: "accept"',
                'candidate_id: "cand-1"',
                'reproduction_result: "result.json"',
                "keep: true",
                "drop_reason: null",
                'source_url: "https://example.com/release-notes"',
                'source_excerpt: "Default behavior changed."',
                'retrieved_at: "2026-01-01"',
                'version_old: "1.0.0"',
                'version_new: "2.0.0"',
                'api_surface: ["toy_drift.value"]',
                'review_notes: "Synthetic accepted case for packaging tests."',
                'schema_version: "1"',
                'created_at: "2026-01-01T00:00:00"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert main(["oracle", "generate", "--case", str(case), "--out", str(oracle)]) == 0
    return case, oracle / "oracle_spec.yaml"
