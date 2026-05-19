# php_toy_drift

Offline PHP toy drift candidate for `ToyDrift\value`.

The same public PHP client calls:

```php
require_once "ToyDrift.php";
echo ToyDrift\value() . PHP_EOL;
```

Package roots:

- `old/ToyDrift.php` returns `old`
- `new/ToyDrift.php` returns `new`

The PHP adapter runs each side with `include_path` pointing at the selected local
package root. This case is deterministic: no network, clock, randomness, or
filesystem input is used by the client.
