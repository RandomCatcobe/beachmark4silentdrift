"""
Data schema for drift candidates flowing through the mining pipeline.

A DriftCandidate is the unit produced by Layer 1 (CHANGELOG/release-note mining).
Downstream layers (auto-reproduce, oracle generation) add fields without
breaking this base contract.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


ARTIFACT_SCHEMA_VERSION = "1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


class ArtifactType(str, Enum):
    """File-based artifact families shared across pipeline stages."""

    CANDIDATE = "candidate"
    TRIAGE = "triage"
    REPRODUCTION = "reproduction"
    CURATION = "curation"
    ORACLE = "oracle"
    BENCHMARK_PACKAGE = "benchmark_package"
    AUDIT_REPORT = "audit_report"


class ArtifactStatus(str, Enum):
    """Lifecycle status for an artifact record."""

    PLANNED = "planned"
    CREATED = "created"
    VALIDATED = "validated"
    FAILED = "failed"


@dataclass
class ArtifactRecord:
    """A small manifest entry for any file produced by the pipeline."""

    artifact_type: ArtifactType
    path: str
    status: ArtifactStatus = ArtifactStatus.CREATED
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)
    producer: str = ""
    candidate_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        d = asdict(self)
        d["artifact_type"] = self.artifact_type.value
        d["status"] = self.status.value
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "ArtifactRecord":
        d = json.loads(text)
        d["artifact_type"] = ArtifactType(d["artifact_type"])
        d["status"] = ArtifactStatus(d["status"])
        return cls(**d)


class TriageDecision(str, Enum):
    ACCEPT_FOR_REPRODUCTION = "accept_for_reproduction"
    REJECT_HARD_BREAK = "reject_hard_break"
    REJECT_ADDITIVE_FEATURE = "reject_additive_feature"
    REJECT_BUGFIX_ONLY = "reject_bugfix_only"
    REJECT_NOT_SILENT = "reject_not_silent"
    BORDERLINE = "borderline"
    NEEDS_MORE_CONTEXT = "needs_more_context"


@dataclass
class TriageRecord:
    candidate_id: str
    decision: Optional[TriageDecision] = None
    notes: str = ""
    reviewer: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class ReproductionRecord:
    candidate_id: str
    status: ArtifactStatus = ArtifactStatus.PLANNED
    harness_path: Optional[str] = None
    result_path: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CurationRecord:
    candidate_id: str
    status: ArtifactStatus = ArtifactStatus.PLANNED
    keep_reason: str = ""
    drop_reason: str = ""
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class OracleRecord:
    candidate_id: str
    status: ArtifactStatus = ArtifactStatus.PLANNED
    public_test_path: Optional[str] = None
    hidden_test_path: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class BenchmarkPackageRecord:
    package_id: str
    candidate_ids: list[str] = field(default_factory=list)
    status: ArtifactStatus = ArtifactStatus.PLANNED
    package_path: Optional[str] = None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class AuditReportRecord:
    report_id: str
    package_id: str
    status: ArtifactStatus = ArtifactStatus.PLANNED
    report_path: Optional[str] = None
    findings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)


class DriftCategory(str, Enum):
    """High/medium priority categories from the research plan.

    Keep this small and orthogonal. New categories require explicit review;
    rule extractors should never invent a category not on this list.
    """
    UNIT_SHIFT = "unit_shift"                  # cents<->dollars, ms<->s, m<->ft
    TIMEZONE_SHIFT = "timezone_shift"           # UTC<->local, naive<->aware
    PAGINATION_SEMANTICS = "pagination_semantics"  # offset<->cursor, bounds
    DEFAULT_SHIFT = "default_shift"             # limits, regions, sort order, locale
    ORDERING_CHANGE = "ordering_change"         # relevance<->recency<->random
    LOCALE_ENCODING = "locale_encoding"         # charset, formatting, CLDR
    FIELD_MEANING = "field_meaning"             # "count" counts something different
    NULL_EMPTY = "null_empty"                   # null vs empty vs missing
    AUTH_SCOPE = "auth_scope"                   # permission semantics
    RATE_LIMIT_SCOPE = "rate_limit_scope"
    UNCATEGORIZED = "uncategorized"             # explicit "we noticed but unsure"


class Confidence(str, Enum):
    """Confidence that this is genuine silent drift, not a hard break.

    high              = clear evidence in source (paraphrased dev complaint
                        of being blindsided + behavior change with stable call shape)
    uncertain_silence = behavior change exists, but documentation trail
                        suggests notice may have existed somewhere
    weak              = candidate signal only; needs Layer 2 reproduce to keep
    """
    HIGH = "high"
    UNCERTAIN_SILENCE = "uncertain_silence"
    WEAK = "weak"


@dataclass
class Evidence:
    """One piece of textual evidence backing a candidate.

    We never store more than ~400 chars verbatim from any single source — both
    for copyright hygiene and because the LLM-paraphrased summary is what
    downstream stages should actually read.
    """
    url: str
    source_type: str           # "changelog" | "github_pr" | "github_issue" | "stackoverflow" | "reddit"
    snippet_raw: str           # short verbatim excerpt for traceability (<=400 chars)
    snippet_paraphrased: str   # our paraphrase, copyright-safe
    retrieved_at: str          # ISO timestamp

    def truncate(self) -> "Evidence":
        _marker = "...[truncated]"
        if len(self.snippet_raw) > 400 and not self.snippet_raw.endswith(_marker):
            self.snippet_raw = self.snippet_raw[:400] + _marker
        return self


@dataclass
class DriftCandidate:
    """A single candidate silent-drift case.

    The provenance chain is:
        Evidence (raw)
        -> rule extractor sets {category_guess, confidence=weak, why_flagged}
        -> LLM extractor refines {category, confidence, summary, hypothesis}
        -> (downstream) Layer 2 reproduce sets reproducer + actual_diff
    """
    # --- identity ---
    candidate_id: str           # sha1 of (library + version + first_url)[:16]
    library: str                # e.g. "spring-boot", "hibernate-orm"
    ecosystem: str              # "jvm" | "python" | "go" | "rust" | "js" | "other"

    # --- versioning ---
    version_new: str            # version where drift was introduced (best guess)
    version_old: Optional[str] = None  # version that had old behavior

    # --- classification ---
    category: DriftCategory = DriftCategory.UNCATEGORIZED
    confidence: Confidence = Confidence.WEAK

    # --- content ---
    title: str = ""             # short human-readable label
    summary_paraphrased: str = ""  # 2-3 sentence paraphrase of what changed
    reproduce_hypothesis: str = ""  # if known: minimal code path that triggers it
    api_surface: list[str] = field(default_factory=list)  # e.g. ["FileReader", "InputStreamReader"]

    # --- provenance ---
    evidence: list[Evidence] = field(default_factory=list)

    # --- pipeline bookkeeping ---
    why_flagged: list[str] = field(default_factory=list)  # rule names that matched
    extracted_by: str = "rule"  # "rule" | "llm" | "human"
    created_at: str = field(default_factory=utc_now_iso)
    pipeline_stage: int = 1     # 1=mined, 2=reproduced, 3=oracle_built, 4=human_approved

    # --- downstream fields, optional ---
    reproducer_path: Optional[str] = None    # path to docker repro dir
    docker_image_old: Optional[str] = None
    docker_image_new: Optional[str] = None
    oracle_test_path: Optional[str] = None

    @staticmethod
    def make_id(library: str, version_new: str, first_url: str) -> str:
        key = f"{library}::{version_new}::{first_url}"
        return hashlib.sha1(key.encode()).hexdigest()[:16]

    def to_jsonl(self) -> str:
        d = asdict(self)
        # Enum -> str
        d["category"] = self.category.value
        d["confidence"] = self.confidence.value
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "DriftCandidate":
        d = json.loads(line)
        d["category"] = DriftCategory(d["category"])
        d["confidence"] = Confidence(d["confidence"])
        d["evidence"] = [Evidence(**e) for e in d["evidence"]]
        return cls(**d)
