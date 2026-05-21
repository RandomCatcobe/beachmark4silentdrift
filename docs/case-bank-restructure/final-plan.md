# Case Bank Structure Plan (Final)

## Core Principles

- Case folders are self-contained: a case can be copied and used independently
  without relying on sibling case folders.
- Probe source code is committed, but dependency products are not committed.
- Oracle material is physically isolated under `hidden/`, so evaluation
  packaging can strip one stable directory without parsing file contents.
- Raw local logs do not enter the case bank. Reproduction results are reduced
  to structured assertions before they are committed.
- This plan is plan-only. It does not migrate existing cases or implement the
  CLI commands.

## Directory Structure

```text
docs/case-bank/
  README.md
  indexes/
    by-scenario.md
    by-language.md
    by-drift-pattern.md
    by-api-surface.md
    by-status.md
  cases/
    <primary-scenario>/
      <case-id-slug>/
        case.md
        evidence.md
        env.md
        metadata.json
        client/
          .gitignore
          probe.{ext}
          [build-def-file]
        hidden/
          oracle.md
          expected.json
```

The stable ownership unit is:

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

The folder path is stable once created. Confirm `primary_scenario` before
creating the case folder.

## Client Directory By Ecosystem

`client/` contains only the source and build definition files needed to run the
probe. It must not contain dependency products, package caches, generated build
outputs, or local virtual environments.

```text
# Python / Ruby / PHP
client/
  .gitignore
  probe.py          # probe.rb / probe.php

# JavaScript / TypeScript
client/
  .gitignore
  probe.js
  package.json      # declares how old/new package versions are selected

# Go
client/
  .gitignore
  probe.go
  go.mod            # committed
  go.sum            # committed when generated

# JVM (Java)
client/
  .gitignore
  probe/
    src/main/java/probe/Probe.java
  pom.xml           # or build.gradle

# .NET
client/
  .gitignore
  Program.cs
  probe.csproj
```

Recommended `client/.gitignore` template:

```gitignore
__pycache__/
*.pyc
node_modules/
vendor/
.venv/
target/
bin/
obj/
*.class
*.jar
.gradle/
```

## File Contracts

### `case.md` (public)

Contains:

- API or behavior under test
- version boundary (`old` -> `new`)
- old behavior in prose
- new behavior in prose
- why the drift is silent
- realistic impact scenario

Must not contain:

- expected outputs
- stdout samples
- checker conditions

### `evidence.md` (public)

Contains:

- official changelog, migration guide, issue, announcement, or documentation
  URLs
- short source notes

Must not contain:

- local reproduction logs
- stdout/stderr dumps

### `env.md` (public)

Contains:

- language/runtime/platform version requirements
- package name, old version, and new version
- install or version-switching method, such as `pip install library==X.Y`,
  `nvm use`, or `sdk use java`
- adapter/API-surface type, such as `library-api`, `runtime-api`, or
  `framework-api`
- known environment caveats, such as OS, architecture, timezone, or old runtime
  requirements
- probe invocation shape, such as "accepts one string argument and emits JSON to
  stdout"
- exact reproduction command shape (no literal expected outputs or stdout dumps)

Must not contain:

- expected outputs
- oracle conditions

### `metadata.json` (public)

Machine-readable registry entry used for index generation, status filtering, and
evaluation packaging. It references oracle material by `case_id` only. A legacy
`data/` path must never be used as canonical case content, but a single read-only
`provenance` pointer to the reproduction artifact the case was reduced from is
allowed and recommended.

Example:

```json
{
  "case_id": "DOTNET-08",
  "slug": "dotnet-08-fluentvalidation-email",
  "title": "FluentValidation default EmailAddress behavior changed",
  "status": "verified_keep",
  "primary_scenario": "validation-and-policy",
  "application_scenarios": ["validation-and-policy", "identity-and-contact-data"],
  "ecosystems": ["dotnet"],
  "languages": ["csharp"],
  "api_surfaces": ["library-api", "validator"],
  "drift_patterns": ["default-changed", "validation-relaxed"],
  "failure_modes": ["silent-acceptance-change"],
  "determinism": "local-deterministic",
  "external_dependencies": "package-cache",
  "old_version": "8.6.2",
  "new_version": "9.0.0",
  "source_urls": [
    "https://docs.fluentvalidation.net/en/latest/upgrading-to-9.html"
  ],
  "provenance": {
    "reproduction_result": "data/verification/dotnet_fluentvalidation_email/attempt_003/result.json",
    "verified_at": "2026-05-21"
  }
}
```

Field names and meanings are locked once the JSON Schema is finalized. Fields
may be added later, but locked fields must not be renamed or removed.

### `hidden/oracle.md` (stripped before evaluation)

Contains:

- keep condition
- reject condition
- hard-break condition
- allowed noise
- specific fields or stdout fragments used for judgment

`oracle.md` is the prose judgment spec. `hidden/expected.json` is the machine
assertion form. They must stay consistent, and `expected.json` is authoritative
for automated checker execution.

### `hidden/expected.json` (stripped before evaluation)

Uses one shared outer schema so the checker does not need case-specific parsers:

```json
{
  "schema_version": 1,
  "case_id": "DOTNET-08",
  "assertions": [
    {
      "name": "borderline email acceptance changed",
      "field": "results.a@b",
      "old": false,
      "new": true
    }
  ]
}
```

`field` uses a simple dotted key path. `results.a@b` means the top-level
`results` object has a key literally named `a@b`. Do not use JSONPath. Do not
support array indexes in the first schema version; if array checks are needed,
split them into named assertions.

`schema_version` 1 is provisional. When a flat dotted-key assertion cannot
express the drift (for example nested array shapes), the case may instead ship an
executable `hidden/test_behavior.py` as the authoritative checker, reusing the
existing `silent_drift_miner/oracle.py` machinery. `expected.json` and any
executable checker must stay consistent.

## Submission Flow After Reproduction

Commit into the case folder:

| File | Contents |
|---|---|
| `client/probe.*` | minimal source code that triggers the drift |
| `hidden/expected.json` | structured assertions reduced from reproduction output |
| `hidden/oracle.md` | judgment logic |
| `metadata.json` | status updated to `verified_keep` |

Do not commit into the case folder:

| Content | Destination |
|---|---|
| raw stdout/stderr logs | local only, or `data/reproductions/<case>/` as runtime artifacts |
| runtime environments such as `.venv`, `node_modules`, `vendor`, `bin`, `obj` | local temporary directories ignored by `.gitignore` |

`expected.json` is a lossy reduction of raw logs. Noise, timestamps, irrelevant
lines, and environment chatter are discarded. `oracle.md` must document allowed
noise because the committed assertion file only retains judgment-relevant data.
Reduce `expected.json` from the artifact named in
`metadata.provenance.reproduction_result`.

## Evaluation Packaging

Command shape:

```bash
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

Packaging rules:

- copy every case folder
- remove `hidden/` from every copied case folder
- keep `case.md`, `evidence.md`, `env.md`, `metadata.json`, and `client/`

Required package validation:

```text
assert eval_package/ contains no path segment named hidden
assert eval_package/ contains no oracle.md
assert eval_package/ contains no expected.json
assert every packaged case folder contains client/
```

## Status Values

| Value | Meaning |
|---|---|
| `idea_only` | located but not locally reproduced |
| `verified_keep` | locally reproduced; old/new both exit 0; meaningful silent drift confirmed |
| `rejected_no_diff` | locally checked and no behavioral diff observed |
| `blocked_runtime` | unavailable old/new runtime pair is required |
| `blocked_dependency` | package or service dependency is unavailable |
| `needs_source` | plausible, but source evidence is insufficient |

## Index Generation

Indexes are generated views over case `metadata.json` files. They must not be
hand-maintained after the generator exists.

```bash
python -m case_bank index build --out docs/case-bank/indexes/
```

The `case_bank index build` command must exist before case migration starts. It
must run without error when `docs/case-bank/cases/` is empty.

After any case addition or metadata change, regenerate indexes. Add this as a
pre-commit hook or CI check once the first migrated cases exist.

## Tag Taxonomy

### Primary Scenario

Use one as the folder path segment for each case:

- `validation-and-policy`
- `parsing-and-ingestion`
- `serialization-and-binding`
- `time-and-localization`
- `state-and-lifecycle`
- `routing-and-identity`
- `commerce-order-flow`
- `inventory-and-fulfillment`
- `observability-and-logging`
- `runtime-semantics`

### Drift Pattern

- `default-changed`
- `field-semantics-changed`
- `field-removed-or-masked`
- `type-or-shape-changed`
- `parser-rule-changed`
- `ordering-changed`
- `bundled-data-changed`
- `runtime-locale-changed`
- `validation-relaxed`
- `validation-strictness-increased`
- `success-but-no-effect`
- `out-of-order-event`
- `old-state-overwrite`

`default-policy-changed` is intentionally merged into `default-changed`. Use
`validation-relaxed` or `validation-strictness-increased` when a validator
policy shift needs direction.

### Failure Mode

- `silent-value-change`
- `silent-acceptance-change`
- `silent-rejection-change`
- `wrong-entity`
- `wrong-route`
- `stale-state`
- `missing-field`
- `wrong-type`
- `wrong-order`
- `wrong-timezone`
- `wrong-locale`
- `wrong-inventory`
- `wrong-fulfillment`
- `wrong-refund-or-payment-state`

### Determinism / Benchmark Construction

- `local-deterministic`
- `package-cache`
- `runtime-pair`
- `service-contract`
- `mockable-service`
- `requires-live-credential`

## Current State To Target Mapping

This plan is designed on top of assets that already exist. Resolve the following
explicitly before any migration runs, so the result is not a second parallel
case bank:

- Existing root `cases/`: the top-level `cases/` directory already holds per-case
  `client/`, `candidate.json`, and `README.md`. Decide whether it is folded into
  `docs/case-bank/cases/` or retired.
- Existing oracle products `data/oracle/<case>/`: these already implement
  `hidden/expected.json`, `hidden/test_behavior.py`, `oracle_spec.yaml`, and
  `public/`. The new layout reuses this split rather than reinventing it.
- Tooling: `case_bank index build` and `pack` must reuse or extend the existing
  `silent_drift_miner/bench.py` (packaging) and `silent_drift_miner/oracle.py`
  (oracle generation) instead of duplicating them. State the reuse-vs-replace
  decision before Phase 2.
- Provenance: verified reproduction evidence lives under
  `data/verification/<case>/`; `metadata.provenance.reproduction_result` points
  there.

## Migration Phases

### Phase 1: Lock Schema

Finalize `metadata.json` field names and types. Write a JSON Schema file for
validation. After this point, fields may be added, but existing fields must not
be renamed or removed.

### Phase 2: Implement Generators And Packaging

Implement:

```bash
python -m case_bank index build --out docs/case-bank/indexes/
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

Requirements:

- `index build` succeeds on an empty `cases/` directory
- `pack` strips `hidden/`
- package validation assertions pass

### Phase 3: Migrate Verified Cases

Only migrate `verified_keep` cases first. Confirm `primary_scenario` before
creating the folder.

Suggested initial mapping (canonical IDs/slugs from
`docs/language-drift-verification-log.md`):

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

A case is migrated only when all required files exist:

- `case.md`
- `evidence.md`
- `env.md`
- `metadata.json`
- `client/` with minimal probe source
- `hidden/oracle.md`
- `hidden/expected.json`

### Phase 4: Maintain Indexes

Run `index build` after every case addition or metadata update. Add this check
to CI or pre-commit.

### Phase 5: Decide Legacy Idea-Bank Fate

After the first five migrated cases look right, decide whether to:

- keep old idea-bank Markdown files as legacy snapshots
- redirect them to `docs/case-bank/`
- move them to `docs/legacy/`

Do not make this decision earlier.

## Key Differences From The Previous Proposal

| Previous proposal | Final proposal |
|---|---|
| `oracle.md` flat in case folder | `oracle.md` under `hidden/` |
| `reproduction.md` with stdout summary | removed; stdout assertions live in `hidden/expected.json` |
| no `env.md` | `env.md` owns dependency and environment instructions |
| `metadata.json` included `data/` file paths | `metadata.json` carries no legacy `data/` path as canonical content; one advisory `provenance` pointer allowed |
| no probe source | `client/` contains minimal probe source |
| manual indexes allowed | generator CLI required before migration |
| both `default-changed` and `default-policy-changed` existed | only `default-changed`; validator direction uses validation tags |
| Phase 3 had no scenario mapping | Phase 3 has explicit mapping, confirmed before folder creation |
