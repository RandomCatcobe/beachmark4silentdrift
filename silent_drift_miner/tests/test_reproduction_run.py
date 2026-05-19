from __future__ import annotations

import json
from pathlib import Path

from silent_drift_miner.cli import main
from silent_drift_miner.reproduction import (
    PythonEnvironmentDefinition,
    ReproductionSpec,
    write_reproduction_spec,
)


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
    assert (first / "old" / "Dockerfile").exists()
    assert (first / "new" / "Dockerfile").exists()
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


def test_reproduce_run_ignores_json_version_metadata(tmp_path) -> None:
    old_pkg, new_pkg = _toy_packages(
        tmp_path,
        old_value="same",
        new_value="same",
        old_version_metadata="1.0.0",
        new_version_metadata="2.0.0",
    )
    client = tmp_path / "client.py"
    spec = tmp_path / "spec.json"
    out_root = tmp_path / "repro"
    client.write_text(
        (
            "import json\n"
            "import toy_drift\n"
            "print(json.dumps({"
            "'toy_version': toy_drift.__version__, "
            "'value': toy_drift.value()"
            "}, sort_keys=True))\n"
        ),
        encoding="utf-8",
    )
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
    assert result["diff"]["details"]["raw_stdout_changed"] is True
    assert result["diff"]["details"]["stdout_compared_after_version_metadata"] is True


def test_reproduce_run_classifies_import_failure(tmp_path) -> None:
    old_pkg = tmp_path / "old_pkg"
    new_pkg = tmp_path / "new_pkg"
    old_pkg.mkdir()
    new_pkg.mkdir()
    client = tmp_path / "client.py"
    spec = tmp_path / "spec.json"
    out_root = tmp_path / "repro"
    client.write_text("import missing_package\n", encoding="utf-8")
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
    assert result["drop_reason"] == "import_failed"


def test_reproduce_run_can_install_local_packages_in_isolated_venvs(tmp_path) -> None:
    client = tmp_path / "client.py"
    spec_path = tmp_path / "spec.json"
    out_root = tmp_path / "repro"
    client.write_text("import toy_drift\nprint(toy_drift.value())\n", encoding="utf-8")
    spec = ReproductionSpec(
        candidate_id="cand-install",
        library="toy-drift",
        old_version="1.0.0",
        new_version="2.0.0",
        client_file=str(client),
        old_environment=PythonEnvironmentDefinition(
            label="old",
            library="toy-drift",
            version="1.0.0",
            install_command=_write_toy_package_command("old"),
        ),
        new_environment=PythonEnvironmentDefinition(
            label="new",
            library="toy-drift",
            version="2.0.0",
            install_command=_write_toy_package_command("new"),
        ),
    )
    write_reproduction_spec(spec, spec_path)

    assert main(
        [
            "reproduce",
            "run",
            "--spec",
            str(spec_path),
            "--out",
            str(out_root),
            "--install",
            "--venv-root",
            str(tmp_path / "venvs"),
            "--build-timeout",
            "120",
        ]
    ) == 0

    result = json.loads((out_root / "attempt_001" / "result.json").read_text(encoding="utf-8"))
    assert result["keep"] is True
    assert result["drop_reason"] is None
    assert result["old_run"]["build_exit_code"] == 0
    assert result["new_run"]["build_exit_code"] == 0
    assert (out_root / "attempt_001" / "old" / "stdout.txt").read_text(encoding="utf-8").strip() == "old"
    assert (out_root / "attempt_001" / "new" / "stdout.txt").read_text(encoding="utf-8").strip() == "new"


def _toy_packages(
    tmp_path: Path,
    old_value: str = "old",
    new_value: str = "new",
    old_version_metadata: str = "1.0.0",
    new_version_metadata: str = "2.0.0",
) -> tuple[Path, Path]:
    old_pkg = tmp_path / "old_pkg"
    new_pkg = tmp_path / "new_pkg"
    for root, value, version in [
        (old_pkg, old_value, old_version_metadata),
        (new_pkg, new_value, new_version_metadata),
    ]:
        package = root / "toy_drift"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(
            f"__version__ = {version!r}\n\n"
            f"def value():\n    return {value!r}\n",
            encoding="utf-8",
        )
    return old_pkg, new_pkg


def _write_toy_package_command(value: str) -> list[str]:
    script = (
        "from pathlib import Path; import site; "
        "root = Path(site.getsitepackages()[0]) / 'toy_drift'; "
        "root.mkdir(parents=True, exist_ok=True); "
        f"(root / '__init__.py').write_text(\"def value():\\n    return {value!r}\\n\", encoding='utf-8')"
    )
    return ["python", "-c", script]
