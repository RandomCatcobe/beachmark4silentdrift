# PHP-13: ksort SORT_REGULAR orders numeric keys before string keys

## API Or Behavior Under Test

ksort with SORT_REGULAR on mixed string and numeric keys in php-core.

## Version Boundary

PHP 8.1.34 -> PHP 8.2.31

## Old Behavior

Alphabetical string keys are ordered before numeric keys.

## New Behavior

Numeric keys are ordered before alphabetical string keys.

## Why The Drift Is Silent

ksort returns success and the array retains all keys and values, but iteration order changes.

## Realistic Impact Scenario

Code that serializes, signs, diffs, or applies precedence based on sorted key order can produce different outputs.
