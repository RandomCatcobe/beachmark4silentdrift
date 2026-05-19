"""Leak-controlled client generation prompt artifacts."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .schema import ARTIFACT_SCHEMA_VERSION, utc_now_iso


ALLOWED_PROMPT_FIELDS = (
    "library",
    "ecosystem",
    "version_old",
    "version_new",
    "api_surface",
    "public_intent",
    "allowed_imports",
    "forbidden_terms",
)
FORBIDDEN_PROMPT_FIELDS = (
    "expected_old_output",
    "expected_new_output",
    "oracle",
    "hidden_oracle_path",
    "repair_hint",
    "observed_diff",
    "curated_truth",
)
DEFAULT_FORBIDDEN_TERMS = (
    "withheld expected outputs",
    "private validation logic",
    "private validation paths",
    "repair hints",
    "observed old/new diffs",
    "curated truth labels",
)


@dataclass
class ClientGenerationArtifacts:
    candidate_id: str
    prompt_path: str
    metadata_path: str
    generated_client_path: str
    provider: str
    model: str | None
    redacted: bool
    dry_run: bool
    api_key_present: bool
    forbidden_fields: list[str] = field(default_factory=lambda: list(FORBIDDEN_PROMPT_FIELDS))
    schema_version: str = ARTIFACT_SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def load_candidate_record(candidate_path: Path, candidate_id: str) -> dict[str, Any]:
    if not candidate_path.exists():
        raise FileNotFoundError(f"candidate file not found: {candidate_path}")
    if candidate_path.suffix == ".jsonl":
        with candidate_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                record = json.loads(raw)
                if record.get("candidate_id") == candidate_id:
                    return record
    else:
        record = json.loads(candidate_path.read_text(encoding="utf-8"))
        if record.get("candidate_id") == candidate_id:
            return record
    raise ValueError(f"candidate_id not found: {candidate_id}")


def build_redacted_prompt(
    candidate: dict[str, Any],
    allowed_imports: list[str] | None = None,
    forbidden_terms: list[str] | None = None,
) -> str:
    forbidden = list(DEFAULT_FORBIDDEN_TERMS)
    forbidden.extend(forbidden_terms or [])
    context = {
        "library": candidate.get("library", ""),
        "ecosystem": candidate.get("ecosystem", ""),
        "version_old": candidate.get("version_old") or candidate.get("old_version") or "",
        "version_new": candidate.get("version_new") or candidate.get("new_version") or "",
        "api_surface": candidate.get("api_surface") or [],
        "public_intent": _public_intent(candidate),
        "allowed_imports": allowed_imports or _default_allowed_imports(candidate),
        "forbidden_terms": forbidden,
    }
    prompt = [
        "You are writing a minimal Python reproduction client.",
        "Use only the redacted public context below.",
        "Do not infer or include withheld outputs, private validation logic, private paths, repair hints, or truth labels.",
        "Return only Python source code for a client with a main() entrypoint.",
        "",
        "Public context:",
        json.dumps(context, indent=2, ensure_ascii=False),
        "",
        "Constraints:",
        "- Keep the client deterministic.",
        "- Do not read clocks, network, random sources, or local files unless explicitly required by public_intent.",
        "- Print a JSON object with enough public observations for the reproduction harness to diff.",
    ]
    text = "\n".join(prompt) + "\n"
    _assert_redacted(text, candidate, forbidden)
    return text


def write_client_generation_artifacts(
    candidate_path: Path,
    candidate_id: str,
    out_path: Path,
    redacted: bool = True,
    dry_run: bool = False,
    model: str | None = None,
    provider: str = "anthropic",
    allowed_imports: list[str] | None = None,
    forbidden_terms: list[str] | None = None,
    prompt_out: Path | None = None,
    metadata_out: Path | None = None,
) -> ClientGenerationArtifacts:
    if not redacted:
        raise ValueError("only redacted client generation is supported")

    candidate = load_candidate_record(candidate_path, candidate_id)
    prompt_path = prompt_out or out_path.with_suffix(out_path.suffix + ".prompt.md")
    metadata_path = metadata_out or out_path.with_suffix(out_path.suffix + ".metadata.json")
    prompt = build_redacted_prompt(candidate, allowed_imports=allowed_imports, forbidden_terms=forbidden_terms)

    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    api_key_present = bool(os.environ.get("ANTHROPIC_API_KEY"))
    artifacts = ClientGenerationArtifacts(
        candidate_id=candidate_id,
        prompt_path=str(prompt_path),
        metadata_path=str(metadata_path),
        generated_client_path=str(out_path),
        provider=provider,
        model=model,
        redacted=redacted,
        dry_run=dry_run,
        api_key_present=api_key_present,
    )
    metadata_path.write_text(artifacts.to_json() + "\n", encoding="utf-8")

    if dry_run:
        out_path.write_text(_dry_run_client(candidate), encoding="utf-8")
        return artifacts
    if not api_key_present:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set; prompt and metadata were written, "
            "rerun with --dry-run or configure a provider before live generation"
        )
    raise NotImplementedError("live client generation provider is not implemented yet")


def _public_intent(candidate: dict[str, Any]) -> str:
    api_surface = candidate.get("api_surface") or []
    if api_surface:
        return f"Exercise public behavior of {', '.join(api_surface)} without expected old/new outputs."
    title = candidate.get("title") or candidate.get("summary_paraphrased") or ""
    return title or "Exercise the public API surface described by the candidate metadata."


def _default_allowed_imports(candidate: dict[str, Any]) -> list[str]:
    imports = ["json"]
    library = candidate.get("library")
    if isinstance(library, str) and library:
        imports.append(library.replace("-", "_"))
    return imports


def _assert_redacted(text: str, candidate: dict[str, Any], forbidden_terms: list[str]) -> None:
    lowered = text.lower()
    for field in FORBIDDEN_PROMPT_FIELDS:
        if field.lower() in lowered:
            raise ValueError(f"prompt contains forbidden field: {field}")
        value = candidate.get(field)
        if value and str(value).lower() in lowered:
            raise ValueError(f"prompt contains forbidden value from {field}")


def _dry_run_client(candidate: dict[str, Any]) -> str:
    library = candidate.get("library") or "target_library"
    api_surface = candidate.get("api_surface") or []
    surface_comment = ", ".join(api_surface) if api_surface else "public API surface"
    return (
        '"""Dry-run generated client scaffold from redacted public context."""\n'
        "from __future__ import annotations\n\n"
        "import json\n\n\n"
        "def main() -> None:\n"
        f"    # TODO: exercise {surface_comment} from {library!r}.\n"
        "    print(json.dumps({\"status\": \"dry_run_scaffold\"}, sort_keys=True))\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    main()\n"
    )
