# Sequential 30-Case Verification Run - 2026-05-21

Scope requested: verify 30 candidates in source order. For any candidate that cannot be fully reproduced, record the first blocked verification step.

Step vocabulary:
- `source_check`: primary source or local idea-bank evidence reviewed.
- `fixture_created`: executable probe/client created.
- `dependency_acquired`: old and new runtimes/packages available locally.
- `old_run`: old side executed.
- `new_run`: new side executed.
- `output_assertion`: old/new outputs compared against expected semantic drift.
- `case_packaged`: promoted to case-bank artifact.

Environment snapshot:
- .NET PATH runtime: `C:\Program Files (x86)\dotnet\dotnet.exe`, runtimes 3.1.3 and 5.0.10, no SDK listed.
- .NET SDK used for attempts: `C:\Users\canglan\scoop\apps\dotnet-sdk\10.0.300\dotnet.exe`, SDK 10.0.300, runtime 10.0.8 only.
- Go: `go1.26.3 windows/amd64`.
- Node: `v25.6.1`, npm `11.9.0`.
- JVM: Temurin JDK 17.0.19, Maven 3.9.16.

Queue:

| # | Candidate | Status | First blocked step | Artifact / notes |
|---:|---|---|---|---|
| 1 | DOTNET-01 | blocked | `dependency_acquired` | Requires paired .NET 6/7 runtime behavior. Local SDK is .NET 10 only; `dotnet-install` attempt produced no installed SDK artifact. |
| 2 | DOTNET-02 | blocked | `dependency_acquired` | Requires paired .NET 8/9 runtime behavior. Local SDK is .NET 10 only; `dotnet-install` attempt produced no installed SDK artifact. |
| 3 | DOTNET-03 | blocked | `dependency_acquired` | Requires runnable .NET Core 3.1 vs .NET 5+ globalization pair. PATH has runtime-only 3.1/5 x86 and no matching SDK toolchain. |
| 4 | DOTNET-04 | blocked | `dependency_acquired` | Requires paired .NET 6/7 runtime behavior. Local SDK is .NET 10 only; `dotnet-install` attempt produced no installed SDK artifact. |
| 5 | DOTNET-05 | verified_keep | | `data/verification/sequential_30/DOTNET-05`: Binder 6.0 prints `NewValue`; Binder 7.0 prints `InitialValue\|NewValue`. |
| 6 | DOTNET-06 | blocked | `old_run/new_run` | `data/verification/sequential_30/DOTNET-06`: EF Core 2.2/3.0 dependencies restored, but both fail on .NET 10 query initialization before semantic assertion. |
| 7 | DOTNET-07 | blocked | `fixture_created` | EF Core JSON enum storage needs a provider-backed relational JSON-column fixture; no deterministic provider fixture completed in this run. |
| 8 | DOTNET-09 | verified_keep | | `data/verification/sequential_30/DOTNET-09`: CsvHelper 9.2.3 parses `A;B` as one field; 10.0.0 under `de-DE` parses two fields. |
| 9 | DOTNET-10 | no_behavior_diff | `output_assertion` | `data/verification/sequential_30/DOTNET-10`: first collection-without-setter probe prints `2\|3` on both 9.0.0 and 10.0.0. |
| 10 | GO-001 | verified_keep | | `data/verification/sequential_30/GO-001`: Go 1.23.12 marshals `{"count":0}`; Go 1.26.3 marshals `{}` for `omitzero`. |
| 11 | GO-003 | verified_keep | | `data/verification/sequential_30/GO-003`: `httpmuxgo121=1` yields no pattern; default Go 1.26 yields `GET /posts/{id}`. |
| 12 | GO-004 | blocked | `dependency_acquired` | Requires Go 1.16 old side. `go1.16.15 download` was attempted but reached only 27.4% before stopping this run. |
| 13 | GO-005 | blocked | `dependency_acquired` | Requires Go 1.16 old side. `go1.16.15 download` was attempted but reached only 27.4% before stopping this run. |
| 14 | GO-006 | verified_keep | | `data/verification/sequential_30/GO-006`: Go 1.23.12 emits compiler text outside JSON; Go 1.26.3 emits `build-output` / `build-fail` JSON events. |
| 15 | GO-007 | verified_keep | | `data/verification/sequential_30/GO-007`: yaml.v2 parses `on/no` as booleans; yaml.v3 parses them as strings. |
| 16 | GO-008 | no_behavior_diff | `output_assertion` | `data/verification/sequential_30/GO-008`: first TOML float/NaN/Inf probe output is identical on v1.5.0 and v1.6.0. |
| 17 | GO-009 | blocked | `fixture_created` | Protobuf synthetic-oneof deterministic marshal case needs generated/synthetic descriptors; no minimal no-`protoc` fixture completed. |
| 18 | GO-010 | blocked | `dependency_acquired` | validator/v10 planned v11 default is not available as a released dependency pair. |
| 19 | JS-01 | verified_keep | | `data/verification/sequential_30/JS-01`: Node 12 small-ICU shows no supported tested locales and `M01`; Node 13 shows full locale support and `enero`. |
| 20 | JS-02 | verified_keep | | `data/verification/sequential_30/JS-02`: npm 6 lockfileVersion 1; npm 7 lockfileVersion 2. |
| 21 | JS-03 | verified_keep | | `data/verification/sequential_30/JS-03`: Prettier 2.8.8 omits trailing function-call comma; 3.0.0 adds it under the same print width. |
| 22 | JS-04 | verified_keep | | `data/verification/sequential_30/JS-04`: Jest 28 snapshot includes `Object { ... }`; Jest 29 snapshot prints plain `{ ... }`. |
| 23 | JS-05 | verified_keep | | `data/verification/sequential_30/JS-05`: Mongoose 6 cast removes unknown query key; Mongoose 7 keeps `{"unknown":"x"}`. |
| 24 | JS-07 | blocked | `new_run` | `data/verification/sequential_30/JS-07`: Tailwind v3 CLI runs; Tailwind v4 CLI fails with `Missing field negated on ScannerOptions.sources`, including Node 20 retry. |
| 25 | JS-08 | no_behavior_diff | `output_assertion` | `data/verification/sequential_30/JS-08`: Marked 7.0.5 and 8.0.0 produce identical heading/email HTML for the tested probe. |
| 26 | JS-10 | verified_keep | | `data/verification/sequential_30/JS-10`: Handlebars 4.5.3 reads prototype value; 4.6.0 renders blank. |
| 27 | JVM-JAVA-01 | verified_keep | | `data/verification/sequential_30/JVM-JAVA-01`: Jackson XML 2.11.4 reads empty element as `NULL:null`; 2.12.0 as `STRING:""`. |
| 28 | JVM-JAVA-02 | verified_keep | | `data/verification/sequential_30/JVM-JAVA-02`: Gson 2.9.0 returns `null`; 2.9.1 returns enum `VALUE` for `toString()` wire value. |
| 29 | JVM-JAVA-03 | verified_keep | | `data/verification/sequential_30/JVM-JAVA-03`: Hibernate 5.6 native count returns `java.math.BigInteger`; Hibernate 6.0 returns `java.lang.Long`. |
| 30 | JVM-JAVA-04 | verified_keep | | `data/verification/sequential_30/JVM-JAVA-04`: Spring Boot 2.5.14 default is `ANT_PATH_MATCHER`; 2.6.0 default is `PATH_PATTERN_PARSER`. |

Summary:
- Verified keep: 16/30.
- No behavior difference in first executable probe: 3/30.
- Blocked with exact first failed step: 11/30.
