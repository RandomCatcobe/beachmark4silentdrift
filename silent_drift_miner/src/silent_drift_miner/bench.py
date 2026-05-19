"""Benchmark package assembly."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .curation import load_curated_case
from .oracle import load_oracle_spec


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
    public_src = Path(oracle.public_readme_path).parent
    public_dst = package_dir / "public"
    shutil.copytree(public_src, public_dst)
    manifest = {
        "task_id": case.case_id,
        "case_id": case.case_id,
        "candidate_id": case.candidate_id,
        "levels": levels,
        "public_dir": "public",
    }
    (package_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return package_dir
