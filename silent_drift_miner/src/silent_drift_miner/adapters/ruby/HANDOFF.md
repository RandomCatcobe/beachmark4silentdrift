# Ruby Adapter Handoff

This adapter supports local deterministic Ruby CLI reproductions: run the same
client with old/new local package roots on `RUBYLIB`/`-I` and emit
`ReproductionResult` compatible JSON.

Current status:

- The repository-level adapter contract marks `ruby` as active.
- The adapter deliberately avoids Bundler installation and network access in
  its first implementation.
- Tests use a fake Ruby executable for deterministic coverage and a real Ruby
  smoke test skipped when `ruby` is absent.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/ruby/`
- `cases/ruby_toy_drift/`
- `silent_drift_miner/tests/test_ruby_adapter.py`

Known next steps for a coordinator:

- Add real Ruby cases only after the local toy lifecycle is stable.
- Add Bundler support only if a concrete deterministic case needs it and the
  package/audit boundary remains unchanged.
