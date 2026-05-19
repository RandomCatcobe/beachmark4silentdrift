# PHP Adapter Boundary

The user asked to adapt additional languages gradually, one at a time. PHP is
the next ecosystem opened after JVM and JS.

## Allowed PHP Scope

PHP work may handle local, deterministic PHP CLI cases that need:

- old/new local package roots
- shared PHP client files
- `include_path`-based file loading
- PHP CLI arguments passed before the client file
- program arguments passed to the client
- optional local include paths
- adapter-level tests for real PHP smoke runs, skipped when PHP is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The PHP adapter does not yet permit:

- Composer network installs as a default path
- web-server or framework request harnesses
- database, queue, cache, or external service fixtures
- cloud service replay harnesses
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- implementing Ruby, Go, Rust, or .NET adapters in the same step

## Implementation Rule

Keep PHP-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/php/
```

Shared surfaces may name PHP as active and may expose PHP tool requirements, but
new PHP behavior should stay in the PHP adapter unless a coordinator explicitly
asks for broader lifecycle changes.
