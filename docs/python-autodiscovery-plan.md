# Python Autodiscovery Markdown Plan

Release status: implemented in `v0.11.0` as local Markdown memory helpers. This
plan prepares the workflow, but it does not start the real discovery/search
batch.

## Goal

Build a model-driven loop for finding real Python silent-drift cases without
turning the process into a brittle state machine.

The target workflow is:

1. The model reads the existing Markdown idea bank before searching.
2. The model searches for new Python drift ideas.
3. The model appends each useful idea, failed attempt, and accepted case back to
   Markdown.
4. The next model run reads the Markdown and deliberately looks elsewhere.

The intended scale is 200 discovery attempts. A discovery attempt does not have
to become a benchmark case. It only has to leave useful evidence, a clear reason
if it failed, and enough context for the next model to avoid repeating it.

## Non-Goal

Do not build a state machine as the primary judge of quality.

Mechanical statuses are too shallow for this task because most real-case failure
is semantic: release-note ambiguity, API surface overlap, version availability,
packaging quirks, external-service dependence, or behavior that is real but not
suitable for a benchmark.

Markdown is the source of memory. The model is expected to read, compare, and
decide.

## Core Artifacts

### `docs/python-drift-idea-bank.md`

One append-only Markdown file for all searched ideas.

It should contain:

- promising ideas
- rejected ideas
- duplicate warnings
- package-specific notes
- successful accepted cases
- search terms that were already exhausted

This file is the main anti-duplication tool. The model starts every batch by
reading it.

### `docs/python-drift-run-log.md`

One append-only Markdown file for batch-level notes.

It should contain:

- run date
- model/operator
- search budget
- packages searched
- ideas added
- ideas rejected
- cases promoted to reproduction
- cases accepted into benchmark
- unresolved questions

This is not a database. It is a human-readable operating log.

### Case Artifacts

Only ideas that survive manual/model review should move into the existing
case pipeline:

- `cases/<case_id>/`
- `data/reproductions/<case_id>/`
- `data/oracle/<case_id>/`
- `data/packages/<case_id>/`
- `data/audit/<case_id>.json`

The Markdown files remember all the things that did not make it that far.

## Idea Card Format

Each discovered idea should be appended as a card.

```markdown
## IDEA-YYYYMMDD-NNN: short package/API summary

- Package: `package-name`
- API surface: `module.function`, `Class.method`, or behavior area
- Candidate versions: old `x.y.z`, new `a.b.c`
- Source:
  - URL:
  - Release/changelog section:
  - Quote or paraphrase:
- Behavior hypothesis:
  Same client code may produce different output because ...
- Why this may be silent drift:
  Existing code can keep running without an exception, but semantics change.
- Reproduction sketch:
  Minimal imports, inputs, and expected observable output difference.
- Duplicate check:
  Similar to:
  Different because:
- Risk notes:
  Version install risk, external dependency risk, platform risk, nondeterminism.
- Next action:
  Search deeper / try reproduction / reject / merge with prior idea.
```

The important part is the duplicate check. The model should compare the new idea
against previous cards by package, API surface, version range, drift category,
and evidence source.

## Rejected Idea Format

Rejected ideas stay in the idea bank. They are valuable because they prevent
future runs from wasting time.

```markdown
## REJECTED-YYYYMMDD-NNN: short summary

- Package:
- API surface:
- Source:
- Tried because:
- Rejected because:
  - not silent drift
  - evidence too vague
  - duplicate of prior idea
  - old version unavailable
  - install conflict
  - needs network/service/database/GPU/browser
  - behavior depends on current time, locale, OS, randomness, or external data
  - no behavior difference after reproduction attempt
  - oracle would leak the answer
- What future runs should avoid:
- What future runs may still try:
```

This replaces low-quality status transitions. The rejection text should teach the
next model where not to go.

## Accepted Case Note Format

When an idea becomes a real benchmark case, add a short note back to the idea
bank.

```markdown
## ACCEPTED-YYYYMMDD-NNN: case_id

- Case id:
- Package:
- API surface:
- Versions:
- Source:
- Reproduction path:
- Oracle path:
- Package path:
- Audit path:
- Why it is non-duplicate:
- Follow-up ideas nearby:
```

Accepted cases are also duplicate anchors. Future discovery should avoid
nearby variants unless the behavior is genuinely different.

## Model Loop For One Batch

For each batch, the model should do this:

1. Read `docs/python-drift-idea-bank.md` if it exists.
2. Read `docs/python-drift-run-log.md` if it exists.
3. Pick packages or APIs that are underrepresented in the idea bank.
4. Search release notes, changelogs, migration guides, and issue discussions.
5. For every useful lead, append an idea card.
6. For every dead end, append a rejected card when the failure teaches something.
7. Promote only the strongest ideas into reproduction work.
8. Add a batch summary to the run log.

The model should not try to fill a quota with weak cases. A run with 200 attempts
and 180 useful rejections is still progress.

## Duplicate Avoidance By Reading

Before searching, the model should extract an informal avoid list from the idea
bank:

- packages already saturated
- APIs already tried
- version ranges already tested
- release-note phrases already exhausted
- failure patterns already observed
- accepted cases that should not be cloned

The model may still revisit a package if it chooses a different API surface or a
different drift category. It should explicitly say why the new idea is not a
duplicate.

## Search Direction Seeds

Prefer packages with rich changelogs and deterministic local behavior:

- `pandas`
- `numpy`
- `pydantic`
- `sqlalchemy`
- `scikit-learn`
- `pytest`
- `click`
- `httpx`
- `requests`
- `attrs`
- `python-dateutil`
- `Pillow`
- `matplotlib`
- `fastapi`
- `typer`

Good drift categories:

- default value changes
- dtype or coercion changes
- parsing changes
- timezone or locale semantics
- ordering or sorting changes
- null/empty handling
- warning-to-error or error-to-warning changes
- validation strictness changes
- alias or field resolution changes
- path, URL, or encoding behavior changes

Avoid early:

- cloud APIs
- services requiring credentials
- database server setup
- GPU/runtime-heavy packages
- browser-only behavior
- cases that require live network calls
- cases where the only difference is a hard import failure

## Promotion Criteria

An idea is worth trying as a real case when:

- the source evidence is public and specific
- old and new versions are likely installable
- the behavior can be observed with a short local Python client
- the output difference is deterministic
- the case does not need hidden external state
- it is not just a breaking import or removed symbol
- it is not a near-duplicate of an accepted or rejected card

The promotion decision should be written in prose, not inferred from a status
field.

## 200 Attempt Expectation

The expected output of 200 attempts is not 200 benchmark cases.

A realistic run may produce:

- 200 idea or rejection cards
- 40 to 80 reproduction-worthy ideas
- 10 to 30 stable accepted benchmark cases
- a much better map of which package areas are exhausted

The Markdown memory is the main product of the failed attempts. It makes the next
200 attempts smarter.

## Local CLI Support

The `v0.11.0` local implementation is intentionally small. It only helps the model
write and reread Markdown memory.

Initialize the default files:

```bash
silent-drift-miner autodiscovery init
```

Append cards:

```bash
silent-drift-miner autodiscovery idea ...
silent-drift-miner autodiscovery reject ...
silent-drift-miner autodiscovery accept ...
silent-drift-miner autodiscovery log ...
```

Before a new search batch, ask for a model-readable avoid summary:

```bash
silent-drift-miner autodiscovery avoid-list
```

Check whether the Markdown memory is ready:

```bash
silent-drift-miner autodiscovery readiness
```

Generate the brief for the next model run without starting discovery:

```bash
silent-drift-miner autodiscovery brief --attempts 10 --out docs/python-drift-next-run.md
```

These commands are helpers for writing Markdown. They are not judges, workflow
states, or quality gates.

Run a small manual/model-guided pilot of 10 attempts before adding any heavier
automation. Only automate once the cards are useful.
