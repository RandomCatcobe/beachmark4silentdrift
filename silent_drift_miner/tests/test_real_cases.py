from __future__ import annotations

import json
import py_compile
from pathlib import Path


CASES_ROOT = Path(__file__).resolve().parents[2] / "cases"


def test_pandas_str_replace_case_manifest_has_required_fields() -> None:
    manifest = json.loads((CASES_ROOT / "pandas_str_replace_regex_default" / "candidate.json").read_text(encoding="utf-8"))

    assert manifest["case_id"] == "pandas_str_replace_regex_default"
    assert manifest["library"] == "pandas"
    assert manifest["version_old"] == "1.5.3"
    assert manifest["version_new"] == "2.0.3"
    assert manifest["source_url"].startswith("https://pandas.pydata.org/")
    assert "reproduce plan" in manifest["reproduction_command"]
    assert manifest["client_file"] == "client.py"


def test_pandas_str_replace_client_compiles() -> None:
    py_compile.compile(str(CASES_ROOT / "pandas_str_replace_regex_default" / "client.py"), doraise=True)


def test_pydantic_optional_field_case_manifest_has_required_fields() -> None:
    manifest = json.loads((CASES_ROOT / "pydantic_optional_field_required" / "candidate.json").read_text(encoding="utf-8"))

    assert manifest["case_id"] == "pydantic_optional_field_required"
    assert manifest["library"] == "pydantic"
    assert manifest["version_old"] == "1.10.15"
    assert manifest["version_new"] == "2.7.4"
    assert manifest["source_url"].startswith("https://pydantic.dev/")
    assert "reproduce plan" in manifest["reproduction_command"]
    assert manifest["client_file"] == "client.py"


def test_pydantic_optional_field_client_compiles() -> None:
    py_compile.compile(str(CASES_ROOT / "pydantic_optional_field_required" / "client.py"), doraise=True)


def test_pydantic_field_alias_case_manifest_has_required_fields() -> None:
    manifest = json.loads((CASES_ROOT / "pydantic_field_alias_none" / "candidate.json").read_text(encoding="utf-8"))

    assert manifest["case_id"] == "pydantic_field_alias_none"
    assert manifest["library"] == "pydantic"
    assert manifest["version_old"] == "1.10.15"
    assert manifest["version_new"] == "2.7.4"
    assert manifest["source_url"].startswith("https://pydantic.dev/")
    assert "reproduce plan" in manifest["reproduction_command"]
    assert manifest["client_file"] == "client.py"


def test_pydantic_field_alias_client_compiles() -> None:
    py_compile.compile(str(CASES_ROOT / "pydantic_field_alias_none" / "client.py"), doraise=True)
