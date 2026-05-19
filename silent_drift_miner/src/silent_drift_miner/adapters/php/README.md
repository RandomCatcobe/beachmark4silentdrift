# PHP Adapter

The PHP adapter is the next non-Python adapter after JVM and JS. It is
intentionally narrow: local deterministic PHP CLI runs only, no Composer install
or network access.

Supported shape:

- one or more local old package roots
- one or more local new package roots
- one shared PHP client file
- run both sides with `php`
- use `include_path` to point at local package roots
- emit the existing `ReproductionResult`-compatible JSON files

Offline toy case:

```text
cases/php_toy_drift/
  client.php
  old/ToyDrift.php
  new/ToyDrift.php
```

CLI usage:

```bash
silent-drift-miner reproduce plan \
  --ecosystem php \
  --candidate-id php-toy-drift \
  --library toy-drift \
  --old-version 1.0.0 \
  --new-version 2.0.0 \
  --client-file cases/php_toy_drift/client.php \
  --old-package-path cases/php_toy_drift/old \
  --new-package-path cases/php_toy_drift/new \
  --out data/reproductions/php-toy-drift/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/php-toy-drift/spec.json \
  --out data/reproductions/php-toy-drift
```

Local environment note:

- `php` is required to run real PHP cases.
- `composer` remains optional because the first adapter path uses local package
  roots.
