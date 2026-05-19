"""Offline synthetic end-to-end demo for Phase 1.

The demo mines the bundled pandas fixture, builds a triage queue, marks the
first candidate, and exports accepted candidates. It uses no network and no
LLM API.

Run from this package directory:
    python tools/demo_synthetic_e2e.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from silent_drift_miner.cli import main  # noqa: E402
from silent_drift_miner.triage import load_triage_queue  # noqa: E402


def run() -> int:
    artifact_root = ROOT.parent / ".demo_artifacts" / "synthetic_e2e"
    fixture = ROOT / "data" / "fixtures" / "pandas_changelog.md"
    candidates = artifact_root / "candidates" / "pandas.jsonl"
    queue = artifact_root / "triage" / "pandas_queue.jsonl"
    accepted = artifact_root / "triage" / "pandas_accepted.jsonl"

    rc = main(
        [
            "mine",
            "--library",
            "pandas",
            "--ecosystem",
            "python",
            "--source",
            str(fixture),
            "--source-url",
            "fixture://pandas_changelog.md",
            "--artifact-root",
            str(artifact_root),
            "--out",
            str(candidates),
            "--llm-filter",
        ]
    )
    if rc != 0:
        return rc

    rc = main(
        [
            "triage",
            "build",
            "--artifact-root",
            str(artifact_root),
            "--candidates",
            str(candidates),
            "--out",
            str(queue),
        ]
    )
    if rc != 0:
        return rc

    items = load_triage_queue(queue)
    if items:
        rc = main(
            [
                "triage",
                "mark",
                "--artifact-root",
                str(artifact_root),
                "--queue",
                str(queue),
                "--candidate-id",
                items[0]["candidate_id"],
                "--decision",
                "accept_for_reproduction",
                "--notes",
                "synthetic demo accepted first candidate",
            ]
        )
        if rc != 0:
            return rc

    return main(
        [
            "triage",
            "export",
            "--artifact-root",
            str(artifact_root),
            "--queue",
            str(queue),
            "--out",
            str(accepted),
            "--decision",
            "accept_for_reproduction",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(run())
