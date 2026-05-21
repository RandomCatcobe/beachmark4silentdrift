# Case Folder Contract

Canonical reference: `final-plan.md`.

Each case folder lives at:

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

Required files:

```text
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

## Public Files

- `case.md`: problem statement, behavior boundary, why silent, impact scenario.
  No expected outputs, stdout samples, or checker conditions.
- `evidence.md`: source URLs and short notes. No local logs.
- `env.md`: runtime, package versions, install/switching method, adapter/API
  surface, environment caveats, and probe invocation shape. No expected output.
- `metadata.json`: machine-readable registry entry. No legacy `data/` artifact
  paths as canonical content; one read-only `provenance` pointer to the
  reproduction artifact is allowed.
- `client/`: minimal probe source and required build definition files only.

## Hidden Files

- `hidden/oracle.md`: prose judgment spec.
- `hidden/expected.json`: machine assertions with the shared wrapper schema.

`hidden/` is stripped during evaluation packaging.

## Client Rules

Commit:

- minimal probe source
- required build definition files, such as `package.json`, `go.mod`, `pom.xml`,
  or `probe.csproj`
- lock files only when the ecosystem requires them for a minimal source-level
  build, such as `go.sum`

Do not commit:

- `node_modules/`
- `vendor/`
- `.venv/`
- `target/`
- `bin/`
- `obj/`
- package caches
- generated jars/classes

Recommended `client/.gitignore`:

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

## `hidden/expected.json` Wrapper

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

`field` is a simple dotted key path. It is not JSONPath and does not support
array indexes in schema version 1. Schema version 1 is provisional: a case whose
drift cannot be expressed this way may instead ship an executable
`hidden/test_behavior.py` as the authoritative checker.
