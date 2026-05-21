# Migration Plan

Canonical reference: `final-plan.md`.

## Guardrails

- This branch contains only the restructure proposal.
- Do not create `docs/case-bank/` until the schema is approved.
- Do not migrate cases until `index build` and `pack` exist.
- Do not modify legacy idea-bank Markdown files during planning.
- Use `origin/main` at `643b608` as the full snapshot source.
- Verified reproduction evidence lives under `data/verification/<case>/`;
  `metadata.provenance.reproduction_result` points there and is the reduce
  source for `hidden/expected.json`.
- Reconcile with existing assets before migrating: fold or retire the top-level
  `cases/` directory, and reuse `silent_drift_miner/bench.py` and
  `silent_drift_miner/oracle.py` rather than duplicating packaging/oracle logic.

## Phase 1: Lock Schema

- finalize `metadata.json` field names and types
- write JSON Schema validation
- allow additive fields later, but no renames or removals after lock

## Phase 2: Implement Generators And Packaging

Required commands:

```bash
python -m case_bank index build --out docs/case-bank/indexes/
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

Requirements:

- `index build` handles an empty `cases/` directory
- `pack` copies cases and strips `hidden/`
- package validation proves there are no `hidden/`, `oracle.md`, or
  `expected.json` files in the eval package
- every packaged case still contains `client/`

## Phase 3: Migrate Verified Cases

Migrate only `verified_keep` cases first. Confirm `primary_scenario` before
creating the folder.

| Case ID | Slug | Suggested `primary_scenario` |
|---|---|---|
| PY-SD-010 | `py-attrs-nan-equality` | `runtime-semantics` |
| JS-06 | `js-zod-optional-defaults` | `validation-and-policy` |
| JS-09 | `js-dotenv-hash-comments` | `parsing-and-ingestion` |
| GO-002 | `go-timer-channel-capacity` | `state-and-lifecycle` |
| RB-RACK-005 | `ruby-rack-semicolon-query` | `parsing-and-ingestion` |
| PHP-07 | `php-carbon-timestamp-timezone` | `time-and-localization` |
| JVM-JAVA-07 | `jvm-commons-csv-enum-header` | `parsing-and-ingestion` |
| DOTNET-08 | `dotnet-08-fluentvalidation-email` | `validation-and-policy` |

Completion criteria for each migrated case:

- `case.md`
- `evidence.md`
- `env.md`
- `metadata.json`
- `client/` with minimal probe
- `hidden/oracle.md`
- `hidden/expected.json`

## Phase 4: Maintain Indexes

- run `index build` after every case addition or metadata update
- add the check to pre-commit or CI

## Phase 5: Decide Legacy Idea-Bank Fate

After the first five migrated cases look right, decide whether to keep legacy
Markdown as snapshots, redirect them, or move them under `docs/legacy/`.
