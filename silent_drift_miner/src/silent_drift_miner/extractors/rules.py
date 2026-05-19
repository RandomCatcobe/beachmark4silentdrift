"""
Rule-based prescreen.

This is intentionally noisy-but-cheap: it converts a changelog section into
small chunks (bullets or paragraphs) and scores each chunk for "smells like
silent semantic drift" using regex/keyword rules.

Anything above `threshold` becomes a WEAK DriftCandidate that the LLM layer
then either upgrades to UNCERTAIN_SILENCE / HIGH, or rejects.

We deliberately keep precision low and recall high here. False positives are
cheap (the LLM will drop them); false negatives are fatal (lost cases).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from ..schema import (
    Confidence,
    DriftCandidate,
    DriftCategory,
    Evidence,
)


# -----------------------------------------------------------------------
# Signal patterns: behavior-change language that doesn't imply hard break
# -----------------------------------------------------------------------
# Each rule has (name, regex, category_hint, score).
# `category_hint` is just a guess; the LLM layer makes the final call.
# Score is roughly: "how confident am I this is silent-ish drift?"

SIGNAL_RULES: list[tuple[str, re.Pattern, DriftCategory, int]] = [
    # generic default-change phrasing — strongest weak signal
    ("default_changed_from_to",
     re.compile(r"default(?:s|ed)?\s+(?:has\s+)?(?:been\s+)?(?:changed|updated)\s+(?:from|to)\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("changed_default_value",  # the "X changed (their)? default value from ... to ..." inversion
     re.compile(r"\bchanged\s+(?:its|their|the)?\s*default\s+value\s+from\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("now_defaults_to",
     re.compile(r"\bnow\s+defaults?\s+to\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("now_x_by_default",  # "follow redirects are now enabled by default"
     re.compile(r"\bare?\s+now\s+\w+(?:\s+\w+){0,3}\s+by\s+default\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("no_longer_x_by_default",  # "trailing slash matching is no longer enabled by default"
     re.compile(r"\bno\s+longer\s+\w+(?:\s+\w+){0,3}\s+by\s+default\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("the_default_for_x_is_now",
     re.compile(r"\bthe\s+default\s+(?:value\s+)?(?:for\s+\w+\s+)?is\s+now\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 4),
    ("default_value_of",
     re.compile(r"default\s+value\s+of\s+\S+\s+(?:is|has|changed)", re.I),
     DriftCategory.DEFAULT_SHIFT, 3),

    # behavior-change phrasing
    ("no_longer_returns",
     re.compile(r"\bno\s+longer\s+(?:returns?|matches?|includes?|defaults?|treats?)\b", re.I),
     DriftCategory.DEFAULT_SHIFT, 3),
    ("previously_now",
     re.compile(r"\bpreviously\b.{0,80}\bnow\b", re.I | re.S),
     DriftCategory.UNCATEGORIZED, 3),
    ("behaviour_change",
     re.compile(r"\bbehavi(?:ou)?r\s+(?:change|has\s+changed|is\s+now)\b", re.I),
     DriftCategory.UNCATEGORIZED, 3),
    ("now_uses",
     re.compile(r"\bnow\s+uses\b", re.I),
     DriftCategory.UNCATEGORIZED, 2),

    # timezone
    ("timezone_default",
     re.compile(r"\b(?:timezone|time\s*zone|tz|UTC)\b.{0,40}\b(?:default|changed|now)\b", re.I),
     DriftCategory.TIMEZONE_SHIFT, 4),
    ("zone_id_offset",
     re.compile(r"\b(?:ZoneId|ZoneOffset|tzdata|tzdb|CLDR)\b", re.I),
     DriftCategory.TIMEZONE_SHIFT, 2),

    # locale / encoding
    ("charset_default",
     re.compile(r"\b(?:charset|encoding|UTF-?8|default\s+charset)\b.{0,40}\b(?:default|changed|now)\b", re.I),
     DriftCategory.LOCALE_ENCODING, 4),
    ("locale_default",
     re.compile(r"\blocale\b.{0,40}\b(?:default|changed|now)\b", re.I),
     DriftCategory.LOCALE_ENCODING, 3),

    # pagination / count
    ("page_size_default",
     re.compile(r"\b(?:page\s*size|per[_\s-]?page|limit|max\w*\s*results)\b.{0,40}\b(?:default|changed|now|increased|decreased)\b", re.I),
     DriftCategory.PAGINATION_SEMANTICS, 4),
    ("cursor_or_offset",
     re.compile(r"\b(?:cursor[-_]based|offset[-_]based|keyset)\s+pagination\b", re.I),
     DriftCategory.PAGINATION_SEMANTICS, 3),
    ("total_count_semantics",
     re.compile(r"\btotal[_\s-]*hits?|track_total_hits\b", re.I),
     DriftCategory.FIELD_MEANING, 3),

    # ordering
    ("sort_order_default",
     re.compile(r"\b(?:sort|order|ordering|sorted)\b.{0,40}\b(?:default|changed|now|relevance|recency)\b", re.I),
     DriftCategory.ORDERING_CHANGE, 3),
    ("partition_default",
     re.compile(r"\b(?:partition|partitioner|partition\s*assignment)\b.{0,60}\b(?:default|sticky|round[-\s]?robin|uniform|changed)\b", re.I),
     DriftCategory.ORDERING_CHANGE, 4),

    # unit shifts
    ("unit_seconds_ms",
     re.compile(r"\b(?:milliseconds?|microseconds?|nanoseconds?|seconds?)\b.{0,40}\b(?:default|changed|now|return|return\s*type|precision)\b", re.I),
     DriftCategory.UNIT_SHIFT, 3),
    ("unit_currency",
     re.compile(r"\b(?:cents|dollars|minor\s+units?|major\s+units?)\b", re.I),
     DriftCategory.UNIT_SHIFT, 3),

    # null / empty / missing
    ("null_vs_empty",
     re.compile(r"\b(?:returns?|emits?)\s+(?:null|empty|an\s+empty\s+(?:list|array|map))\s+instead\s+of\b", re.I),
     DriftCategory.NULL_EMPTY, 4),
    ("absent_field",
     re.compile(r"\b(?:field|property|attribute)\s+\w+\s+(?:is\s+)?(?:no\s+longer\s+)?(?:populated|present|included)\b", re.I),
     DriftCategory.NULL_EMPTY, 3),
]


# Anti-patterns: language that says "this is a loud, visible break" -> not silent
ANTI_RULES: list[tuple[str, re.Pattern, int]] = [
    ("removed_or_deleted",
     re.compile(r"\b(?:removed|deleted|dropped\s+support\s+for)\b", re.I), 3),
    ("breaking_change_explicit",
     re.compile(r"\bbreaking[\s-]change\b", re.I), 2),  # mild down-weight; sometimes BC is silent
    ("throws_exception",
     re.compile(r"\bnow\s+throws?\b|\bwill\s+throw\b", re.I), 3),
    ("compile_error",
     re.compile(r"\bcompil(?:e|ation)\s+error\b", re.I), 4),
    ("bugfix_marker",
     re.compile(r"^\s*(?:fix(?:es|ed)?|bugfix)\b[:\s]", re.I | re.M), 2),
    ("type_signature_change",
     re.compile(r"\b(?:signature|return\s+type|parameter\s+type)\s+(?:of\s+\w+\s+)?(?:changed|is\s+now)\b", re.I), 2),
]


@dataclass
class RuleHit:
    rule_name: str
    category: DriftCategory
    score: int
    snippet: str


def _chunk_section(section_body: str) -> list[str]:
    """Split a release-note section into bullet-sized chunks.

    Strategy:
      1. If the section has markdown bullets, each bullet (and its continuation
         lines) is a chunk.
      2. Otherwise, split on blank lines.
      3. Drop chunks shorter than 25 chars (usually noise like 'See #123').
    """
    text = section_body.strip()
    # normalize line endings
    text = text.replace("\r\n", "\n")

    bullet_re = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.M)
    if bullet_re.search(text):
        # split, keeping bullet content together
        parts: list[str] = []
        cur: list[str] = []
        for line in text.split("\n"):
            if bullet_re.match(line) and cur:
                parts.append("\n".join(cur).strip())
                cur = [line]
            else:
                cur.append(line)
        if cur:
            parts.append("\n".join(cur).strip())
    else:
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    return [p for p in parts if len(p) >= 25]


def score_chunk(chunk: str) -> tuple[int, list[RuleHit], DriftCategory]:
    """Score a chunk; return (score, hits, dominant_category)."""
    hits: list[RuleHit] = []
    score = 0
    for name, pat, cat, s in SIGNAL_RULES:
        if pat.search(chunk):
            hits.append(RuleHit(name, cat, s, chunk[:200]))
            score += s
    for name, pat, penalty in ANTI_RULES:
        if pat.search(chunk):
            score -= penalty
            hits.append(RuleHit(f"ANTI::{name}", DriftCategory.UNCATEGORIZED, -penalty, ""))

    # pick dominant positive category by accumulated score; tie-break by
    # specificity (a concrete bucket beats the generic default_shift bucket).
    cat_scores: dict[DriftCategory, int] = {}
    for h in hits:
        if h.score > 0:
            cat_scores[h.category] = cat_scores.get(h.category, 0) + h.score
    if not cat_scores:
        return score, hits, DriftCategory.UNCATEGORIZED
    # higher specificity = preferred when scores tie
    specificity = {
        DriftCategory.TIMEZONE_SHIFT: 5,
        DriftCategory.LOCALE_ENCODING: 5,
        DriftCategory.UNIT_SHIFT: 5,
        DriftCategory.PAGINATION_SEMANTICS: 5,
        DriftCategory.ORDERING_CHANGE: 4,
        DriftCategory.NULL_EMPTY: 4,
        DriftCategory.FIELD_MEANING: 4,
        DriftCategory.AUTH_SCOPE: 4,
        DriftCategory.RATE_LIMIT_SCOPE: 4,
        DriftCategory.DEFAULT_SHIFT: 2,        # most generic positive bucket
        DriftCategory.UNCATEGORIZED: 0,
    }
    dominant = max(cat_scores.items(),
                   key=lambda kv: (kv[1], specificity.get(kv[0], 0)))[0]
    return score, hits, dominant


def extract_candidates(
    library: str,
    ecosystem: str,
    version_label: str,
    section_body: str,
    source_url: str,
    threshold: int = 4,
    retrieved_at: str = "",
) -> list[DriftCandidate]:
    """Run rule scoring over one release-note section."""
    out: list[DriftCandidate] = []
    for chunk in _chunk_section(section_body):
        score, hits, dominant = score_chunk(chunk)
        if score < threshold:
            continue
        positive_rules = [h.rule_name for h in hits if h.score > 0]
        ev = Evidence(
            url=source_url,
            source_type="changelog",
            snippet_raw=chunk,
            snippet_paraphrased="",  # filled by LLM stage
            retrieved_at=retrieved_at,
        ).truncate()
        cand = DriftCandidate(
            candidate_id=DriftCandidate.make_id(library, version_label, source_url + "#" + chunk[:60]),
            library=library,
            ecosystem=ecosystem,
            version_new=version_label,
            version_old=None,
            category=dominant,
            confidence=Confidence.WEAK,
            title=_make_title(chunk),
            summary_paraphrased="",
            reproduce_hypothesis="",
            api_surface=[],
            evidence=[ev],
            why_flagged=positive_rules,
            extracted_by="rule",
            pipeline_stage=1,
        )
        out.append(cand)
    return out


def _make_title(chunk: str) -> str:
    # first non-empty line, stripped of markdown bullet markers, truncated
    first = next((ln.strip() for ln in chunk.split("\n") if ln.strip()), "")
    first = re.sub(r"^[-*+]\s+|^\d+\.\s+", "", first)
    return first[:120]
