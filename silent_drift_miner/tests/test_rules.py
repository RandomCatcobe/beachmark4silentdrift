"""Tests for rule prescreen + schema roundtrip. Run with:
    cd src && python -m unittest discover -s ../tests -t .
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make src/ importable when running from repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from silent_drift_miner.extractors.rules import (  # noqa: E402
    extract_candidates,
    score_chunk,
    _chunk_section,
)
from silent_drift_miner.schema import (  # noqa: E402
    Confidence,
    DriftCandidate,
    DriftCategory,
    Evidence,
)


class TestChunkSplitting(unittest.TestCase):
    def test_bullets_split(self):
        text = """
- First bullet about something boring
- Second bullet that mentions the default has been updated to UTF-8
- Third bullet about a removal
"""
        chunks = _chunk_section(text)
        self.assertEqual(len(chunks), 3)
        self.assertTrue(any("default has been updated" in c for c in chunks))

    def test_paragraphs_split(self):
        text = """
First paragraph talking about something.

Second paragraph that says the timezone default is now UTC.

Third paragraph.
"""
        chunks = _chunk_section(text)
        # min length is 25 chars; "Third paragraph." is shorter -> filtered out
        self.assertEqual(len(chunks), 2)


class TestRuleScoring(unittest.TestCase):
    def test_positive_signal_hit(self):
        chunk = "The default charset for InputStreamReader is now UTF-8 on JDK 18."
        score, hits, cat = score_chunk(chunk)
        self.assertGreaterEqual(score, 4)
        self.assertEqual(cat, DriftCategory.LOCALE_ENCODING)

    def test_anti_signal_reduces_score(self):
        chunk = "Removed the deprecated foo() method; this is a breaking change."
        score, hits, cat = score_chunk(chunk)
        self.assertLessEqual(score, 0)

    def test_timezone_signal(self):
        chunk = "The timezone default is now UTC for new connections."
        score, hits, cat = score_chunk(chunk)
        self.assertGreaterEqual(score, 4)
        self.assertEqual(cat, DriftCategory.TIMEZONE_SHIFT)

    def test_pagination_signal(self):
        chunk = "The default page size has been increased from 10 to 100."
        score, hits, cat = score_chunk(chunk)
        self.assertGreaterEqual(score, 4)
        self.assertEqual(cat, DriftCategory.PAGINATION_SEMANTICS)

    def test_partition_signal(self):
        chunk = "The default partitioner is now sticky instead of round-robin."
        score, hits, cat = score_chunk(chunk)
        self.assertGreaterEqual(score, 4)
        self.assertEqual(cat, DriftCategory.ORDERING_CHANGE)


class TestExtractEndToEnd(unittest.TestCase):
    def test_extract_produces_weak_candidates(self):
        section = """
- The default charset is now UTF-8 across standard I/O classes.
- Removed the deprecated readLine(int) overload.
- Fixed a bug in toString().
- The timezone default has changed from system to UTC.
"""
        cands = extract_candidates(
            library="jdk",
            ecosystem="jvm",
            version_label="18",
            section_body=section,
            source_url="https://example.com/release",
            threshold=4,
            retrieved_at="2024-01-01T00:00:00",
        )
        # we expect at least the charset and timezone bullets to make it through
        self.assertGreaterEqual(len(cands), 2)
        cats = {c.category for c in cands}
        self.assertIn(DriftCategory.LOCALE_ENCODING, cats)
        self.assertIn(DriftCategory.TIMEZONE_SHIFT, cats)
        for c in cands:
            self.assertEqual(c.confidence, Confidence.WEAK)
            self.assertEqual(c.extracted_by, "rule")
            self.assertTrue(c.candidate_id)
            self.assertTrue(c.evidence and c.evidence[0].url)


class TestSchemaRoundtrip(unittest.TestCase):
    def test_jsonl_roundtrip(self):
        c = DriftCandidate(
            candidate_id="abc",
            library="lib",
            ecosystem="jvm",
            version_new="1.0",
            category=DriftCategory.TIMEZONE_SHIFT,
            confidence=Confidence.UNCERTAIN_SILENCE,
            title="t",
            summary_paraphrased="s",
            api_surface=["A.b"],
            evidence=[Evidence(
                url="https://x",
                source_type="changelog",
                snippet_raw="raw",
                snippet_paraphrased="p",
                retrieved_at="2024",
            )],
            why_flagged=["timezone_default"],
        )
        line = c.to_jsonl()
        back = DriftCandidate.from_jsonl(line)
        self.assertEqual(back.candidate_id, c.candidate_id)
        self.assertEqual(back.category, DriftCategory.TIMEZONE_SHIFT)
        self.assertEqual(back.confidence, Confidence.UNCERTAIN_SILENCE)
        self.assertEqual(back.evidence[0].url, "https://x")


if __name__ == "__main__":
    unittest.main()
