# Go Adapter

The Go adapter is the next non-Python adapter after JVM, JS, PHP, Ruby, and
.NET. It is intentionally narrow: local deterministic Go CLI runs only, no
`go get` or network module download by default.

Supported shape:

- one or more local old package roots
- one or more local new package roots
- one shared Go client package or file
- run both sides with `go run`
- expose local package roots through `GO_ADAPTER_PACKAGE_PATHS`
- emit the existing `ReproductionResult`-compatible JSON files

Offline toy case:

```text
cases/go_toy_drift/
  client/go.mod
  client/main.go
  old/value.txt
  new/value.txt
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem go \
  --candidate-id go-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/go_toy_drift/client \
  --old-package-path cases/go_toy_drift/old \
  --new-package-path cases/go_toy_drift/new \
  --out data/reproductions/go-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/go-toy-drift/spec.json \
  --out data/reproductions/go-toy-drift
```

Local environment note:

- `go` is required to run real Go cases.
- Network module download is disabled by default through `GOPROXY=off` and
  `GOSUMDB=off` unless a future concrete case explicitly needs otherwise.
