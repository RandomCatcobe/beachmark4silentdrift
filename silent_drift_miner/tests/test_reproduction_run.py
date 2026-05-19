from __future__ import annotations

import json
from pathlib import Path

from silent_drift_miner.cli import main


def test_reproduce_run_captures_diff_and_allocates_attempts(tmp_path) -> None:
    old_pkg, new_pkg = _toy_packages(tmp_path)
    client = tmp_path / "client.py"
    spec = tmp_path / "spec.json"
    out_root = tmp_path / "reproductions" / "cand-1"
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
    first = out_root / "attempt_001"
    assert (first / "old" / "stdout.txt").read_text(encoding="utf-8").strip() == "old"
    assert (first / "new" / "stdout.txt").read_text(encoding="utf-8").strip() == "new"
    result = json.loads((first / "result.json").read_text(encoding="utf-8"))
    assert result["keep"] is True
    assert result["drop_reason"] is None
    assert result["diff"]["summary"] == "stdout changed"

    assert main(["reproduce", "run", "--spec", str(spec), "--out", str(out_root)]) == 0
    assert (out_root / "attempt_002" / "result.json").exists()


def test_reproduce_summarize_reads_result(tmp_path, capsys) -> None:
    old_pkg, new_pkg = _toy_packages(tmp_path)
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

    assert main(["reproduce", "summarize", "--result", str(out_root / "attempt_001" / "result.json")]) == 0

    output = capsys.readouterr().out
    assert '"keep": true' in output
    assert "stdout changed" in output


def test_reproduce_run_drops_no_behavior_diff(tmp_path) -> None:
    old_pkg, new_pkg = _toy_packages(tmp_path, old_value="same", new_value="same")
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

    result = json.loads((out_root / "attempt_001" / "result.json").read_text(encoding="utf-8"))
    assert result["keep"] is False
    assert result["drop_reason"] == "no_behavior_diff"


def _toy_packages(tmp_path: Path, old_value: str = "old", new_value: str = "new") -> tuple[Path, Path]:
    old_pkg = tmp_path / "old_pkg"
    new_pkg = tmp_path / "new_pkg"
    for root, value in [(old_pkg, old_value), (new_pkg, new_value)]:
        package = root / "toy_drift"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            f"def value():\n    return {value!r}\n",
            encoding="utf-8",
        )
    return old_pkg, new_pkg
