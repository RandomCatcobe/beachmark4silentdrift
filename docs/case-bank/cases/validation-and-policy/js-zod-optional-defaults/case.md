# JS-06: Zod optional defaults are applied inside object parsing

## API Or Behavior Under Test

z.object with optional fields that also define defaults in zod.

## Version Boundary

zod 3.25.76 -> zod 4.1.12

## Old Behavior

Parsing an object with a missing optional defaulted field leaves the field absent.

## New Behavior

Parsing the same object materializes the field with its default value.

## Why The Drift Is Silent

The schema and parse call are unchanged and validation succeeds in both versions.

## Realistic Impact Scenario

Configuration, form, or payload-normalization code can start sending fields that downstream systems previously treated as omitted.
