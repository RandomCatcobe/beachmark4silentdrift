# JavaScript/Node Adapter Boundary

The user explicitly asked to adapt additional languages gradually, one at a
time. JS is the first ecosystem opened after JVM.

## Allowed JS Scope

JS work may handle local, deterministic Node cases that need:

- old/new local package roots
- shared JavaScript client files
- `NODE_PATH`-based module lookup
- Node arguments passed before the client file
- program arguments passed to the client
- optional local module paths
- adapter-level tests for real Node smoke runs, skipped when Node is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The JS adapter does not yet permit:

- npm/pnpm/yarn network installs as a default path
- browser automation or DOM harnesses
- TypeScript transpilation, bundlers, or framework-specific runners
- cloud service replay harnesses
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- implementing PHP, Ruby, Go, Rust, or .NET adapters in the same step

## Implementation Rule

Keep JS-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/js/
```

Shared surfaces may name JS as active and may expose JS tool requirements, but
new JS behavior should stay in the JS adapter unless a coordinator explicitly
asks for broader lifecycle changes.
