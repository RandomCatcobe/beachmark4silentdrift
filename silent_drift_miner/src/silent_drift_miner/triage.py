"""Triage queue helpers for Phase 1."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, TypedDict

from .schema import DriftCandidate, TriageDecision, utc_now_iso


class TriageItem(TypedDict):
    candidate_id: str
    candidate: dict
    decision: Optional[str]
    notes: str
    reviewer: str
    created_at: str
    updated_at: str


def build_queue_items(candidates: list[DriftCandidate]) -> list[TriageItem]:
    seen: set[str] = set()
    items: list[TriageItem] = []
    for candidate in candidates:
        if candidate.candidate_id in seen:
            raise ValueError(f"duplicate candidate_id {candidate.candidate_id!r}")
        seen.add(candidate.candidate_id)
        now = utc_now_iso()
        items.append(
            {
                "candidate_id": candidate.candidate_id,
                "candidate": json.loads(candidate.to_jsonl()),
                "decision": None,
                "notes": "",
                "reviewer": "",
                "created_at": now,
                "updated_at": now,
            }
        )
    return items


def load_triage_queue(path: Path) -> list[TriageItem]:
    items: list[TriageItem] = []
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
                _validate_item(item)
            except Exception as exc:
                raise ValueError(f"line {lineno}: malformed triage queue item: {exc}") from exc
            items.append(item)
    return items


def write_triage_queue(items: list[TriageItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for item in items:
            _validate_item(item)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    tmp.replace(path)


def find_next_item(items: list[TriageItem]) -> Optional[TriageItem]:
    for item in items:
        if item.get("decision") is None:
            return item
    return None


def mark_queue_item(
    items: list[TriageItem],
    candidate_id: str,
    decision_value: str,
    notes: str = "",
    reviewer: str = "",
    overwrite: bool = False,
) -> TriageItem:
    decision = TriageDecision(decision_value)
    for item in items:
        if item["candidate_id"] != candidate_id:
            continue
        if item.get("decision") is not None and not overwrite:
            raise ValueError(
                f"candidate {candidate_id!r} already has decision {item['decision']!r}; "
                "use --overwrite to change it"
            )
        item["decision"] = decision.value
        item["notes"] = notes
        item["reviewer"] = reviewer
        item["updated_at"] = utc_now_iso()
        return item
    raise ValueError(f"candidate_id not found: {candidate_id}")


def export_candidate_rows(
    items: list[TriageItem],
    decision_value: Optional[str] = None,
    include_undecided: bool = False,
) -> list[str]:
    if decision_value is not None:
        decision_value = TriageDecision(decision_value).value

    rows: list[str] = []
    for item in items:
        decision = item.get("decision")
        if decision_value is not None and decision != decision_value:
            continue
        if decision_value is None and decision is None and not include_undecided:
            continue
        candidate = DriftCandidate.from_jsonl(json.dumps(item["candidate"], ensure_ascii=False))
        rows.append(candidate.to_jsonl())
    return rows


def queue_summary(items: list[TriageItem]) -> dict[str, Any]:
    by_decision: dict[str, int] = {}
    undecided = 0
    for item in items:
        decision = item.get("decision")
        if decision is None:
            undecided += 1
            continue
        by_decision[decision] = by_decision.get(decision, 0) + 1
    return {
        "total": len(items),
        "undecided": undecided,
        "by_decision": by_decision,
    }


def _validate_item(item: TriageItem) -> None:
    candidate_id = item.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ValueError("missing candidate_id")
    candidate = item.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("missing candidate snapshot")
    if candidate.get("candidate_id") != candidate_id:
        raise ValueError("candidate snapshot id mismatch")
    decision = item.get("decision")
    if decision is not None:
        TriageDecision(decision)
