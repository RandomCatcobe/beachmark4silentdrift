"""
End-to-end Layer-1 pipeline + CLI.

Stages:
  1. load target list from configs/targets.yaml
  2. for each target: fetch releases (and/or CHANGELOG file) via GitHub
  3. for each release section: rule-prescreen -> WEAK candidates
  4. LLM refinement (optional, gated on ANTHROPIC_API_KEY)
  5. write JSONL to data/candidates/<library>.jsonl
  6. emit summary report

Run:
    python -m silent_drift_miner.cli mine --config configs/targets.yaml
    python -m silent_drift_miner.cli mine --library spring-boot   # ad-hoc
    python -m silent_drift_miner.cli stats
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .artifacts import ArtifactStore
from .extractors.llm import LLMConfig, LLMRefiner
from .extractors.rules import extract_candidates
from .schema import ArtifactType, Confidence, DriftCandidate, DriftCategory, utc_now_iso
from .sources.github_changelog import (
    GitHubFetcher,
    ReleaseDoc,
    split_changelog_into_sections,
)

# ----------------------- config loading -----------------------

@dataclass
class Target:
    library: str
    owner: str
    repo: str
    ecosystem: str
    use_releases_api: bool = True
    use_changelog_file: bool = False
    max_releases: int = 30
    enabled: bool = True


def _load_yaml(path: Path) -> dict:
    """Minimal YAML loader so we don't add PyYAML as a dependency.

    Supports the simple shape used in configs/targets.yaml:
        targets:
          - library: spring-boot
            owner: spring-projects
            ...
    """
    try:
        import yaml  # type: ignore
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ImportError:
        pass

    # tiny hand-rolled parser for our specific schema
    out: dict = {"targets": []}
    cur: Optional[dict] = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("targets:"):
            continue
        if line.lstrip().startswith("- "):
            if cur:
                out["targets"].append(cur)
            cur = {}
            kv = line.lstrip()[2:]
            if ":" in kv:
                k, v = kv.split(":", 1)
                cur[k.strip()] = _coerce(v.strip())
        elif ":" in line and cur is not None:
            k, v = line.split(":", 1)
            cur[k.strip()] = _coerce(v.strip())
    if cur:
        out["targets"].append(cur)
    return out


def _coerce(v: str):
    if v.lower() in ("true", "yes"): return True
    if v.lower() in ("false", "no"): return False
    try: return int(v)
    except ValueError: pass
    return v.strip().strip('"').strip("'")


def load_targets(config_path: Path) -> list[Target]:
    data = _load_yaml(config_path)
    out: list[Target] = []
    for item in data.get("targets", []):
        out.append(Target(
            library=item["library"],
            owner=item["owner"],
            repo=item["repo"],
            ecosystem=item.get("ecosystem", "other"),
            use_releases_api=item.get("use_releases_api", True),
            use_changelog_file=item.get("use_changelog_file", False),
            max_releases=int(item.get("max_releases", 30)),
            enabled=item.get("enabled", True),
        ))
    return out


# ----------------------- mining for one target -----------------------

def mine_target(target: Target, fetcher: GitHubFetcher, threshold: int) -> list[DriftCandidate]:
    """Run rule-based mining over one library; return WEAK candidates."""
    docs: list[ReleaseDoc] = []
    if target.use_releases_api:
        try:
            docs.extend(fetcher.fetch_releases(target.owner, target.repo, target.max_releases))
        except Exception as e:
            print(f"[fetch] releases API failed for {target.library}: {e}", file=sys.stderr)
    if target.use_changelog_file:
        try:
            f = fetcher.fetch_changelog_file(target.owner, target.repo)
            if f:
                docs.append(f)
        except Exception as e:
            print(f"[fetch] changelog file failed for {target.library}: {e}", file=sys.stderr)

    if not docs:
        print(f"[fetch] no documents for {target.library}", file=sys.stderr)
        return []

    now_iso = utc_now_iso()
    candidates: list[DriftCandidate] = []
    for d in docs:
        if d.source_type == "changelog_file":
            sections = list(split_changelog_into_sections(d.body))
        else:
            sections = [(d.tag or d.name, d.body)]
        for version_label, section_body in sections:
            cands = extract_candidates(
                library=target.library,
                ecosystem=target.ecosystem,
                version_label=version_label,
                section_body=section_body,
                source_url=d.html_url,
                threshold=threshold,
                retrieved_at=now_iso,
            )
            candidates.extend(cands)
    return candidates


# ----------------------- output -----------------------

def write_candidates_jsonl(cands: list[DriftCandidate], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in cands:
            f.write(c.to_jsonl() + "\n")


def load_candidates_jsonl(path: Path) -> list[DriftCandidate]:
    out: list[DriftCandidate] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(DriftCandidate.from_jsonl(line))
    return out


def summarize(cands: list[DriftCandidate]) -> dict:
    cat_counter = Counter(c.category.value for c in cands)
    conf_counter = Counter(c.confidence.value for c in cands)
    by_lib = Counter(c.library for c in cands)
    by_ecosystem = Counter(c.ecosystem for c in cands)
    return {
        "total": len(cands),
        "by_category": dict(cat_counter),
        "by_confidence": dict(conf_counter),
        "by_library": dict(by_lib),
        "by_ecosystem": dict(by_ecosystem),
    }


# ----------------------- CLI -----------------------

def candidate_dir(out_dir: Optional[str], artifact_root: Optional[str]) -> Path:
    if artifact_root is None:
        return Path(out_dir or "data/candidates")
    store = ArtifactStore(artifact_root)
    if out_dir is None:
        return store.dir_for(ArtifactType.CANDIDATE)
    return store.resolve_user_path(out_dir)

def cmd_mine(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"config not found: {config_path}", file=sys.stderr)
        return 2

    targets = load_targets(config_path)
    if args.library:
        targets = [t for t in targets if t.library == args.library]
        if not targets:
            print(f"library {args.library!r} not in config", file=sys.stderr)
            return 2
    else:
        disabled = [t.library for t in targets if not t.enabled]
        targets = [t for t in targets if t.enabled]
        if disabled:
            print(f"[config] skipping disabled targets: {', '.join(disabled)}", file=sys.stderr)

    cache_dir = Path(args.cache_dir)
    out_dir = candidate_dir(args.out_dir, args.artifact_root)
    fetcher = GitHubFetcher(cache_dir=cache_dir)

    refiner = LLMRefiner(LLMConfig()) if args.use_llm else None
    if refiner is not None and not refiner.enabled:
        print("[llm] no API key found; LLM stage will be skipped per-call")

    all_after: list[DriftCandidate] = []
    for t in targets:
        print(f"\n=== mining {t.library} ({t.ecosystem}) ===")
        weak = mine_target(t, fetcher, threshold=args.threshold)
        print(f"  rule prescreen: {len(weak)} WEAK candidates")
        if refiner is not None and refiner.enabled and weak:
            kept = refiner.refine_batch(weak)
            print(f"  LLM refinement: kept {len(kept)} of {len(weak)}")
        else:
            kept = weak

        out_path = out_dir / f"{t.library}.jsonl"
        write_candidates_jsonl(kept, out_path)
        print(f"  wrote -> {out_path}")
        all_after.extend(kept)

    s = summarize(all_after)
    print("\n=== summary ===")
    print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    out_dir = candidate_dir(args.out_dir, args.artifact_root)
    all_c: list[DriftCandidate] = []
    for p in sorted(out_dir.glob("*.jsonl")):
        all_c.extend(load_candidates_jsonl(p))
    s = summarize(all_c)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 2

    errors: list[str] = []
    seen_ids: set[str] = set()
    total = 0
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            try:
                c = DriftCandidate.from_jsonl(raw)
            except Exception as e:
                errors.append(f"line {lineno}: parse error — {e}")
                continue
            if c.candidate_id in seen_ids:
                errors.append(f"line {lineno}: duplicate candidate_id {c.candidate_id!r}")
            seen_ids.add(c.candidate_id)
            if not c.library:
                errors.append(f"line {lineno}: missing library")
            if not c.title:
                errors.append(f"line {lineno}: missing title")
            # round-trip check
            try:
                rt = DriftCandidate.from_jsonl(c.to_jsonl())
                if rt.candidate_id != c.candidate_id:
                    errors.append(f"line {lineno}: round-trip id mismatch")
            except Exception as e:
                errors.append(f"line {lineno}: round-trip error — {e}")

    if errors:
        for msg in errors:
            print(f"ERROR {msg}", file=sys.stderr)
        print(f"\n{len(errors)} error(s) in {total} candidates — {path}", file=sys.stderr)
        return 1

    print(f"OK — {total} candidates validated in {path}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    out_dir = candidate_dir(args.out_dir, args.artifact_root)
    path = out_dir / f"{args.library}.jsonl"
    cands = load_candidates_jsonl(path)
    if args.only_category:
        cands = [c for c in cands if c.category.value == args.only_category]
    if args.min_confidence:
        order = {"weak": 0, "uncertain_silence": 1, "high": 2}
        threshold = order[args.min_confidence]
        cands = [c for c in cands if order[c.confidence.value] >= threshold]
    cands = cands[: args.limit]
    for c in cands:
        print("─" * 80)
        print(f"[{c.confidence.value}/{c.category.value}] {c.library} {c.version_new}")
        print(f"  title: {c.title}")
        if c.summary_paraphrased:
            print(f"  summary: {c.summary_paraphrased}")
        if c.api_surface:
            print(f"  api: {', '.join(c.api_surface)}")
        if c.why_flagged:
            print(f"  rules: {', '.join(c.why_flagged)}")
        if c.evidence:
            print(f"  url: {c.evidence[0].url}")
    print("─" * 80)
    print(f"total shown: {len(cands)}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="silent-drift-miner")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_mine = sub.add_parser("mine", help="run the mining pipeline")
    p_mine.add_argument("--config", default="configs/targets.yaml")
    p_mine.add_argument("--library", default=None, help="only mine this library from config")
    p_mine.add_argument("--cache-dir", default="data/raw_changelogs")
    p_mine.add_argument("--artifact-root", default=None,
                        help="artifact root; when set, outputs cannot escape this directory")
    p_mine.add_argument("--out-dir", default=None)
    p_mine.add_argument("--threshold", type=int, default=4,
                        help="rule score threshold to emit a WEAK candidate")
    llm_group = p_mine.add_mutually_exclusive_group()
    llm_group.add_argument("--use-llm", action="store_true", default=False,
                           help="enable LLM refinement (needs ANTHROPIC_API_KEY)")
    llm_group.add_argument("--no-llm", dest="use_llm", action="store_false",
                           help="disable LLM refinement (default)")
    p_mine.set_defaults(func=cmd_mine)

    p_stats = sub.add_parser("stats", help="print summary over all candidates")
    p_stats.add_argument("--artifact-root", default=None,
                         help="artifact root; defaults candidate input to <root>/candidates")
    p_stats.add_argument("--out-dir", default=None)
    p_stats.set_defaults(func=cmd_stats)

    p_show = sub.add_parser("show", help="show candidates for one library")
    p_show.add_argument("library")
    p_show.add_argument("--artifact-root", default=None,
                        help="artifact root; defaults candidate input to <root>/candidates")
    p_show.add_argument("--out-dir", default=None)
    p_show.add_argument("--limit", type=int, default=20)
    p_show.add_argument("--only-category", default=None)
    p_show.add_argument("--min-confidence", default=None,
                        choices=["weak", "uncertain_silence", "high"])
    p_show.set_defaults(func=cmd_show)

    p_validate = sub.add_parser("validate-candidates",
                                help="validate JSONL schema and round-trip for a candidates file")
    p_validate.add_argument("path", help="path to a candidates .jsonl file")
    p_validate.set_defaults(func=cmd_validate)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
