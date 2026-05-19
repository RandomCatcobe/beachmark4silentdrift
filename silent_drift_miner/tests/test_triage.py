from __future__ import annotations

import json

from silent_drift_miner.cli import main, write_candidates_jsonl
from silent_drift_miner.schema import Confidence, DriftCandidate, DriftCategory, Evidence
from silent_drift_miner.triage import export_candidate_rows, load_triage_queue, mark_queue_item


def _candidate(candidate_id: str, title: str) -> DriftCandidate:
    return DriftCandidate(
        candidate_id=candidate_id,
        library="pandas",
        ecosystem="python",
        version_new="2.0.0",
        category=DriftCategory.DEFAULT_SHIFT,
        confidence=Confidence.WEAK,
        title=title,
        evidence=[
            Evidence(
                url=f"https://example.com/{candidate_id}",
                source_type="changelog",
                snippet_raw="raw",
                snippet_paraphrased="paraphrase",
                retrieved_at="2026-01-01T00:00:00",
            )
        ],
    )


def test_triage_build_mark_and_export_roundtrip(tmp_path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    queue_path = tmp_path / "triage" / "queue.jsonl"
    accepted_path = tmp_path / "triage" / "accepted.jsonl"
    write_candidates_jsonl(
        [_candidate("cand-a", "first"), _candidate("cand-b", "second")],
        candidates_path,
    )

    assert main(["triage", "build", "--candidates", str(candidates_path), "--out", str(queue_path)]) == 0
    items = load_triage_queue(queue_path)

    assert [item["candidate_id"] for item in items] == ["cand-a", "cand-b"]
    assert all(item["decision"] is None for item in items)

    assert main(
        [
            "triage",
            "mark",
            "--queue",
            str(queue_path),
            "--candidate-id",
            "cand-a",
            "--decision",
            "accept_for_reproduction",
            "--notes",
            "default changed",
        ]
    ) == 0

    marked = load_triage_queue(queue_path)
    assert marked[0]["decision"] == "accept_for_reproduction"
    assert marked[0]["notes"] == "default changed"

    assert main(
        [
            "triage",
            "export",
            "--queue",
            str(queue_path),
            "--out",
            str(accepted_path),
            "--decision",
            "accept_for_reproduction",
        ]
    ) == 0

    rows = [json.loads(line) for line in accepted_path.read_text(encoding="utf-8").splitlines()]
    assert [row["candidate_id"] for row in rows] == ["cand-a"]


def test_triage_mark_requires_overwrite_for_existing_decision(tmp_path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    queue_path = tmp_path / "queue.jsonl"
    write_candidates_jsonl([_candidate("cand-a", "first")], candidates_path)
    assert main(["triage", "build", "--candidates", str(candidates_path), "--out", str(queue_path)]) == 0
    items = load_triage_queue(queue_path)

    mark_queue_item(items, "cand-a", "borderline")
    try:
        mark_queue_item(items, "cand-a", "needs_more_context")
    except ValueError as exc:
        assert "use --overwrite" in str(exc)
    else:
        raise AssertionError("expected overwrite guard")

    changed = mark_queue_item(items, "cand-a", "needs_more_context", overwrite=True)
    assert changed["decision"] == "needs_more_context"


def test_triage_export_skips_undecided_by_default(tmp_path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    queue_path = tmp_path / "queue.jsonl"
    write_candidates_jsonl([_candidate("cand-a", "first")], candidates_path)
    assert main(["triage", "build", "--candidates", str(candidates_path), "--out", str(queue_path)]) == 0

    items = load_triage_queue(queue_path)

    assert export_candidate_rows(items) == []
    assert len(export_candidate_rows(items, include_undecided=True)) == 1
