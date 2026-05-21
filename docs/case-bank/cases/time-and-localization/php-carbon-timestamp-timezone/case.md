# PHP-07: Carbon timestamp creation defaults to UTC

## API Or Behavior Under Test

Carbon::createFromTimestamp without explicit timezone in nesbot/carbon.

## Version Boundary

nesbot/carbon 2.73.0 -> 3.11.4

## Old Behavior

Timestamp creation without an explicit timezone follows the PHP default timezone.

## New Behavior

The same call defaults to UTC.

## Why The Drift Is Silent

The static factory still succeeds and returns a Carbon instance.

## Realistic Impact Scenario

Applications that serialize timestamps without passing a timezone can shift displayed or persisted offsets.
