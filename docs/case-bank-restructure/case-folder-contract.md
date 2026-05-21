# Case Folder Contract

Each individual case lives in one folder:

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

The folder name should be stable, lowercase, and specific:

```text
validation-and-policy/dotnet-08-fluentvalidation-email/
time-and-localization/php-07-carbon-timestamp-timezone/
parsing-and-ingestion/jvm-java-07-commons-csv-enum-header/
```

## Required Files

### `metadata.json`

Machine-readable registry entry. This is the source of truth for search,
filtering, index generation, and benchmark packaging.

Required fields:

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
  "drift_patterns": ["default-policy-changed", "validation-relaxed"],
  "failure_modes": ["silent-acceptance-change"],
  "determinism": "local-deterministic",
  "external_dependencies": "package-cache",
  "old_version": "8.6.2",
  "new_version": "9.0.0",
  "source_urls": [],
  "reproduction_result": "data/verification/dotnet_fluentvalidation_email/attempt_003/result.json"
}
```

### `case.md`

Human-readable problem statement:

- API or behavior under test
- version boundary
- old behavior
- new behavior
- why it is silent
- realistic impact

### `evidence.md`

Source-backed evidence only:

- official docs, changelogs, migration guides, service announcements, or issues
- short source notes and URLs
- no local reproduction logs

### `reproduction.md`

Local reproduction recipe:

- adapter ecosystem
- dependency roots
- client path
- exact command shape
- old/new stdout summary
- known environment caveats

### `oracle.md`

Benchmark judgment contract:

- keep condition
- reject condition
- hard-break condition
- allowed noise
- exact fields or stdout fragments used for comparison

## Status Values

- `idea_only`: located but not locally reproduced.
- `verified_keep`: reproduced locally, old/new exit 0, meaningful silent diff.
- `rejected_no_diff`: locally checked and no behavioral diff observed.
- `blocked_runtime`: needs unavailable old/new runtime.
- `blocked_dependency`: package or service dependency unavailable.
- `needs_source`: plausible but insufficient source evidence.
