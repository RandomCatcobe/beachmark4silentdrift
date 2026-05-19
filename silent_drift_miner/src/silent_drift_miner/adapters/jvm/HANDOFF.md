# JVM Adapter Handoff

This adapter supports local deterministic JVM reproductions: compile old/new
source roots with the same Java client, run the configured main class, and emit
the existing `ReproductionResult`-compatible JSON. JVM special cases are open
for multiple source roots, classpath/JAR entries, resources, JVM args, and
program args.

Current status:

- The repository-level adapter contract marks `jvm` as active.
- The local environment gate is blocked on this machine because `java` and
  `javac` are not available in PATH.
- Tests use a fake toolchain so the adapter behavior is verified without
  pretending the real JVM environment is available.

Owned files:

- `silent_drift_miner/src/silent_drift_miner/adapters/jvm/`
- `cases/jvm_toy_drift/`
- `silent_drift_miner/tests/test_jvm_adapter.py`

Known next steps for a coordinator:

- Install or expose a JDK, then rerun `silent-drift-miner ecosystem env-check --target jvm`.
- Add CLI dispatch only after the JVM runner is validated with a real JDK.
