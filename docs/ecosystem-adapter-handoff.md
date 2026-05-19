# Ecosystem Adapter Handoff

This is the handoff note for a future model that may implement non-Python ecosystem adapters.

## Current State

The Python package pipeline is the only active execution path:

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

The reserved ecosystems are:

| Ecosystem | Status | Required tools | Notes |
| --- | --- | --- | --- |
| `python` | `active` | `python`, `pip` | Existing stable path in `silent_drift_miner.reproduction`. |
| `jvm` | `reserved` | `java` | First intended non-Python adapter, with optional `mvn`/`gradle`. |
| `go` | `reserved` | `go` | Reserved only. |
| `rust` | `reserved` | `cargo`, `rustc` | Reserved only. |

## What Future Models May Do

Only after an explicit user command to implement an adapter:

- Add one ecosystem at a time.
- Preserve the same lifecycle and artifact separation used by Python.
- Produce `ReproductionResult`-compatible JSON.
- Map ecosystem-specific failures back to shared drop reasons where possible.
- Add offline toy fixtures before attempting real cases.
- Keep environment-specific logic inside the adapter boundary.

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

The current repository reserves interfaces only. A future model should treat this as a contract and work queue, not permission to broaden scope.
