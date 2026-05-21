# Case Bank Restructure Proposal

This folder is a branch-local planning area for the next case-bank structure.
It does not migrate or rewrite the current idea-bank Markdown files.

## Intent

The future bank should be a case registry, not a set of language-only notes.
Language remains a first-class tag, but the primary browsing path should support
application scenarios such as data import, validation, order state sync, routing,
serialization, time handling, and observability.

## Proposed Root

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
        reproduction.md
        oracle.md
        metadata.json
```

The required three-level shape is:

```text
case-bank root -> primary scenario folder -> individual case folder
```

The case folder is the unit of ownership. Indexes are generated or maintained as
views over metadata, not as the canonical source of case details.

## Planning Files

- `plan.md`: phased migration plan and approval gates.
- `case-folder-contract.md`: required files for every individual case folder.
- `tag-taxonomy.md`: proposed application scenario tags and cross-cutting tags.
