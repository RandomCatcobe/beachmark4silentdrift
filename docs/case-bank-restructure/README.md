# Case Bank Restructure

This folder contains the final planning proposal for the next case-bank layout.
The implemented case bank now lives at `docs/case-bank/`, with indexing and
packaging commands exposed through `python -m case_bank`.

Canonical plan:

- `final-plan.md`

Supporting views:

- `case-folder-contract.md`: per-case file contract and client directory rules.
- `plan.md`: migration phases and approval gates.
- `tag-taxonomy.md`: allowed scenario, drift-pattern, failure-mode, and
  construction tags.

## Core Decisions

- A case folder is self-contained and can be copied independently.
- Minimal probe source code is committed.
- Dependency products are not committed.
- Oracle content is physically isolated under `hidden/`.
- Evaluation packaging strips `hidden/` as a directory, with no file-content
  parsing.
- Raw logs do not enter the case bank; `hidden/expected.json` stores only the
  lossy structured assertions needed by the checker.

## Proposed Target Root

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
