# PHP Adapter Handoff

This adapter supports local deterministic PHP CLI reproductions: run the same
client with old/new local package roots on `include_path` and emit
`ReproductionResult` compatible JSON.

Current status:

- The repository-level adapter contract marks `php` as active.
- The adapter deliberately avoids Composer installation and network access in
  its first implementation.
- Tests use a fake PHP executable for deterministic coverage and a real PHP
  smoke test skipped when `php` is absent.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/php/`
- `cases/php_toy_drift/`
- `silent_drift_miner/tests/test_php_adapter.py`

Known next steps for a coordinator:

- Add real PHP cases only after the local toy lifecycle is stable.
- Add Composer support only if a concrete deterministic case needs it and the
  package/audit boundary remains unchanged.
