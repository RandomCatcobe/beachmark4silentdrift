# GO-002: Go timer channels changed observable capacity

## API Or Behavior Under Test

time.NewTimer channel observability in go-stdlib-time.

## Version Boundary

Go 1.22 timer behavior -> Go 1.23 timer behavior

## Old Behavior

Timer channels expose buffered-channel capacity behavior.

## New Behavior

Timer channels expose unbuffered-channel capacity behavior.

## Why The Drift Is Silent

The time.NewTimer call compiles and runs in both modes; only observable channel state changes.

## Realistic Impact Scenario

Polling or diagnostics code that treats timer channel length or capacity as a state signal can take a different path.
