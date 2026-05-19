"""Curation manifests for reproduced cases."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .reproduction import ReproductionResult, load_reproduction_result
from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


class CurationDecision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"


@dataclass
class CuratedCase:
    case_id: str
    decision: CurationDecision
    candidate_id: str
    reproduction_result: str
    keep: bool
    drop_reason: Optional[str] = None
    source_url: Optional[str] = None
    source_excerpt: Optional[str] = None
    retrieved_at: Optional[str] = None
    ecosystem: Optional[str] = None
    version_old: Optional[str] = None
    version_new: Optional[str] = None
    api_surface: list[str] = field(default_factory=list)
    review_notes: Optional[str] = None
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_yaml(self) -> str:
        data = asdict(self)
        data["decision"] = self.decision.value
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {_yaml_scalar(value)}")
        return "\n".join(lines) + "\n"


def create_curated_case(
    result_path: Path,
    decision: str,
    case_id: str,
    source_url: str | None = None,
    source_excerpt: str | None = None,
    retrieved_at: str | None = None,
    ecosystem: str | None = None,
    version_old: str | None = None,
    version_new: str | None = None,
    api_surface: list[str] | None = None,
    review_notes: str | None = None,
) -> CuratedCase:
    result = load_reproduction_result(result_path)
    curation_decision = CurationDecision(decision)
    _validate_decision_matches_result(result, curation_decision)
    return CuratedCase(
        case_id=case_id,
        decision=curation_decision,
        candidate_id=result.candidate_id,
        reproduction_result=str(result_path),
        keep=result.keep,
        drop_reason=result.drop_reason.value if result.drop_reason else None,
        source_url=source_url,
        source_excerpt=source_excerpt,
        retrieved_at=retrieved_at,
        ecosystem=ecosystem,
        version_old=version_old,
        version_new=version_new,
        api_surface=list(api_surface or []),
        review_notes=review_notes,
    )


def write_curated_case(case: CuratedCase, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(case.to_yaml(), encoding="utf-8")


def load_curated_case(path: Path) -> CuratedCase:
    data = _read_simple_yaml(path)
    data["decision"] = CurationDecision(data["decision"])
    return CuratedCase(**data)


def _validate_decision_matches_result(
    result: ReproductionResult,
    decision: CurationDecision,
) -> None:
    if decision == CurationDecision.ACCEPT and not result.keep:
        raise ValueError("cannot accept a reproduction result with keep=false")
    if decision == CurationDecision.REJECT and result.keep:
        raise ValueError("cannot reject a reproduction result with keep=true")


def _yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(value, ensure_ascii=False)


def _read_simple_yaml(path: Path) -> dict:
    data = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, value = raw.split(":", 1)
        value = value.strip()
        if value == "null":
            parsed = None
        elif value == "true":
            parsed = True
        elif value == "false":
            parsed = False
        else:
            parsed = json.loads(value)
        data[key.strip()] = parsed
    return data
