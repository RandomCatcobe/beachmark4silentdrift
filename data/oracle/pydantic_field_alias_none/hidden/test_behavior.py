"""Hidden pytest oracle.

Verifies that the curated reproduction captured a real old/new behavior diff.
"""

import json
from pathlib import Path


def test_behavior_matches_expected():
    expected = json.loads((Path(__file__).parent / "expected.json").read_text())
    assert expected["keep"] is True
    assert expected["old_stdout"] != expected["new_stdout"]
    assert expected["diff_summary"]
