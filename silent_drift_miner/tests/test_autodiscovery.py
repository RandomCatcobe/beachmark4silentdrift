from __future__ import annotations

from silent_drift_miner.autodiscovery import parse_cards
from silent_drift_miner.cli import main


def test_autodiscovery_cli_records_markdown_memory(tmp_path, capsys) -> None:
    idea_bank = tmp_path / "python-drift-idea-bank.md"
    run_log = tmp_path / "python-drift-run-log.md"

    assert main(["autodiscovery", "init", "--idea-bank", str(idea_bank), "--run-log", str(run_log)]) == 0
    assert "# Python Drift Idea Bank" in idea_bank.read_text(encoding="utf-8")
    assert "# Python Drift Run Log" in run_log.read_text(encoding="utf-8")

    assert main(
        [
            "autodiscovery",
            "idea",
            "--idea-bank",
            str(idea_bank),
            "--id",
            "IDEA-20260519-001",
            "--title",
            "pandas read_csv dtype default",
            "--package",
            "pandas",
            "--api-surface",
            "read_csv",
            "--versions",
            "old 1.5.3, new 2.0.0",
            "--source-url",
            "https://example.com/pandas",
            "--evidence",
            "dtype inference changed",
            "--behavior-hypothesis",
            "same CSV may infer a different dtype",
            "--silent-drift-reason",
            "client keeps running but data semantics change",
            "--reproduction-sketch",
            "read a tiny CSV and print dtype",
            "--duplicate-different-because",
            "not the existing uint8 overflow case",
            "--risk-note",
            "version install may need numpy constraints",
            "--next-action",
            "try reproduction",
        ]
    ) == 0

    assert main(
        [
            "autodiscovery",
            "reject",
            "--idea-bank",
            str(idea_bank),
            "--id",
            "REJECTED-20260519-001",
            "--title",
            "requests timeout wording",
            "--package",
            "requests",
            "--api-surface",
            "Session.request",
            "--source",
            "https://example.com/requests",
            "--tried-because",
            "release note mentioned timeout",
            "--rejected-because",
            "not silent drift",
            "--future-avoid",
            "avoid timeout-only requests notes without behavior examples",
            "--future-may-try",
            "retry adapter changes with local mock server",
        ]
    ) == 0

    assert main(
        [
            "autodiscovery",
            "accept",
            "--idea-bank",
            str(idea_bank),
            "--id",
            "ACCEPTED-20260519-001",
            "--case-id",
            "pandas_read_csv_uint8_overflow",
            "--package",
            "pandas",
            "--api-surface",
            "read_csv",
            "--versions",
            "old 1.5.3, new 2.0.0",
            "--source",
            "https://example.com/pandas",
            "--reproduction-path",
            "data/reproductions/pandas_read_csv_uint8_overflow/result.json",
            "--oracle-path",
            "data/oracle/pandas_read_csv_uint8_overflow/oracle_spec.yaml",
            "--package-path",
            "data/packages/pandas_read_csv_uint8_overflow",
            "--audit-path",
            "data/audit/pandas_read_csv_uint8_overflow.json",
            "--why-non-duplicate",
            "accepted anchor for this API/version behavior",
            "--follow-up-idea",
            "look for pandas parser null handling elsewhere",
        ]
    ) == 0

    assert main(
        [
            "autodiscovery",
            "log",
            "--run-log",
            str(run_log),
            "--title",
            "pilot batch",
            "--model-or-operator",
            "codex",
            "--search-budget",
            "10 attempts",
            "--package-searched",
            "pandas",
            "--idea-added",
            "IDEA-20260519-001",
            "--idea-rejected",
            "REJECTED-20260519-001",
            "--accepted",
            "pandas_read_csv_uint8_overflow",
            "--note",
            "markdown memory stayed model-readable",
        ]
    ) == 0

    bank_text = idea_bank.read_text(encoding="utf-8")
    assert "## IDEA-20260519-001: pandas read_csv dtype default" in bank_text
    assert "## REJECTED-20260519-001: requests timeout wording" in bank_text
    assert "## ACCEPTED-20260519-001: pandas_read_csv_uint8_overflow" in bank_text
    assert "avoid timeout-only requests notes without behavior examples" in bank_text

    cards = parse_cards(idea_bank)
    assert [card["kind"] for card in cards] == ["IDEA", "REJECTED", "ACCEPTED"]
    assert cards[0]["package"] == "pandas"
    assert cards[1]["future_avoid"] == "avoid timeout-only requests notes without behavior examples"

    assert "pilot batch" in run_log.read_text(encoding="utf-8")
    capsys.readouterr()


def test_autodiscovery_avoid_list_summarizes_existing_cards(tmp_path, capsys) -> None:
    idea_bank = tmp_path / "ideas.md"
    avoid_out = tmp_path / "avoid.md"
    idea_bank.write_text(
        """# Python Drift Idea Bank

## IDEA-20260519-001: pandas parser idea

- Package: `pandas`
- API surface: `read_csv`

## REJECTED-20260519-001: requests timeout wording

- Package: `requests`
- API surface: `Session.request`
- Rejected because:
- not silent drift
- What future runs should avoid: avoid timeout-only requests notes

## ACCEPTED-20260519-001: pandas_read_csv_uint8_overflow

- Case id: `pandas_read_csv_uint8_overflow`
- Package: `pandas`
- API surface: `read_csv`
- Versions: old 1.5.3, new 2.0.0
""",
        encoding="utf-8",
    )

    assert main(["autodiscovery", "avoid-list", "--idea-bank", str(idea_bank), "--out", str(avoid_out)]) == 0

    summary = avoid_out.read_text(encoding="utf-8")
    assert "`pandas` (2 cards)" in summary
    assert "`requests` (1 card)" in summary
    assert "`pandas`: `read_csv`" in summary
    assert "pandas_read_csv_uint8_overflow" in summary
    assert "avoid timeout-only requests notes" in summary
    assert "Python Drift Avoid Summary" in capsys.readouterr().out


def test_autodiscovery_readiness_and_brief_do_not_start_discovery(tmp_path, capsys) -> None:
    idea_bank = tmp_path / "idea-bank.md"
    run_log = tmp_path / "run-log.md"
    plan = tmp_path / "plan.md"
    brief = tmp_path / "next-run.md"
    readiness = tmp_path / "readiness.md"

    plan.write_text("# Plan\n", encoding="utf-8")
    assert main(["autodiscovery", "init", "--idea-bank", str(idea_bank), "--run-log", str(run_log)]) == 0
    assert main(
        [
            "autodiscovery",
            "readiness",
            "--idea-bank",
            str(idea_bank),
            "--run-log",
            str(run_log),
            "--plan",
            str(plan),
            "--run-brief",
            str(brief),
            "--out",
            str(readiness),
        ]
    ) == 0

    readiness_text = readiness.read_text(encoding="utf-8")
    assert "Plan: ok" in readiness_text
    assert "Next-run brief: missing" in readiness_text
    assert "Ready for a model-guided discovery batch" in readiness_text

    assert main(
        [
            "autodiscovery",
            "brief",
            "--idea-bank",
            str(idea_bank),
            "--run-log",
            str(run_log),
            "--attempts",
            "10",
            "--package-focus",
            "pandas",
            "--out",
            str(brief),
        ]
    ) == 0

    brief_text = brief.read_text(encoding="utf-8")
    assert "Python Drift Next-Run Brief" in brief_text
    assert "Start only when explicitly asked to begin searching" in brief_text
    assert "Target discovery attempts: 10" in brief_text
    assert "- pandas" in brief_text
    assert "Current Idea Bank" in brief_text
    assert "wrote autodiscovery next-run brief" in capsys.readouterr().out
