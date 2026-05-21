# Go Drift Idea Bank

Independent language idea bank for local, deterministic Go silent-drift candidates.

## RUN-20260520-001: Independent Go Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: Go has enough standard-library and module material; no exhaustion judgment.
- Promotion note: prefer cases that can be reproduced with local package roots and controlled `go.mod` versions; avoid network module download assumptions in benchmark packaging.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| GO-001 | `encoding/json` | `json.Marshal` struct tag option `omitzero` | Go <1.24 -> Go >=1.24 | https://go.dev/doc/go1.24 | A field tagged `json:"t,omitzero"` was previously emitted because the option was unknown; Go 1.24 omits zero values. | Struct tags are strings; old and new compile and marshal successfully. | Define a zero `time.Time` field tagged `json:"t,omitzero"`; compare JSON. | High |
| GO-002 | `time` | `time.NewTimer`, `time.NewTicker`, channel `len`/`cap` | module `go 1.22` behavior -> `go 1.23` behavior | https://go.dev/doc/go1.23 | Timer/ticker channels changed from buffered capacity `1` to unbuffered capacity `0`; polling `len(t.C)` changes. | Same APIs and code run; only channel observability and stale-send behavior change. | Set `go.mod` `go 1.22` vs `go 1.23`; print `cap(time.NewTimer(time.Hour).C)`. | High |
| GO-003 | `net/http` | `http.ServeMux.HandleFunc` patterns and `Request.PathValue` | Go <1.22 -> Go >=1.22 | https://go.dev/doc/go1.22 | Pattern `/items/{id}` changes from literal brace matching to wildcard segment matching. | Existing string patterns register; requests route differently at runtime. | Register `/items/{id}` and request `/items/123`; compare match and `PathValue("id")`. | High |
| GO-004 | `net/url`, `net/http` | `URL.Query`, `url.ParseQuery`, `Request.FormValue` | Go <1.17 -> Go >=1.17 | https://go.dev/doc/go1.17 | Query settings containing raw semicolons are no longer accepted as separators. | `URL.Query()` ignores invalid semicolon-bearing settings without forcing callers to inspect an error. | Parse `http://x/?a=1;b=2&c=3`; compare query map. | High |
| GO-005 | `mime/multipart` | `(*multipart.Part).FileName()` | Go <1.17 -> Go >=1.17 | https://go.dev/doc/go1.17 | Multipart filenames are now passed through `filepath.Base`; path-like uploaded filenames lose directory components. | Multipart parsing succeeds; downstream code sees a different filename string. | Parse a part with `filename="../dir/payload.txt"`; compare `FileName()`. | High |
| GO-006 | `go` tool | `go test -json` output | Go <1.24 -> Go >=1.24 | https://go.dev/doc/go1.24 | Build output and build failures are now emitted as JSON events interleaved with test JSON. | Same CLI command succeeds/fails similarly, but log parsers receive different records. | In a package with a compile error, run `go test -json ./...`; compare stdout event stream. | High |
| GO-007 | `gopkg.in/yaml.v2` / `gopkg.in/yaml.v3` | `yaml.Unmarshal` into untyped maps | yaml v2 -> yaml v3 | https://github.com/go-yaml/yaml/tree/v3 | YAML 1.1 booleans like `yes`/`on` decode as strings unless the destination is a typed `bool`; v2 untyped maps may decode them as bools. | Same unmarshal call and valid YAML; resulting Go value type changes. | Unmarshal `a: yes` into `map[string]any`; print type and value. | Medium-high |
| GO-008 | `github.com/BurntSushi/toml` | `toml.NewEncoder(...).Encode` float output | v1.5.x -> v1.6.0 | https://github.com/BurntSushi/toml/releases/tag/v1.6.0 | Large floats are encoded using exponent syntax so values round-trip correctly; textual TOML output changes. | Encoding still succeeds with same API; only serialized text changes. | Encode `map[string]float64{"x": 5e22}` and compare output. | High |
| GO-009 | `google.golang.org/protobuf` | `proto.MarshalOptions{Deterministic:true}.Marshal` on synthetic oneofs | <v1.31.0 -> >=v1.31.0 | https://github.com/protocolbuffers/protobuf-go/releases/tag/v1.31.0 | Deterministic sorting of synthetic oneofs was fixed; proto3 optional fields may produce different deterministic wire bytes/order. | Same generated message and marshal call compile; bytes can drift without semantic message changes. | Generate a proto3 message with several `optional` scalar fields, set fields, marshal deterministically. | Medium |
| GO-010 | `github.com/go-playground/validator/v10` | `validator.New().Struct` with `required` on struct fields | v10 default -> planned v11 default | https://pkg.go.dev/github.com/go-playground/validator/v10#WithRequiredStructEnabled | Required validation for non-pointer struct fields is opt-in in v10 and documented as the v11 default. | Same tags and `Struct` call return a different validation result. | Validate a struct with nested `validate:"required"` non-pointer struct field under v10 default vs opt-in / v11 default. | High |

## Verification Log

| Date | ID | Status | Evidence |
|---|---|---|---|
| 2026-05-21 | GO-002 | Verified by Go adapter pipeline | Source checked against Go 1.23 release notes. Reproduction result: `data\verification\go_timer_channel\attempt_001\result.json`. Old side uses `GODEBUG=asynctimerchan=1` for Go 1.22 timer behavior and prints `{"cap":1,"len":0}`; new side uses `GODEBUG=asynctimerchan=0` for Go 1.23 behavior and prints `{"cap":0,"len":0}`. Both exit 0; stdout differs. |
