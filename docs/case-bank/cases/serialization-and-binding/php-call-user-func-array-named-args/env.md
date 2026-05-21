# Environment For PHP-11

- Runtime: PHP CLI 7.4.33 and 8.0.30.
- Package versions: PHP core only; no Composer dependencies.
- Version switching: run the same probe with the selected PHP executable.
- Adapter/API surface: runtime-api, dynamic-call binding.
- Probe shape: run probe.php and parse one JSON object from stdout.
- Command shape: php client/probe.php with the old or new PHP executable.
