# Environment For GO-002

- Runtime: Go toolchain capable of selecting Go 1.22 and Go 1.23 timer behavior.
- Package versions: Go standard library time behavior for 1.22 and 1.23.
- Version switching: use GODEBUG=asynctimerchan=1 for old behavior and GODEBUG=asynctimerchan=0 for new behavior.
- Adapter/API surface: runtime-api.
- Probe shape: run probe.go and parse one JSON object from stdout.
- Command shape: GODEBUG=asynctimerchan=<mode> go run client/probe.go.
