"""
LLM precision filter.

Layer 1b: takes the WEAK candidates from the rule prescreen and asks an LLM
to either:
  - reject  -> drop the candidate
  - keep    -> upgrade confidence, fill summary_paraphrased,
                reproduce_hypothesis, api_surface, version_old

We use Anthropic's API by default (claude-sonnet-4-6 is plenty for this).
The call is gated behind ANTHROPIC_API_KEY; if missing, refine() is a no-op
that prints a warning but keeps the rule output untouched. That way the rest
of the pipeline still runs end-to-end without an API key.

Cost note: each call is ~600 input tokens (system+candidate context) and
~300 output tokens. For 500 weak candidates, that's roughly $0.20 with
Sonnet at current pricing. Keep batching in mind if you scale to 5k+.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from ..schema import Confidence, DriftCandidate, DriftCategory


CATEGORY_VALUES = [c.value for c in DriftCategory]

SYSTEM_PROMPT = """You are a precision filter for a research dataset on
silent API drift. You receive ONE candidate excerpt from a library's
release notes that was flagged by a noisy keyword prescreen, and decide
whether it actually describes silent semantic drift.

Silent drift means ALL of:
  1. The public API call shape (name, parameters, return type) is unchanged.
  2. The library's behavior changed in a way that lets existing client code
     keep running but produce wrong results (different defaults, units,
     timezone, ordering, inclusion rules, field meaning, null/empty).
  3. The change is plausibly missable: not a loud "BREAKING" header with
     migration instructions in the same paragraph.

EXCLUDE (return reject):
  - signature changes, deletions, exceptions newly thrown
  - bug fixes ("fixed wrong X" — this is not drift)
  - additive features that don't alter existing call behavior
  - deprecations that come with a clear warning at call time

You MUST respond with ONLY valid JSON matching this schema:
{
  "verdict": "keep" | "reject",
  "category": one of %s,
  "confidence": "high" | "uncertain_silence",
  "version_old_guess": string or null,
  "summary_paraphrased": string (2-3 sentences, your own words),
  "reproduce_hypothesis": string (1-2 sentences on minimal code path),
  "api_surface": list of strings (concrete class/method/config names),
  "reasoning": string (1 sentence, why keep or reject)
}

Rules for the JSON content:
  - NEVER quote more than 12 consecutive words from the input.
  - "confidence=high" only if the text itself describes the change as
    quietly happening (e.g. user complaint pattern, "default was silently
    updated"); otherwise "uncertain_silence".
  - "category" must be on the allowed list verbatim.
  - If verdict is "reject", still fill category="uncategorized",
    confidence="uncertain_silence", and other fields as empty strings/lists.
""" % json.dumps(CATEGORY_VALUES)


USER_TEMPLATE = """Library: {library}  (ecosystem: {ecosystem})
Version this excerpt is from: {version_new}
Rule prescreen flags: {why_flagged}
Source URL: {source_url}

--- excerpt start ---
{chunk}
--- excerpt end ---

Return JSON only."""


@dataclass
class LLMConfig:
    model: str = "claude-sonnet-4-6"  # 4.6 is plenty for this filter
    api_url: str = "https://api.anthropic.com/v1/messages"
    api_version: str = "2023-06-01"
    max_tokens: int = 600
    timeout_s: int = 60
    request_pause: float = 0.3
    api_key_env: str = "ANTHROPIC_API_KEY"


class LLMRefiner:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.cfg = config or LLMConfig()
        self.api_key = os.environ.get(self.cfg.api_key_env)
        self._last_call = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def refine_batch(self, candidates: list[DriftCandidate]) -> list[DriftCandidate]:
        """Refine each candidate; drop those the LLM rejects."""
        if not self.enabled:
            print(f"[llm] ANTHROPIC_API_KEY not set; skipping refinement of "
                  f"{len(candidates)} candidates (keeping as WEAK)")
            return candidates

        kept: list[DriftCandidate] = []
        errors = 0
        for i, cand in enumerate(candidates):
            try:
                refined = self._refine_one(cand)
            except Exception as e:
                print(f"[llm] {type(e).__name__} on candidate {cand.candidate_id}: {e}")
                kept.append(cand)  # keep as WEAK on error rather than lose data
                errors += 1
                continue
            if refined is not None:
                kept.append(refined)
            if (i + 1) % 10 == 0:
                print(f"[llm] refined {i+1}/{len(candidates)} (kept so far: {len(kept)})")
        print(f"[llm] done: {len(kept)}/{len(candidates)} kept, {errors} errors")
        return kept

    def _refine_one(self, cand: DriftCandidate) -> Optional[DriftCandidate]:
        chunk = cand.evidence[0].snippet_raw if cand.evidence else ""
        url = cand.evidence[0].url if cand.evidence else ""
        user = USER_TEMPLATE.format(
            library=cand.library,
            ecosystem=cand.ecosystem,
            version_new=cand.version_new,
            why_flagged=", ".join(cand.why_flagged),
            source_url=url,
            chunk=chunk,
        )
        resp = self._call_anthropic(SYSTEM_PROMPT, user)
        parsed = _parse_json_response(resp)
        if not parsed:
            return cand  # keep as WEAK if parsing failed

        if parsed.get("verdict") != "keep":
            return None

        try:
            cand.category = DriftCategory(parsed.get("category", "uncategorized"))
        except ValueError:
            cand.category = DriftCategory.UNCATEGORIZED
        try:
            cand.confidence = Confidence(parsed.get("confidence", "uncertain_silence"))
        except ValueError:
            cand.confidence = Confidence.UNCERTAIN_SILENCE
        cand.version_old = parsed.get("version_old_guess") or None
        cand.summary_paraphrased = parsed.get("summary_paraphrased", "")
        cand.reproduce_hypothesis = parsed.get("reproduce_hypothesis", "")
        cand.api_surface = parsed.get("api_surface", []) or []
        cand.extracted_by = "llm"
        if cand.evidence:
            cand.evidence[0].snippet_paraphrased = cand.summary_paraphrased
        return cand

    def _call_anthropic(self, system: str, user: str) -> str:
        # rudimentary pacing
        elapsed = time.time() - self._last_call
        if elapsed < self.cfg.request_pause:
            time.sleep(self.cfg.request_pause - elapsed)
        self._last_call = time.time()

        payload = {
            "model": self.cfg.model,
            "max_tokens": self.cfg.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.cfg.api_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", self.api_key)
        req.add_header("anthropic-version", self.cfg.api_version)
        try:
            with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"anthropic HTTP {e.code}: {e.read()[:200]!r}") from e
        obj = json.loads(body)
        # response shape: {"content": [{"type":"text","text": "..."}], ...}
        parts = obj.get("content", [])
        text_chunks = [p.get("text", "") for p in parts if p.get("type") == "text"]
        return "\n".join(text_chunks)


class OfflineLLMFilter:
    """Deterministic no-network stand-in for the precision filter.

    This keeps fixture/demo runs shaped like the LLM path without sending any
    text to an API. It intentionally stays conservative and transparent.
    """

    enabled = True

    KEEP_TERMS = (
        "default",
        "now",
        "changed",
        "previously",
        "no longer",
        "instead of",
        "behavior",
        "behaviour",
    )
    REJECT_TERMS = (
        "deprecated",
        "removed",
        "deleted",
        "compile error",
        "now throws",
        "will throw",
    )

    def refine_batch(self, candidates: list[DriftCandidate]) -> list[DriftCandidate]:
        kept: list[DriftCandidate] = []
        for cand in candidates:
            refined = self._refine_one(cand)
            if refined is not None:
                kept.append(refined)
        return kept

    def _refine_one(self, cand: DriftCandidate) -> Optional[DriftCandidate]:
        text = " ".join(
            [
                cand.title,
                cand.summary_paraphrased,
                cand.evidence[0].snippet_raw if cand.evidence else "",
            ]
        ).lower()
        if any(term in text for term in self.REJECT_TERMS):
            return None
        if not any(term in text for term in self.KEEP_TERMS):
            return None

        cand.confidence = Confidence.UNCERTAIN_SILENCE
        cand.extracted_by = "llm_filter"
        if not cand.summary_paraphrased:
            cand.summary_paraphrased = (
                f"Offline filter kept this {cand.category.value} candidate because "
                "the excerpt describes changed runtime behavior with the public call shape intact."
            )
        if cand.evidence and not cand.evidence[0].snippet_paraphrased:
            cand.evidence[0].snippet_paraphrased = cand.summary_paraphrased
        if not cand.reproduce_hypothesis:
            cand.reproduce_hypothesis = (
                "Compare the same client call or configuration on the old and new versions, "
                "then assert that the observed default behavior differs."
            )
        if not cand.api_surface and cand.evidence:
            cand.api_surface = _extract_api_surface(cand.evidence[0].snippet_raw)
        return cand


def _extract_api_surface(text: str) -> list[str]:
    backticked = re.findall(r"`([^`]+)`", text)
    dotted = re.findall(r"\b[A-Za-z_][\w]*(?:\.[A-Za-z_][\w-]*)+\b", text)
    seen: set[str] = set()
    out: list[str] = []
    for item in backticked + dotted:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out[:6]


def _parse_json_response(text: str) -> Optional[dict]:
    """Be lenient: strip code fences, find first {...} block."""
    text = text.strip()
    # strip ```json ... ``` fences if present
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S)
    # find outermost JSON object
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
