# jvm_toy_drift

Offline JVM toy drift candidate for `example.toy.ToyDrift.value`.

The same public Java client calls:

```java
System.out.println(ToyDrift.value());
```

Source roots:

- `old/example/toy/ToyDrift.java` returns `old`
- `new/example/toy/ToyDrift.java` returns `new`

The JVM adapter compiles each source root with the same client and compares the
old/new stdout. This case is deterministic: no network, clock, randomness, or
filesystem input is used by the client.

Programmatic reproduction uses `silent_drift_miner.adapters.jvm.JvmAdapter`.
The shared CLI has not been changed for JVM dispatch yet.
