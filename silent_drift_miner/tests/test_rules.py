"""Tests for rule prescreen + schema roundtrip."""
from __future__ import annotations

from silent_drift_miner.cli import load_candidates_jsonl, summarize, write_candidates_jsonl
from silent_drift_miner.extractors.rules import _chunk_section, extract_candidates, score_chunk
from silent_drift_miner.schema import Confidence, DriftCandidate, DriftCategory, Evidence


def test_bullets_split() -> None:
    text = """
- First bullet about something boring
- Second bullet that mentions the default has been updated to UTF-8
- Third bullet about a removal
"""
    chunks = _chunk_section(text)

    assert len(chunks) == 3
    assert any("default has been updated" in chunk for chunk in chunks)


def test_paragraphs_split() -> None:
    text = """
First paragraph talking about something.

Second paragraph that says the timezone default is now UTC.

Third paragraph.
"""
    chunks = _chunk_section(text)

    assert len(chunks) == 2


def test_positive_signal_hit() -> None:
    chunk = "The default charset for InputStreamReader is now UTF-8 on JDK 18."
    score, _hits, category = score_chunk(chunk)

    assert score >= 4
    assert category == DriftCategory.LOCALE_ENCODING


def test_anti_signal_reduces_score() -> None:
    chunk = "Removed the deprecated foo() method; this is a breaking change."
    score, _hits, _category = score_chunk(chunk)

    assert score <= 0


def test_timezone_signal() -> None:
    chunk = "The timezone default is now UTC for new connections."
    score, _hits, category = score_chunk(chunk)

    assert score >= 4
    assert category == DriftCategory.TIMEZONE_SHIFT


def test_pagination_signal() -> None:
    chunk = "The default page size has been increased from 10 to 100."
    score, _hits, category = score_chunk(chunk)

    assert score >= 4
    assert category == DriftCategory.PAGINATION_SEMANTICS


def test_partition_signal() -> None:
    chunk = "The default partitioner is now sticky instead of round-robin."
    score, _hits, category = score_chunk(chunk)

    assert score >= 4
    assert category == DriftCategory.ORDERING_CHANGE


def test_extract_produces_weak_candidates() -> None:
    section = """
- The default charset is now UTF-8 across standard I/O classes.
- Removed the deprecated readLine(int) overload.
- Fixed a bug in toString().
- The timezone default has changed from system to UTC.
"""
    candidates = extract_candidates(
        library="jdk",
        ecosystem="jvm",
        version_label="18",
        section_body=section,
        source_url="https://example.com/release",
        threshold=4,
        retrieved_at="2024-01-01T00:00:00",
    )

    assert len(candidates) >= 2
    categories = {candidate.category for candidate in candidates}
    assert DriftCategory.LOCALE_ENCODING in categories
    assert DriftCategory.TIMEZONE_SHIFT in categories
    for candidate in candidates:
        assert candidate.confidence == Confidence.WEAK
        assert candidate.extracted_by == "rule"
        assert candidate.candidate_id
        assert candidate.evidence and candidate.evidence[0].url


def test_jsonl_roundtrip() -> None:
    candidate = _candidate()

    line = candidate.to_jsonl()
    back = DriftCandidate.from_jsonl(line)

    assert back.candidate_id == candidate.candidate_id
    assert back.category == DriftCategory.TIMEZONE_SHIFT
    assert back.confidence == Confidence.UNCERTAIN_SILENCE
    assert back.evidence[0].url == "https://x"


def test_candidate_file_roundtrip_uses_tmp_path(tmp_path) -> None:
    path = tmp_path / "candidates" / "lib.jsonl"
    candidate = _candidate()

    write_candidates_jsonl([candidate], path)
    loaded = load_candidates_jsonl(path)

    assert [item.candidate_id for item in loaded] == [candidate.candidate_id]


def test_summary_counts_source_type() -> None:
    summary = summarize([_candidate()])

    assert summary["by_source"] == {"changelog": 1}


def _candidate() -> DriftCandidate:
    return DriftCandidate(
        candidate_id="abc",
        library="lib",
        ecosystem="jvm",
        version_new="1.0",
        category=DriftCategory.TIMEZONE_SHIFT,
        confidence=Confidence.UNCERTAIN_SILENCE,
        title="t",
        summary_paraphrased="s",
        api_surface=["A.b"],
        evidence=[
            Evidence(
                url="https://x",
                source_type="changelog",
                snippet_raw="raw",
                snippet_paraphrased="p",
                retrieved_at="2024",
            )
        ],
        why_flagged=["timezone_default"],
    )
