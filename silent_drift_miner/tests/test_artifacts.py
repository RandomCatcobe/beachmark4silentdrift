from __future__ import annotations

import json
from dataclasses import asdict

import pytest

from silent_drift_miner.artifacts import ArtifactStore
from silent_drift_miner.schema import (
    ArtifactRecord,
    ArtifactStatus,
    ArtifactType,
    TriageDecision,
    TriageRecord,
)


def test_artifact_record_roundtrip() -> None:
    record = ArtifactRecord(
        artifact_type=ArtifactType.CANDIDATE,
        path="candidates/pandas.jsonl",
        status=ArtifactStatus.VALIDATED,
        producer="pytest",
        candidate_ids=["abc"],
        metadata={"count": 1},
    )

    back = ArtifactRecord.from_json(record.to_json())

    assert back.artifact_type == ArtifactType.CANDIDATE
    assert back.status == ArtifactStatus.VALIDATED
    assert back.metadata == {"count": 1}


def test_triage_record_uses_shared_decision_enum() -> None:
    record = TriageRecord(
        candidate_id="abc",
        decision=TriageDecision.ACCEPT_FOR_REPRODUCTION,
        notes="clear default shift",
    )

    payload = json.loads(json.dumps(asdict(record), default=lambda value: value.value))

    assert payload["decision"] == "accept_for_reproduction"


def test_artifact_store_maps_outputs_under_root(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")

    candidate_path = store.path_for(ArtifactType.CANDIDATE, "pandas.jsonl")
    output_path = store.prepare_output_path(candidate_path)

    assert output_path == tmp_path / "artifacts" / "candidates" / "pandas.jsonl"
    assert output_path.parent.exists()
    assert store.relative_to_root(output_path) == "candidates\\pandas.jsonl" or store.relative_to_root(output_path) == "candidates/pandas.jsonl"


def test_artifact_store_rejects_escape(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "artifacts")

    with pytest.raises(ValueError, match="escapes root"):
        store.resolve("..", "outside.jsonl")

    with pytest.raises(ValueError, match="escapes root"):
        store.prepare_output_path(tmp_path / "outside.jsonl")
