# Ruby Adapter Boundary

The user asked to adapt additional languages gradually, one at a time. Ruby is
the next ecosystem opened after JVM, JS, and PHP.

## Allowed Ruby Scope

Ruby work may handle local, deterministic Ruby CLI cases that need:

- old/new local package roots
- shared Ruby client files
- `RUBYLIB`/`-I` based file loading
- Ruby CLI arguments passed before the client file
- program arguments passed to the client
- optional local load paths
- adapter-level tests for real Ruby smoke runs, skipped when Ruby is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The Ruby adapter does not yet permit:

- Bundler or RubyGems network installs as a default path
- Rails web-server or framework request harnesses
- database, queue, cache, or external service fixtures
- cloud service replay harnesses
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- implementing Go, Rust, or .NET adapters in the same step

## Implementation Rule

Keep Ruby-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/ruby/
```

Shared surfaces may name Ruby as active and may expose Ruby tool requirements,
but new Ruby behavior should stay in the Ruby adapter unless a coordinator
explicitly asks for broader lifecycle changes.
