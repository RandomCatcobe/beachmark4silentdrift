"""Oracle generation for curated Python cases."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .curation import CurationDecision, load_curated_case
from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


@dataclass
class OracleSpec:
    case_id: str
    candidate_id: str
    case_path: str
    template: str = "pytest"
    hidden_test_path: str = ""
    expected_path: str = ""
    public_readme_path: str = ""
    starter_client_path: str = ""
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_yaml(self) -> str:
        data = asdict(self)
        return "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in data.items()) + "\n"


def generate_pytest_oracle(case_path: Path, out_dir: Path) -> OracleSpec:
    case = load_curated_case(case_path)
    if case.decision != CurationDecision.ACCEPT:
        raise ValueError("oracle generation requires an accepted curated case")

    hidden_dir = out_dir / "hidden"
    public_dir = out_dir / "public"
    validation_dir = out_dir / "validation"
    hidden_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    spec = OracleSpec(
        case_id=case.case_id,
        candidate_id=case.candidate_id,
        case_path=str(case_path),
        hidden_test_path=str(hidden_dir / "test_behavior.py"),
        expected_path=str(hidden_dir / "expected.json"),
        public_readme_path=str(public_dir / "README.md"),
        starter_client_path=str(public_dir / "starter_client.py"),
    )
    (out_dir / "oracle_spec.yaml").write_text(spec.to_yaml(), encoding="utf-8")
    (hidden_dir / "expected.json").write_text(
        json.dumps(
            {
                "case_id": case.case_id,
                "candidate_id": case.candidate_id,
                "expected_behavior": "author hidden oracle expectation here",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (hidden_dir / "test_behavior.py").write_text(_hidden_test_template(), encoding="utf-8")
    (public_dir / "README.md").write_text(_public_readme(case.case_id), encoding="utf-8")
    (public_dir / "starter_client.py").write_text(_starter_client_template(), encoding="utf-8")
    return spec


def _hidden_test_template() -> str:
    return '''"""Hidden pytest oracle.

Fill in the expected behavior after human verification. This file stays out of
public task packages.
"""

import json
from pathlib import Path


def test_behavior_matches_expected():
    expected = json.loads((Path(__file__).parent / "expected.json").read_text())
    assert expected["expected_behavior"]
'''


def _public_readme(case_id: str) -> str:
    return (
        f"# {case_id}\n\n"
        "Implement or adapt `starter_client.py` to reproduce the documented behavior.\n"
        "Public files intentionally omit expected old/new outputs.\n"
    )


def _starter_client_template() -> str:
    return (
        '"""Public starter client for the reproduced case."""\n\n'
        "def main():\n"
        "    raise NotImplementedError('fill in the public client entrypoint')\n\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
    )
