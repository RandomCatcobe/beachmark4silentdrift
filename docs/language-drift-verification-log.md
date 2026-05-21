# Language Drift Verification Log

Independent verification record for language-specific silent-drift candidates. This file records what was actually checked by the coordinator, separate from subagent idea-bank claims.

## 2026-05-20: First Pipeline Verification Pass

### Local Tool Availability

| Ecosystem | Pipeline runnable locally now? | Evidence |
|---|---:|---|
| Python | yes | `silent_drift_miner.cli ecosystem env-check --target python` passed with system Python 3.12.3. |
| JavaScript / Node | yes | `silent_drift_miner.cli ecosystem env-check --target js` passed with Node and npm available. PowerShell blocks `npm.ps1`, so commands use `npm.cmd`. |
| Go | no | `env-check --target go` failed: `go` not found. |
| JVM / Java | no | `env-check --target jvm` failed: `java` and `javac` not found. |
| .NET | no | `dotnet --version` reports no compatible SDK installed. |
| PHP | no | `env-check --target php` failed: `php` not found. |
| Ruby | no | `env-check --target ruby` failed: `ruby` not found. |

### Verified By Reproduction

| Candidate | Ecosystem | Source checked | Pipeline result | Old behavior | New behavior | Verdict |
|---|---|---|---|---|---|---|
| JS-06 / `js-zod-optional-defaults` | JS | https://zod.dev/v4/changelog | `data\verification\js_zod_optional_defaults\attempt_001\result.json` | `zod@3.25.76`: `parse({})` returns `{}` | `zod@4.1.12`: `parse({})` returns `{"a":"tuna"}` | verified true silent drift; both exit 0 |
| JS-09 / `js-dotenv-hash-comments` | JS | https://github.com/motdotla/dotenv | `data\verification\js_dotenv_hash_comments\attempt_001\result.json` | `dotenv@14.3.2`: `SECRET=abc#def` parses as `abc#def` | `dotenv@15.0.1`: same input parses as `abc` unless quoted | verified true silent drift; both exit 0 |
| PY-SD-010 / `py-attrs-nan-equality` | Python | https://www.attrs.org/en/24.1.0/changelog.html | `data\verification\python_attrs_nan_equality\attempt_002\result.json` | `attrs==23.2.0`: shared-`nan` attrs instances compare equal | `attrs==24.1.0`: same instances compare unequal | verified true silent drift; both exit 0 |

### Needs Toolchain Before Local Reproduction

The following language banks have candidates and source URLs, but local reproduction cannot be claimed on this machine yet because the required toolchain is missing:

- Go: `go` not installed.
- JVM / Java: `java` and `javac` not installed.
- .NET: SDK not installed.
- PHP: `php` not installed.
- Ruby: `ruby` not installed.

For these ecosystems, the next verification step is either installing the required toolchain or running the same adapter pipeline on a machine/worktree where the toolchain exists. Until then, the entries remain source-backed ideas, not locally reproduced cases.

## 2026-05-21: Current Environment Pipeline Pass

### Local Tool Availability

| Ecosystem | Pipeline runnable locally now? | Evidence |
|---|---:|---|
| Python | yes | `python --version` -> Python 3.12.3; re-ran Python reproduction pipeline. |
| JavaScript / Node | yes | `node --version` -> v25.6.1; `npm.cmd --version` -> 11.9.0; re-ran JS reproduction pipeline. |
| Go | yes | `go version` -> go1.26.3 windows/amd64; ran Go adapter pipeline for GO-002. |
| JVM / Java | yes | `java`/`javac` available; Maven available after environment refresh. Ran JVM adapter against vendored Maven jars for JVM-JAVA-07. |
| .NET | yes | PATH still points first at a runtime-only x86 `dotnet`, but `C:\Users\canglan\scoop\apps\dotnet-sdk\current\dotnet.exe` exposes SDK 10.0.300. Ran .NET adapter with explicit SDK path. |
| PHP | yes | `php --version` -> PHP 8.5.6; Composer available. Composer needed `php -d extension=openssl ...` because `openssl` is present but disabled in the default PHP CLI ini. Ran PHP adapter for PHP-07. |
| Ruby | yes | `ruby --version` -> ruby 4.0.4; `bundle --version` -> 4.0.10; ran Ruby adapter pipeline for RB-RACK-005. |

### Verified By Reproduction

| Candidate | Ecosystem | Pipeline result | Old behavior | New behavior | Verdict |
|---|---|---|---|---|---|
| JS-06 / `js-zod-optional-defaults` | JS | `data\verification\js_zod_optional_defaults\attempt_002\result.json` | `zod@3.25.76`: `parse({})` returns `{}` | `zod@4.1.12`: `parse({})` returns `{"a":"tuna"}` | re-verified true silent drift; both exit 0 |
| JS-09 / `js-dotenv-hash-comments` | JS | `data\verification\js_dotenv_hash_comments\attempt_002\result.json` | `dotenv@14.3.2`: `SECRET=abc#def` parses as `abc#def` | `dotenv@15.0.1`: same input parses as `abc` unless quoted | re-verified true silent drift; both exit 0 |
| PY-SD-010 / `py-attrs-nan-equality` | Python | `data\verification\python_attrs_nan_equality\attempt_003\result.json` | `attrs==23.2.0`: shared-`nan` attrs instances compare equal | `attrs==24.1.0`: same instances compare unequal | re-verified true silent drift; both exit 0 |
| GO-002 / `go-timer-channel-capacity` | Go | `data\verification\go_timer_channel\attempt_001\result.json` | Go 1.22 timer behavior via `GODEBUG=asynctimerchan=1`: `{"cap":1,"len":0}` | Go 1.23 timer behavior via `GODEBUG=asynctimerchan=0`: `{"cap":0,"len":0}` | verified true silent drift; both exit 0 |
| RB-RACK-005 / `ruby-rack-semicolon-query` | Ruby | `data\verification\ruby_rack_semicolon_query\attempt_001\result.json` | `rack-2.2.9`: `a=1;b=2&c=3` parses as `a=1,b=2,c=3` | `rack-3.1.0`: same input parses as `a="1;b=2",c=3` | verified true silent drift; both exit 0 |
| PHP-07 / `php-carbon-timestamp-timezone` | PHP | `data\verification\php_carbon_timestamp_timezone\attempt_001\result.json` | `nesbot/carbon 2.73.0`: `Carbon::createFromTimestamp(0)` follows PHP default timezone, yielding `1969-12-31T19:00:00-05:00` under `America/New_York` | `nesbot/carbon 3.11.4`: same call defaults to UTC, yielding `1970-01-01T00:00:00+00:00` | verified true silent drift; both exit 0 |
| JVM-JAVA-07 / `jvm-commons-csv-enum-header` | JVM | `data\verification\jvm_commons_csv_enum_header\attempt_001\result.json` | `commons-csv 1.9.0`: `CSVRecord.get(Header.X)` uses `Header.X.toString()` and returns column `Y` -> `right` | `commons-csv 1.10.0`: same call uses `Header.X.name()` and returns column `X` -> `left` | verified true silent drift; both exit 0 |
| DOTNET-08 / `dotnet-fluentvalidation-email` | .NET | `data\verification\dotnet_fluentvalidation_email\attempt_003\result.json` | `FluentValidation 8.6.2`: default `EmailAddress()` rejects `a@b` and `x y@example.com` | `FluentValidation 9.0.0`: default `EmailAddress()` accepts both because it switched to simple ASP.NET Core-compatible validation | verified true silent drift; both exit 0 |

### Rejected / Not Yet Runnable

| Candidate | Ecosystem | Status | Reason |
|---|---|---|---|
| RB-FAR-007 / Faraday query encoding | Ruby | rejected by local check | `faraday` 1.0.0 and 1.0.1 both returned `q=a+b` for `Faraday::Utils.build_query(q: "a b")`; no observed drift. |
| PHP-01 / PHP loose comparison | PHP | not runnable as old/new pipeline here | Current machine only has PHP 8.5.6; this candidate needs PHP 7.4 vs 8.0 runtimes. |
| JVM-JAVA-10 / default charset | JVM | not runnable as old/new pipeline here | Current machine only exposes JDK 21; this candidate needs JDK 17 vs 18 behavior or another old/new JDK pair. |
| DOTNET runtime-version candidates | .NET | not runnable as old/new runtime pipeline here | Current confirmed SDK path exposes .NET 10 only; package-level .NET candidates are runnable through explicit NuGet package paths, but runtime-bound .NET 6/7/8/9 comparisons still need matching runtimes/SDKs. |
