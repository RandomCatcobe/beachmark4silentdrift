# Go Adapter Boundary

The user asked to adapt additional languages gradually, one at a time. Go is
the next ecosystem opened after JVM, JS, PHP, Ruby, and .NET.

## Allowed Go Scope

Go work may handle local, deterministic Go CLI cases that need:

- old/new local package roots
- shared Go client package directories or files
- package-root discovery through `GO_ADAPTER_PACKAGE_PATHS`
- `go run` execution
- Go command arguments passed before the client package
- program arguments passed after the client package
- optional local module/reference paths
- adapter-level tests for real Go smoke runs, skipped when Go is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The Go adapter does not yet permit:

- `go get` or network module download as a default path
- generated workspaces or module graph rewriting as a default path
- database, queue, cache, or external service fixtures
- cloud service replay harnesses
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- implementing Rust in the same step

## Implementation Rule

Keep Go-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/go/
```

Shared surfaces may name Go as active and may expose Go tool requirements, but
new Go behavior should stay in the Go adapter unless a coordinator explicitly
asks for broader lifecycle changes.
