from __future__ import annotations

import json

from silent_drift_miner.cli import main
from silent_drift_miner.client_generation import build_redacted_prompt


def test_redacted_prompt_omits_forbidden_candidate_fields() -> None:
    candidate = _candidate_record()

    prompt = build_redacted_prompt(candidate)

    lowered = prompt.lower()
    assert "expected_old_output" not in lowered
    assert "expected_new_output" not in lowered
    assert "observed_diff" not in lowered
    assert "curated_truth" not in lowered
    assert "secret_old" not in prompt
    assert "secret_new" not in prompt
    assert "pandas.Series.str.replace" in prompt


def test_generate_client_dry_run_writes_prompt_metadata_and_scaffold(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "generated_client.py"
    candidate.write_text(json.dumps(_candidate_record()), encoding="utf-8")

    assert main(
        [
            "reproduce",
            "generate-client",
            "--candidate",
            str(candidate),
            "--candidate-id",
            "cand-1",
            "--redacted",
            "--dry-run",
            "--out",
            str(out),
        ]
    ) == 0

    prompt = out.with_suffix(".py.prompt.md")
    metadata = out.with_suffix(".py.metadata.json")
    assert out.exists()
    assert prompt.exists()
    assert metadata.exists()
    assert "secret_new" not in prompt.read_text(encoding="utf-8")
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert payload["api_key_present"] is False


def test_generate_client_missing_api_key_fails_after_writing_audit_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    candidate = tmp_path / "candidate.json"
    out = tmp_path / "generated_client.py"
    candidate.write_text(json.dumps(_candidate_record()), encoding="utf-8")

    assert main(
        [
            "reproduce",
            "generate-client",
            "--candidate",
            str(candidate),
            "--candidate-id",
            "cand-1",
            "--redacted",
            "--out",
            str(out),
        ]
    ) == 1

    assert not out.exists()
    assert out.with_suffix(".py.prompt.md").exists()
    assert out.with_suffix(".py.metadata.json").exists()


def _candidate_record() -> dict:
    return {
        "candidate_id": "cand-1",
        "library": "pandas",
        "ecosystem": "python",
        "version_old": "1.5.3",
        "version_new": "2.0.3",
        "api_surface": ["pandas.Series.str.replace"],
        "expected_old_output": "secret_old",
        "expected_new_output": "secret_new",
        "observed_diff": {"new": "secret_new"},
        "curated_truth": "secret_truth",
    }
