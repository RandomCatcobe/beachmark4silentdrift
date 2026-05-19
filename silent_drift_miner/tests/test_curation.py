from __future__ import annotations

from pathlib import Path

from silent_drift_miner.cli import main
from silent_drift_miner.curation import load_curated_case


def test_curate_create_accepts_kept_reproduction(tmp_path) -> None:
    result = _kept_result(tmp_path)
    out = tmp_path / "curated" / "case.yaml"

    assert main(
        [
            "curate",
            "create",
            "--reproduction-result",
            str(result),
            "--decision",
            "accept",
            "--case-id",
            "toy_case_001",
            "--out",
            str(out),
        ]
    ) == 0

    text = out.read_text(encoding="utf-8")
    assert 'case_id: "toy_case_001"' in text
    assert 'decision: "accept"' in text
    assert 'candidate_id: "cand-1"' in text
    assert "keep: true" in text


def test_curate_create_rejects_mismatched_decision(tmp_path) -> None:
    result = _kept_result(tmp_path)
    out = tmp_path / "curated" / "case.yaml"

    assert main(
        [
            "curate",
            "create",
            "--reproduction-result",
            str(result),
            "--decision",
            "reject",
            "--case-id",
            "toy_case_001",
            "--out",
            str(out),
        ]
    ) == 1
    assert not out.exists()


def test_curate_create_stores_result_path_relative_to_case_file(tmp_path, monkeypatch) -> None:
    result = _kept_result(tmp_path)
    out = tmp_path / "curated" / "case.yaml"
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "curate",
            "create",
            "--reproduction-result",
            str(result.relative_to(tmp_path)),
            "--decision",
            "accept",
            "--case-id",
            "toy_case_001",
            "--out",
            str(out.relative_to(tmp_path)),
        ]
    ) == 0

    case = load_curated_case(out)
    assert Path(out.parent / case.reproduction_result).resolve() == result.resolve()


def _kept_result(tmp_path: Path) -> Path:
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
    out_root = tmp_path / "repro"
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
    assert main(["reproduce", "run", "--spec", str(spec), "--out", str(out_root)]) == 0
    return out_root / "attempt_001" / "result.json"
