"""Audit checks for packaged benchmark tasks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .curation import load_curated_case
from .oracle import load_oracle_spec


LEAK_TERMS = ("expected.json", "hidden/", "/hidden", "old_stdout", "new_stdout")
ALLOWED_LEVELS = {"L1", "L2", "L3"}
REQUIRED_CASE_PROVENANCE = (
    "source_url",
    "source_excerpt",
    "retrieved_at",
    "version_old",
    "version_new",
    "review_notes",
)


def audit_package(package_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    _require(package_dir / "manifest.json", findings)
    _require(package_dir / "case.yaml", findings)
    _require(package_dir / "oracle_spec.yaml", findings)
    public_dir = package_dir / "public"
    _require(public_dir, findings)
    if (package_dir / "hidden").exists():
        findings.append({"check": "hidden_split", "message": "package must not contain hidden oracle files"})

    manifest = _load_json(package_dir / "manifest.json", findings)
    case = _load_case(package_dir / "case.yaml", findings)
    oracle = _load_oracle(package_dir / "oracle_spec.yaml", findings)
    if manifest and case:
        _check_manifest_case(manifest, case, findings)
    if case and oracle:
        _check_case_oracle(case, oracle, findings)
    if manifest:
        reproduction_result = package_dir / str(manifest.get("reproduction_result", ""))
        if not reproduction_result.exists():
            findings.append({
                "check": "reproducibility_status",
                "message": "package is missing reproduction_result.json",
            })

    if public_dir.exists():
        for path in public_dir.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for term in LEAK_TERMS:
                if term in text:
                    findings.append({
                        "check": "public_leakage",
                        "message": f"public file {path.relative_to(package_dir)} contains {term!r}",
                    })
    return {
        "package": str(package_dir),
        "pass": not findings,
        "findings": findings,
    }


def write_audit_report(report: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _require(path: Path, findings: list[dict[str, str]]) -> None:
    if not path.exists():
        findings.append({"check": "package_structure", "message": f"missing {path.name}"})


def _load_json(path: Path, findings: list[dict[str, str]]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        findings.append({"check": "package_structure", "message": f"invalid JSON {path.name}: {exc}"})
        return None


def _load_case(path: Path, findings: list[dict[str, str]]):
    if not path.exists():
        return None
    try:
        return load_curated_case(path)
    except Exception as exc:
        findings.append({"check": "package_structure", "message": f"invalid case.yaml: {exc}"})
        return None


def _load_oracle(path: Path, findings: list[dict[str, str]]):
    if not path.exists():
        return None
    try:
        return load_oracle_spec(path)
    except Exception as exc:
        findings.append({"check": "package_structure", "message": f"invalid oracle_spec.yaml: {exc}"})
        return None


def _check_manifest_case(manifest: dict[str, Any], case, findings: list[dict[str, str]]) -> None:
    if manifest.get("case_id") != case.case_id:
        findings.append({"check": "provenance", "message": "manifest case_id does not match case.yaml"})
    if manifest.get("candidate_id") != case.candidate_id:
        findings.append({"check": "provenance", "message": "manifest candidate_id does not match case.yaml"})
    levels = set(manifest.get("levels") or [])
    if not levels or not levels <= ALLOWED_LEVELS:
        findings.append({"check": "package_structure", "message": "levels must be a non-empty subset of L1,L2,L3"})
    if not case.keep:
        findings.append({"check": "reproducibility_status", "message": "packaged case must have keep=true"})
    for field in REQUIRED_CASE_PROVENANCE:
        if not getattr(case, field, None):
            findings.append({"check": "provenance", "message": f"case.yaml missing {field}"})
    if not case.api_surface:
        findings.append({"check": "provenance", "message": "case.yaml missing api_surface"})


def _check_case_oracle(case, oracle, findings: list[dict[str, str]]) -> None:
    if oracle.case_id != case.case_id:
        findings.append({"check": "provenance", "message": "oracle case_id does not match case.yaml"})
    if oracle.candidate_id != case.candidate_id:
        findings.append({"check": "provenance", "message": "oracle candidate_id does not match case.yaml"})
