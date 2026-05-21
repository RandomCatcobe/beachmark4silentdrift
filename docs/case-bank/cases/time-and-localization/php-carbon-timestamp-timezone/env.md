# Environment For PHP-07

- Runtime: PHP CLI with Composer-installed Carbon roots available.
- Package versions: nesbot/carbon 2.73.0 and 3.11.4.
- Version switching: set PHP_INCLUDE_PATH to a Composer root containing the selected version.
- Adapter/API surface: library-api.
- Probe shape: run probe.php and parse one JSON object from stdout.
- Command shape: PHP_INCLUDE_PATH=<old-or-new-composer-root> php client/probe.php.
