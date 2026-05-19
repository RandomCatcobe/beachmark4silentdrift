from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("SILENT_DRIFT_SKIP_REAL_TOOLCHAIN_SMOKE") != "1":
        return

    skip_real_toolchain = pytest.mark.skip(
        reason="real toolchain smoke tests disabled by SILENT_DRIFT_SKIP_REAL_TOOLCHAIN_SMOKE"
    )
    for item in items:
        if "_runs_toy_case_with_real_" in item.name:
            item.add_marker(skip_real_toolchain)
