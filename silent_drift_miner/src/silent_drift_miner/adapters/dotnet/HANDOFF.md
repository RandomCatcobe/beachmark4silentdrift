# .NET Adapter Handoff

This adapter supports local deterministic .NET CLI reproductions: run the same
client project with old/new local package roots exposed through
`DOTNET_ADAPTER_PACKAGE_PATHS` and emit `ReproductionResult` compatible JSON.

Current status:

- The repository-level adapter contract marks `dotnet` as active.
- The adapter deliberately avoids NuGet installation and network access in its
  first implementation.
- Tests use a fake `dotnet` executable for deterministic coverage and a real
  .NET smoke test skipped when `dotnet` is absent.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/dotnet/`
- `cases/dotnet_toy_drift/`
- `silent_drift_miner/tests/test_dotnet_adapter.py`

Known next steps for a coordinator:

- Add real .NET cases only after the local toy lifecycle is stable.
- Add NuGet restore support only if a concrete deterministic case needs it and
  the package/audit boundary remains unchanged.
