"""Evaluation packaging facade for case-bank folders."""
from __future__ import annotations

from pathlib import Path

from silent_drift_miner.bench import create_case_bank_eval_package


def pack_cases(src_root: Path, out_root: Path) -> Path:
    return create_case_bank_eval_package(src_root, out_root)
