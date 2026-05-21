"""Repository-root entry shim for case-bank tools."""
from __future__ import annotations

import sys
from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "silent_drift_miner" / "src"
if _SOURCE_ROOT.is_dir():
    sys.path.insert(0, str(_SOURCE_ROOT))

_SOURCE_PACKAGE = _SOURCE_ROOT / "case_bank"
if _SOURCE_PACKAGE.is_dir():
    __path__.append(str(_SOURCE_PACKAGE))

__all__ = ["__version__"]

__version__ = "0.1.0"
