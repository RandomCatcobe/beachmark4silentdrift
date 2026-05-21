# RB-RACK-005: Rack stops treating semicolons as query separators

## API Or Behavior Under Test

Rack::Utils.parse_nested_query in rack.

## Version Boundary

rack 2.2.9 -> rack 3.1.0

## Old Behavior

A semicolon in the query string is treated as a parameter separator.

## New Behavior

The same semicolon remains inside the preceding parameter value.

## Why The Drift Is Silent

Parsing succeeds in both versions and returns a params hash either way.

## Realistic Impact Scenario

Applications or middleware that accept legacy semicolon-separated query parameters can route or authorize based on different parsed values.
