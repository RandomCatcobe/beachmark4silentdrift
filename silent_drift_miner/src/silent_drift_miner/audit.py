"""Audit checks for packaged benchmark tasks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LEAK_TERMS = ("expected.json", "hidden", "old output", "new output")


def audit_package(package_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    _require(package_dir / "manifest.json", findings)
    _require(package_dir / "case.yaml", findings)
    _require(package_dir / "oracle_spec.yaml", findings)
    public_dir = package_dir / "public"
    _require(public_dir, findings)
    if (package_dir / "hidden").exists():
        findings.append({"check": "hidden_split", "message": "package must not contain hidden oracle files"})

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
