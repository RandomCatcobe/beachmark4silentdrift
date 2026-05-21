# Environment For PHP-13

- Runtime: PHP CLI 8.1.34 and 8.2.31.
- Package versions: PHP core only; no Composer dependencies.
- Version switching: run the same probe with the selected PHP executable.
- Adapter/API surface: runtime-api, array sorting.
- Probe shape: run probe.php and parse one JSON object from stdout.
- Command shape: php client/probe.php with the old or new PHP executable.
