"""Build the initial docs/case-bank migration from verified reproduction assets."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_BANK = ROOT / "docs" / "case-bank"
CLIENT_GITIGNORE = """__pycache__/
*.pyc
node_modules/
vendor/
.venv/
target/
bin/
obj/
*.class
*.jar
.gradle/
"""


CASES = [
    {
        "case_id": "PY-SD-010",
        "slug": "py-attrs-nan-equality",
        "title": "attrs generated equality changed for shared NaN values",
        "primary_scenario": "runtime-semantics",
        "application_scenarios": ["runtime-semantics", "state-and-lifecycle"],
        "ecosystems": ["python"],
        "languages": ["python"],
        "api_surfaces": ["library-api"],
        "drift_patterns": ["field-semantics-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "package-cache",
        "old_version": "23.2.0",
        "new_version": "24.1.0",
        "source_urls": ["https://www.attrs.org/en/24.1.0/changelog.html"],
        "provenance": "data/verification/python_attrs_nan_equality/attempt_003/result.json",
        "verified_at": "2026-05-21",
        "library": "attrs",
        "api": "generated equality for attrs classes",
        "boundary": "attrs 23.2.0 -> attrs 24.1.0",
        "old_behavior": "Two attrs instances that share the same NaN object compare equal through tuple-style comparison.",
        "new_behavior": "The same two instances compare unequal after generated equality switches to chained attribute comparisons.",
        "silent_reason": "The class definition and comparison expression both still run and return a boolean.",
        "impact": "Cache keys, deduplication, or tests that compare model instances containing shared NaN sentinels can flip decisions without a type or call-site change.",
        "evidence": "The attrs changelog records the generated equality-method change that avoids tuple comparison behavior.",
        "env": [
            "Runtime: Python 3.10 or newer.",
            "Package versions: attrs 23.2.0 and attrs 24.1.0.",
            "Version switching: create isolated environments and install attrs==23.2.0 or attrs==24.1.0.",
            "Adapter/API surface: library-api.",
            "Probe shape: run probe.py and parse one JSON object from stdout.",
            "Command shape: python client/probe.py after installing the selected attrs version.",
        ],
        "client": ("data/verification/python_attrs_nan_equality/client.py", "probe.py"),
        "assertions": [
            {"name": "shared NaN equality changed", "field": "equal", "old": True, "new": False}
        ],
    },
    {
        "case_id": "JS-06",
        "slug": "js-zod-optional-defaults",
        "title": "Zod optional defaults are applied inside object parsing",
        "primary_scenario": "validation-and-policy",
        "application_scenarios": ["validation-and-policy", "serialization-and-binding"],
        "ecosystems": ["js"],
        "languages": ["javascript"],
        "api_surfaces": ["library-api", "validator"],
        "drift_patterns": ["default-changed", "type-or-shape-changed"],
        "failure_modes": ["missing-field", "silent-value-change"],
        "external_dependencies": "package-cache",
        "old_version": "3.25.76",
        "new_version": "4.1.12",
        "source_urls": ["https://zod.dev/v4/changelog"],
        "provenance": "data/verification/js_zod_optional_defaults/attempt_002/result.json",
        "verified_at": "2026-05-21",
        "library": "zod",
        "api": "z.object with optional fields that also define defaults",
        "boundary": "zod 3.25.76 -> zod 4.1.12",
        "old_behavior": "Parsing an object with a missing optional defaulted field leaves the field absent.",
        "new_behavior": "Parsing the same object materializes the field with its default value.",
        "silent_reason": "The schema and parse call are unchanged and validation succeeds in both versions.",
        "impact": "Configuration, form, or payload-normalization code can start sending fields that downstream systems previously treated as omitted.",
        "evidence": "The Zod v4 changelog documents defaults inside optional fields being applied during parsing.",
        "env": [
            "Runtime: Node.js with a package root containing zod.",
            "Package versions: zod 3.25.76 and zod 4.1.12.",
            "Version switching: run with NODE_PATH or an equivalent package root pointing at the selected zod installation.",
            "Adapter/API surface: library-api, validator.",
            "Probe shape: run probe.js and parse one JSON object from stdout.",
            "Command shape: NODE_PATH=<old-or-new-node_modules> node client/probe.js.",
        ],
        "client": ("data/verification/js_zod_optional_defaults/client.js", "probe.js"),
        "package_json": {"package": "zod", "old": "3.25.76", "new": "4.1.12"},
        "assertions": [
            {"name": "optional default key presence changed", "field": "parsed.a", "old": "<missing>", "new": "tuna"}
        ],
    },
    {
        "case_id": "JS-09",
        "slug": "js-dotenv-hash-comments",
        "title": "dotenv starts treating unquoted hash text as comments",
        "primary_scenario": "parsing-and-ingestion",
        "application_scenarios": ["parsing-and-ingestion", "serialization-and-binding"],
        "ecosystems": ["js"],
        "languages": ["javascript"],
        "api_surfaces": ["library-api", "parser", "config-file"],
        "drift_patterns": ["parser-rule-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "package-cache",
        "old_version": "14.3.2",
        "new_version": "15.0.1",
        "source_urls": ["https://github.com/motdotla/dotenv#comments"],
        "provenance": "data/verification/js_dotenv_hash_comments/attempt_002/result.json",
        "verified_at": "2026-05-21",
        "library": "dotenv",
        "api": "dotenv.parse for .env content",
        "boundary": "dotenv 14.3.2 -> dotenv 15.0.1",
        "old_behavior": "An unquoted hash character inside a value remains part of the parsed value.",
        "new_behavior": "The same unquoted hash starts a comment, so only the prefix before the hash is parsed as the value.",
        "silent_reason": "The .env input parses successfully in both versions and the key is still present.",
        "impact": "Secrets, tokens, and connection strings containing hash characters can be truncated unless they are quoted.",
        "evidence": "The dotenv README documents hash comments and the need to quote values containing #.",
        "env": [
            "Runtime: Node.js with a package root containing dotenv.",
            "Package versions: dotenv 14.3.2 and dotenv 15.0.1.",
            "Version switching: run with NODE_PATH or an equivalent package root pointing at the selected dotenv installation.",
            "Adapter/API surface: library-api, parser, config-file.",
            "Probe shape: run probe.js and parse one JSON object from stdout.",
            "Command shape: NODE_PATH=<old-or-new-node_modules> node client/probe.js.",
        ],
        "client": ("data/verification/js_dotenv_hash_comments/client.js", "probe.js"),
        "package_json": {"package": "dotenv", "old": "14.3.2", "new": "15.0.1"},
        "assertions": [
            {"name": "unquoted hash value truncates", "field": "parsed.SECRET", "old": "abc#def", "new": "abc"}
        ],
    },
    {
        "case_id": "GO-002",
        "slug": "go-timer-channel-capacity",
        "title": "Go timer channels changed observable capacity",
        "primary_scenario": "state-and-lifecycle",
        "application_scenarios": ["state-and-lifecycle", "runtime-semantics"],
        "ecosystems": ["go"],
        "languages": ["go"],
        "api_surfaces": ["runtime-api", "library-api"],
        "drift_patterns": ["field-semantics-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "runtime-pair",
        "old_version": "1.22",
        "new_version": "1.23",
        "source_urls": ["https://go.dev/doc/go1.23"],
        "provenance": "data/verification/go_timer_channel/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "go-stdlib-time",
        "api": "time.NewTimer channel observability",
        "boundary": "Go 1.22 timer behavior -> Go 1.23 timer behavior",
        "old_behavior": "Timer channels expose buffered-channel capacity behavior.",
        "new_behavior": "Timer channels expose unbuffered-channel capacity behavior.",
        "silent_reason": "The time.NewTimer call compiles and runs in both modes; only observable channel state changes.",
        "impact": "Polling or diagnostics code that treats timer channel length or capacity as a state signal can take a different path.",
        "evidence": "The Go 1.23 release notes describe the timer and ticker channel behavior change.",
        "env": [
            "Runtime: Go toolchain capable of selecting Go 1.22 and Go 1.23 timer behavior.",
            "Package versions: Go standard library time behavior for 1.22 and 1.23.",
            "Version switching: use GODEBUG=asynctimerchan=1 for old behavior and GODEBUG=asynctimerchan=0 for new behavior.",
            "Adapter/API surface: runtime-api.",
            "Probe shape: run probe.go and parse one JSON object from stdout.",
            "Command shape: GODEBUG=asynctimerchan=<mode> go run client/probe.go.",
        ],
        "client": ("data/verification/go_timer_channel/client/main.go", "probe.go"),
        "extra_client": [("data/verification/go_timer_channel/client/go.mod", "go.mod")],
        "assertions": [
            {"name": "timer channel capacity changed", "field": "cap", "old": 1, "new": 0}
        ],
    },
    {
        "case_id": "RB-RACK-005",
        "slug": "ruby-rack-semicolon-query",
        "title": "Rack stops treating semicolons as query separators",
        "primary_scenario": "parsing-and-ingestion",
        "application_scenarios": ["parsing-and-ingestion", "routing-and-identity"],
        "ecosystems": ["ruby"],
        "languages": ["ruby"],
        "api_surfaces": ["library-api", "parser"],
        "drift_patterns": ["parser-rule-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "package-cache",
        "old_version": "2.2.9",
        "new_version": "3.1.0",
        "source_urls": ["https://rack.github.io/rack/3.1/CHANGELOG_md.html"],
        "provenance": "data/verification/ruby_rack_semicolon_query/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "rack",
        "api": "Rack::Utils.parse_nested_query",
        "boundary": "rack 2.2.9 -> rack 3.1.0",
        "old_behavior": "A semicolon in the query string is treated as a parameter separator.",
        "new_behavior": "The same semicolon remains inside the preceding parameter value.",
        "silent_reason": "Parsing succeeds in both versions and returns a params hash either way.",
        "impact": "Applications or middleware that accept legacy semicolon-separated query parameters can route or authorize based on different parsed values.",
        "evidence": "Rack 3.x changelog and upgrade notes document the semicolon query parsing change.",
        "env": [
            "Runtime: Ruby with rack available on the load path.",
            "Package versions: rack 2.2.9 and rack 3.1.0.",
            "Version switching: pass the selected rack lib directory with -I or RUBYLIB.",
            "Adapter/API surface: library-api, parser.",
            "Probe shape: run probe.rb and parse one JSON object from stdout.",
            "Command shape: ruby -I <old-or-new-rack-lib> client/probe.rb.",
        ],
        "client": ("data/verification/ruby_rack_semicolon_query/client.rb", "probe.rb"),
        "assertions": [
            {"name": "semicolon remains in first value", "field": "parsed.a", "old": "1", "new": "1;b=2"},
            {"name": "second semicolon key disappears", "field": "parsed.b", "old": "2", "new": "<missing>"},
        ],
    },
    {
        "case_id": "PHP-07",
        "slug": "php-carbon-timestamp-timezone",
        "title": "Carbon timestamp creation defaults to UTC",
        "primary_scenario": "time-and-localization",
        "application_scenarios": ["time-and-localization", "serialization-and-binding"],
        "ecosystems": ["php"],
        "languages": ["php"],
        "api_surfaces": ["library-api"],
        "drift_patterns": ["default-changed"],
        "failure_modes": ["wrong-timezone"],
        "external_dependencies": "package-cache",
        "old_version": "2.73.0",
        "new_version": "3.11.4",
        "source_urls": ["https://carbon.nesbot.com/docs/#api-carbon-3"],
        "provenance": "data/verification/php_carbon_timestamp_timezone/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "nesbot/carbon",
        "api": "Carbon::createFromTimestamp without explicit timezone",
        "boundary": "nesbot/carbon 2.73.0 -> 3.11.4",
        "old_behavior": "Timestamp creation without an explicit timezone follows the PHP default timezone.",
        "new_behavior": "The same call defaults to UTC.",
        "silent_reason": "The static factory still succeeds and returns a Carbon instance.",
        "impact": "Applications that serialize timestamps without passing a timezone can shift displayed or persisted offsets.",
        "evidence": "Carbon 3 documentation records the timestamp factory default timezone change.",
        "env": [
            "Runtime: PHP CLI with Composer-installed Carbon roots available.",
            "Package versions: nesbot/carbon 2.73.0 and 3.11.4.",
            "Version switching: set PHP_INCLUDE_PATH to a Composer root containing the selected version.",
            "Adapter/API surface: library-api.",
            "Probe shape: run probe.php and parse one JSON object from stdout.",
            "Command shape: PHP_INCLUDE_PATH=<old-or-new-composer-root> php client/probe.php.",
        ],
        "client": ("data/verification/php_carbon_timestamp_timezone/client.php", "probe.php"),
        "assertions": [
            {"name": "timestamp timezone default changed", "field": "timezone", "old": "America/New_York", "new": "+00:00"},
            {"name": "formatted timestamp shifted to UTC", "field": "format", "old": "1969-12-31T19:00:00-05:00", "new": "1970-01-01T00:00:00+00:00"},
        ],
    },
    {
        "case_id": "PHP-11",
        "slug": "php-call-user-func-array-named-args",
        "title": "call_user_func_array binds string keys as named arguments",
        "primary_scenario": "serialization-and-binding",
        "application_scenarios": ["serialization-and-binding", "runtime-semantics"],
        "ecosystems": ["php"],
        "languages": ["php"],
        "api_surfaces": ["runtime-api", "library-api"],
        "drift_patterns": ["field-semantics-changed", "type-or-shape-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "runtime-pair",
        "old_version": "7.4.33",
        "new_version": "8.0.30",
        "source_urls": [
            "https://www.php.net/manual/en/function.call-user-func-array.php",
            "https://www.php.net/manual/en/migration80.incompatible.php",
            "https://php.watch/versions/8.0/named-parameters",
        ],
        "provenance": "data/verification/php_call_user_func_array_named_args/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "php-core",
        "api": "call_user_func_array with string-keyed argument arrays",
        "boundary": "PHP 7.4.33 -> PHP 8.0.30",
        "old_behavior": "String keys in the argument array are ignored and arguments bind by insertion order.",
        "new_behavior": "The same string keys are interpreted as named parameter names and bind by name.",
        "silent_reason": "The function call succeeds in both runtimes and returns an array with the same shape, but values bind to different parameters.",
        "impact": "Plugin dispatchers, hook systems, or dynamic method invocations that pass associative arrays can silently swap business values between parameters.",
        "evidence": "The PHP 8 named-parameters migration notes document string-key handling in call_user_func_array.",
        "env": [
            "Runtime: PHP CLI 7.4.33 and 8.0.30.",
            "Package versions: PHP core only; no Composer dependencies.",
            "Version switching: run the same probe with the selected PHP executable.",
            "Adapter/API surface: runtime-api, dynamic-call binding.",
            "Probe shape: run probe.php and parse one JSON object from stdout.",
            "Command shape: php client/probe.php with the old or new PHP executable.",
        ],
        "client": ("data/verification/php_call_user_func_array_named_args/client.php", "probe.php"),
        "assertions": [
            {"name": "first parameter binding changed", "field": "call_user_func_array.first", "old": "B", "new": "A"},
            {"name": "second parameter binding changed", "field": "call_user_func_array.second", "old": "A", "new": "B"},
        ],
    },
    {
        "case_id": "PHP-12",
        "slug": "php-htmlspecialchars-default-flags",
        "title": "htmlspecialchars default flags escape single quotes",
        "primary_scenario": "serialization-and-binding",
        "application_scenarios": ["serialization-and-binding", "validation-and-policy"],
        "ecosystems": ["php"],
        "languages": ["php"],
        "api_surfaces": ["runtime-api", "library-api"],
        "drift_patterns": ["default-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "runtime-pair",
        "old_version": "8.0.30",
        "new_version": "8.1.34",
        "source_urls": [
            "https://www.php.net/manual/en/migration81.incompatible.php",
            "https://php.watch/versions/8.1/html-entity-default-value-changes",
        ],
        "provenance": "data/verification/php_htmlspecialchars_default_flags/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "php-core",
        "api": "htmlspecialchars with omitted flags",
        "boundary": "PHP 8.0.30 -> PHP 8.1.34",
        "old_behavior": "The default flags do not escape single quotes.",
        "new_behavior": "The same call escapes single quotes because the default flags include ENT_QUOTES.",
        "silent_reason": "The function succeeds in both versions and returns a string, but the emitted HTML entity content changes.",
        "impact": "Template snapshots, sanitizer expectations, or downstream parsers can observe changed escaped content without a call-site change.",
        "evidence": "PHP 8.1 migration notes document the default flags changing from ENT_COMPAT to ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401.",
        "env": [
            "Runtime: PHP CLI 8.0.30 and 8.1.34.",
            "Package versions: PHP core only; no Composer dependencies.",
            "Version switching: run the same probe with the selected PHP executable.",
            "Adapter/API surface: runtime-api, HTML escaping.",
            "Probe shape: run probe.php and parse one JSON object from stdout.",
            "Command shape: php client/probe.php with the old or new PHP executable.",
        ],
        "client": ("data/verification/php_htmlspecialchars_default_flags/client.php", "probe.php"),
        "assertions": [
            {"name": "default escaped text changed", "field": "default_htmlspecialchars", "old": "Tom's &lt;tag&gt;", "new": "Tom&#039;s &lt;tag&gt;"},
        ],
    },
    {
        "case_id": "PHP-13",
        "slug": "php-ksort-regular-mixed-keys",
        "title": "ksort SORT_REGULAR orders numeric keys before string keys",
        "primary_scenario": "parsing-and-ingestion",
        "application_scenarios": ["parsing-and-ingestion", "serialization-and-binding"],
        "ecosystems": ["php"],
        "languages": ["php"],
        "api_surfaces": ["runtime-api", "library-api"],
        "drift_patterns": ["ordering-changed"],
        "failure_modes": ["wrong-order", "silent-value-change"],
        "external_dependencies": "runtime-pair",
        "old_version": "8.1.34",
        "new_version": "8.2.31",
        "source_urls": [
            "https://php.watch/versions/8.2/ksort-SORT_REGULAR-order-changes",
            "https://www.php.net/ksort",
        ],
        "provenance": "data/verification/php_ksort_regular_mixed_keys/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "php-core",
        "api": "ksort with SORT_REGULAR on mixed string and numeric keys",
        "boundary": "PHP 8.1.34 -> PHP 8.2.31",
        "old_behavior": "Alphabetical string keys are ordered before numeric keys.",
        "new_behavior": "Numeric keys are ordered before alphabetical string keys.",
        "silent_reason": "ksort returns success and the array retains all keys and values, but iteration order changes.",
        "impact": "Code that serializes, signs, diffs, or applies precedence based on sorted key order can produce different outputs.",
        "evidence": "PHP.Watch records the PHP 8.2 bug fix that changed ksort(..., SORT_REGULAR) ordering for mixed keys.",
        "env": [
            "Runtime: PHP CLI 8.1.34 and 8.2.31.",
            "Package versions: PHP core only; no Composer dependencies.",
            "Version switching: run the same probe with the selected PHP executable.",
            "Adapter/API surface: runtime-api, array sorting.",
            "Probe shape: run probe.php and parse one JSON object from stdout.",
            "Command shape: php client/probe.php with the old or new PHP executable.",
        ],
        "client": ("data/verification/php_ksort_regular_mixed_keys/client.php", "probe.php"),
        "assertions": [
            {"name": "sorted key order changed", "field": "sorted_keys", "old": ["a", "b", 1, 2], "new": [1, 2, "a", "b"]},
            {"name": "sorted value order changed", "field": "sorted_values", "old": ["letter-a", "letter-b", "number-one", "number-two"], "new": ["number-one", "number-two", "letter-a", "letter-b"]},
        ],
    },
    {
        "case_id": "JVM-JAVA-07",
        "slug": "jvm-commons-csv-enum-header",
        "title": "Commons CSV enum header lookup changed from toString to name",
        "primary_scenario": "parsing-and-ingestion",
        "application_scenarios": ["parsing-and-ingestion", "serialization-and-binding"],
        "ecosystems": ["jvm"],
        "languages": ["java"],
        "api_surfaces": ["library-api", "parser"],
        "drift_patterns": ["field-semantics-changed"],
        "failure_modes": ["silent-value-change"],
        "external_dependencies": "package-cache",
        "old_version": "1.9.0",
        "new_version": "1.10.0",
        "source_urls": ["https://commons.apache.org/proper/commons-csv/changes.html"],
        "provenance": "data/verification/jvm_commons_csv_enum_header/attempt_001/result.json",
        "verified_at": "2026-05-21",
        "library": "org.apache.commons:commons-csv",
        "api": "CSVRecord.get(Enum)",
        "boundary": "commons-csv 1.9.0 -> 1.10.0",
        "old_behavior": "Enum header lookup uses the enum constant's toString value.",
        "new_behavior": "The same lookup uses the enum constant's name value.",
        "silent_reason": "The CSV input, enum type, and get call compile and run in both versions.",
        "impact": "CSV ingestion code using enums with custom toString values can read a different column without any exception.",
        "evidence": "Apache Commons CSV changes document the enum lookup behavior change.",
        "env": [
            "Runtime: Java and either Maven or local commons-csv jars.",
            "Package versions: commons-csv 1.9.0 and 1.10.0.",
            "Version switching: compile and run with the selected commons-csv jar or Maven dependency version.",
            "Adapter/API surface: library-api, parser.",
            "Probe shape: run the Java probe and parse one JSON object from stdout.",
            "Command shape: mvn -Dcommons.csv.version=<old-or-new> -f client/pom.xml compile exec:java.",
        ],
        "client": ("data/verification/jvm_commons_csv_enum_header/DriftClient.java", "probe/src/main/java/probe/Probe.java"),
        "jvm": True,
        "assertions": [
            {"name": "enum header lookup target changed", "field": "viaEnum", "old": "right", "new": "left"}
        ],
    },
    {
        "case_id": "DOTNET-08",
        "slug": "dotnet-08-fluentvalidation-email",
        "title": "FluentValidation default EmailAddress behavior changed",
        "primary_scenario": "validation-and-policy",
        "application_scenarios": ["validation-and-policy", "identity-and-contact-data"],
        "ecosystems": ["dotnet"],
        "languages": ["csharp"],
        "api_surfaces": ["library-api", "validator"],
        "drift_patterns": ["default-changed", "validation-relaxed"],
        "failure_modes": ["silent-acceptance-change"],
        "external_dependencies": "package-cache",
        "old_version": "8.6.2",
        "new_version": "9.0.0",
        "source_urls": ["https://docs.fluentvalidation.net/en/latest/upgrading-to-9.html"],
        "provenance": "data/verification/dotnet_fluentvalidation_email/attempt_003/result.json",
        "verified_at": "2026-05-21",
        "library": "FluentValidation",
        "api": "RuleFor(x => x.Email).EmailAddress()",
        "boundary": "FluentValidation 8.6.2 -> 9.0.0",
        "old_behavior": "The default email validator rejects borderline values that do not match the older regex-style policy.",
        "new_behavior": "The same validator accepts values that satisfy the simpler ASP.NET Core-compatible policy.",
        "silent_reason": "Validation returns a normal result object in both versions; only IsValid decisions change.",
        "impact": "Signup, account-update, or data-quality gates can silently accept email-like strings that were previously rejected.",
        "evidence": "The FluentValidation 9 upgrade guide documents the default EmailAddress validator change.",
        "env": [
            "Runtime: .NET SDK capable of building the console probe.",
            "Package versions: FluentValidation 8.6.2 and 9.0.0.",
            "Version switching: set DOTNET_ADAPTER_PACKAGE_PATH to the selected NuGet package root.",
            "Adapter/API surface: library-api, validator.",
            "Probe shape: run the console project and parse one JSON object from stdout.",
            "Command shape: DOTNET_ADAPTER_PACKAGE_PATH=<old-or-new-package-root> dotnet run --project client/probe.csproj.",
        ],
        "client": ("data/verification/dotnet_fluentvalidation_email/client/Program.cs", "Program.cs"),
        "extra_client": [("data/verification/dotnet_fluentvalidation_email/client/DotnetFluentValidationEmail.csproj", "probe.csproj")],
        "dotnet": True,
        "assertions": [
            {"name": "borderline short-domain email acceptance changed", "field": "results.a@b", "old": False, "new": True},
            {"name": "space-containing email acceptance changed", "field": "results.x y@example.com", "old": False, "new": True},
        ],
    },
]


def main() -> None:
    write_root_docs()
    for case in CASES:
        write_case(case)


def write_root_docs() -> None:
    CASE_BANK.mkdir(parents=True, exist_ok=True)
    (CASE_BANK / "README.md").write_text(
        "\n".join(
            [
                "# SilentDrift Case Bank",
                "",
                "This directory is the self-contained case-bank layout described in `docs/case-bank-restructure/final-plan.md`.",
                "",
                "Each case lives under `cases/<primary-scenario>/<case-id-slug>/` and contains public task files, a minimal probe client, and hidden oracle material.",
                "",
                "Public evaluation packaging strips every `hidden/` directory without parsing file contents.",
                "",
                "## Commands",
                "",
                "```bash",
                "python -m case_bank index build --out docs/case-bank/indexes/",
                "python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/",
                "```",
                "",
                "The generated indexes are views over `metadata.json` files and should be regenerated after any case metadata change.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_case(case: dict) -> None:
    case_dir = CASE_BANK / "cases" / case["primary_scenario"] / case["slug"]
    client_dir = case_dir / "client"
    hidden_dir = case_dir / "hidden"
    client_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "case.md").write_text(render_case_md(case), encoding="utf-8")
    (case_dir / "evidence.md").write_text(render_evidence_md(case), encoding="utf-8")
    (case_dir / "env.md").write_text(render_env_md(case), encoding="utf-8")
    (case_dir / "metadata.json").write_text(
        json.dumps(metadata(case), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (hidden_dir / "oracle.md").write_text(render_oracle_md(case), encoding="utf-8")
    (hidden_dir / "expected.json").write_text(
        json.dumps(
            {"schema_version": 1, "case_id": case["case_id"], "assertions": case["assertions"]},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_client(case, client_dir)


def write_client(case: dict, client_dir: Path) -> None:
    (client_dir / ".gitignore").write_text(CLIENT_GITIGNORE, encoding="utf-8")
    copy_client(case["client"][0], client_dir / case["client"][1], jvm=case.get("jvm", False))
    for src, dst in case.get("extra_client", []):
        copy_client(src, client_dir / dst, dotnet=dst.endswith(".csproj"))
    if "package_json" in case:
        package = case["package_json"]
        (client_dir / "package.json").write_text(
            json.dumps(
                {
                    "private": True,
                    "scripts": {"probe": "node probe.js"},
                    "silentDrift": {
                        "package": package["package"],
                        "old": package["old"],
                        "new": package["new"],
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if case.get("jvm"):
        (client_dir / "pom.xml").write_text(jvm_pom(), encoding="utf-8")


def copy_client(src: str, dst: Path, *, jvm: bool = False, dotnet: bool = False) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = (ROOT / src).read_text(encoding="utf-8")
    if jvm:
        text = "package probe;\n\n" + text
        text = text.replace("public class DriftClient", "public class Probe")
    if dotnet:
        text = text.replace("DotnetFluentValidationEmail", "Probe")
    dst.write_text(text, encoding="utf-8")


def metadata(case: dict) -> dict:
    return {
        "case_id": case["case_id"],
        "slug": case["slug"],
        "title": case["title"],
        "status": "verified_keep",
        "primary_scenario": case["primary_scenario"],
        "application_scenarios": case["application_scenarios"],
        "ecosystems": case["ecosystems"],
        "languages": case["languages"],
        "api_surfaces": case["api_surfaces"],
        "drift_patterns": case["drift_patterns"],
        "failure_modes": case["failure_modes"],
        "determinism": "local-deterministic",
        "external_dependencies": case["external_dependencies"],
        "old_version": case["old_version"],
        "new_version": case["new_version"],
        "source_urls": case["source_urls"],
        "provenance": {
            "reproduction_result": case["provenance"],
            "verified_at": case["verified_at"],
        },
    }


def render_case_md(case: dict) -> str:
    return "\n".join(
        [
            f"# {case['case_id']}: {case['title']}",
            "",
            f"## API Or Behavior Under Test",
            "",
            f"{case['api']} in {case['library']}.",
            "",
            "## Version Boundary",
            "",
            case["boundary"],
            "",
            "## Old Behavior",
            "",
            case["old_behavior"],
            "",
            "## New Behavior",
            "",
            case["new_behavior"],
            "",
            "## Why The Drift Is Silent",
            "",
            case["silent_reason"],
            "",
            "## Realistic Impact Scenario",
            "",
            case["impact"],
            "",
        ]
    )


def render_evidence_md(case: dict) -> str:
    lines = [f"# Evidence For {case['case_id']}", "", "## Source URLs", ""]
    lines.extend(f"- {url}" for url in case["source_urls"])
    lines.extend(["", "## Source Notes", "", case["evidence"], ""])
    return "\n".join(lines)


def render_env_md(case: dict) -> str:
    lines = [f"# Environment For {case['case_id']}", ""]
    lines.extend(f"- {item}" for item in case["env"])
    lines.append("")
    return "\n".join(lines)


def render_oracle_md(case: dict) -> str:
    assertion_lines = [
        f"- `{item['field']}`: old `{item['old']}` and new `{item['new']}`."
        for item in case["assertions"]
    ]
    return "\n".join(
        [
            f"# Hidden Oracle For {case['case_id']}",
            "",
            "## Keep Condition",
            "",
            "Keep the case when both old and new probes exit successfully and all machine assertions in `expected.json` match.",
            "",
            "## Reject Condition",
            "",
            "Reject the case when the compared fields are equal, missing in both runs, or the observed difference is caused only by environment noise.",
            "",
            "## Hard-Break Condition",
            "",
            "Treat install failure, compile failure, import failure, or a nonzero probe exit as a blocked or hard-break result rather than a silent drift.",
            "",
            "## Allowed Noise",
            "",
            "Ignore package version fields, absolute paths, timestamps, build logs, stderr chatter, and dependency-cache locations.",
            "",
            "## Assertions",
            "",
            *assertion_lines,
            "",
        ]
    )


def jvm_pom() -> str:
    return """<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>silentdrift</groupId>
  <artifactId>commons-csv-enum-header-probe</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.source>11</maven.compiler.source>
    <maven.compiler.target>11</maven.compiler.target>
    <commons.csv.version>1.9.0</commons.csv.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.apache.commons</groupId>
      <artifactId>commons-csv</artifactId>
      <version>${commons.csv.version}</version>
    </dependency>
  </dependencies>
  <build>
    <sourceDirectory>probe/src/main/java</sourceDirectory>
    <plugins>
      <plugin>
        <groupId>org.codehaus.mojo</groupId>
        <artifactId>exec-maven-plugin</artifactId>
        <version>3.1.0</version>
        <configuration>
          <mainClass>probe.Probe</mainClass>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""


if __name__ == "__main__":
    main()
