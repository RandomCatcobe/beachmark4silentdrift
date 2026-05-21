# Hidden Oracle For GO-002

## Keep Condition

Keep the case when both old and new probes exit successfully and all machine assertions in `expected.json` match.

## Reject Condition

Reject the case when the compared fields are equal, missing in both runs, or the observed difference is caused only by environment noise.

## Hard-Break Condition

Treat install failure, compile failure, import failure, or a nonzero probe exit as a blocked or hard-break result rather than a silent drift.

## Allowed Noise

Ignore package version fields, absolute paths, timestamps, build logs, stderr chatter, and dependency-cache locations.

## Assertions

- `cap`: old `1` and new `0`.
