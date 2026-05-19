from __future__ import annotations

import json

from silent_drift_miner.cli import main
from silent_drift_miner.reproduction import load_reproduction_spec


def test_reproduce_plan_writes_spec_with_old_and_new_envs(tmp_path) -> None:
    client_file = tmp_path / "client.py"
    out = tmp_path / "data" / "reproductions" / "cand-1" / "spec.json"
    client_file.write_text("print('hello')\n", encoding="utf-8")

    rc = main(
        [
            "reproduce",
            "plan",
            "--candidate-id",
            "cand-1",
            "--library",
            "pandas",
            "--old-version",
            "1.5.3",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(client_file),
            "--old-python-executable",
            "python-old",
            "--new-python-executable",
            "python-new",
            "--extra-package",
            "numpy==1.24.4",
            "--out",
            str(out),
        ]
    )

    assert rc == 0
    spec = load_reproduction_spec(out)
    assert spec.candidate_id == "cand-1"
    assert spec.old_environment.install_command[-1] == "pandas==1.5.3"
    assert spec.new_environment.install_command[-1] == "pandas==2.0.0"
    assert "numpy==1.24.4" in spec.old_environment.install_command
    assert "numpy==1.24.4" in spec.new_environment.install_command
    assert spec.old_environment.python_executable == "python-old"
    assert spec.new_environment.python_executable == "python-new"
    assert spec.client_file == str(client_file)


def test_reproduce_plan_rejects_missing_client_file(tmp_path) -> None:
    out = tmp_path / "spec.json"

    rc = main(
        [
            "reproduce",
            "plan",
            "--candidate-id",
            "cand-1",
            "--library",
            "pandas",
            "--old-version",
            "1.5.3",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(tmp_path / "missing.py"),
            "--out",
            str(out),
        ]
    )

    assert rc == 2
    assert not out.exists()


def test_reproduction_spec_json_is_plain_data(tmp_path) -> None:
    client_file = tmp_path / "client.py"
    out = tmp_path / "spec.json"
    client_file.write_text("print('hello')\n", encoding="utf-8")
    assert main(
        [
            "reproduce",
            "plan",
            "--candidate-id",
            "cand-1",
            "--library",
            "pandas",
            "--old-version",
            "1.5.3",
            "--new-version",
            "2.0.0",
            "--client-file",
            str(client_file),
            "--out",
            str(out),
        ]
    ) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert payload["old_environment"]["label"] == "old"
    assert payload["new_environment"]["label"] == "new"
