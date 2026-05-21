# PHP-12: htmlspecialchars default flags escape single quotes

## API Or Behavior Under Test

htmlspecialchars with omitted flags in php-core.

## Version Boundary

PHP 8.0.30 -> PHP 8.1.34

## Old Behavior

The default flags do not escape single quotes.

## New Behavior

The same call escapes single quotes because the default flags include ENT_QUOTES.

## Why The Drift Is Silent

The function succeeds in both versions and returns a string, but the emitted HTML entity content changes.

## Realistic Impact Scenario

Template snapshots, sanitizer expectations, or downstream parsers can observe changed escaped content without a call-site change.
