"""Generated Markdown indexes for case-bank metadata."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .schema import load_metadata

INDEX_SPECS = {
    "by-scenario.md": ("Cases By Scenario", "application_scenarios"),
    "by-language.md": ("Cases By Language", "languages"),
    "by-drift-pattern.md": ("Cases By Drift Pattern", "drift_patterns"),
    "by-api-surface.md": ("Cases By API Surface", "api_surfaces"),
    "by-status.md": ("Cases By Status", "status"),
}


def build_indexes(cases_root: Path, out_dir: Path) -> list[Path]:
    cases = discover_cases(cases_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, (title, field) in INDEX_SPECS.items():
        path = out_dir / filename
        path.write_text(_render_index(title, field, cases, cases_root), encoding="utf-8")
        written.append(path)
    return written


def discover_cases(cases_root: Path) -> list[dict]:
    if not cases_root.exists():
        return []
    cases: list[dict] = []
    for metadata_path in sorted(cases_root.rglob("metadata.json")):
        metadata = load_metadata(metadata_path)
        metadata["_path"] = metadata_path.parent
        cases.append(metadata)
    return sorted(cases, key=lambda item: (item["primary_scenario"], item["case_id"]))


def _render_index(title: str, field: str, cases: list[dict], cases_root: Path) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        values = case[field]
        if isinstance(values, str):
            values = [values]
        for value in values:
            grouped[value].append(case)

    lines = [
        f"# {title}",
        "",
        "Generated from `docs/case-bank/cases/**/metadata.json`.",
        "",
    ]
    if not grouped:
        lines.append("_No cases yet._")
        lines.append("")
        return "\n".join(lines)

    for group in sorted(grouped):
        lines.extend(
            [
                f"## {group}",
                "",
                "| Case ID | Title | Status | Ecosystems | Path |",
                "|---|---|---|---|---|",
            ]
        )
        for case in sorted(grouped[group], key=lambda item: item["case_id"]):
            path = _relative_path(case["_path"], cases_root)
            ecosystems = ", ".join(case["ecosystems"])
            lines.append(
                f"| `{case['case_id']}` | {case['title']} | `{case['status']}` | "
                f"{ecosystems} | `{path}` |"
            )
        lines.append("")
    return "\n".join(lines)


def _relative_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()
