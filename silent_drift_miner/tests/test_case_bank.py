from __future__ import annotations

import json
from pathlib import Path

from case_bank.__main__ import main as case_bank_main
from case_bank.index import build_indexes, discover_cases


def test_case_bank_index_build_succeeds_on_empty_cases_dir(tmp_path: Path) -> None:
    cases = tmp_path / "cases"
    indexes = tmp_path / "indexes"
    cases.mkdir()

    written = build_indexes(cases, indexes)

    assert len(written) == 5
    assert (indexes / "by-status.md").read_text(encoding="utf-8").startswith("# Cases By Status")


def test_case_bank_pack_strips_hidden_files(tmp_path: Path) -> None:
    src = tmp_path / "cases"
    case_dir = src / "validation-and-policy" / "toy-case"
    hidden = case_dir / "hidden"
    client = case_dir / "client"
    hidden.mkdir(parents=True)
    client.mkdir()
    (case_dir / "case.md").write_text("# Toy\n", encoding="utf-8")
    (case_dir / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
    (case_dir / "env.md").write_text("# Env\n", encoding="utf-8")
    (case_dir / "metadata.json").write_text("{}\n", encoding="utf-8")
    (client / "probe.py").write_text("print('ok')\n", encoding="utf-8")
    (hidden / "oracle.md").write_text("secret\n", encoding="utf-8")
    (hidden / "expected.json").write_text("{}\n", encoding="utf-8")

    out = tmp_path / "eval_package"

    assert case_bank_main(["pack", "--src", str(src), "--out", str(out)]) == 0
    packaged_case = out / "validation-and-policy" / "toy-case"
    assert (packaged_case / "client" / "probe.py").exists()
    assert not (packaged_case / "hidden").exists()
    assert not list(out.rglob("expected.json"))
    assert not list(out.rglob("oracle.md"))


def test_committed_case_bank_has_initial_verified_cases() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    cases = discover_cases(repo_root / "docs" / "case-bank" / "cases")
    ids = {case["case_id"] for case in cases}

    assert ids == {
        "PY-SD-010",
        "JS-06",
        "JS-09",
        "GO-002",
        "RB-RACK-005",
        "PHP-07",
        "JVM-JAVA-07",
        "DOTNET-08",
    }
    for case in cases:
        case_dir = case["_path"]
        assert (case_dir / "client").is_dir()
        assert (case_dir / "hidden" / "expected.json").exists()
        expected = json.loads((case_dir / "hidden" / "expected.json").read_text(encoding="utf-8"))
        assert expected["case_id"] == case["case_id"]
        assert expected["assertions"]
