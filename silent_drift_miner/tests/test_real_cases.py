from __future__ import annotations

import json
import py_compile
from pathlib import Path


CASE_ROOT = Path(__file__).resolve().parents[2] / "cases" / "pandas_str_replace_regex_default"


def test_pandas_str_replace_case_manifest_has_required_fields() -> None:
    manifest = json.loads((CASE_ROOT / "candidate.json").read_text(encoding="utf-8"))

    assert manifest["case_id"] == "pandas_str_replace_regex_default"
    assert manifest["library"] == "pandas"
    assert manifest["version_old"] == "1.5.3"
    assert manifest["version_new"] == "2.0.3"
    assert manifest["source_url"].startswith("https://pandas.pydata.org/")
    assert "reproduce plan" in manifest["reproduction_command"]
    assert manifest["client_file"] == "client.py"


def test_pandas_str_replace_client_compiles() -> None:
    py_compile.compile(str(CASE_ROOT / "client.py"), doraise=True)
