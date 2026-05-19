from __future__ import annotations

import json

from silent_drift_miner.cli import main


def test_mine_source_with_offline_llm_filter(tmp_path) -> None:
    fixture = tmp_path / "fixture.md"
    out = tmp_path / "candidates" / "pandas.jsonl"
    fixture.write_text(
        """
## Version 2.0.0

- The default value of `numeric_only` now defaults to False. Previously,
  non-numeric columns were silently dropped.
- `DataFrame.applymap` is deprecated; use `DataFrame.map` instead.
""",
        encoding="utf-8",
    )

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
            "fixture://pandas.md",
            "--out",
            str(out),
            "--llm-filter",
        ]
    )

    assert rc == 0
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["confidence"] == "uncertain_silence"
    assert rows[0]["extracted_by"] == "llm_filter"


def test_stats_and_show_accept_file_paths(tmp_path, capsys) -> None:
    fixture = tmp_path / "fixture.md"
    out = tmp_path / "candidates.jsonl"
    fixture.write_text(
        """
## Version 2.0.0

- The timezone default is now UTC for new connections.
""",
        encoding="utf-8",
    )
    assert main(["mine", "--library", "lib", "--source", str(fixture), "--out", str(out)]) == 0
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]

    assert main(["stats", str(out)]) == 0
    stats_output = capsys.readouterr().out
    assert '"total": 1' in stats_output

    assert main(["show", str(out), "--candidate-id", rows[0]["candidate_id"]]) == 0
    show_output = capsys.readouterr().out
    assert rows[0]["candidate_id"] not in show_output
    assert "timezone" in show_output.lower()
