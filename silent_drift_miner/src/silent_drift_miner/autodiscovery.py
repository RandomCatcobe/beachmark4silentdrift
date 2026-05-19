"""Markdown memory for model-guided Python drift autodiscovery."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IDEA_BANK = Path("docs/python-drift-idea-bank.md")
DEFAULT_RUN_LOG = Path("docs/python-drift-run-log.md")
DEFAULT_PLAN = Path("docs/python-autodiscovery-plan.md")
DEFAULT_RUN_BRIEF = Path("docs/python-drift-next-run.md")

CARD_RE = re.compile(
    r"^## (?P<kind>IDEA|REJECTED|ACCEPTED)-(?P<date>\d{8})-(?P<num>\d{3})(?::\s*)?(?P<title>.*)$",
    re.MULTILINE,
)


@dataclass
class IdeaCard:
    title: str
    package: str = ""
    api_surface: str = ""
    versions: str = ""
    source_url: str = ""
    source_section: str = ""
    evidence: str = ""
    behavior_hypothesis: str = ""
    silent_drift_reason: str = ""
    reproduction_sketch: str = ""
    duplicate_similar_to: str = ""
    duplicate_different_because: str = ""
    risk_notes: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass
class RejectedCard:
    title: str
    package: str = ""
    api_surface: str = ""
    source: str = ""
    tried_because: str = ""
    rejected_because: list[str] = field(default_factory=list)
    future_avoid: str = ""
    future_may_try: str = ""


@dataclass
class AcceptedCard:
    case_id: str
    package: str = ""
    api_surface: str = ""
    versions: str = ""
    source: str = ""
    reproduction_path: str = ""
    oracle_path: str = ""
    package_path: str = ""
    audit_path: str = ""
    why_non_duplicate: str = ""
    follow_up_ideas: list[str] = field(default_factory=list)


@dataclass
class RunLogEntry:
    title: str
    model_or_operator: str = ""
    search_budget: str = ""
    packages_searched: list[str] = field(default_factory=list)
    ideas_added: list[str] = field(default_factory=list)
    ideas_rejected: list[str] = field(default_factory=list)
    promoted: list[str] = field(default_factory=list)
    accepted: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def init_memory(idea_bank: Path = DEFAULT_IDEA_BANK, run_log: Path = DEFAULT_RUN_LOG) -> None:
    _ensure_file(
        idea_bank,
        "# Python Drift Idea Bank\n\n"
        "Append-only memory for Python silent-drift discovery ideas, rejected leads, duplicate warnings, "
        "and accepted cases.\n\n"
    )
    _ensure_file(
        run_log,
        "# Python Drift Run Log\n\n"
        "Append-only batch notes for model-guided Python silent-drift discovery.\n\n"
    )


def append_idea(path: Path, card: IdeaCard, card_id: str | None = None) -> str:
    card_id = card_id or next_card_id(path, "IDEA")
    _append_section(path, _render_idea(card_id, card))
    return card_id


def append_rejected(path: Path, card: RejectedCard, card_id: str | None = None) -> str:
    card_id = card_id or next_card_id(path, "REJECTED")
    _append_section(path, _render_rejected(card_id, card))
    return card_id


def append_accepted(path: Path, card: AcceptedCard, card_id: str | None = None) -> str:
    card_id = card_id or next_card_id(path, "ACCEPTED")
    _append_section(path, _render_accepted(card_id, card))
    return card_id


def append_run_log(path: Path, entry: RunLogEntry) -> None:
    today = _today()
    section = "\n".join(
        [
            f"## RUN-{today}: {entry.title}",
            "",
            f"- Model/operator: {entry.model_or_operator}",
            f"- Search budget: {entry.search_budget}",
            "- Packages searched:",
            *_list_items(entry.packages_searched),
            "- Ideas added:",
            *_list_items(entry.ideas_added),
            "- Ideas rejected:",
            *_list_items(entry.ideas_rejected),
            "- Cases promoted to reproduction:",
            *_list_items(entry.promoted),
            "- Cases accepted into benchmark:",
            *_list_items(entry.accepted),
            "- Notes:",
            *_list_items(entry.notes),
            "",
        ]
    )
    _append_section(path, section)


def next_card_id(path: Path, kind: str) -> str:
    date = _today()
    max_seen = 0
    if path.exists():
        for match in CARD_RE.finditer(path.read_text(encoding="utf-8")):
            if match.group("kind") == kind and match.group("date") == date:
                max_seen = max(max_seen, int(match.group("num")))
    return f"{kind}-{date}-{max_seen + 1:03d}"


def build_avoid_summary(path: Path) -> str:
    cards = parse_cards(path)
    packages = Counter(card.get("package", "") for card in cards if card.get("package"))
    api_by_package: dict[str, set[str]] = defaultdict(set)
    accepted: list[str] = []
    rejection_lessons: list[str] = []

    for card in cards:
        package = card.get("package", "")
        api_surface = card.get("api_surface", "")
        if package and api_surface:
            api_by_package[package].add(api_surface)
        if card["kind"] == "ACCEPTED":
            accepted.append(_compact_anchor(card))
        if card["kind"] == "REJECTED" and card.get("future_avoid"):
            rejection_lessons.append(card["future_avoid"])

    lines = ["# Python Drift Avoid Summary", ""]
    lines.append("## Packages Already Mentioned")
    if packages:
        for package, count in sorted(packages.items()):
            lines.append(f"- `{package}` ({count} card{'s' if count != 1 else ''})")
    else:
        lines.append("- None yet")
    lines.append("")

    lines.append("## API Surfaces Already Mentioned")
    if api_by_package:
        for package in sorted(api_by_package):
            apis = ", ".join(f"`{api}`" for api in sorted(api_by_package[package]))
            lines.append(f"- `{package}`: {apis}")
    else:
        lines.append("- None yet")
    lines.append("")

    lines.append("## Accepted Case Anchors")
    lines.extend(_list_items(accepted))
    lines.append("")

    lines.append("## Rejection Lessons")
    lines.extend(_list_items(rejection_lessons))
    lines.append("")
    return "\n".join(lines)


def build_readiness_report(
    idea_bank: Path = DEFAULT_IDEA_BANK,
    run_log: Path = DEFAULT_RUN_LOG,
    plan: Path = DEFAULT_PLAN,
    run_brief: Path = DEFAULT_RUN_BRIEF,
) -> str:
    cards = parse_cards(idea_bank)
    counts = Counter(card["kind"] for card in cards)
    checks = [
        ("Plan", plan.exists(), str(plan)),
        ("Idea bank", idea_bank.exists(), str(idea_bank)),
        ("Run log", run_log.exists(), str(run_log)),
        ("Next-run brief", run_brief.exists(), str(run_brief)),
    ]

    lines = ["# Python Drift Autodiscovery Readiness", ""]
    lines.append("## Files")
    for label, exists, path in checks:
        status = "ok" if exists else "missing"
        lines.append(f"- {label}: {status} - `{path}`")
    lines.append("")

    lines.append("## Idea Bank Counts")
    lines.append(f"- Ideas: {counts.get('IDEA', 0)}")
    lines.append(f"- Rejected: {counts.get('REJECTED', 0)}")
    lines.append(f"- Accepted: {counts.get('ACCEPTED', 0)}")
    lines.append("")

    lines.append("## Ready Command")
    lines.append("```bash")
    lines.append("silent-drift-miner autodiscovery brief --out docs/python-drift-next-run.md")
    lines.append("```")
    lines.append("")

    if all(exists for _, exists, _ in checks[:3]):
        lines.append("Ready for a model-guided discovery batch after generating or refreshing the next-run brief.")
    else:
        lines.append("Not ready: initialize missing Markdown memory before starting discovery.")
    lines.append("")
    return "\n".join(lines)


def build_run_brief(
    idea_bank: Path = DEFAULT_IDEA_BANK,
    run_log: Path = DEFAULT_RUN_LOG,
    attempts: int = 10,
    package_focus: list[str] | None = None,
) -> str:
    package_focus = package_focus or []
    idea_bank_text = _read_or_placeholder(idea_bank, "Idea bank missing. Run autodiscovery init first.")
    run_log_text = _read_or_placeholder(run_log, "Run log missing. Run autodiscovery init first.")
    avoid_summary = build_avoid_summary(idea_bank)

    lines = [
        "# Python Drift Next-Run Brief",
        "",
        "This brief prepares the next model-guided discovery batch. It does not start the batch.",
        "",
        "## Batch Budget",
        f"- Target discovery attempts: {attempts}",
        "- Start only when explicitly asked to begin searching.",
        "- Append every useful idea or useful failure back to Markdown.",
        "",
        "## Package Focus",
        *_list_items(package_focus),
        "",
        "## Operating Rules",
        "- Read the idea bank before searching.",
        "- Prefer a new package, API surface, version range, or drift category.",
        "- Do not clone accepted cases or rejected dead ends.",
        "- Record rejections when they teach future runs what to avoid.",
        "- Promote only evidence-backed, deterministic, local Python behavior changes.",
        "- Keep source quotes short and paraphrase where possible.",
        "",
        "## Avoid Summary",
        avoid_summary.rstrip(),
        "",
        "## Append Commands",
        "```bash",
        "silent-drift-miner autodiscovery idea ...",
        "silent-drift-miner autodiscovery reject ...",
        "silent-drift-miner autodiscovery accept ...",
        "silent-drift-miner autodiscovery log ...",
        "```",
        "",
        "## Current Idea Bank",
        idea_bank_text.rstrip(),
        "",
        "## Current Run Log",
        run_log_text.rstrip(),
        "",
    ]
    return "\n".join(lines)


def parse_cards(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    cards: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    rejected_reasons: list[str] = []

    def flush() -> None:
        nonlocal current, rejected_reasons
        if current is None:
            return
        if rejected_reasons:
            current["rejected_because"] = "; ".join(rejected_reasons)
        cards.append(current)
        current = None
        rejected_reasons = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        match = CARD_RE.match(raw)
        if match:
            flush()
            current = {
                "kind": match.group("kind"),
                "id": f"{match.group('kind')}-{match.group('date')}-{match.group('num')}",
                "title": match.group("title").strip(),
            }
            continue
        if current is None:
            continue
        line = raw.strip()
        if line.startswith("- Package:"):
            current["package"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- API surface:"):
            current["api_surface"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- Candidate versions:") or line.startswith("- Versions:"):
            current["versions"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- Case id:"):
            current["case_id"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- What future runs should avoid:"):
            current.pop("_in_rejected_because", None)
            current["future_avoid"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- What future runs may still try:"):
            current.pop("_in_rejected_because", None)
            current["future_may_try"] = _strip_value(line.split(":", 1)[1])
        elif line.startswith("- ") and current.get("_in_rejected_because") == "1":
            rejected_reasons.append(_strip_value(line[2:]))
        elif line == "- Rejected because:":
            current["_in_rejected_because"] = "1"
        elif line and not line.startswith("- "):
            current.pop("_in_rejected_because", None)
    flush()
    for card in cards:
        card.pop("_in_rejected_because", None)
    return cards


def _render_idea(card_id: str, card: IdeaCard) -> str:
    risks = card.risk_notes or [""]
    return "\n".join(
        [
            f"## {card_id}: {card.title}",
            "",
            f"- Package: `{card.package}`",
            f"- API surface: `{card.api_surface}`",
            f"- Candidate versions: {card.versions}",
            "- Source:",
            f"  - URL: {card.source_url}",
            f"  - Release/changelog section: {card.source_section}",
            f"  - Quote or paraphrase: {card.evidence}",
            f"- Behavior hypothesis: {card.behavior_hypothesis}",
            f"- Why this may be silent drift: {card.silent_drift_reason}",
            f"- Reproduction sketch: {card.reproduction_sketch}",
            "- Duplicate check:",
            f"  - Similar to: {card.duplicate_similar_to}",
            f"  - Different because: {card.duplicate_different_because}",
            "- Risk notes:",
            *_list_items(risks),
            f"- Next action: {card.next_action}",
            "",
        ]
    )


def _render_rejected(card_id: str, card: RejectedCard) -> str:
    reasons = card.rejected_because or [""]
    return "\n".join(
        [
            f"## {card_id}: {card.title}",
            "",
            f"- Package: `{card.package}`",
            f"- API surface: `{card.api_surface}`",
            f"- Source: {card.source}",
            f"- Tried because: {card.tried_because}",
            "- Rejected because:",
            *_list_items(reasons),
            f"- What future runs should avoid: {card.future_avoid}",
            f"- What future runs may still try: {card.future_may_try}",
            "",
        ]
    )


def _render_accepted(card_id: str, card: AcceptedCard) -> str:
    follow_ups = card.follow_up_ideas or [""]
    return "\n".join(
        [
            f"## {card_id}: {card.case_id}",
            "",
            f"- Case id: `{card.case_id}`",
            f"- Package: `{card.package}`",
            f"- API surface: `{card.api_surface}`",
            f"- Versions: {card.versions}",
            f"- Source: {card.source}",
            f"- Reproduction path: {card.reproduction_path}",
            f"- Oracle path: {card.oracle_path}",
            f"- Package path: {card.package_path}",
            f"- Audit path: {card.audit_path}",
            f"- Why it is non-duplicate: {card.why_non_duplicate}",
            "- Follow-up ideas nearby:",
            *_list_items(follow_ups),
            "",
        ]
    )


def _ensure_file(path: Path, text: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_section(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.exists() and path.read_text(encoding="utf-8").strip():
        prefix = "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + text.rstrip() + "\n")


def _list_items(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]


def _strip_value(value: str) -> str:
    return value.strip().strip("`")


def _compact_anchor(card: dict[str, str]) -> str:
    case_id = card.get("case_id") or card.get("title") or card["id"]
    package = card.get("package", "")
    api_surface = card.get("api_surface", "")
    versions = card.get("versions", "")
    return f"{case_id} - `{package}` `{api_surface}` {versions}".rstrip()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _read_or_placeholder(path: Path, placeholder: str) -> str:
    if not path.exists():
        return placeholder + "\n"
    return path.read_text(encoding="utf-8")
