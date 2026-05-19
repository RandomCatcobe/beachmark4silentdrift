from __future__ import annotations

from pathlib import Path

from silent_drift_miner.cli import main


def test_oracle_generate_creates_hidden_and_public_split(tmp_path) -> None:
    case = _accepted_case(tmp_path)
    out = tmp_path / "oracle" / "toy_case_001"

    assert main(
        [
            "oracle",
            "generate",
            "--case",
            str(case),
            "--template",
            "pytest",
            "--out",
            str(out),
        ]
    ) == 0

    assert (out / "oracle_spec.yaml").exists()
    assert (out / "hidden" / "test_behavior.py").exists()
    assert (out / "hidden" / "expected.json").exists()
    public_readme = (out / "public" / "README.md").read_text(encoding="utf-8")
    public_client = (out / "public" / "starter_client.py").read_text(encoding="utf-8")

    assert "expected old/new outputs" in public_readme
    assert "hidden" not in public_readme.lower()
    assert "expected.json" not in public_readme
    assert "expected.json" not in public_client


def test_oracle_generate_rejects_rejected_case(tmp_path) -> None:
    case = tmp_path / "case.yaml"
    case.write_text(
        "\n".join(
            [
                'case_id: "toy_case_001"',
                'decision: "reject"',
                'candidate_id: "cand-1"',
                'reproduction_result: "result.json"',
                "keep: false",
                'drop_reason: "no_behavior_diff"',
                'schema_version: "1"',
                'created_at: "2026-01-01T00:00:00"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert main(["oracle", "generate", "--case", str(case), "--out", str(tmp_path / "oracle")]) == 1


def _accepted_case(tmp_path: Path) -> Path:
    old_pkg = tmp_path / "old_pkg"
    new_pkg = tmp_path / "new_pkg"
    for root, value in [(old_pkg, "old"), (new_pkg, "new")]:
        package = root / "toy_drift"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            f"def value():\n    return {value!r}\n",
            encoding="utf-8",
        )
    client = tmp_path / "client.py"
    spec = tmp_path / "spec.json"
    repro = tmp_path / "repro"
    case = tmp_path / "curated" / "case.yaml"
    client.write_text("import toy_drift\nprint(toy_drift.value())\n", encoding="utf-8")
    assert main(
        [
            "reproduce",
            "plan",
            "--candidate-id",
            "cand-1",
            "--library",
            "toy-drift",
            "--old-version",
            "1.0.0",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(client),
            "--old-package-path",
            str(old_pkg),
            "--new-package-path",
            str(new_pkg),
            "--out",
            str(spec),
        ]
    ) == 0
    assert main(["reproduce", "run", "--spec", str(spec), "--out", str(repro)]) == 0
    assert main(
        [
            "curate",
            "create",
            "--reproduction-result",
            str(repro / "attempt_001" / "result.json"),
            "--decision",
            "accept",
            "--case-id",
            "toy_case_001",
            "--out",
            str(case),
        ]
    ) == 0
    return case
