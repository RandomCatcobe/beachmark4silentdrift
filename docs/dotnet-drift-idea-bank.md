# .NET Drift Idea Bank

Independent language idea bank for local, deterministic .NET/C# silent-drift candidates.

## RUN-20260520-001: Independent .NET Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: .NET has abundant candidate material; no exhaustion judgment.
- Promotion note: prefer pure console/project-root cases. Avoid ASP.NET server and database fixtures unless replaced with in-process deterministic equivalents.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| DOTNET-01 | System.Text.Json | `JsonSerializer.Serialize<object>(value, options)` with custom `JsonConverter<object>` | .NET 6 and earlier -> .NET 7 | https://learn.microsoft.com/en-us/dotnet/core/compatibility/serialization/7.0/polymorphic-serialization | Root-level `object` serialization with a custom `object` converter changes from polymorphic runtime serialization to converter output. | Same call succeeds and returns valid JSON, but payload changes. | Register converter writing `42`; serialize `(object)0`; compare JSON. | High |
| DOTNET-02 | System.Text.Json | `JsonSerializer.Deserialize<JsonDocument>("null")` | .NET 8 and earlier -> .NET 9 | https://learn.microsoft.com/en-us/dotnet/core/compatibility/serialization/9.0/jsondocument-props | JSON `null` deserializes to `null` before, but to a non-null `JsonDocument` whose root kind is `Null` after. | Both deserialize successfully; downstream null checks flip. | Print `doc is null` and `doc?.RootElement.ValueKind` for input `null`. | High |
| DOTNET-03 | .NET runtime globalization | `string.Compare`, casing, sorting, culture APIs | .NET Core 3.1 and earlier on Windows -> .NET 5+ on modern Windows | https://learn.microsoft.com/en-us/dotnet/core/compatibility/globalization/5.0/icu-globalization-api | Windows globalization switches from NLS to ICU, changing culture-sensitive comparisons, casing, sort keys, and normalization. | APIs succeed; ordered output or equality decisions differ. | Sort or compare culture-sensitive strings under a fixed culture across runtimes. | High |
| DOTNET-04 | .NET runtime core libraries | `DateTime.AddDays`, `AddMilliseconds`, other `Add*` double overloads | .NET 6 and earlier -> .NET 7 | https://learn.microsoft.com/en-us/dotnet/core/compatibility/core-libraries/7.0/datetime-add-precision | `double` arguments are no longer rounded to the nearest millisecond; full double precision is used. | Calls succeed and dates look valid, but ticks can differ. | Compare `new DateTime(2000,1,1).AddDays(0.0000001).Ticks`. | High |
| DOTNET-05 | Microsoft.Extensions.Configuration | `ConfigurationBinder.Bind` into `Dictionary<string, string[]>` | .NET 6 and earlier -> .NET 7 | https://learn.microsoft.com/en-us/dotnet/core/compatibility/extensions/7.0/config-bind-dictionary | Binding the same key to a mutable collection value now appends values instead of replacing the collection. | No exception; resulting options contain extra retained values. | Bind config key `Key:0=NewValue` into existing dictionary value `["InitialValue"]`. | High |
| DOTNET-06 | EF Core | `AsNoTracking().Include(...)` query materialization | EF Core 2.x -> 3.0+ | https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-3.x/breaking-changes | No-tracking queries stop doing identity resolution, so repeated related rows materialize as distinct object instances. | Query succeeds and data values match, but reference identity and graph shape differ. | Query products including a shared category with `AsNoTracking`; compare `ReferenceEquals`. | High |
| DOTNET-07 | EF Core | Enums mapped inside EF JSON columns | EF Core 7 -> 8 | https://learn.microsoft.com/en-us/ef/core/what-is-new/ef-core-8.0/breaking-changes | Enums in JSON are stored as integers by default instead of strings. | Save succeeds, but persisted JSON representation changes. | Map an owned JSON type containing an enum, save one row, inspect generated JSON. | High |
| DOTNET-08 | FluentValidation | `RuleFor(x => x.Email).EmailAddress()` | FluentValidation 8.x -> 9.0 | https://docs.fluentvalidation.net/en/latest/upgrading-to-9.html | Default email validation switches from .NET 4.x-style regex to ASP.NET Core-compatible simple `@` check. | Validation returns a result object; pass/fail decisions change. | Validate borderline email addresses and compare `IsValid`. | High |
| DOTNET-09 | CsvHelper | Default delimiter selection in reader/parser configuration | CsvHelper 9.x -> 10.0 | https://joshclose.github.io/CsvHelper/change-log | Default delimiter changes from comma to `CultureInfo.CurrentCulture.TextInfo.ListSeparator`. | CSV reads successfully but field splitting changes under cultures whose list separator is not comma. | Set culture with semicolon list separator; read `A;B`; compare field count and values. | Medium-high |
| DOTNET-10 | AutoMapper | Mapping collections and destination member reuse, especially `UseDestinationValue` inheritance | AutoMapper 9.x -> 10.0 | https://docs.automapper.org/en/stable/10.0-Upgrade-Guide.html | Collections are mapped by default even without setters, and `UseDestinationValue` is inherited by default. | Mapping succeeds, but destination objects or collections may be reused or mutated differently. | Map a DTO onto an existing destination with initialized child collection; compare identity and contents. | Medium-high |

## Verification Log

### 2026-05-21: DOTNET-08 FluentValidation email default

- Pipeline result: `data\verification\dotnet_fluentvalidation_email\attempt_003\result.json`
- SDK note: PATH resolves first to runtime-only `C:\Program Files (x86)\dotnet\dotnet.exe`; reproduction uses explicit SDK executable `C:\Users\canglan\scoop\apps\dotnet-sdk\current\dotnet.exe` (SDK 10.0.300).
- Dependency roots: NuGet global cache `fluentvalidation\8.6.2` and `fluentvalidation\9.0.0`.
- Client: `data\verification\dotnet_fluentvalidation_email\client`, with package DLL selected by `DOTNET_ADAPTER_PACKAGE_PATH`.
- Old behavior: FluentValidation 8.6.2 default `EmailAddress()` returns `false` for `a@b` and `x y@example.com`.
- New behavior: FluentValidation 9.0.0 default `EmailAddress()` returns `true` for both, while still rejecting `plainaddress` and `@missing-local`.
- Verdict: keep. True silent drift, both sides exit 0.
