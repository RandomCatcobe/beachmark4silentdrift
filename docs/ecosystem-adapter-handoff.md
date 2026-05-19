# Ecosystem Adapter Handoff

This is the handoff note for a future model that may implement non-Python ecosystem adapters.

## Current State

The Python package pipeline remains the mature production path. JVM, JS, PHP,
Ruby, .NET, and Go are active under explicit one-ecosystem-at-a-time adapter
boundaries:

```text
candidate -> triage -> reproduction -> curation -> oracle -> package -> audit
```

The reserved adapter contract lives in:

```text
silent_drift_miner/src/silent_drift_miner/adapter_contracts.py
```

Inspect the current contract registry with:

```bash
silent-drift-miner ecosystem adapters
silent-drift-miner ecosystem adapters --target jvm
```

The adapter statuses are:

| Ecosystem | Status | Required tools | Notes |
| --- | --- | --- | --- |
| `python` | `active` | `python`, `pip` | Existing stable path in `silent_drift_miner.reproduction`. |
| `jvm` | `active` | `java`, `javac` | First non-Python adapter. JVM special cases are open only when local and deterministic; optional `mvn`/`gradle`. |
| `js` | `active` | `node` | Second non-Python adapter. Local deterministic Node package-root reproductions only; optional `npm`/`pnpm`/`yarn`. |
| `php` | `active` | `php` | Third non-Python adapter. Local deterministic PHP CLI include-path reproductions only; optional `composer`. |
| `ruby` | `active` | `ruby` | Fourth non-Python adapter. Local deterministic Ruby CLI load-path reproductions only; optional `bundle`. |
| `dotnet` | `active` | `dotnet` | Fifth non-Python adapter. Local deterministic .NET CLI project-root reproductions only; optional `nuget`. |
| `go` | `active` | `go` | Sixth non-Python adapter. Local deterministic Go CLI package-root reproductions only. |
| `rust` | `reserved` | `cargo`, `rustc` | Reserved only. |

## What Future Models May Do

Only after an explicit user command to implement an adapter:

- Add one ecosystem at a time.
- Preserve the same lifecycle and artifact separation used by Python.
- Produce `ReproductionResult`-compatible JSON.
- Map ecosystem-specific failures back to shared drop reasons where possible.
- Add offline toy fixtures before attempting real cases.
- Keep environment-specific logic inside the adapter boundary.

## Parallel Agent Rules

When multiple GPT/model agents work on ecosystem adapters at the same time, each agent must use an isolated branch or worktree:

- JVM agent: `adapter-jvm`
- Go agent: `adapter-go`
- JS/TypeScript agent: `adapter-js`
- PHP agent: `adapter-php`
- Ruby agent: `adapter-ruby`
- Rust agent: `adapter-rust`
- .NET agent: `adapter-dotnet`

Each agent owns only its ecosystem-specific directory:

```text
silent_drift_miner/src/silent_drift_miner/adapters/jvm/
silent_drift_miner/src/silent_drift_miner/adapters/go/
silent_drift_miner/src/silent_drift_miner/adapters/js/
silent_drift_miner/src/silent_drift_miner/adapters/php/
silent_drift_miner/src/silent_drift_miner/adapters/ruby/
silent_drift_miner/src/silent_drift_miner/adapters/rust/
silent_drift_miner/src/silent_drift_miner/adapters/dotnet/
```

Each agent may submit only:

- Its adapter implementation under its owned directory.
- One offline toy case for that ecosystem.
- Tests scoped to that adapter.
- A short handoff note for that ecosystem.

Parallel agents must not modify shared project surfaces:

- Do not change `pyproject.toml`, package version, release tags, or publishing metadata.
- Do not change the root README or docs index.
- Do not restructure the main CLI.
- Do not rewrite `adapter_contracts.py`, `ecosystems.py`, or Python reproduction code unless the coordinator explicitly asks.
- Do not move existing Python cases, packages, oracle files, or reports.

After parallel work completes, a single coordinator must merge branches in sequence, resolve conflicts, run the full test suite, update the version, write release notes if needed, tag, and push `main`.

The preferred implementation order remains sequential. JVM, JS, PHP, Ruby, .NET,
and Go are now active; Rust should remain last unless the benchmark needs it.
Parallel agents are acceptable for research and candidate-material collection,
but adapter implementation should stay narrow and isolated.

## High-Risk Drift Material Priorities

When collecting candidate materials before implementation, prioritize ecosystems with high silent or cascade drift likelihood:

- `js`: npm transitive dependencies, ESM/CJS boundary changes, TypeScript/runtime mismatches, React/Next/Vite defaults, HTTP/client serializer defaults.
- `php`: Composer dependency cascades, Laravel/Symfony defaults, Doctrine/Eloquent ORM behavior, serializer/date handling, framework config defaults.
- `ruby`: Rails defaults, ActiveSupport behavior, Bundler/RubyGems dependency cascades, ActiveRecord query semantics, serialization/time handling.
- `dotnet`: NuGet dependency cascades, ASP.NET defaults, System.Text.Json/Newtonsoft behavior, cloud SDK defaults, target framework changes.

Material collection may happen in parallel. Adapter implementation should still happen one ecosystem at a time.
JVM, JS, PHP, Ruby, .NET, and Go are the only non-Python ecosystems currently opened for implementation.

## Stop And Ask Rule

Adapter agents must not attempt large refactors. If the task appears to require changing shared lifecycle schema, replacing the Python runner, redesigning the CLI, adding a new oracle family, or changing packaging/audit semantics, stop immediately.

When stopping, record:

- What adapter was being attempted.
- What file or contract caused the blocker.
- Why the change appears larger than the owned adapter directory.
- The smallest question the user or coordinator must answer.

Then ask instead of continuing.

## What Future Models Must Not Do By Default

Do not implement any of the following unless the user explicitly asks for that exact expansion:

- Cloud-service replay harnesses for Gemini, S3, or other remote APIs.
- Current-bug tracks without a clean old/new version pair.
- CUDA/GPU-specific execution.
- Legacy-policy exceptions for old drifts.
- Statistical, performance, distributional, or long-running reliability oracles.

## Suggested First Implementation Order

1. Read `docs/python-pipeline-boundaries.md`.
2. Read `docs/phase-6-ecosystem-expansion.md`.
3. Inspect `adapter_contracts.py` and `ecosystems.py`.
4. Add a minimal adapter module for exactly one target ecosystem.
5. Add a toy offline case for that ecosystem.
6. Prove the full lifecycle through package and audit.
7. Do not migrate existing Python code unless the user explicitly asks.

## Handoff Rule

The current repository now has active local deterministic adapters for JVM, JS,
PHP, Ruby, .NET, and Go. A future model should treat those adapters as narrow
contracts and work queues, not permission to broaden scope. Rust remains
reserved until the user explicitly opens it.
