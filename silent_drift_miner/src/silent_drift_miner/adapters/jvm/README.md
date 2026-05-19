# JVM Adapter

The JVM adapter is the first non-Python adapter implementation. It stays inside
the ecosystem adapter boundary. The user opened JVM special cases on
2026-05-19. JS, PHP, Ruby, .NET, and Go are also active now; Rust remains
reserved.

Supported shape:

- one local old Java source root
- one local new Java source root
- one shared Java client file
- compile both sides with `javac`
- run the configured main class with `java`
- emit the existing `ReproductionResult`-compatible JSON files

Allowed JVM special-case inputs:

- multiple source roots through `old_source_paths` and `new_source_paths`
- local classpath/JAR entries through `classpath`, `old_classpath`, or `new_classpath`
- resource directories through `resource_paths`, `old_resource_paths`, or `new_resource_paths`
- JVM arguments through `jvm_args`, `old_jvm_args`, or `new_jvm_args`
- program arguments through `program_args`, `old_program_args`, or `new_program_args`

Offline toy case:

```text
cases/jvm_toy_drift/
  client/DriftClient.java
  old/example/toy/ToyDrift.java
  new/example/toy/ToyDrift.java
```

Programmatic usage:

```python
from silent_drift_miner.adapter_contracts import AdapterPlanRequest, AdapterRunRequest
from silent_drift_miner.adapters.jvm import JvmAdapter

adapter = JvmAdapter()
spec = adapter.plan(AdapterPlanRequest(
    candidate_id="jvm-toy-drift",
    ecosystem="jvm",
    library="toy-drift",
    old_version="1.0.0",
    new_version="2.0.0",
    client_file="cases/jvm_toy_drift/client/DriftClient.java",
    out_path="data/reproductions/jvm-toy-drift/spec.json",
    metadata={
        "old_source_path": "cases/jvm_toy_drift/old",
        "new_source_path": "cases/jvm_toy_drift/new",
        "main_class": "DriftClient",
    },
))
result = adapter.run(AdapterRunRequest(
    spec_path=str(spec),
    out_dir="data/reproductions/jvm-toy-drift",
))
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem jvm \
  --candidate-id jvm-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/jvm_toy_drift/client/DriftClient.java \
  --old-source-path cases/jvm_toy_drift/old \
  --new-source-path cases/jvm_toy_drift/new \
  --out data/reproductions/jvm-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/jvm-toy-drift/spec.json \
  --out data/reproductions/jvm-toy-drift
```

Local environment note:

- `java` and `javac` are both needed to run real JVM cases.
- The adapter-level real-JDK smoke test is skipped when either executable is
  missing.
