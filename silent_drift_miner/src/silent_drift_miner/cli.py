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
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .artifacts import ArtifactStore
from .audit import audit_package, write_audit_report
from .adapter_contracts import AdapterPlanRequest, AdapterRunRequest, adapter_contract_report_json
from .adapters.dotnet import DotnetAdapter
from .adapters.go import GoAdapter
from .adapters.js import JsAdapter
from .adapters.jvm import JvmAdapter
from .adapters.php import PhpAdapter
from .adapters.ruby import RubyAdapter
from .autodiscovery import (
    AcceptedCard,
    DEFAULT_IDEA_BANK,
    DEFAULT_RUN_LOG,
    IdeaCard,
    RejectedCard,
    RunLogEntry,
    append_accepted,
    append_idea,
    append_rejected,
    append_run_log,
    build_avoid_summary,
    init_memory,
)
from .bench import create_benchmark_package
from .client_generation import write_client_generation_artifacts
from .curation import CurationDecision, create_curated_case, write_curated_case
from .ecosystems import check_ecosystem_environment, evaluate_adapter_gates
from .extractors.llm import LLMConfig, LLMRefiner, OfflineLLMFilter
from .oracle import generate_pytest_oracle, validate_pytest_oracle
from .extractors.rules import extract_candidates
from .python_status import build_python_status_report
from .schema import ArtifactType, Confidence, DriftCandidate, DriftCategory, TriageDecision, utc_now_iso
from .reproduction import (
    create_reproduction_spec,
    load_reproduction_result,
    load_reproduction_spec,
    run_reproduction_spec,
    write_reproduction_spec,
)
from .sources.github_changelog import (
    GitHubFetcher,
    ReleaseDoc,
    split_changelog_into_sections,
)
from .triage import (
    build_queue_items,
    export_candidate_rows,
    find_next_item,
    load_triage_queue,
    mark_queue_item,
    queue_summary,
    write_triage_queue,
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


def mine_source_file(
    library: str,
    ecosystem: str,
    source_path: Path,
    source_url: str,
    threshold: int,
) -> list[DriftCandidate]:
    body = source_path.read_text(encoding="utf-8")
    sections = list(split_changelog_into_sections(body)) or [(source_path.stem, body)]
    now_iso = utc_now_iso()
    candidates: list[DriftCandidate] = []
    for version_label, section_body in sections:
        candidates.extend(
            extract_candidates(
                library=library,
                ecosystem=ecosystem,
                version_label=version_label,
                section_body=section_body,
                source_url=source_url,
                threshold=threshold,
                retrieved_at=now_iso,
            )
        )
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
    by_source = Counter(c.evidence[0].source_type if c.evidence else "(none)" for c in cands)
    return {
        "total": len(cands),
        "by_category": dict(cat_counter),
        "by_confidence": dict(conf_counter),
        "by_library": dict(by_lib),
        "by_ecosystem": dict(by_ecosystem),
        "by_source": dict(by_source),
    }


# ----------------------- CLI -----------------------

def candidate_dir(out_dir: Optional[str], artifact_root: Optional[str]) -> Path:
    if artifact_root is None:
        return Path(out_dir or "data/candidates")
    store = ArtifactStore(artifact_root)
    if out_dir is None:
        return store.dir_for(ArtifactType.CANDIDATE)
    return store.resolve_user_path(out_dir)


def artifact_path(path: str, artifact_root: Optional[str]) -> Path:
    if artifact_root is None:
        return Path(path)
    return ArtifactStore(artifact_root).resolve_user_path(path)


def candidate_file_arg(path: str, artifact_root: Optional[str]) -> Path:
    if artifact_root is None:
        return Path(path)
    return ArtifactStore(artifact_root).resolve_user_path(path)


def build_refiner(mode: str):
    if mode == "api":
        refiner = LLMRefiner(LLMConfig())
        if not refiner.enabled:
            print("[llm] no API key found; LLM stage will be skipped per-call")
        return refiner
    if mode == "offline":
        return OfflineLLMFilter()
    return None


def refine_candidates(refiner, candidates: list[DriftCandidate]) -> list[DriftCandidate]:
    if refiner is not None and refiner.enabled and candidates:
        kept = refiner.refine_batch(candidates)
        print(f"  precision filter: kept {len(kept)} of {len(candidates)}")
        return kept
    return candidates

def cmd_mine(args: argparse.Namespace) -> int:
    out_dir = candidate_dir(args.out_dir, args.artifact_root)
    refiner = build_refiner(args.llm_mode)

    if args.source:
        if not args.library:
            print("--library is required when --source is used", file=sys.stderr)
            return 2
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"source not found: {source_path}", file=sys.stderr)
            return 2
        source_url = args.source_url or source_path.as_posix()
        print(f"\n=== mining {args.library} ({args.ecosystem}) from {source_path} ===")
        weak = mine_source_file(
            library=args.library,
            ecosystem=args.ecosystem,
            source_path=source_path,
            source_url=source_url,
            threshold=args.threshold,
        )
        print(f"  rule prescreen: {len(weak)} WEAK candidates")
        kept = refine_candidates(refiner, weak)
        out_path = candidate_file_arg(args.out, args.artifact_root) if args.out else out_dir / f"{args.library}.jsonl"
        write_candidates_jsonl(kept, out_path)
        print(f"  wrote -> {out_path}")
        print("\n=== summary ===")
        print(json.dumps(summarize(kept), indent=2, ensure_ascii=False))
        return 0

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
    fetcher = GitHubFetcher(cache_dir=cache_dir)

    all_after: list[DriftCandidate] = []
    for t in targets:
        print(f"\n=== mining {t.library} ({t.ecosystem}) ===")
        weak = mine_target(t, fetcher, threshold=args.threshold)
        print(f"  rule prescreen: {len(weak)} WEAK candidates")
        kept = refine_candidates(refiner, weak)

        out_path = out_dir / f"{t.library}.jsonl"
        write_candidates_jsonl(kept, out_path)
        print(f"  wrote -> {out_path}")
        all_after.extend(kept)

    s = summarize(all_after)
    print("\n=== summary ===")
    print(json.dumps(s, indent=2, ensure_ascii=False))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    all_c: list[DriftCandidate] = []
    paths = args.paths or []
    if not paths:
        paths = [str(candidate_dir(args.out_dir, args.artifact_root))]
    for raw_path in paths:
        path = candidate_file_arg(raw_path, args.artifact_root) if args.artifact_root else Path(raw_path)
        if path.is_dir():
            for p in sorted(path.glob("*.jsonl")):
                all_c.extend(load_candidates_jsonl(p))
        else:
            all_c.extend(load_candidates_jsonl(path))
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
    target = Path(args.target)
    if target.suffix == ".jsonl" or target.exists():
        path = candidate_file_arg(args.target, args.artifact_root) if args.artifact_root else target
    else:
        out_dir = candidate_dir(args.out_dir, args.artifact_root)
        path = out_dir / f"{args.target}.jsonl"
    cands = load_candidates_jsonl(path)
    if args.candidate_id:
        cands = [c for c in cands if c.candidate_id == args.candidate_id]
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


def cmd_triage_build(args: argparse.Namespace) -> int:
    candidates_path = artifact_path(args.candidates, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    candidates = load_candidates_jsonl(candidates_path)
    items = build_queue_items(candidates)
    write_triage_queue(items, out_path)
    print(f"wrote {len(items)} triage items -> {out_path}")
    print(json.dumps(queue_summary(items), indent=2, ensure_ascii=False))
    return 0


def cmd_triage_next(args: argparse.Namespace) -> int:
    queue_path = artifact_path(args.queue, args.artifact_root)
    items = load_triage_queue(queue_path)
    item = find_next_item(items)
    if item is None:
        print("OK no undecided candidates")
        return 0
    if args.json:
        print(json.dumps(item, ensure_ascii=False))
        return 0

    candidate = item["candidate"]
    print(f"candidate_id: {item['candidate_id']}")
    print(f"library: {candidate.get('library')}")
    print(f"version_new: {candidate.get('version_new')}")
    print(f"category: {candidate.get('category')}")
    print(f"confidence: {candidate.get('confidence')}")
    print(f"title: {candidate.get('title')}")
    evidence = candidate.get("evidence") or []
    if evidence:
        print(f"url: {evidence[0].get('url')}")
    return 0


def cmd_triage_mark(args: argparse.Namespace) -> int:
    queue_path = artifact_path(args.queue, args.artifact_root)
    try:
        items = load_triage_queue(queue_path)
        item = mark_queue_item(
            items=items,
            candidate_id=args.candidate_id,
            decision_value=args.decision,
            notes=args.notes,
            reviewer=args.reviewer,
            overwrite=args.overwrite,
        )
        write_triage_queue(items, queue_path)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    print(f"marked {item['candidate_id']} -> {item['decision']}")
    return 0


def cmd_triage_export(args: argparse.Namespace) -> int:
    queue_path = artifact_path(args.queue, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    try:
        items = load_triage_queue(queue_path)
        rows = export_candidate_rows(
            items,
            decision_value=args.decision,
            include_undecided=args.include_undecided,
        )
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(row + "\n")
    print(f"exported {len(rows)} candidates -> {out_path}")
    return 0


def cmd_reproduce_plan(args: argparse.Namespace) -> int:
    client_file = Path(args.client_file)
    if not client_file.exists():
        print(f"client file not found: {client_file}", file=sys.stderr)
        return 2

    out_path = artifact_path(args.out, args.artifact_root)
    ecosystem = getattr(args, "ecosystem", "python").lower()
    if ecosystem == "jvm":
        if not args.old_source_path or not args.new_source_path:
            print("ERROR JVM reproduction requires --old-source-path and --new-source-path", file=sys.stderr)
            return 2
        metadata = {
            "old_source_paths": args.old_source_path,
            "new_source_paths": args.new_source_path,
            "classpath": args.classpath,
            "old_classpath": args.old_classpath,
            "new_classpath": args.new_classpath,
            "resource_paths": args.resource_path,
            "old_resource_paths": args.old_resource_path,
            "new_resource_paths": args.new_resource_path,
            "jvm_args": args.jvm_arg,
            "old_jvm_args": args.old_jvm_arg,
            "new_jvm_args": args.new_jvm_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "main_class": args.main_class,
            "java_executable": args.java_executable,
            "javac_executable": args.javac_executable,
        }
        try:
            JvmAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="jvm",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote JVM reproduction spec -> {out_path}")
        return 0
    if ecosystem == "js":
        if not args.old_package_path or not args.new_package_path:
            print("ERROR JS reproduction requires --old-package-path and --new-package-path", file=sys.stderr)
            return 2
        metadata = {
            "old_package_path": args.old_package_path,
            "new_package_path": args.new_package_path,
            "module_paths": args.module_path,
            "old_module_paths": args.old_module_path,
            "new_module_paths": args.new_module_path,
            "node_args": args.node_arg,
            "old_node_args": args.old_node_arg,
            "new_node_args": args.new_node_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "node_executable": args.node_executable,
        }
        try:
            JsAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="js",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote JS reproduction spec -> {out_path}")
        return 0
    if ecosystem == "php":
        if not args.old_package_path or not args.new_package_path:
            print("ERROR PHP reproduction requires --old-package-path and --new-package-path", file=sys.stderr)
            return 2
        metadata = {
            "old_package_path": args.old_package_path,
            "new_package_path": args.new_package_path,
            "include_paths": args.include_path,
            "old_include_paths": args.old_include_path,
            "new_include_paths": args.new_include_path,
            "php_args": args.php_arg,
            "old_php_args": args.old_php_arg,
            "new_php_args": args.new_php_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "php_executable": args.php_executable,
        }
        try:
            PhpAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="php",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote PHP reproduction spec -> {out_path}")
        return 0
    if ecosystem == "ruby":
        if not args.old_package_path or not args.new_package_path:
            print("ERROR Ruby reproduction requires --old-package-path and --new-package-path", file=sys.stderr)
            return 2
        metadata = {
            "old_package_path": args.old_package_path,
            "new_package_path": args.new_package_path,
            "load_paths": args.load_path,
            "old_load_paths": args.old_load_path,
            "new_load_paths": args.new_load_path,
            "ruby_args": args.ruby_arg,
            "old_ruby_args": args.old_ruby_arg,
            "new_ruby_args": args.new_ruby_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "ruby_executable": args.ruby_executable,
        }
        try:
            RubyAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="ruby",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote Ruby reproduction spec -> {out_path}")
        return 0
    if ecosystem == "dotnet":
        if not args.old_package_path or not args.new_package_path:
            print("ERROR .NET reproduction requires --old-package-path and --new-package-path", file=sys.stderr)
            return 2
        metadata = {
            "old_package_path": args.old_package_path,
            "new_package_path": args.new_package_path,
            "reference_paths": args.reference_path,
            "old_reference_paths": args.old_reference_path,
            "new_reference_paths": args.new_reference_path,
            "dotnet_args": args.dotnet_arg,
            "old_dotnet_args": args.old_dotnet_arg,
            "new_dotnet_args": args.new_dotnet_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "dotnet_executable": args.dotnet_executable,
            "no_restore": not args.dotnet_restore,
        }
        try:
            DotnetAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="dotnet",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote .NET reproduction spec -> {out_path}")
        return 0
    if ecosystem == "go":
        if not args.old_package_path or not args.new_package_path:
            print("ERROR Go reproduction requires --old-package-path and --new-package-path", file=sys.stderr)
            return 2
        metadata = {
            "old_package_path": args.old_package_path,
            "new_package_path": args.new_package_path,
            "module_paths": args.go_module_path,
            "old_module_paths": args.old_go_module_path,
            "new_module_paths": args.new_go_module_path,
            "go_args": args.go_arg,
            "old_go_args": args.old_go_arg,
            "new_go_args": args.new_go_arg,
            "program_args": args.program_arg,
            "old_program_args": args.old_program_arg,
            "new_program_args": args.new_program_arg,
            "go_executable": args.go_executable,
            "no_network": not args.go_network,
        }
        try:
            GoAdapter().plan(
                AdapterPlanRequest(
                    candidate_id=args.candidate_id,
                    ecosystem="go",
                    library=args.library,
                    old_version=args.old_version,
                    new_version=args.new_version,
                    client_file=str(client_file),
                    out_path=str(out_path),
                    metadata=metadata,
                )
            )
        except Exception as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            return 1
        print(f"wrote Go reproduction spec -> {out_path}")
        return 0
    if ecosystem != "python":
        print(f"ERROR unsupported reproduction ecosystem: {args.ecosystem}", file=sys.stderr)
        return 2

    spec = create_reproduction_spec(
        candidate_id=args.candidate_id,
        library=args.library,
        old_version=args.old_version,
        new_version=args.new_version,
        client_file=client_file,
        old_package_path=args.old_package_path,
        new_package_path=args.new_package_path,
        old_python_executable=args.old_python_executable,
        new_python_executable=args.new_python_executable,
        extra_packages=args.extra_package,
        old_extra_packages=args.old_extra_package,
        new_extra_packages=args.new_extra_package,
    )
    write_reproduction_spec(spec, out_path)
    print(f"wrote reproduction spec -> {out_path}")
    return 0


def cmd_reproduce_run(args: argparse.Namespace) -> int:
    spec_path = artifact_path(args.spec, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    try:
        spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
        if spec_payload.get("ecosystem") == "jvm":
            result_path = JvmAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                    metadata={"build_timeout_s": args.build_timeout},
                )
            )
            result = load_reproduction_result(result_path)
        elif spec_payload.get("ecosystem") == "js":
            result_path = JsAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                )
            )
            result = load_reproduction_result(result_path)
        elif spec_payload.get("ecosystem") == "php":
            result_path = PhpAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                )
            )
            result = load_reproduction_result(result_path)
        elif spec_payload.get("ecosystem") == "ruby":
            result_path = RubyAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                )
            )
            result = load_reproduction_result(result_path)
        elif spec_payload.get("ecosystem") == "dotnet":
            result_path = DotnetAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                )
            )
            result = load_reproduction_result(result_path)
        elif spec_payload.get("ecosystem") == "go":
            result_path = GoAdapter().run(
                AdapterRunRequest(
                    spec_path=str(spec_path),
                    out_dir=str(out_path),
                    timeout_s=args.timeout,
                )
            )
            result = load_reproduction_result(result_path)
        else:
            spec = load_reproduction_spec(spec_path)
            venv_root = Path(args.venv_root) if args.venv_root else None
            result = run_reproduction_spec(
                spec,
                out_path,
                timeout_s=args.timeout,
                install=args.install,
                venv_root=venv_root,
                build_timeout_s=args.build_timeout,
            )
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"wrote reproduction result -> {Path(result.attempt_dir) / 'result.json'}")
    print(json.dumps({
        "keep": result.keep,
        "drop_reason": result.drop_reason.value if result.drop_reason else None,
        "summary": result.diff.summary,
    }, ensure_ascii=False))
    return 0


def cmd_reproduce_summarize(args: argparse.Namespace) -> int:
    result_path = artifact_path(args.result, args.artifact_root)
    try:
        result = load_reproduction_result(result_path)
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "candidate_id": result.candidate_id,
        "attempt_dir": result.attempt_dir,
        "keep": result.keep,
        "drop_reason": result.drop_reason.value if result.drop_reason else None,
        "diff_summary": result.diff.summary,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_reproduce_generate_client(args: argparse.Namespace) -> int:
    candidate_path = artifact_path(args.candidate, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    prompt_out = artifact_path(args.prompt_out, args.artifact_root) if args.prompt_out else None
    metadata_out = artifact_path(args.metadata_out, args.artifact_root) if args.metadata_out else None
    try:
        artifacts = write_client_generation_artifacts(
            candidate_path=candidate_path,
            candidate_id=args.candidate_id,
            out_path=out_path,
            redacted=args.redacted,
            dry_run=args.dry_run,
            model=args.model,
            provider=args.provider,
            allowed_imports=args.allowed_import,
            forbidden_terms=args.forbidden_term,
            prompt_out=prompt_out,
            metadata_out=metadata_out,
        )
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(artifacts.to_json())
    return 0


def cmd_curate_create(args: argparse.Namespace) -> int:
    result_path = artifact_path(args.reproduction_result, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    try:
        case = create_curated_case(
            result_path,
            args.decision,
            args.case_id,
            source_url=args.source_url,
            source_excerpt=args.source_excerpt,
            retrieved_at=args.retrieved_at,
            ecosystem=args.ecosystem,
            version_old=args.version_old,
            version_new=args.version_new,
            api_surface=args.api_surface,
            review_notes=args.review_notes,
        )
        if not Path(args.reproduction_result).is_absolute():
            case.reproduction_result = os.path.relpath(result_path, start=out_path.parent)
        write_curated_case(case, out_path)
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"wrote curated case -> {out_path}")
    return 0


def cmd_oracle_generate(args: argparse.Namespace) -> int:
    if args.template != "pytest":
        print("ERROR only --template pytest is supported", file=sys.stderr)
        return 2
    case_path = artifact_path(args.case, args.artifact_root)
    out_dir = artifact_path(args.out, args.artifact_root)
    try:
        generate_pytest_oracle(case_path, out_dir)
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"wrote oracle -> {out_dir}")
    return 0


def cmd_oracle_validate(args: argparse.Namespace) -> int:
    oracle_path = artifact_path(args.oracle, args.artifact_root)
    try:
        result = validate_pytest_oracle(oracle_path, args.mode)
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(result.to_json())
    return 0 if result.pass_ else 1


def cmd_bench_package(args: argparse.Namespace) -> int:
    case_path = artifact_path(args.case, args.artifact_root)
    oracle_path = artifact_path(args.oracle, args.artifact_root)
    out_root = artifact_path(args.out, args.artifact_root)
    levels = [level.strip() for level in args.levels.split(",") if level.strip()]
    try:
        package_dir = create_benchmark_package(case_path, oracle_path, levels, out_root)
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(f"wrote benchmark package -> {package_dir}")
    return 0


def cmd_audit_case(args: argparse.Namespace) -> int:
    package_dir = artifact_path(args.package, args.artifact_root)
    out_path = artifact_path(args.out, args.artifact_root)
    report = audit_package(package_dir)
    write_audit_report(report, out_path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


def cmd_ecosystem_gates(args: argparse.Namespace) -> int:
    report = evaluate_adapter_gates(
        packages_root=Path(args.packages),
        audit_root=Path(args.audit),
        target_ecosystem=args.target,
        required_python_cases=args.min_python_cases,
    )
    text = report.to_json()
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.pass_ else 1


def cmd_ecosystem_env_check(args: argparse.Namespace) -> int:
    report = check_ecosystem_environment(args.target)
    text = report.to_json()
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.pass_ else 1


def cmd_ecosystem_adapters(args: argparse.Namespace) -> int:
    try:
        text = adapter_contract_report_json(args.target)
    except KeyError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def cmd_python_status(args: argparse.Namespace) -> int:
    report = build_python_status_report(
        cases_root=Path(args.cases),
        packages_root=Path(args.packages),
        min_audited_cases=args.min_cases,
    )
    text = report.to_json()
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report.pass_ else 1


def cmd_autodiscovery_init(args: argparse.Namespace) -> int:
    init_memory(Path(args.idea_bank), Path(args.run_log))
    print(f"initialized autodiscovery markdown memory -> {args.idea_bank}, {args.run_log}")
    return 0


def cmd_autodiscovery_idea(args: argparse.Namespace) -> int:
    card = IdeaCard(
        title=args.title,
        package=args.package,
        api_surface=args.api_surface,
        versions=args.versions,
        source_url=args.source_url,
        source_section=args.source_section,
        evidence=args.evidence,
        behavior_hypothesis=args.behavior_hypothesis,
        silent_drift_reason=args.silent_drift_reason,
        reproduction_sketch=args.reproduction_sketch,
        duplicate_similar_to=args.duplicate_similar_to,
        duplicate_different_because=args.duplicate_different_because,
        risk_notes=args.risk_note,
        next_action=args.next_action,
    )
    card_id = append_idea(Path(args.idea_bank), card, card_id=args.id)
    print(f"appended idea card -> {card_id}")
    return 0


def cmd_autodiscovery_reject(args: argparse.Namespace) -> int:
    card = RejectedCard(
        title=args.title,
        package=args.package,
        api_surface=args.api_surface,
        source=args.source,
        tried_because=args.tried_because,
        rejected_because=args.rejected_because,
        future_avoid=args.future_avoid,
        future_may_try=args.future_may_try,
    )
    card_id = append_rejected(Path(args.idea_bank), card, card_id=args.id)
    print(f"appended rejected card -> {card_id}")
    return 0


def cmd_autodiscovery_accept(args: argparse.Namespace) -> int:
    card = AcceptedCard(
        case_id=args.case_id,
        package=args.package,
        api_surface=args.api_surface,
        versions=args.versions,
        source=args.source,
        reproduction_path=args.reproduction_path,
        oracle_path=args.oracle_path,
        package_path=args.package_path,
        audit_path=args.audit_path,
        why_non_duplicate=args.why_non_duplicate,
        follow_up_ideas=args.follow_up_idea,
    )
    card_id = append_accepted(Path(args.idea_bank), card, card_id=args.id)
    print(f"appended accepted card -> {card_id}")
    return 0


def cmd_autodiscovery_log(args: argparse.Namespace) -> int:
    entry = RunLogEntry(
        title=args.title,
        model_or_operator=args.model_or_operator,
        search_budget=args.search_budget,
        packages_searched=args.package_searched,
        ideas_added=args.idea_added,
        ideas_rejected=args.idea_rejected,
        promoted=args.promoted,
        accepted=args.accepted,
        notes=args.note,
    )
    append_run_log(Path(args.run_log), entry)
    print(f"appended autodiscovery run log -> {args.run_log}")
    return 0


def cmd_autodiscovery_avoid(args: argparse.Namespace) -> int:
    text = build_avoid_summary(Path(args.idea_bank))
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="silent-drift-miner")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_mine = sub.add_parser("mine", help="run the mining pipeline")
    p_mine.add_argument("--config", default="configs/targets.yaml")
    p_mine.add_argument("--library", default=None, help="only mine this library from config")
    p_mine.add_argument("--ecosystem", default="other", help="ecosystem for --source mining")
    p_mine.add_argument("--source", default=None, help="local changelog/release-note fixture")
    p_mine.add_argument("--source-url", default=None, help="stable provenance URL for --source")
    p_mine.add_argument("--cache-dir", default="data/raw_changelogs")
    p_mine.add_argument("--artifact-root", default=None,
                        help="artifact root; when set, outputs cannot escape this directory")
    p_mine.add_argument("--out-dir", default=None)
    p_mine.add_argument("--out", default=None, help="candidate JSONL output for single --source mining")
    p_mine.add_argument("--threshold", type=int, default=4,
                        help="rule score threshold to emit a WEAK candidate")
    llm_group = p_mine.add_mutually_exclusive_group()
    llm_group.add_argument("--use-llm", dest="llm_mode", action="store_const", const="api", default="none",
                           help="enable LLM refinement (needs ANTHROPIC_API_KEY)")
    llm_group.add_argument("--no-llm", dest="llm_mode", action="store_const", const="none",
                           help="disable LLM refinement (default)")
    llm_group.add_argument("--llm-filter", dest="llm_mode", action="store_const", const="offline",
                           help="run deterministic offline precision filter")
    p_mine.set_defaults(func=cmd_mine)

    p_stats = sub.add_parser("stats", help="print summary over all candidates")
    p_stats.add_argument("paths", nargs="*", help="candidate JSONL files or directories")
    p_stats.add_argument("--artifact-root", default=None,
                         help="artifact root; defaults candidate input to <root>/candidates")
    p_stats.add_argument("--out-dir", default=None)
    p_stats.set_defaults(func=cmd_stats)

    p_show = sub.add_parser("show", help="show candidates for one library")
    p_show.add_argument("target", help="library name or candidate JSONL file")
    p_show.add_argument("--artifact-root", default=None,
                        help="artifact root; defaults candidate input to <root>/candidates")
    p_show.add_argument("--out-dir", default=None)
    p_show.add_argument("--candidate-id", default=None)
    p_show.add_argument("--limit", type=int, default=20)
    p_show.add_argument("--only-category", default=None)
    p_show.add_argument("--min-confidence", default=None,
                        choices=["weak", "uncertain_silence", "high"])
    p_show.set_defaults(func=cmd_show)

    p_validate = sub.add_parser("validate-candidates",
                                help="validate JSONL schema and round-trip for a candidates file")
    p_validate.add_argument("path", help="path to a candidates .jsonl file")
    p_validate.set_defaults(func=cmd_validate)

    p_triage = sub.add_parser("triage", help="build and mark triage queues")
    triage_sub = p_triage.add_subparsers(dest="triage_cmd", required=True)

    p_triage_build = triage_sub.add_parser("build", help="build a triage queue from candidates")
    p_triage_build.add_argument("--artifact-root", default=None,
                                help="artifact root; outputs cannot escape this directory")
    p_triage_build.add_argument("--candidates", required=True)
    p_triage_build.add_argument("--out", required=True)
    p_triage_build.set_defaults(func=cmd_triage_build)

    p_triage_next = triage_sub.add_parser("next", help="show the next undecided candidate")
    p_triage_next.add_argument("--artifact-root", default=None,
                               help="artifact root; queue path must stay inside this directory")
    p_triage_next.add_argument("--queue", required=True)
    p_triage_next.add_argument("--json", action="store_true")
    p_triage_next.set_defaults(func=cmd_triage_next)

    decisions = [d.value for d in TriageDecision]
    p_triage_mark = triage_sub.add_parser("mark", help="mark one triage decision")
    p_triage_mark.add_argument("--artifact-root", default=None,
                               help="artifact root; queue path must stay inside this directory")
    p_triage_mark.add_argument("--queue", required=True)
    p_triage_mark.add_argument("--candidate-id", required=True)
    p_triage_mark.add_argument("--decision", required=True, choices=decisions)
    p_triage_mark.add_argument("--notes", default="")
    p_triage_mark.add_argument("--reviewer", default="")
    p_triage_mark.add_argument("--overwrite", action="store_true")
    p_triage_mark.set_defaults(func=cmd_triage_mark)

    p_triage_export = triage_sub.add_parser("export", help="export candidates from a queue")
    p_triage_export.add_argument("--artifact-root", default=None,
                                 help="artifact root; output cannot escape this directory")
    p_triage_export.add_argument("--queue", required=True)
    p_triage_export.add_argument("--out", required=True)
    p_triage_export.add_argument("--decision", choices=decisions, default=None)
    p_triage_export.add_argument("--include-undecided", action="store_true")
    p_triage_export.set_defaults(func=cmd_triage_export)

    p_reproduce = sub.add_parser("reproduce", help="plan and run reproductions")
    reproduce_sub = p_reproduce.add_subparsers(dest="reproduce_cmd", required=True)

    p_reproduce_plan = reproduce_sub.add_parser("plan", help="create a reproduction spec")
    p_reproduce_plan.add_argument("--artifact-root", default=None,
                                  help="artifact root; output cannot escape this directory")
    p_reproduce_plan.add_argument(
        "--ecosystem",
        default="python",
        choices=["python", "jvm", "js", "php", "ruby", "dotnet", "go"],
    )
    p_reproduce_plan.add_argument("--candidate-id", required=True)
    p_reproduce_plan.add_argument("--library", required=True)
    p_reproduce_plan.add_argument("--old-version", required=True)
    p_reproduce_plan.add_argument("--new-version", required=True)
    p_reproduce_plan.add_argument("--client-file", required=True)
    p_reproduce_plan.add_argument("--old-package-path", default=None,
                                  help="offline package directory added to PYTHONPATH for old run")
    p_reproduce_plan.add_argument("--new-package-path", default=None,
                                  help="offline package directory added to PYTHONPATH for new run")
    p_reproduce_plan.add_argument("--old-python-executable", default="python",
                                  help="base Python used for the old run or isolated venv")
    p_reproduce_plan.add_argument("--new-python-executable", default="python",
                                  help="base Python used for the new run or isolated venv")
    p_reproduce_plan.add_argument("--extra-package", action="append", default=[],
                                  help="additional package spec installed before both old and new library versions")
    p_reproduce_plan.add_argument("--old-extra-package", action="append", default=[],
                                  help="additional package spec installed only before the old library version")
    p_reproduce_plan.add_argument("--new-extra-package", action="append", default=[],
                                  help="additional package spec installed only before the new library version")
    p_reproduce_plan.add_argument("--old-source-path", action="append", default=[],
                                  help="JVM old source root or source file; repeat for multiple roots")
    p_reproduce_plan.add_argument("--new-source-path", action="append", default=[],
                                  help="JVM new source root or source file; repeat for multiple roots")
    p_reproduce_plan.add_argument("--classpath", action="append", default=[],
                                  help="JVM shared classpath entry, such as a local JAR")
    p_reproduce_plan.add_argument("--old-classpath", action="append", default=[],
                                  help="JVM old-only classpath entry")
    p_reproduce_plan.add_argument("--new-classpath", action="append", default=[],
                                  help="JVM new-only classpath entry")
    p_reproduce_plan.add_argument("--resource-path", action="append", default=[],
                                  help="JVM shared resource directory placed on the runtime classpath")
    p_reproduce_plan.add_argument("--old-resource-path", action="append", default=[],
                                  help="JVM old-only resource directory")
    p_reproduce_plan.add_argument("--new-resource-path", action="append", default=[],
                                  help="JVM new-only resource directory")
    p_reproduce_plan.add_argument("--jvm-arg", action="append", default=[],
                                  help="JVM argument passed before -cp, such as -Dkey=value")
    p_reproduce_plan.add_argument("--old-jvm-arg", action="append", default=[],
                                  help="JVM old-only argument")
    p_reproduce_plan.add_argument("--new-jvm-arg", action="append", default=[],
                                  help="JVM new-only argument")
    p_reproduce_plan.add_argument("--program-arg", action="append", default=[],
                                  help="argument passed to the JVM client main class")
    p_reproduce_plan.add_argument("--old-program-arg", action="append", default=[],
                                  help="old-only argument passed to the JVM client main class")
    p_reproduce_plan.add_argument("--new-program-arg", action="append", default=[],
                                  help="new-only argument passed to the JVM client main class")
    p_reproduce_plan.add_argument("--main-class", default="DriftClient",
                                  help="JVM client main class")
    p_reproduce_plan.add_argument("--java-executable", default="java")
    p_reproduce_plan.add_argument("--javac-executable", default="javac")
    p_reproduce_plan.add_argument("--module-path", action="append", default=[],
                                  help="JS shared module path added to NODE_PATH")
    p_reproduce_plan.add_argument("--old-module-path", action="append", default=[],
                                  help="JS old-only module path added to NODE_PATH")
    p_reproduce_plan.add_argument("--new-module-path", action="append", default=[],
                                  help="JS new-only module path added to NODE_PATH")
    p_reproduce_plan.add_argument("--node-arg", action="append", default=[],
                                  help="JS shared node argument passed before the client file")
    p_reproduce_plan.add_argument("--old-node-arg", action="append", default=[],
                                  help="JS old-only node argument")
    p_reproduce_plan.add_argument("--new-node-arg", action="append", default=[],
                                  help="JS new-only node argument")
    p_reproduce_plan.add_argument("--node-executable", default="node")
    p_reproduce_plan.add_argument("--include-path", action="append", default=[],
                                  help="PHP shared include path")
    p_reproduce_plan.add_argument("--old-include-path", action="append", default=[],
                                  help="PHP old-only include path")
    p_reproduce_plan.add_argument("--new-include-path", action="append", default=[],
                                  help="PHP new-only include path")
    p_reproduce_plan.add_argument("--php-arg", action="append", default=[],
                                  help="PHP shared argument passed before -d include_path")
    p_reproduce_plan.add_argument("--old-php-arg", action="append", default=[],
                                  help="PHP old-only argument")
    p_reproduce_plan.add_argument("--new-php-arg", action="append", default=[],
                                  help="PHP new-only argument")
    p_reproduce_plan.add_argument("--php-executable", default="php")
    p_reproduce_plan.add_argument("--load-path", action="append", default=[],
                                  help="Ruby shared load path added to RUBYLIB/-I")
    p_reproduce_plan.add_argument("--old-load-path", action="append", default=[],
                                  help="Ruby old-only load path added to RUBYLIB/-I")
    p_reproduce_plan.add_argument("--new-load-path", action="append", default=[],
                                  help="Ruby new-only load path added to RUBYLIB/-I")
    p_reproduce_plan.add_argument("--ruby-arg", action="append", default=[],
                                  help="Ruby shared argument passed before the client file")
    p_reproduce_plan.add_argument("--old-ruby-arg", action="append", default=[],
                                  help="Ruby old-only argument")
    p_reproduce_plan.add_argument("--new-ruby-arg", action="append", default=[],
                                  help="Ruby new-only argument")
    p_reproduce_plan.add_argument("--ruby-executable", default="ruby")
    p_reproduce_plan.add_argument("--reference-path", action="append", default=[],
                                  help=".NET shared reference path exposed in DOTNET_ADAPTER_PACKAGE_PATHS")
    p_reproduce_plan.add_argument("--old-reference-path", action="append", default=[],
                                  help=".NET old-only reference path")
    p_reproduce_plan.add_argument("--new-reference-path", action="append", default=[],
                                  help=".NET new-only reference path")
    p_reproduce_plan.add_argument("--dotnet-arg", action="append", default=[],
                                  help=".NET shared argument passed before --")
    p_reproduce_plan.add_argument("--old-dotnet-arg", action="append", default=[],
                                  help=".NET old-only argument")
    p_reproduce_plan.add_argument("--new-dotnet-arg", action="append", default=[],
                                  help=".NET new-only argument")
    p_reproduce_plan.add_argument("--dotnet-executable", default="dotnet")
    p_reproduce_plan.add_argument("--dotnet-restore", action="store_true",
                                  help="allow dotnet run to perform restore instead of passing --no-restore")
    p_reproduce_plan.add_argument("--go-module-path", action="append", default=[],
                                  help="Go shared local module/reference path")
    p_reproduce_plan.add_argument("--old-go-module-path", action="append", default=[],
                                  help="Go old-only local module/reference path")
    p_reproduce_plan.add_argument("--new-go-module-path", action="append", default=[],
                                  help="Go new-only local module/reference path")
    p_reproduce_plan.add_argument("--go-arg", action="append", default=[],
                                  help="Go shared argument passed before the client package")
    p_reproduce_plan.add_argument("--old-go-arg", action="append", default=[],
                                  help="Go old-only argument")
    p_reproduce_plan.add_argument("--new-go-arg", action="append", default=[],
                                  help="Go new-only argument")
    p_reproduce_plan.add_argument("--go-executable", default="go")
    p_reproduce_plan.add_argument("--go-network", action="store_true",
                                  help="allow go run to use normal network module lookup")
    p_reproduce_plan.add_argument("--out", required=True)
    p_reproduce_plan.set_defaults(func=cmd_reproduce_plan)

    p_reproduce_run = reproduce_sub.add_parser("run", help="run old/new clients from a spec")
    p_reproduce_run.add_argument("--artifact-root", default=None,
                                 help="artifact root; output cannot escape this directory")
    p_reproduce_run.add_argument("--spec", required=True)
    p_reproduce_run.add_argument("--out", required=True)
    p_reproduce_run.add_argument("--timeout", type=int, default=30)
    p_reproduce_run.add_argument("--install", action="store_true",
                                 help="create isolated venvs and run each side's install command before the client")
    p_reproduce_run.add_argument("--venv-root", default=None,
                                 help="directory for reusable isolated reproduction venvs")
    p_reproduce_run.add_argument("--build-timeout", type=int, default=300,
                                 help="seconds allowed for venv creation and dependency install")
    p_reproduce_run.set_defaults(func=cmd_reproduce_run)

    p_reproduce_summarize = reproduce_sub.add_parser("summarize", help="summarize a reproduction result")
    p_reproduce_summarize.add_argument("--artifact-root", default=None,
                                       help="artifact root; result path must stay inside this directory")
    p_reproduce_summarize.add_argument("--result", required=True)
    p_reproduce_summarize.set_defaults(func=cmd_reproduce_summarize)

    p_reproduce_generate_client = reproduce_sub.add_parser(
        "generate-client",
        help="build leak-controlled client-generation prompt artifacts",
    )
    p_reproduce_generate_client.add_argument("--artifact-root", default=None,
                                             help="artifact root; outputs cannot escape this directory")
    p_reproduce_generate_client.add_argument("--candidate", required=True)
    p_reproduce_generate_client.add_argument("--candidate-id", required=True)
    p_reproduce_generate_client.add_argument("--redacted", action="store_true")
    p_reproduce_generate_client.add_argument("--dry-run", action="store_true",
                                             help="write a deterministic scaffold instead of calling a live LLM")
    p_reproduce_generate_client.add_argument("--provider", default="anthropic")
    p_reproduce_generate_client.add_argument("--model", default=None)
    p_reproduce_generate_client.add_argument("--allowed-import", action="append", default=[])
    p_reproduce_generate_client.add_argument("--forbidden-term", action="append", default=[])
    p_reproduce_generate_client.add_argument("--prompt-out", default=None)
    p_reproduce_generate_client.add_argument("--metadata-out", default=None)
    p_reproduce_generate_client.add_argument("--out", required=True)
    p_reproduce_generate_client.set_defaults(func=cmd_reproduce_generate_client)

    p_curate = sub.add_parser("curate", help="create curated case manifests")
    curate_sub = p_curate.add_subparsers(dest="curate_cmd", required=True)

    p_curate_create = curate_sub.add_parser("create", help="create an accepted or rejected case manifest")
    p_curate_create.add_argument("--artifact-root", default=None,
                                 help="artifact root; output cannot escape this directory")
    p_curate_create.add_argument("--reproduction-result", required=True)
    p_curate_create.add_argument("--decision", required=True,
                                 choices=[d.value for d in CurationDecision])
    p_curate_create.add_argument("--case-id", required=True)
    p_curate_create.add_argument("--source-url", default=None)
    p_curate_create.add_argument("--source-excerpt", default=None)
    p_curate_create.add_argument("--retrieved-at", default=None)
    p_curate_create.add_argument("--ecosystem", default=None)
    p_curate_create.add_argument("--version-old", default=None)
    p_curate_create.add_argument("--version-new", default=None)
    p_curate_create.add_argument("--api-surface", action="append", default=[])
    p_curate_create.add_argument("--review-notes", default=None)
    p_curate_create.add_argument("--out", required=True)
    p_curate_create.set_defaults(func=cmd_curate_create)

    p_oracle = sub.add_parser("oracle", help="generate and validate oracles")
    oracle_sub = p_oracle.add_subparsers(dest="oracle_cmd", required=True)

    p_oracle_generate = oracle_sub.add_parser("generate", help="generate a pytest oracle scaffold")
    p_oracle_generate.add_argument("--artifact-root", default=None,
                                   help="artifact root; output cannot escape this directory")
    p_oracle_generate.add_argument("--case", required=True)
    p_oracle_generate.add_argument("--template", default="pytest")
    p_oracle_generate.add_argument("--out", required=True)
    p_oracle_generate.set_defaults(func=cmd_oracle_generate)

    p_oracle_validate = oracle_sub.add_parser("validate", help="run hidden pytest oracle validation")
    p_oracle_validate.add_argument("--artifact-root", default=None,
                                   help="artifact root; oracle path must stay inside this directory")
    p_oracle_validate.add_argument("--oracle", required=True)
    p_oracle_validate.add_argument("--mode", required=True, choices=["old", "new", "fixed"])
    p_oracle_validate.set_defaults(func=cmd_oracle_validate)

    p_bench = sub.add_parser("bench", help="package benchmark tasks")
    bench_sub = p_bench.add_subparsers(dest="bench_cmd", required=True)

    p_bench_package = bench_sub.add_parser("package", help="package a curated case and oracle")
    p_bench_package.add_argument("--artifact-root", default=None,
                                 help="artifact root; output cannot escape this directory")
    p_bench_package.add_argument("--case", required=True)
    p_bench_package.add_argument("--oracle", required=True)
    p_bench_package.add_argument("--levels", default="L1,L2,L3")
    p_bench_package.add_argument("--out", required=True)
    p_bench_package.set_defaults(func=cmd_bench_package)

    p_audit = sub.add_parser("audit", help="audit packaged benchmark tasks")
    audit_sub = p_audit.add_subparsers(dest="audit_cmd", required=True)

    p_audit_case = audit_sub.add_parser("case", help="audit one benchmark package")
    p_audit_case.add_argument("--artifact-root", default=None,
                              help="artifact root; output cannot escape this directory")
    p_audit_case.add_argument("--package", required=True)
    p_audit_case.add_argument("--out", required=True)
    p_audit_case.set_defaults(func=cmd_audit_case)

    p_ecosystem = sub.add_parser("ecosystem", help="inspect ecosystem expansion gates")
    ecosystem_sub = p_ecosystem.add_subparsers(dest="ecosystem_cmd", required=True)

    p_ecosystem_gates = ecosystem_sub.add_parser("gates", help="check whether a new adapter can be enabled")
    p_ecosystem_gates.add_argument("--target", required=True, help="target ecosystem, e.g. jvm")
    p_ecosystem_gates.add_argument("--packages", default="data/packages")
    p_ecosystem_gates.add_argument("--audit", default="data/audit")
    p_ecosystem_gates.add_argument("--min-python-cases", type=int, default=3)
    p_ecosystem_gates.add_argument("--out", default=None)
    p_ecosystem_gates.set_defaults(func=cmd_ecosystem_gates)

    p_ecosystem_env = ecosystem_sub.add_parser("env-check", help="check local tools for an ecosystem adapter")
    p_ecosystem_env.add_argument("--target", required=True, help="target ecosystem, e.g. jvm")
    p_ecosystem_env.add_argument("--out", default=None)
    p_ecosystem_env.set_defaults(func=cmd_ecosystem_env_check)

    p_ecosystem_adapters = ecosystem_sub.add_parser(
        "adapters",
        help="list ecosystem adapter contracts",
    )
    p_ecosystem_adapters.add_argument("--target", default=None, help="optional ecosystem filter")
    p_ecosystem_adapters.add_argument("--out", default=None)
    p_ecosystem_adapters.set_defaults(func=cmd_ecosystem_adapters)

    p_python = sub.add_parser("python", help="inspect Python-only benchmark lifecycle status")
    python_sub = p_python.add_subparsers(dest="python_cmd", required=True)

    p_python_status = python_sub.add_parser("status", help="report Python lifecycle completion")
    p_python_status.add_argument("--cases", default="cases")
    p_python_status.add_argument("--packages", default="data/packages")
    p_python_status.add_argument("--min-cases", type=int, default=3)
    p_python_status.add_argument("--out", default=None)
    p_python_status.set_defaults(func=cmd_python_status)

    p_autodiscovery = sub.add_parser(
        "autodiscovery",
        help="maintain Markdown memory for Python drift discovery",
    )
    autodiscovery_sub = p_autodiscovery.add_subparsers(dest="autodiscovery_cmd", required=True)

    p_autodiscovery_init = autodiscovery_sub.add_parser(
        "init",
        help="create the Markdown idea bank and run log if missing",
    )
    p_autodiscovery_init.add_argument("--idea-bank", default=str(DEFAULT_IDEA_BANK))
    p_autodiscovery_init.add_argument("--run-log", default=str(DEFAULT_RUN_LOG))
    p_autodiscovery_init.set_defaults(func=cmd_autodiscovery_init)

    p_autodiscovery_idea = autodiscovery_sub.add_parser("idea", help="append a discovered idea card")
    p_autodiscovery_idea.add_argument("--idea-bank", default=str(DEFAULT_IDEA_BANK))
    p_autodiscovery_idea.add_argument("--id", default=None, help="optional stable card id")
    p_autodiscovery_idea.add_argument("--title", required=True)
    p_autodiscovery_idea.add_argument("--package", default="")
    p_autodiscovery_idea.add_argument("--api-surface", default="")
    p_autodiscovery_idea.add_argument("--versions", default="")
    p_autodiscovery_idea.add_argument("--source-url", default="")
    p_autodiscovery_idea.add_argument("--source-section", default="")
    p_autodiscovery_idea.add_argument("--evidence", default="")
    p_autodiscovery_idea.add_argument("--behavior-hypothesis", default="")
    p_autodiscovery_idea.add_argument("--silent-drift-reason", default="")
    p_autodiscovery_idea.add_argument("--reproduction-sketch", default="")
    p_autodiscovery_idea.add_argument("--duplicate-similar-to", default="")
    p_autodiscovery_idea.add_argument("--duplicate-different-because", default="")
    p_autodiscovery_idea.add_argument("--risk-note", action="append", default=[])
    p_autodiscovery_idea.add_argument("--next-action", default="")
    p_autodiscovery_idea.set_defaults(func=cmd_autodiscovery_idea)

    p_autodiscovery_reject = autodiscovery_sub.add_parser("reject", help="append a rejected idea card")
    p_autodiscovery_reject.add_argument("--idea-bank", default=str(DEFAULT_IDEA_BANK))
    p_autodiscovery_reject.add_argument("--id", default=None, help="optional stable card id")
    p_autodiscovery_reject.add_argument("--title", required=True)
    p_autodiscovery_reject.add_argument("--package", default="")
    p_autodiscovery_reject.add_argument("--api-surface", default="")
    p_autodiscovery_reject.add_argument("--source", default="")
    p_autodiscovery_reject.add_argument("--tried-because", default="")
    p_autodiscovery_reject.add_argument("--rejected-because", action="append", default=[])
    p_autodiscovery_reject.add_argument("--future-avoid", default="")
    p_autodiscovery_reject.add_argument("--future-may-try", default="")
    p_autodiscovery_reject.set_defaults(func=cmd_autodiscovery_reject)

    p_autodiscovery_accept = autodiscovery_sub.add_parser("accept", help="append an accepted case anchor")
    p_autodiscovery_accept.add_argument("--idea-bank", default=str(DEFAULT_IDEA_BANK))
    p_autodiscovery_accept.add_argument("--id", default=None, help="optional stable card id")
    p_autodiscovery_accept.add_argument("--case-id", required=True)
    p_autodiscovery_accept.add_argument("--package", default="")
    p_autodiscovery_accept.add_argument("--api-surface", default="")
    p_autodiscovery_accept.add_argument("--versions", default="")
    p_autodiscovery_accept.add_argument("--source", default="")
    p_autodiscovery_accept.add_argument("--reproduction-path", default="")
    p_autodiscovery_accept.add_argument("--oracle-path", default="")
    p_autodiscovery_accept.add_argument("--package-path", default="")
    p_autodiscovery_accept.add_argument("--audit-path", default="")
    p_autodiscovery_accept.add_argument("--why-non-duplicate", default="")
    p_autodiscovery_accept.add_argument("--follow-up-idea", action="append", default=[])
    p_autodiscovery_accept.set_defaults(func=cmd_autodiscovery_accept)

    p_autodiscovery_log = autodiscovery_sub.add_parser("log", help="append a batch-level run note")
    p_autodiscovery_log.add_argument("--run-log", default=str(DEFAULT_RUN_LOG))
    p_autodiscovery_log.add_argument("--title", required=True)
    p_autodiscovery_log.add_argument("--model-or-operator", default="")
    p_autodiscovery_log.add_argument("--search-budget", default="")
    p_autodiscovery_log.add_argument("--package-searched", action="append", default=[])
    p_autodiscovery_log.add_argument("--idea-added", action="append", default=[])
    p_autodiscovery_log.add_argument("--idea-rejected", action="append", default=[])
    p_autodiscovery_log.add_argument("--promoted", action="append", default=[])
    p_autodiscovery_log.add_argument("--accepted", action="append", default=[])
    p_autodiscovery_log.add_argument("--note", action="append", default=[])
    p_autodiscovery_log.set_defaults(func=cmd_autodiscovery_log)

    p_autodiscovery_avoid = autodiscovery_sub.add_parser(
        "avoid-list",
        help="summarize packages, APIs, accepted anchors, and rejection lessons from the idea bank",
    )
    p_autodiscovery_avoid.add_argument("--idea-bank", default=str(DEFAULT_IDEA_BANK))
    p_autodiscovery_avoid.add_argument("--out", default=None)
    p_autodiscovery_avoid.set_defaults(func=cmd_autodiscovery_avoid)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
