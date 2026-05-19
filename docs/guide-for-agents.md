# Agent Guide: Finding Silent Behavioral Drift Cases for SilentDrift

> This guide is for autonomous agents (LLMs, code-search agents, etc.) tasked with discovering
> and submitting Silent Behavioral Drift candidates to the beachmark4silentdrift pipeline.
> Read the entire guide before acting. Precision matters more than volume.

Before expanding the pipeline, read `docs/python-pipeline-boundaries.md`. Agents must not build
cloud-service harnesses, current-bug tracks, GPU/CUDA paths, legacy policy exceptions, or complex
statistical/performance oracles unless the user explicitly commands that expansion.

---

## 1. Exact Definition

A **Silent Behavioral Drift** case satisfies ALL of the following:

1. **Call-shape stability**: The public API surface (function signature, parameter names, import path) is **unchanged** between version `V_old` and version `V_new`.
2. **Observable output change**: Running the same client code against `V_old` vs `V_new` produces **different stdout, stderr, or return values** in at least one deterministic scenario.
3. **No exception on the happy path**: The call completes without raising an exception in both versions (on the canonical usage that triggers the drift).
4. **Silent delivery**: The change was **not prominently announced** as a breaking change in the primary changelog or migration guide entry for that version. A buried footnote counts as silent; a top-level "BREAKING" header does not.
5. **Reproducibility**: The difference is **deterministic** — same inputs, same output, no dependence on wall-clock time, random seeds, or external network state.

Formally:

```
∀ (call_site C, input I):
  API_shape(V_old, C) == API_shape(V_new, C)   ← same call, no rewrite needed
  ∧ output(V_old, C, I) ≠ output(V_new, C, I)  ← different result
  ∧ ¬raises_exception(V_new, C, I)              ← silent
  ∧ is_deterministic(C, I)                      ← reproducible
```

---

## 2. Accept / Reject Decision Tree

```
CANDIDATE SIGNAL FOUND
        │
        ▼
Is the API call shape identical in both versions?
(same import path, same function name, same required params)
  NO  → REJECT  (reason: hard_break or api_change)
  YES ↓

Does calling it in the canonical way raise an exception in V_new?
  YES → REJECT  (reason: reject_hard_break)
  NO  ↓

Is the output / behavior / side-effect observably different?
  NO  → REJECT  (reason: no_behavior_diff)
  YES ↓

Is the difference deterministic given fixed inputs?
  NO  → REJECT  (reason: flaky_output)
  YES ↓

Is this change already prominently labeled "BREAKING" at the top of
the official migration guide or changelog entry?
  YES → REJECT  (reason: reject_not_silent) [still worth noting as borderline if buried]
  NO  ↓

Can you identify a specific version pair (V_old, V_new)?
  NO  → DEFER   (decision: needs_more_context) — submit with what you have
  YES ↓

ACCEPT → decision: accept_for_reproduction
```

---

## 3. Drift Categories (use the closest match)

| Category | Canonical Pattern | Example |
|----------|-------------------|---------|
| `default_shift` | A parameter's default value changes | `sort=True` → `sort=False` in groupby |
| `timezone_shift` | Timezone-naive becomes aware, or UTC vs local | `datetime.utcnow()` → UTC-aware datetime |
| `unit_shift` | Numeric result changes unit silently | ms → s, cents → dollars |
| `pagination_semantics` | Page numbering, cursor, or limit default changes | page 0-indexed → 1-indexed |
| `ordering_change` | Sort order or iteration order changes | insertion order vs sort order |
| `null_empty` | None vs [] vs missing distinction changes | empty list returned instead of None |
| `field_meaning` | A return field changes what it counts/represents | "count" now excludes nulls |
| `locale_encoding` | Default charset or locale changes | latin-1 → utf-8 |
| `auth_scope` | Default permission or scope changes silently | read-only becomes read-write |
| `rate_limit_scope` | Default rate limit bucket changes | per-IP → per-token |
| `uncategorized` | Real drift, but category unclear | use this if unsure |

---

## 4. Source Search Strategy

### Priority 1 — Official Migration Guides

These are the highest-yield sources. Search for pages titled:
- `<library> migration guide`
- `<library> what's new in version X`
- `<library> upgrading`

Target phrases in the document body:

```
"default" AND ("changed" OR "now" OR "instead of" OR "previously")
"now defaults to"
"default value.*changed"
"behavior.*changed"
"previously.*now"
```

Reject entries that contain any of these in the same sentence:
```
"removed"  "deleted"  "no longer supported"
"now raises"  "now throws"  "exception"
"must now"  "required"  "mandatory"
```

### Priority 2 — CHANGELOG Files

Look for the library's `CHANGELOG.md`, `CHANGELOG.rst`, or GitHub Releases page.
Focus on **major version bumps** (1.x → 2.x, 2.x → 3.x).
Minor versions can contain drift but at lower density.

GitHub URL patterns to fetch:
```
https://raw.githubusercontent.com/{owner}/{repo}/main/CHANGELOG.md
https://raw.githubusercontent.com/{owner}/{repo}/main/CHANGES.rst
https://api.github.com/repos/{owner}/{repo}/releases
```

### Priority 3 — GitHub Issues and PRs

Search pattern:
```
repo:{owner}/{repo} label:"breaking change" OR label:"behavior change"
"behavior changed" after upgrade
"unexpected result" after {version}
```

Filter for issues where:
- The reporter says "my code didn't change"
- The title or body contains version numbers
- The issue is closed and labeled as "by design" or "working as intended" (confirms it was intentional)

### Priority 4 — Stack Overflow

Query patterns:
```
site:stackoverflow.com "{library}" "behavior changed" after:2020
site:stackoverflow.com "{library}" "unexpected" "upgrade" after:2020
```

Look for answers that say "this changed in version X" with an accepted answer explaining the default change.

### Target Libraries (ordered by expected case density)

```
pandas          pydantic        requests
sqlalchemy      fastapi         httpx
numpy           starlette       urllib3
flask           django          celery
boto3           aiohttp         click
```

---

## 5. Submitting a Candidate via CLI

### Option A — Mine from a local fixture file (preferred for known excerpts)

```bash
# Save the relevant changelog excerpt to a local file
cat > /tmp/my_excerpt.md << 'EOF'
## Version 2.0.0

- The default value of `observed` in `DataFrame.groupby()` has changed.
  Previously, unobserved categories were included by default. Now only
  observed categories are returned unless `observed=False` is passed.
EOF

# Mine without LLM (fast, rule-based only)
silent-drift mine \
  --library pandas \
  --ecosystem python \
  --source /tmp/my_excerpt.md \
  --source-url https://pandas.pydata.org/docs/whatsnew/v2.0.0.html \
  --no-llm \
  --out data/candidates/pandas.jsonl

# Mine with offline precision filter (upgrades confidence without API call)
silent-drift mine \
  --library pandas \
  --source /tmp/my_excerpt.md \
  --source-url https://... \
  --llm-filter \
  --out data/candidates/pandas.jsonl

# Validate output
silent-drift validate-candidates data/candidates/pandas.jsonl
```

### Option B — Mine from GitHub directly (requires network)

```bash
# Mine all enabled Python targets from config
silent-drift mine --ecosystem python

# Mine one specific library
silent-drift mine --library pandas
```

### Option C — Build triage queue and mark a candidate

```bash
# Build a triage queue from an existing candidates file
silent-drift triage build \
  --candidates data/candidates/pandas.jsonl \
  --out data/triage/pandas_queue.jsonl

# Inspect next undecided candidate
silent-drift triage next --queue data/triage/pandas_queue.jsonl

# Accept a candidate for reproduction
silent-drift triage mark \
  --queue data/triage/pandas_queue.jsonl \
  --candidate-id <id_from_above> \
  --decision accept_for_reproduction \
  --notes "pandas 1.5.3→2.0.0: groupby observed default change confirmed in whatsnew"

# Other valid decisions
# --decision reject_hard_break          ← API removed or throws
# --decision reject_additive_feature    ← new behavior is additive, old still works unchanged
# --decision reject_bugfix_only         ← a fix that doesn't affect any valid prior usage
# --decision reject_not_silent          ← prominently documented breaking change
# --decision borderline                 ← real drift but borderline silent; flag for human review
# --decision needs_more_context         ← version pair unclear or behavior uncertain
```

---

## 6. Output Quality Requirements

A submitted candidate must include:

| Field | Requirement |
|-------|-------------|
| `library` | Exact PyPI package name (lowercase, hyphens) |
| `ecosystem` | `"python"` for now |
| `version_new` | Exact version string where drift appears (e.g. `"2.0.0"`) |
| `version_old` | Exact version string before the drift, or `null` if unknown |
| `category` | One of the 11 categories above — do NOT invent new ones |
| `confidence` | `"weak"` (rule only), `"uncertain_silence"` (offline filter), `"high"` (LLM confirmed) |
| `title` | ≤ 120 chars. Format: `"<API>: <old behavior> → <new behavior>"` |
| `summary_paraphrased` | 2–3 sentences. State: (1) what the old behavior was, (2) what changed, (3) how a caller is affected without modifying their code |
| `api_surface` | List of affected symbols: `["DataFrame.groupby"]` |
| `evidence[0].url` | Stable URL to the changelog/migration guide entry |
| `evidence[0].snippet_raw` | Verbatim excerpt from source, ≤ 400 chars |

**DO NOT include in any field:**
- Expected old/new outputs (oracle leakage)
- Hidden test logic or repair hints
- Reproduction results or diffs

---

## 7. Confidence Assignment Rules

Assign confidence based on the extraction method, not your subjective certainty:

```
extracted_by = "rule"    → confidence = "weak"
extracted_by = "llm_filter" (offline) → confidence = "uncertain_silence"
extracted_by = "llm"     → confidence as returned by the LLM ("high" or "uncertain_silence")
extracted_by = "human"   → confidence = "high" if directly observed, else "uncertain_silence"
```

Do not manually assign `"high"` confidence to rule-extracted candidates. Confidence
is a pipeline tracking field, not a claim about your certainty.

---

## 8. Common False Positives to Reject

### FP1 — Exception path only

> "If you pass `foo=None`, it now raises ValueError instead of returning 0"

Reject unless the canonical call path (no explicit `foo=None`) also changes behavior.
The drift must occur on the **default / common invocation**, not just an edge case.

### FP2 — Deprecation-only change

> "`applymap` is deprecated; use `map` instead"

Reject as `reject_not_silent` if the old function still works identically.
Accept only if the old function's **output changed** (not just its name).

### FP3 — Documentation says "BREAKING" explicitly

If the changelog entry is prefixed with `[BREAKING]`, `BREAKING CHANGE:`, or similar, this is
`reject_not_silent`. A change buried on page 4 of the migration guide after 10 other items
is still worth submitting as `borderline`.

### FP4 — Environment-dependent behavior

> "On Windows, the default encoding is now UTF-8"

This is valid if the behavior change is observable on a controlled platform.
Set `reproduce_hypothesis` to specify the platform in the reproduction spec.

### FP5 — Behavior change requires opt-in to new API

> "The new `strict=True` parameter now validates inputs; old calls without `strict` are unchanged"

If callers who use the old call shape get the exact same result, this is `reject_additive_feature`.

### FP6 — Internal/private API

Signals: leading underscore, `._internal`, `.private`, `__dunder__` (unless `__init__` behavior).
These are not public API surface. Reject.

---

## 9. Batch Search Protocol

When assigned a library to audit, follow this sequence:

```
1. Fetch the last 10 major/minor releases from GitHub Releases API
2. For each release body:
   a. Split into bullet-point chunks
   b. Score each chunk with rule prescreen (use --no-llm first)
   c. Flag chunks scoring ≥ 4 as candidates
3. For the top-scoring chunks, apply --llm-filter (offline) to upgrade confidence
4. Deduplicate by (library, version_new, first_url)
5. Write to data/candidates/<library>.jsonl
6. Run validate-candidates on the output
7. Build triage queue
8. Mark any candidate you can confirm with high confidence as accept_for_reproduction
9. Mark anything uncertain as needs_more_context with a note explaining why
10. Do NOT mark candidates you cannot evaluate as reject_*
```

---

## 10. Full Pipeline Reference (after triage)

For accepted candidates, the pipeline continues:

```bash
# Write a minimal Python client that triggers the drift
# client.py: import library; call the drifted API; print the result

# Plan and run reproduction
silent-drift reproduce plan \
  --candidate-id <id> \
  --library pandas \
  --old-version 1.5.3 --new-version 2.0.0 \
  --client-file client.py \
  --out data/reproductions/<id>/spec.json

silent-drift reproduce run \
  --spec data/reproductions/<id>/spec.json \
  --out data/reproductions/<id>/

# If keep=true, curate the case
silent-drift curate create \
  --reproduction-result data/reproductions/<id>/attempt_001/result.json \
  --decision accept --case-id <case_id> \
  --out data/curated/<case_id>.yaml

# Generate oracle scaffold (human fills in expected.json afterwards)
silent-drift oracle generate \
  --case data/curated/<case_id>.yaml \
  --template pytest \
  --out data/oracle/<case_id>/

# Package and audit
silent-drift bench package \
  --case data/curated/<case_id>.yaml \
  --oracle data/oracle/<case_id>/oracle_spec.yaml \
  --out data/packages/

silent-drift audit case \
  --package data/packages/<case_id>/ \
  --out data/audit/<case_id>.json
```

A case is **benchmark_ready** when:
- `result.json` has `keep: true`
- `curate create` succeeded with `decision: accept`
- `audit case` returns `"pass": true`
- A human has filled in `hidden/expected.json` with real expected behavior
- `oracle validate --mode old` fails (old behavior fails the oracle)
- `oracle validate --mode new` passes (new behavior passes the oracle)

---

## Summary Cheat Sheet

```
ACCEPT when:
  + same call shape, different output
  + no exception on common path
  + deterministic
  + not prominently announced as breaking

REJECT when:
  - function/method deleted or signature changed     → reject_hard_break
  - raises exception on canonical call               → reject_hard_break
  - only DeprecationWarning, old behavior intact     → reject_additive_feature
  - explicitly labeled BREAKING in main changelog    → reject_not_silent
  - output identical between versions                → no_behavior_diff (drop at reproduce stage)
  - non-deterministic / time/random dependent        → reject (flaky_output)

FLAG for human when:
  ? buried in migration guide, not top-level        → borderline
  ? version pair unclear                             → needs_more_context
  ? behavior change only on edge-case inputs         → needs_more_context
```
