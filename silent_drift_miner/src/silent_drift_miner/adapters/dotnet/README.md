# .NET Adapter

The .NET adapter is the next non-Python adapter after JVM, JS, PHP, and Ruby. It
is intentionally narrow: local deterministic .NET CLI project runs only, no
NuGet restore or network access by default.

Supported shape:

- one or more local old package roots
- one or more local new package roots
- one shared .NET client project path
- run both sides with `dotnet run --project`
- expose local package roots through `DOTNET_ADAPTER_PACKAGE_PATHS`
- emit the existing `ReproductionResult`-compatible JSON files

Offline toy case:

```text
cases/dotnet_toy_drift/
  client/ToyDriftClient.csproj
  client/Program.cs
  old/value.txt
  new/value.txt
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem dotnet \
  --candidate-id dotnet-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/dotnet_toy_drift/client \
  --old-package-path cases/dotnet_toy_drift/old \
  --new-package-path cases/dotnet_toy_drift/new \
  --out data/reproductions/dotnet-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/dotnet-toy-drift/spec.json \
  --out data/reproductions/dotnet-toy-drift
```

Local environment note:

- `dotnet` is required to run real .NET cases.
- `nuget` remains optional because the first adapter path uses local package
  roots.
