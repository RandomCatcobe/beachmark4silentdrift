"""Benchmark package assembly."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .curation import load_curated_case
from .oracle import load_oracle_spec

CASE_BANK_STRIPPED_NAMES = {"hidden", "oracle.md", "expected.json"}


def create_benchmark_package(
    case_path: Path,
    oracle_spec_path: Path,
    levels: list[str],
    out_root: Path,
) -> Path:
    case = load_curated_case(case_path)
    oracle = load_oracle_spec(oracle_spec_path)
    if case.case_id != oracle.case_id:
        raise ValueError("case and oracle case_id mismatch")

    package_dir = out_root / case.case_id
    if package_dir.exists():
        raise ValueError(f"package already exists: {package_dir}")
    package_dir.mkdir(parents=True)

    shutil.copy2(case_path, package_dir / "case.yaml")
    shutil.copy2(oracle_spec_path, package_dir / "oracle_spec.yaml")
    reproduction_result = _resolve_link(case_path, case.reproduction_result)
    if reproduction_result.exists():
        shutil.copy2(reproduction_result, package_dir / "reproduction_result.json")
    public_src = Path(oracle.public_readme_path).parent
    public_dst = package_dir / "public"
    shutil.copytree(public_src, public_dst)
    manifest = {
        "task_id": case.case_id,
        "case_id": case.case_id,
        "candidate_id": case.candidate_id,
        "levels": levels,
        "public_dir": "public",
        "reproduction_result": "reproduction_result.json",
    }
    (package_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return package_dir


def create_case_bank_eval_package(src_root: Path, out_root: Path) -> Path:
    """Copy case-bank public files while stripping hidden oracle material."""
    if not src_root.exists():
        raise ValueError(f"case bank source not found: {src_root}")
    if not src_root.is_dir():
        raise ValueError(f"case bank source must be a directory: {src_root}")
    if out_root.exists() and any(out_root.iterdir()):
        raise ValueError(f"package output already exists and is not empty: {out_root}")

    out_root.mkdir(parents=True, exist_ok=True)
    for metadata_path in sorted(src_root.rglob("metadata.json")):
        case_dir = metadata_path.parent
        relative_case_dir = case_dir.relative_to(src_root)
        _copy_case_bank_case(case_dir, out_root / relative_case_dir)

    findings = validate_case_bank_eval_package(out_root)
    if findings:
        raise ValueError("; ".join(findings))
    return out_root


def validate_case_bank_eval_package(package_root: Path) -> list[str]:
    findings: list[str] = []
    if not package_root.exists():
        findings.append(f"package root does not exist: {package_root}")
        return findings

    for path in package_root.rglob("*"):
        if "hidden" in path.parts:
            findings.append(f"hidden path leaked into package: {path}")
        if path.name in {"oracle.md", "expected.json"}:
            findings.append(f"oracle file leaked into package: {path}")

    for metadata_path in package_root.rglob("metadata.json"):
        case_dir = metadata_path.parent
        if not (case_dir / "client").is_dir():
            findings.append(f"packaged case is missing client/: {case_dir}")
    return findings


def _copy_case_bank_case(case_dir: Path, package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    for child in case_dir.iterdir():
        if child.name in CASE_BANK_STRIPPED_NAMES:
            continue
        destination = package_dir / child.name
        if child.is_dir():
            shutil.copytree(
                child,
                destination,
                ignore=shutil.ignore_patterns(*CASE_BANK_STRIPPED_NAMES),
            )
        else:
            shutil.copy2(child, destination)


def _resolve_link(base_file: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_file.parent / path
