# JVM Special-Case Boundary

The user explicitly opened the JVM special-case boundary on 2026-05-19. This
exception applies only to the JVM adapter and does not open other ecosystems.

## Allowed JVM Special Cases

JVM work may now handle local, deterministic cases that need JVM-specific
execution shape beyond a single source root:

- multiple old/new Java source roots
- explicit classpath entries, including local JARs
- resource directories placed on the runtime classpath
- JVM arguments such as `-Dkey=value`
- program arguments passed to the client main class
- adapter-level tests for real JDK smoke runs, skipped when the JDK is absent

These cases must still produce `ReproductionResult`-compatible JSON and continue
through curation, oracle generation, benchmark packaging, and audit.

## Still Out Of Scope

The JVM exception does not permit:

- cloud service replay harnesses
- GPU or hardware-specific execution
- statistical, performance, probabilistic, or long-running reliability oracles
- current-version bug tracks without a clean old/new version pair
- changing the package/audit/oracle lifecycle for non-JVM ecosystems
- implementing JS, PHP, Ruby, Go, Rust, or .NET adapters

## Implementation Rule

Keep JVM-specific environment logic inside:

```text
silent_drift_miner/src/silent_drift_miner/adapters/jvm/
```

Shared surfaces may name JVM as active and may expose JVM tool requirements, but
new JVM behavior should be implemented in the JVM adapter unless a coordinator
explicitly asks for broader lifecycle changes.
