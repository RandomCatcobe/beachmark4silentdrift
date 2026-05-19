# Go Adapter Handoff

This adapter supports local deterministic Go CLI reproductions: run the same
client package with old/new local package roots exposed through
`GO_ADAPTER_PACKAGE_PATHS` and emit `ReproductionResult` compatible JSON.

Current status:

- The repository-level adapter contract marks `go` as active.
- The adapter deliberately avoids `go get`, module download, and network access
  in its first implementation.
- Tests use a fake `go` executable for deterministic coverage and a real Go
  smoke test skipped when `go` is absent.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/go/`
- `cases/go_toy_drift/`
- `silent_drift_miner/tests/test_go_adapter.py`

Known next steps for a coordinator:

- Add real Go cases only after the local toy lifecycle is stable.
- Add module-replace or workspace support only if a concrete deterministic case
  needs it and the package/audit boundary remains unchanged.
