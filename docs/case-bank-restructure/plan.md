# Restructure Plan

## Guardrails

- Keep existing idea-bank Markdown files untouched until the new structure is
  approved.
- Do not run new reproductions during the restructure.
- Treat the already pushed branch `codex/safety-pre-bank-restructure` as the
  rollback point.
- Build the new structure under a separate root, then migrate cases one by one.

## Phase 1: Approve Shape

Deliverables:

- proposed root: `docs/case-bank/`
- primary path: `cases/<primary-scenario>/<case-id-slug>/`
- required case files
- tag taxonomy
- metadata contract

Approval gate:

- user confirms the path shape and tag taxonomy.

## Phase 2: Create Empty Skeleton

Deliverables:

- `docs/case-bank/README.md`
- `docs/case-bank/indexes/`
- `docs/case-bank/cases/`
- one empty template case folder under `_template/`

No existing case migration in this phase.

## Phase 3: Migrate Verified Cases First

Initial migration set:

- `py-sd-010-attrs-nan-equality`
- `js-06-zod-optional-defaults`
- `js-09-dotenv-hash-comments`
- `go-002-timer-channel-capacity`
- `rb-rack-005-semicolon-query`
- `php-07-carbon-timestamp-timezone`
- `jvm-java-07-commons-csv-enum-header`
- `dotnet-08-fluentvalidation-email`

Each migrated case must include:

- complete `metadata.json`
- evidence URLs
- reproduction result path
- oracle
- primary scenario and secondary scenario tags

## Phase 4: Generate Or Maintain Index Views

Indexes should be views over `metadata.json`, not duplicate canonical content:

- by scenario
- by language/ecosystem
- by drift pattern
- by API surface
- by status

Manual indexes are acceptable first. A generator can come later.

## Phase 5: Decide Legacy Markdown Fate

Options:

- keep current idea banks as legacy snapshots
- replace them with links into `docs/case-bank/`
- move them under `docs/legacy/`

This decision should wait until the first migrated cases look right.
