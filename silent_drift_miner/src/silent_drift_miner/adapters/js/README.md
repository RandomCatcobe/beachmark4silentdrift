# JavaScript/Node Adapter

The JS adapter is the next non-Python adapter after JVM. It is intentionally
narrow: local deterministic Node runs only, no npm install or network access.

Supported shape:

- one or more local old package roots
- one or more local new package roots
- one shared JavaScript client file
- run both sides with `node`
- use `NODE_PATH` to point at local package roots
- emit the existing `ReproductionResult`-compatible JSON files

Offline toy case:

```text
cases/js_toy_drift/
  client.js
  old/toy-drift/index.js
  new/toy-drift/index.js
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem js \
  --candidate-id js-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/js_toy_drift/client.js \
  --old-package-path cases/js_toy_drift/old \
  --new-package-path cases/js_toy_drift/new \
  --out data/reproductions/js-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/js-toy-drift/spec.json \
  --out data/reproductions/js-toy-drift
```

Local environment note:

- `node` is required to run real JS cases.
- `npm`, `pnpm`, and `yarn` remain optional because the first adapter path uses
  local package roots.
