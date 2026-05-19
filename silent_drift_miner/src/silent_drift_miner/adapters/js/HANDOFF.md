# JavaScript/Node Adapter Handoff

This adapter supports local deterministic JS reproductions: run the same client
with old/new local package roots on `NODE_PATH` and emit `ReproductionResult`
compatible JSON.

Current status:

- The repository-level adapter contract marks `js` as active.
- The adapter deliberately avoids package-manager installation and network
  access in its first implementation.
- Tests use a fake Node executable for deterministic coverage and a real Node
  smoke test skipped when `node` is absent.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/js/`
- `cases/js_toy_drift/`
- `silent_drift_miner/tests/test_js_adapter.py`

Known next steps for a coordinator:

- Add real JS cases only after the local toy lifecycle is stable.
- Add npm/pnpm/yarn install support only if a concrete deterministic case needs
  it and the package/audit boundary remains unchanged.
