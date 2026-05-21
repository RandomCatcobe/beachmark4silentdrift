# PY-SD-010: attrs generated equality changed for shared NaN values

## API Or Behavior Under Test

generated equality for attrs classes in attrs.

## Version Boundary

attrs 23.2.0 -> attrs 24.1.0

## Old Behavior

Two attrs instances that share the same NaN object compare equal through tuple-style comparison.

## New Behavior

The same two instances compare unequal after generated equality switches to chained attribute comparisons.

## Why The Drift Is Silent

The class definition and comparison expression both still run and return a boolean.

## Realistic Impact Scenario

Cache keys, deduplication, or tests that compare model instances containing shared NaN sentinels can flip decisions without a type or call-site change.
