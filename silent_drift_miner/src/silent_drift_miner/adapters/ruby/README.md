# Ruby Adapter

The Ruby adapter is the next non-Python adapter after JVM, JS, and PHP. It is
intentionally narrow: local deterministic Ruby CLI runs only, no Bundler install
or network access.

Supported shape:

- one or more local old package roots
- one or more local new package roots
- one shared Ruby client file
- run both sides with `ruby`
- use `RUBYLIB` and `-I` to point at local package roots
- emit the existing `ReproductionResult`-compatible JSON files

Offline toy case:

```text
cases/ruby_toy_drift/
  client.rb
  old/toy_drift.rb
  new/toy_drift.rb
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem ruby \
  --candidate-id ruby-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/ruby_toy_drift/client.rb \
  --old-package-path cases/ruby_toy_drift/old \
  --new-package-path cases/ruby_toy_drift/new \
  --out data/reproductions/ruby-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/ruby-toy-drift/spec.json \
  --out data/reproductions/ruby-toy-drift
```

Local environment note:

- `ruby` is required to run real Ruby cases.
- `bundle` remains optional because the first adapter path uses local package
  roots.
