# .NET Adapter Boundary

The user asked to adapt additional languages gradually, one at a time. .NET is
the next ecosystem opened after JVM, JS, PHP, and Ruby.

## Allowed .NET Scope

.NET work may handle local, deterministic .NET CLI cases that need:

- old/new local package roots
- shared .NET client project paths
- package-root discovery through `DOTNET_ADAPTER_PACKAGE_PATHS`
- `dotnet run --project` execution
- .NET CLI arguments passed before the program argument separator
- program arguments passed after `--`
- optional local reference paths
- adapter-level tests for real .NET smoke runs, skipped when `dotnet` is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The .NET adapter does not yet permit:

- NuGet network installs or restore as a default path
- ASP.NET server/request harnesses
- database, queue, cache, or external service fixtures
- cloud service replay harnesses
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- implementing Go or Rust adapters in the same step

## Implementation Rule

Keep .NET-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/dotnet/
```

Shared surfaces may name .NET as active and may expose .NET tool requirements,
but new .NET behavior should stay in the .NET adapter unless a coordinator
explicitly asks for broader lifecycle changes.
