# silent-drift-miner

Current release: `v0.11.0`.

Current scope:

- Python package lifecycle is mature and has seven audited real cases.
- JVM, JS, PHP, Ruby, .NET, and Go adapters are active for local deterministic
  reproduction paths.
- Rust remains reserved.
- Python autodiscovery has Markdown memory helpers and one accepted
  idea-bank promotion; the real large discovery run has not been started.

分阶段实现路线图（Staged Implementation Roadmap）见 [../docs/README.md](../docs/README.md)，术语对齐（Terminology Alignment）见 [../docs/terminology.md](../docs/terminology.md)。

Layer 1 of the silent-drift benchmark pipeline.
Mines release notes and CHANGELOGs for *silent semantic drift* candidates:
behavior changes that leave the API call shape (name, parameters, return
type) untouched but quietly alter results.

This stage is **stdlib-only** by design — the only external dependency is
network access to GitHub, and Anthropic API access if you want LLM
refinement. PyYAML is optional and not required.

## Pipeline overview

```
  +--------------------+     +------------------+     +------------------+
  |  configs/          |     |  GitHubFetcher   |     |  rule prescreen  |
  |  targets.yaml      | --> |  (releases API + | --> |  -> WEAK         |
  |  (10+ libraries)   |     |   CHANGELOG.md)  |     |     candidates   |
  +--------------------+     +------------------+     +--------+---------+
                                                               |
                                                               v
                                                     +-------------------+
                                                     |  LLM refiner      |
                                                     |  (Anthropic API)  |
                                                     |  reject / keep    |
                                                     |  + paraphrase     |
                                                     +--------+----------+
                                                              |
                                                              v
                                                  data/candidates/<lib>.jsonl
                                                  (UNCERTAIN_SILENCE / HIGH)
```

What's intentionally **not** in this layer:
- docker reproducer generation (Layer 2)
- oracle test writing (Layer 3)
- human review UI (Layer 4)

Layer 1 outputs are the **input** to Layer 2, not benchmark samples yet.

## Install / run

```bash
# editable install (optional but recommended)
pip install -e .

# offline sanity demo using fragments captured from spring-boot wiki
PYTHONPATH=src python tools/demo_offline_spring_boot.py

# real run for one library (needs network access to api.github.com)
PYTHONPATH=src python -m silent_drift_miner.cli mine \
    --library spring-boot \
    --config configs/targets.yaml

# the same with LLM refinement
export ANTHROPIC_API_KEY=sk-ant-...
PYTHONPATH=src python -m silent_drift_miner.cli mine \
    --library spring-boot --use-llm

# inspect what was mined
PYTHONPATH=src python -m silent_drift_miner.cli show spring-boot --limit 20

# aggregate stats across all libraries
PYTHONPATH=src python -m silent_drift_miner.cli stats

# prepare the Python autodiscovery Markdown memory without starting a search
PYTHONPATH=src python -m silent_drift_miner.cli autodiscovery readiness
PYTHONPATH=src python -m silent_drift_miner.cli autodiscovery brief \
    --out ../docs/python-drift-next-run.md
```

For GitHub API runs on more than ~60 calls/hour, set `GITHUB_TOKEN` to
a personal access token (no scopes needed; public repo read works
unauthenticated except for rate-limit lift).

## Two-stage extraction by design

**Stage A — rules** (`extractors/rules.py`).
Cheap regex scoring on each release-note chunk. High recall, deliberately
noisy. Catches phrases like `now defaults to`, `default value from X to Y`,
`no longer enabled by default`. Down-weights loud-break language
(`removed`, `now throws`, signature changes).

**Stage B — LLM** (`extractors/llm.py`).
Each WEAK candidate is shown to Claude with a fixed JSON-output system
prompt. The model either rejects (loud break, additive feature, bug fix,
not drift) or keeps and fills the structured fields.

Why split: stage A throws away ~95% of changelog noise for free, so you
only pay LLM tokens on the ~5% worth thinking about. On a typical large
library this is the difference between $5 and $100 in API spend.

## Output format

One JSONL per library under `data/candidates/<library>.jsonl`. Each line
is a `DriftCandidate` dict — see `src/silent_drift_miner/schema.py`. Key
fields:

| field | meaning |
|---|---|
| `candidate_id` | stable 16-char hash, safe to use as primary key downstream |
| `library`, `ecosystem`, `version_new`, `version_old` | identity + version pair |
| `category` | one of the closed `DriftCategory` enum values |
| `confidence` | `weak` (rule only), `uncertain_silence` (LLM kept), `high` (LLM kept with strong language) |
| `summary_paraphrased` | LLM rewrite in our words (copyright-safe) |
| `reproduce_hypothesis` | guess at minimal code path that triggers drift |
| `api_surface` | concrete classes/methods/config keys mentioned |
| `evidence[]` | provenance: URL + short raw snippet + paraphrase |
| `why_flagged[]` | rule names that matched (debugging the prescreen) |

## What this layer is and isn't

It **is** a high-recall candidate miner that turns thousands of changelog
bullets into a few hundred annotated drift candidates with clean
provenance, in a form Layer 2 can fan out into reproducer attempts.

It **is not** a benchmark. A `DriftCandidate` is unverified text — many
will fail to reproduce, some will be false positives the LLM missed.
That's why pipeline_stage starts at 1; only Layer 2 (reproduce) and
Layer 5 (human approval) move it past stage 3.

## Limitations and known biases

- **Survivor bias**. Only mines what maintainers wrote down. Truly
  silent drift that no one noticed enough to document never shows up.
  Mitigation: cross-link with bug reports in Layer 2.
- **English-only rules**. Stage A patterns are English. Non-English
  CHANGELOGs (e.g. some JP/CN libraries) won't match.
- **One-shot LLM judgment**. Stage B sees only the chunk + version + URL,
  not surrounding context or the actual library code. Some borderline
  cases need Layer 2's reproduce attempt to settle.
- **Rule recall ceiling**. The regex set caught the obvious "default
  changed" / "now defaults to" patterns in tests but will miss drift
  that requires reading several sentences together (e.g. "Hibernate 6.1
  is used by default" → silent unless you know Hibernate 6.1 changed
  timezone storage). Layer 2's diff-based reproduce is what catches
  these.

## Tests

```bash
python -m pytest tests/ -v
```

The current full local suite is pytest-based. As of `v0.11.0`, the CI-mode
suite passes with `102 passed, 6 skipped` when optional real toolchain smoke
tests are skipped. Run it before changing rules, reproduction behavior,
adapters, packaging, or autodiscovery helpers.

## Next steps (Layer 2 sketch)

1. For each candidate above WEAK confidence, attempt:
   - `git clone` library at `version_old` and `version_new`
   - synthesize a minimal client snippet from `api_surface` + LLM
   - run inside two pinned Docker images, capture stdout/stderr/exit
   - keep candidates where the two captures genuinely differ
2. Promote `pipeline_stage` 1 → 2, store `reproducer_path`,
   `docker_image_old`, `docker_image_new` on the candidate.
3. Layer 3 then writes an oracle test asserting the diff. Layer 5 sample-
   audits a subset by hand. Only stage-4 candidates become benchmark items.
