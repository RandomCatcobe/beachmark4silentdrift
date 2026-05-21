# Environment For PHP-12

- Runtime: PHP CLI 8.0.30 and 8.1.34.
- Package versions: PHP core only; no Composer dependencies.
- Version switching: run the same probe with the selected PHP executable.
- Adapter/API surface: runtime-api, HTML escaping.
- Probe shape: run probe.php and parse one JSON object from stdout.
- Command shape: php client/probe.php with the old or new PHP executable.
