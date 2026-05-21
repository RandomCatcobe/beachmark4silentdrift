# Hidden Oracle For PHP-07

## Keep Condition

Keep the case when both old and new probes exit successfully and all machine assertions in `expected.json` match.

## Reject Condition

Reject the case when the compared fields are equal, missing in both runs, or the observed difference is caused only by environment noise.

## Hard-Break Condition

Treat install failure, compile failure, import failure, or a nonzero probe exit as a blocked or hard-break result rather than a silent drift.

## Allowed Noise

Ignore package version fields, absolute paths, timestamps, build logs, stderr chatter, and dependency-cache locations.

## Assertions

- `timezone`: old `America/New_York` and new `+00:00`.
- `format`: old `1969-12-31T19:00:00-05:00` and new `1970-01-01T00:00:00+00:00`.
