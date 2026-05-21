# PHP Drift Idea Bank

Independent language idea bank for local, deterministic PHP silent-drift candidates.

## RUN-20260520-001: Independent PHP Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: PHP has enough core and package material; no exhaustion judgment.
- Promotion note: prefer PHP CLI and package-local cases. Avoid web-server/framework request harnesses unless reduced to deterministic component calls.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| PHP-01 | PHP core | Loose comparison `==`, `!=`, `<=>` | PHP 7.4 -> 8.0 | https://www.php.net/manual/en/migration80.incompatible.php | Non-strict number vs non-numeric-string comparisons changed, e.g. `0 == "foo"` from `true` to `false`. | Same expression parses and runs; only branch choice/output changes. | Evaluate `var_export(0 == "foo")` and `in_array(0, ["foo"])` without strict mode. | High |
| PHP-02 | PHP core | Sorting functions `sort`, `usort`, `uasort`, etc. | PHP 7.4 -> 8.0 | https://www.php.net/manual/en/migration80.incompatible.php | Elements that compare equal may retain a different order because sorting became stable. | Calls still succeed; only ordering of equal items changes. | `usort($rows, fn($a, $b) => $a["group"] <=> $b["group"])` with duplicate groups; print IDs. | High |
| PHP-03 | PHP core | `htmlspecialchars()`, `htmlentities()` defaults | PHP 8.0 -> 8.1 | https://www.php.net/manual/en/migration81.incompatible.php | Default flags changed from `ENT_COMPAT` to `ENT_QUOTES \| ENT_SUBSTITUTE`, so single quotes and malformed UTF-8 encode differently. | Same call with omitted flags succeeds; escaped text changes. | `echo htmlspecialchars("Tom's")`; try malformed UTF-8 input with no flags. | High |
| PHP-04 | Symfony Serializer | `CsvEncoder::decode()` default context | before Symfony Serializer 7.3 -> 7.3 | https://github.com/symfony/serializer/blob/7.3/CHANGELOG.md | Default `as_collection` changed to `true`; decoding one-row CSV may return a list of rows instead of a single row array. | Same encoder call succeeds; array nesting/default shape changes. | `decode("name\nAda\n", "csv")` with no context, then `json_encode()` result. | High |
| PHP-05 | Laravel / Illuminate Filesystem | `Storage::put`, `write`, `writeStream` | Laravel 8.x -> 9.x | https://laravel.com/docs/9.x/upgrade | Existing files are overwritten by default after the Flysystem 3 migration. | Same storage call returns normally; persisted file contents differ. | Create `a.txt` with `old`, call `Storage::put("a.txt", "new")`, then read it back. | High |
| PHP-06 | Laravel / Illuminate Collections | `when()` / `unless()` conditional callback argument | Laravel 8.x -> 9.x | https://laravel.com/docs/9.x/upgrade | Passing a closure as the first argument now uses the closure result as the condition instead of treating the closure object as truthy. | Same fluent call succeeds; callback branch execution changes. | `collect([1])->when(fn() => false, fn($c) => $c->push(2))->all()`. | High |
| PHP-07 | Carbon | `Carbon::createFromTimestamp()` default timezone | Carbon 2 -> 3 | https://carbon.nesbot.com/docs/#api-carbon-3 | Timestamp factory methods without an explicit timezone default to UTC instead of the PHP default timezone. | Same static call succeeds; formatted local time/offset changes. | Set default timezone to `America/New_York`; print `Carbon::createFromTimestamp(0)->format("c")`. | High |
| PHP-08 | Carbon | `diffIn*()` methods such as `diffInDays`, `diffInSeconds` | Carbon 2 -> 3 | https://carbon.nesbot.com/docs/#api-carbon-3 | Diff methods may return signed floats instead of absolute integers. | Same method call succeeds; numeric type, sign, and fractional result can drift. | Compare `$a->diffInSeconds($b)` for reversed times and microsecond offsets. | High |
| PHP-09 | Monolog | Default date formatting in formatters/log output | Monolog 1.x -> 2.0 | https://github.com/Seldaek/monolog/blob/2.x/UPGRADE.md | DateTime values are formatted with timezone and microseconds unless disabled. | Logging still succeeds; emitted log lines change, affecting parsers/snapshots. | Use `LineFormatter` default format on a fixed datetime record and compare output. | High |
| PHP-10 | Guzzle | `Client` request option `idn_conversion` default | Guzzle 6.x -> 7.0 | https://github.com/guzzle/guzzle/blob/master/UPGRADING.md | International domain name conversion is disabled by default in Guzzle 7. | Same request setup can succeed with a mock handler; effective URI host changes. | Send an internationalized-domain URI through `MockHandler` plus history middleware and inspect recorded request URI. | Medium |

## Verification Log

### 2026-05-21: PHP-07 Carbon timestamp timezone

- Pipeline result: `data\verification\php_carbon_timestamp_timezone\attempt_001\result.json`
- Dependency roots: `data\verification\composer\carbon2` (`nesbot/carbon` 2.73.0) and `data\verification\composer\carbon3` (`nesbot/carbon` 3.11.4).
- Environment note: Composer is available, but PHP CLI has `openssl` disabled by default. Package install used `php -d extension=openssl C:\Users\canglan\scoop\apps\composer\current\composer.phar ...`; runtime reproduction itself uses the normal PHP adapter path.
- Old behavior: with PHP default timezone set to `America/New_York`, `Carbon::createFromTimestamp(0)` outputs timezone `America/New_York` and `1969-12-31T19:00:00-05:00`.
- New behavior: same call outputs timezone `+00:00` and `1970-01-01T00:00:00+00:00`.
- Verdict: keep. True silent drift, both sides exit 0.

### 2026-05-21: PHP-11 call_user_func_array named arguments

- Pipeline result: `data\verification\php_call_user_func_array_named_args\attempt_001\result.json`
- Runtime pair: PHP 7.4.33 and PHP 8.0.30.
- Source checked against PHP 8 named-parameters migration notes and `call_user_func_array` documentation.
- Old behavior: string keys in the argument array are ignored; values bind by insertion order, producing `{"first":"B","second":"A"}`.
- New behavior: the same string keys bind as named parameters, producing `{"first":"A","second":"B"}`.
- Verdict: keep. True silent drift, both sides exit 0.

### 2026-05-21: PHP-12 htmlspecialchars default flags

- Pipeline result: `data\verification\php_htmlspecialchars_default_flags\attempt_001\result.json`
- Runtime pair: PHP 8.0.30 and PHP 8.1.34.
- Source checked against PHP 8.1 migration notes and PHP.Watch.
- Old behavior: `htmlspecialchars("Tom's <tag>")` outputs `Tom's &lt;tag&gt;`.
- New behavior: the same call outputs `Tom&#039;s &lt;tag&gt;`.
- Verdict: keep. True silent drift, both sides exit 0.

### 2026-05-21: PHP-13 ksort SORT_REGULAR mixed keys

- Pipeline result: `data\verification\php_ksort_regular_mixed_keys\attempt_001\result.json`
- Runtime pair: PHP 8.1.34 and PHP 8.2.31.
- Source checked against PHP.Watch and `ksort` documentation.
- Old behavior: `ksort($items, SORT_REGULAR)` orders mixed keys as `["a","b",1,2]`.
- New behavior: the same call orders mixed keys as `[1,2,"a","b"]`.
- Verdict: keep. True silent drift, both sides exit 0.
