# Python Drift Idea Bank

Append-only memory for Python silent-drift discovery ideas, rejected leads, duplicate warnings, and accepted cases.

Release context: `v0.11.0` created this memory file. It is intentionally empty
until a real discovery batch is explicitly started.

## IDEA-20260519-001: httpx JSON request body compact serialization

- Package: `httpx`
- Status: Accepted as `ACCEPTED-20260519-001` / `httpx_json_request_body_compact`.
- API surface: `httpx.Request(..., json=...)`, `httpx.post(..., json=...)`
- Candidate versions: old `0.27.2`, new `0.28.0`
- Source:
  - URL: https://github.com/encode/httpx/blob/master/CHANGELOG.md
  - Release/changelog section: `0.28.0 (28th November, 2024)`
  - Quote or paraphrase: The changelog says default JSON request bodies use a more compact representation and may require test updates.
- Behavior hypothesis:
  Same client code constructing a request with `json={"a": 1, "b": 2}` may produce different request body bytes because separators changed from spaced JSON to compact JSON.
- Why this may be silent drift:
  The request API shape is stable and request construction is local; callers comparing bytes, recorded requests, signatures, or fixtures may see changed output without an exception.
- Reproduction sketch:
  Build `httpx.Request("POST", "https://example.test", json={"a": 1, "b": 2})` and print `request.content.decode()` under both versions.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card; existing package anchors are pandas, pydantic, scikit-learn, polars, and numpy.
  Different because: this is a local HTTP client serialization change in `httpx`, not a pandas/pydantic data-model case.
- Risk notes:
  Do not make a live network call. Keep the reproduction to request construction bytes only. Version `0.28.0` also removes deprecated `proxies` and `app`, but those are hard-break paths to avoid.
- Next action:
  Try local isolated reproduction with `0.27.2` and `0.28.0`; if deterministic, promote to reproduction.

## IDEA-20260519-002: Jinja groupby default becomes case-insensitive

- Package: `jinja2`
- API surface: `Environment.from_string(...).render(...)` using the `groupby` filter
- Candidate versions: old `3.0.3`, new `3.1.0`
- Source:
  - URL: https://jinja.palletsprojects.com/en/stable/changes/#version-3-1-0
  - Release/changelog section: `Version 3.1.0`
  - Quote or paraphrase: The `groupby` filter is case-insensitive by default and gained a `case_sensitive` control.
- Behavior hypothesis:
  A template that groups strings or objects by mixed-case values may merge groups that were separate in older Jinja.
- Why this may be silent drift:
  Rendering succeeds in both versions with the same template and context, but the rendered grouping/order/counts can change.
- Reproduction sketch:
  Render a template over items with categories `["CA", "ca", "NY"]`, using `items|groupby("category")`, and print the group keys and lengths.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card.
  Different because: this is template filter grouping semantics, not a Python data-frame/model case.
- Risk notes:
  Avoid deprecated import removals in Jinja 3.1. Use stable public `jinja2.Environment` and filter syntax only.
- Next action:
  Try reproduction with `jinja2==3.0.3` and `jinja2==3.1.0`.

## IDEA-20260519-003: Werkzeug dump_cookie path default transiently drops slash

- Package: `werkzeug`
- API surface: `werkzeug.http.dump_cookie`
- Candidate versions: old `2.2.3`, new `2.3.0`
- Source:
  - URL: https://werkzeug.palletsprojects.com/en/stable/changes/#version-2-3-0
  - Release/changelog section: `Version 2.3.0`
  - Quote or paraphrase: The cookie refactor notes that `dump_cookie` no longer sets `path="/"` by default.
- Behavior hypothesis:
  Same code `dump_cookie("sid", "abc")` may produce a `Set-Cookie` header with `Path=/` in the old version and no path attribute in `2.3.0`.
- Why this may be silent drift:
  The function call remains valid and returns a string in both versions, but downstream cookie scope semantics and snapshot tests can change.
- Reproduction sketch:
  Import `dump_cookie`, call it with only key and value, and print the returned header string.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card.
  Different because: this is HTTP header serialization in Werkzeug.
- Risk notes:
  This appears transient: Werkzeug docs also note `2.3.3` restored `/` as the default path. Reproduce specifically `2.2.3 -> 2.3.0`, not latest-to-latest.
- Next action:
  Try local reproduction with exact versions and decide whether transient drift is acceptable for benchmark policy.

## IDEA-20260519-004: Starlette FileResponse chunk size default increases

- Package: `starlette`
- API surface: `starlette.responses.FileResponse`
- Candidate versions: old `0.17.1`, new `0.18.0`
- Source:
  - URL: https://www.starlette.io/release-notes/#0180-january-23-2022
  - Release/changelog section: `0.18.0 (January 23, 2022)`
  - Quote or paraphrase: The release notes say FileResponse default chunk size changed from 4 KB to 64 KB.
- Behavior hypothesis:
  Same `FileResponse(path)` object may expose a different `chunk_size`, and streaming iteration may emit different chunk boundaries for the same file.
- Why this may be silent drift:
  Construction and response streaming can complete without exceptions, but observable chunking or response object attributes differ.
- Reproduction sketch:
  Create a small temporary file larger than 64 KB, instantiate `FileResponse`, and print `response.chunk_size` or locally consume response body chunks if stable.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card.
  Different because: ASGI file response chunking is not covered by existing Python cases.
- Risk notes:
  Avoid real ASGI server or network. Prefer direct object attribute or in-process response iteration. Check dependency compatibility for older Starlette on current Python.
- Next action:
  Search Starlette test utilities for stable in-process chunk consumption, then try reproduction.

## IDEA-20260519-005: Babel Locale.number_symbols gains numbering-system layer

- Package: `babel`
- API surface: `babel.core.Locale.number_symbols`
- Candidate versions: old `2.13.1`, new `2.14.0`
- Source:
  - URL: https://babel.pocoo.org/en/stable/changelog.html#version-2-14-0
  - Release/changelog section: `Version 2.14.0`
  - Quote or paraphrase: `Locale.number_symbols` now has first-level keys for each numbering system; previous decimal access moves under `latn`.
- Behavior hypothesis:
  Same code inspecting `Locale.parse("en").number_symbols` may see different keys and nested values after upgrade.
- Why this may be silent drift:
  The public property still exists and returns mapping-like data, but callers reading keys or serializing the mapping observe different structure.
- Reproduction sketch:
  Print `list(Locale.parse("en").number_symbols.keys())[:5]` and whether `"decimal"` is a direct key.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card.
  Different because: locale data structure drift in Babel is unrelated to existing pandas/pydantic cases.
- Risk notes:
  Changelog labels this as possibly backwards incompatible, so silence is borderline. The behavior is local and deterministic, but candidate may need human review on silent-policy fit.
- Next action:
  Try local reproduction and record whether the mapping representation is stable enough for an oracle without leaking implementation detail.

## IDEA-20260519-006: Click flag option default is preserved as provided

- Package: `click`
- API surface: `click.option(..., flag_value=..., default=...)` with `CliRunner.invoke`
- Candidate versions: old `8.2.2`, new `8.3.0`
- Source:
  - URL: https://click.palletsprojects.com/en/stable/changes/#version-8-3-0
  - Release/changelog section: `Version 8.3.0`
  - Quote or paraphrase: Click reworked `flag_value` and `default`; the default is now preserved and passed directly.
- Behavior hypothesis:
  A command with feature-switch flags and an explicit non-string/default value may receive a different Python value when invoked with no flag.
- Why this may be silent drift:
  The command declaration and invocation shape remain valid, and `CliRunner` returns normally, but stdout can show a different default value.
- Reproduction sketch:
  Define a small command with paired flag options sharing a parameter name, use `CliRunner().invoke(cmd, [])`, and print the callback's received value.
- Duplicate check:
  Similar to: no current accepted/rejected/idea card.
  Different because: this is CLI option parsing/default semantics.
- Risk notes:
  Click `8.3.x` is very recent. Avoid cases fixed again in `8.3.1+`; pin exact old/new versions and choose a changelog-backed flag scenario.
- Next action:
  Reproduce the simplest documented `flag_value`/`default` behavior with `8.2.2 -> 8.3.0`.

## REJECTED-20260519-007: NetworkX 3.0 matrix-to-array migration is too prominently announced

- Package: `networkx`
- API surface: `google_matrix`, `attr_matrix`, and related NumPy/SciPy matrix-returning algorithms
- Source: https://networkx.org/documentation/stable/release/migration_guide_from_2.x_to_3.0.html and https://networkx.org/documentation/stable/release/release_2.7.html
- Tried because:
  NetworkX 3.0 migration notes describe default NumPy/SciPy implementation shifts and return type moves from matrices to arrays, which are local and deterministic.
- Rejected because:
  - the matrix-to-array migration is a central 3.0 migration-guide topic, not a quiet change
  - NetworkX 2.7 added FutureWarnings for specific return-type changes
  - reproductions may need optional NumPy/SciPy dependency pinning, increasing setup noise
- What future runs should avoid: Do not spend another attempt on NetworkX 2.x -> 3.0 matrix/array return-type changes unless the user explicitly accepts prominent migration-guide cases.
- What future runs may still try: A narrower NetworkX bugfix with identical public call shape, no FutureWarning, no optional SciPy path, and no prominent migration-guide coverage.

## REJECTED-20260519-008: attrs @define on_setattr converters are explicit breaking change

- Package: `attrs`
- API surface: `attrs.define`, `attrs.field(converter=...)`, assignment to attrs instances
- Source: https://www.attrs.org/en/stable/changelog.html
- Tried because:
  The `21.3.0` changelog says converters now run by default when setting an attribute on instances, which could make assignment output change locally.
- Rejected because:
  - the changelog section is explicitly backward-incompatible/breaking
  - the source says the project intentionally fixed a fresh API oversight
  - using it as silent drift would conflict with the "not prominently announced as breaking" requirement
- What future runs should avoid: Avoid `attrs` `21.3.0` `@define` on-setattr converter drift as a benchmark candidate.
- What future runs may still try: Later attrs behavior under non-breaking `Changes` sections, especially deterministic serializer/filter behavior that is not under a backward-incompatible heading.

## REJECTED-20260519-009: urllib3 TLS minimum default needs network-like SSL context and is prominent

- Package: `urllib3`
- API surface: `urllib3.util.create_urllib3_context`, default TLS settings
- Source: https://urllib3.readthedocs.io/en/2.0.0/v2-migration-guide.html
- Tried because:
  The urllib3 v2 migration guide says the default minimum TLS version changed from TLS 1.0 to TLS 1.2.
- Rejected because:
  - the change is listed among important v2 migration changes
  - the user-visible impact normally depends on remote TLS endpoints or platform SSL behavior
  - a local-only SSLContext attribute check may be too implementation-shaped for a useful benchmark task
- What future runs should avoid: Do not use urllib3 v2 TLS minimum/cipher/default certificate behavior for this Python silent-drift batch.
- What future runs may still try: Pure local urllib3 data-structure or parser behavior with deterministic inputs and no TLS service, if not prominently covered by the migration guide.

## REJECTED-20260519-010: FastAPI strict_content_type is explicitly marked breaking

- Package: `fastapi`
- API surface: `FastAPI(strict_content_type=...)`, JSON request body parsing through `TestClient`
- Source: https://fastapi.tiangolo.com/release-notes/#01320
- Tried because:
  FastAPI `0.132.0` defaults to checking JSON request `Content-Type`, so a local `TestClient` request without a valid content type could return a different response.
- Rejected because:
  - the release notes place this under `Breaking Changes`
  - the behavior is intentionally configurable through `strict_content_type=False`
  - this is better treated as a documented breaking migration than silent drift
- What future runs should avoid: Avoid FastAPI `0.132.0` strict content-type default as a silent-drift candidate.
- What future runs may still try: FastAPI or Starlette local response/schema ordering changes that are not under a breaking-change section and do not need a live server.


## IDEA-20260520-001: Matplotlib get_cmap returns a copy

- Package: `matplotlib`
- API surface: `matplotlib.pyplot.get_cmap, matplotlib.cm.get_cmap`
- Candidate versions: old 3.6.3, new 3.7.0
- Source:
  - URL: https://matplotlib.org/3.10.1/api/prev_api_changes/api_changes_3.7.0.html
  - Release/changelog section: API Changes for 3.7.0 / Behaviour Changes
  - Quote or paraphrase: The Matplotlib 3.7 API changes say get_cmap formerly returned a global Colormap and now returns a new copy.
- Behavior hypothesis: Same code that obtains a named colormap twice and mutates the first object may stop leaking that mutation to later get_cmap calls.
- Why this may be silent drift: The function names and arguments remain valid and return Colormap objects in both versions, but object identity and mutation propagation semantics change without an exception.
- Reproduction sketch: Import matplotlib.pyplot as plt; get viridis twice around a set_bad or other local mutation; print whether the second lookup reflects the first mutation or whether object identities differ.
- Duplicate check:
  - Similar to: No existing idea/rejected/accepted card for matplotlib; local anchors for pandas, pydantic, scikit-learn, numpy, and polars are different packages.
  - Different because: This is colormap registry object-copy behavior, not data-frame, validation, model, or array behavior.
- Risk notes:
- Matplotlib is heavier than small utility libraries, but the reproduction can use Agg/no display and no external service.
- Next action: Try isolated reproduction with 3.6.3 and 3.7.0; prefer object identity plus mutation observation over image rendering.

## IDEA-20260520-002: Requests treats application/json as UTF-8

- Package: `requests`
- API surface: `requests.Response.text, requests.Response.json`
- Candidate versions: old 2.25.0, new 2.25.1
- Source:
  - URL: https://raw.githubusercontent.com/psf/requests/main/HISTORY.md
  - Release/changelog section: 2.25.1 (2020-12-16) / Bugfixes
  - Quote or paraphrase: Requests 2.25.1 notes that application/json is treated as utf8 by default to resolve inconsistencies between text and json output.
- Behavior hypothesis: A local Response with Content-Type application/json and non-ASCII UTF-8 bytes may decode text differently after the default encoding fix.
- Why this may be silent drift: Code can construct or receive the same Response object shape and call text or json successfully, while decoded text changes because the implicit charset changed.
- Reproduction sketch: Create requests.Response(), set headers to application/json and _content to UTF-8 JSON bytes containing a non-ASCII character, then print response.encoding and response.text.
- Duplicate check:
  - Similar to: No existing requests package card; urllib3 TLS rejection is adjacent HTTP-client territory but a different package/API/source.
  - Different because: This is pure local response decoding in requests, not TLS context defaults, request-body compact JSON, or live network behavior.
- Risk notes:
- Avoid live HTTP. Check whether chardet/charset_normalizer optional dependencies affect old-version behavior; pin a minimal dependency set if needed.
- Next action: Try 2.25.0 -> 2.25.1 with a hand-built Response object and no network.

## IDEA-20260520-003: pytest default short summary reports failures and errors

- Package: `pytest`
- API surface: `pytest.main([...]) default terminal reporting, -r option default`
- Candidate versions: old 5.3.5, new 5.4.0
- Source:
  - URL: https://pytest.org/en/8.2.x/changelog.html
  - Release/changelog section: pytest 5.4.0 / Features
  - Quote or paraphrase: The changelog says the default for -r changed to fE, which displays failures and errors in the short test summary; -rN restores old behavior.
- Behavior hypothesis: Running pytest against the same failing local test file with default options may emit additional short-summary lines after the version change.
- Why this may be silent drift: pytest.main and the CLI invocation remain valid in both versions; the test failure can be deterministic, while captured stdout/report text changes without a Python exception.
- Reproduction sketch: Write a temporary test file with one deterministic failing assertion, run pytest.main([path]) or python -m pytest path while capturing stdout, and compare short test summary content.
- Duplicate check:
  - Similar to: No existing pytest package card or accepted case; current cases are package APIs such as pandas/pydantic/sklearn.
  - Different because: This is test-runner reporting default output, not library return-value semantics in existing anchors.
- Risk notes:
- The command returns a failing exit code by design; decide whether the pipeline treats nonzero pytest process status as acceptable if wrapped by a Python client that prints captured output.
- Next action: Prototype with pytest 5.3.5 and 5.4.0; reject if nonzero subprocess exit is incompatible with current reproduction policy.

## IDEA-20260520-004: Django default timezone object switches to zoneinfo

- Package: `django`
- API surface: `django.utils.timezone.get_default_timezone, django.utils.timezone.utc`
- Candidate versions: old 3.2.25, new 4.0.0
- Source:
  - URL: https://docs.djangoproject.com/en/5.0/releases/4.0/
  - Release/changelog section: Django 4.0 release notes / zoneinfo default timezone implementation
  - Quote or paraphrase: Django 4.0 release notes say zoneinfo is now the default timezone implementation and pytz support is deprecated.
- Behavior hypothesis: With the same TIME_ZONE setting, code that inspects or serializes the default timezone object may observe a pytz object before the upgrade and a zoneinfo object after it.
- Why this may be silent drift: The settings and timezone API call shape are unchanged, and get_default_timezone can return normally in both versions, but the returned object type and repr can change.
- Reproduction sketch: Configure settings with USE_TZ=True and TIME_ZONE=Europe/Paris, call django.setup() if needed, then print type(timezone.get_default_timezone()).__module__ and repr.
- Duplicate check:
  - Similar to: No existing django package card; pydantic and pandas migration cases are unrelated package anchors.
  - Different because: This is framework timezone implementation drift, not validation/model/dataframe behavior.
- Risk notes:
- Requires a compatible Python, likely 3.10 for Django 4.0. Keep the reproduction settings-only with no database, server, or filesystem project.
- Next action: Try local reproduction on Python 3.10 with Django 3.2.25 and 4.0.0.

## IDEA-20260520-005: Flask session cookie domain stops using SERVER_NAME

- Package: `flask`
- API surface: `flask.sessions.SessionInterface.get_cookie_domain, Set-Cookie domain behavior`
- Candidate versions: old 2.2.5, new 2.3.0
- Source:
  - URL: https://flask.palletsprojects.com/en/stable/changes/
  - Release/changelog section: Version 2.3.0
  - Quote or paraphrase: Flask 2.3.0 notes that SESSION_COOKIE_DOMAIN does not fall back to SERVER_NAME and the default is not to set the domain.
- Behavior hypothesis: The same Flask app configured with SERVER_NAME but no SESSION_COOKIE_DOMAIN may emit a session cookie with a domain before the upgrade and without one after it.
- Why this may be silent drift: The Flask app, session interface, and test client calls remain valid; response headers or get_cookie_domain output change while requests complete locally.
- Reproduction sketch: Create Flask(__name__), set secret_key and SERVER_NAME=example.test, touch session in a route, use app.test_client() to request it, and print the Set-Cookie header or get_cookie_domain(app).
- Duplicate check:
  - Similar to: No existing flask package card; werkzeug cookie path idea is adjacent but a different package and API surface.
  - Different because: This concerns Flask session cookie domain selection from SERVER_NAME, not Werkzeug dump_cookie path serialization.
- Risk notes:
- Use Flask test_client only, no live server. Check exact dependency pins because Flask 2.3 requires Werkzeug 2.3+.
- Next action: Try Flask 2.2.5 -> 2.3.0 with in-process test_client header capture.

## IDEA-20260520-006: Arrow timezone objects migrate from pytz to ZoneInfo

- Package: `arrow`
- API surface: `arrow.get(..., tzinfo=...), Arrow.tzinfo`
- Candidate versions: old 1.3.0, new 1.4.0
- Source:
  - URL: https://arrow.readthedocs.io/en/stable/releases.html
  - Release/changelog section: 1.4.0 release history
  - Quote or paraphrase: Arrow 1.4.0 release history says Arrow migrated to ZoneInfo for timezones instead of pytz.
- Behavior hypothesis: The same arrow.get call with a named timezone may return an Arrow object whose tzinfo type, repr, or downstream timezone API behavior differs after the upgrade.
- Why this may be silent drift: The public arrow.get call shape and Arrow object return remain stable, but timezone implementation semantics are observable without an exception.
- Reproduction sketch: Call arrow.get(2024, 1, 1, tzinfo=Europe/Paris) and print type(obj.tzinfo).__module__, type name, and a stable repr field under both versions.
- Duplicate check:
  - Similar to: No existing arrow package card; Django timezone idea in this same batch is a different package and framework API.
  - Different because: This targets Arrow object construction and its tzinfo implementation, not Django settings-level timezone defaults.
- Risk notes:
- Timezone data availability may vary by platform; use a common IANA zone and pin tzdata if Windows/Python isolation lacks system tzdata.
- Next action: Try Arrow 1.3.0 -> 1.4.0 with a fixed named timezone and no current-time calls.

## REJECTED-20260520-007: SQLAlchemy Row containment is prominent 2.0 migration behavior

- Package: `sqlalchemy`
- API surface: `sqlalchemy.engine.Row.__contains__, Result rows`
- Source: https://docs.sqlalchemy.org/20/changelog/migration_20.html and https://docs.sqlalchemy.org/20/changelog/changelog_20.html
- Tried because: SQLAlchemy 2.0 has local deterministic row semantics: Row is named-tuple-like and containment no longer acts like mapping-key containment.
- Rejected because:
- Reject for this batch because the row behavior is a central SQLAlchemy 2.0 migration-guide topic and the changelog explicitly frames Result rows as 2.0-style behavior; using it would duplicate a prominent migration case rather than silent drift.
- What future runs should avoid: Do not spend another Python autodiscovery attempt on SQLAlchemy 1.4 -> 2.0 Row containment or mapping-vs-named-tuple behavior unless the policy allows prominent migration-guide cases.
- What future runs may still try: A narrower SQLAlchemy bugfix or minor-release parser/default change with identical call shape, no database server, and no prominent 2.0 migration-guide coverage.

## REJECTED-20260520-008: PyYAML 5.1 default loader and flow-style changes are explicit incompatibilities

- Package: `pyyaml`
- API surface: `yaml.load, yaml.dump default_flow_style`
- Source: https://pyyaml.org/wiki/PyYAML and https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load%28input%29-Deprecation
- Tried because: PyYAML 5.1/5.2 mention default Loader changes and default_flow_style=False, which could alter local parsing/dumping output without network services.
- Rejected because:
- Reject because the primary changelog groups the relevant 5.1 changes under Incompatible changes, yaml.load has warning/hard-safety migration baggage, and older exact versions may be noisy on modern Python.
- What future runs should avoid: Avoid PyYAML yaml.load default loader and 5.1 default_flow_style changes as silent-drift candidates for this benchmark policy.
- What future runs may still try: A later PyYAML minor bugfix in safe_load/safe_dump with deterministic output and no explicit incompatible-change label.

## REJECTED-20260520-009: marshmallow TimeDelta float preservation is explicitly backward-incompatible

- Package: `marshmallow`
- API surface: `marshmallow.fields.TimeDelta.deserialize`
- Source: https://marshmallow.readthedocs.io/en/stable/changelog.html
- Tried because: marshmallow 4.0 notes that TimeDelta no longer truncates float values when deserializing, which is a deterministic local output difference for the same Field().deserialize(12.9) call.
- Rejected because:
- Reject because the changelog labels the TimeDelta change as Backwards-incompatible and puts it among major marshmallow 4 incompatibilities, so it is not silent enough for the current discovery criteria.
- What future runs should avoid: Do not use marshmallow 4.0 TimeDelta float truncation/preservation as a silent-drift candidate.
- What future runs may still try: marshmallow 3.x or 4.x bugfix entries not labeled backwards-incompatible where Schema.dump/load returns different data without raising.

## REJECTED-20260520-010: aiohttp ClientTimeout sock_connect default is under breaking-change heading

- Package: `aiohttp`
- API surface: `aiohttp.ClientTimeout default parameters, client connection timeout behavior`
- Source: https://docs.aiohttp.org/en/stable/changes.html#id180
- Tried because: aiohttp 3.10.9 says the default ClientTimeout parameters changed to include sock_connect=30 seconds, and ClientTimeout() can be inspected locally without a network request.
- Rejected because:
- Reject because the entry is placed under Removals and backward incompatible breaking changes, and a meaningful end-user behavior reproduction would normally involve connection timing rather than a simple business-output difference.
- What future runs should avoid: Avoid aiohttp 3.10.9 ClientTimeout sock_connect default as a silent-drift benchmark candidate.
- What future runs may still try: Pure local aiohttp request/response object serialization changes outside breaking-change sections, with no live server and no timeout-dependent oracle.

## IDEA-20260520-011: Python-Markdown footnotes order by reference occurrence

- Package: `markdown`
- API surface: `markdown.markdown(..., extensions=["footnotes"])`
- Candidate versions: old `3.8.2`, new `3.9.0`
- Source:
  - URL: https://python-markdown.github.io/changelog/
  - Release/changelog section: `3.9.0` / `Changed`
  - Quote or paraphrase: The changelog says footnotes are ordered by reference occurrence, with a config option to restore definition ordering.
- Behavior hypothesis:
  Same Markdown input with footnote definitions in one order and references in another may render footnote HTML in a different order after upgrade.
- Why this may be silent drift:
  The `markdown.markdown` call and `footnotes` extension name remain valid and return HTML in both versions, but output ordering changes.
- Reproduction sketch:
  Render text containing `[^b]` before `[^a]` while defining `[^a]` before `[^b]`; print the generated footnote list fragment.
- Duplicate check:
  Similar to: no existing `markdown` package card; prior `jinja2` card is template rendering but a different package and API.
  Different because: this is Markdown footnote output ordering, not Jinja grouping or Python data-frame/model behavior.
- Risk notes:
  Python-Markdown `3.10.0` reverted this default, so reproduce the exact `3.8.2 -> 3.9.0` range or decide whether transient default drift is acceptable.
- Next action:
  Try isolated rendering under `markdown==3.8.2` and `markdown==3.9.0`, then review whether transient drift should be promoted.

## IDEA-20260520-012: multidict popitem removes latest entry

- Package: `multidict`
- API surface: `multidict.MultiDict.popitem`
- Candidate versions: old `6.2.0`, new `6.3.0`
- Source:
  - URL: https://multidict.aio-libs.org/en/stable/changes/
  - Release/changelog section: `6.3.0` / `Features`
  - Quote or paraphrase: The changelog says `MultiDict.popitem()` changed from removing the first entry to removing the latest entry.
- Behavior hypothesis:
  A `MultiDict` with multiple inserted keys may return and remove a different key/value pair from the same `popitem()` call after upgrade.
- Why this may be silent drift:
  The method call remains public and valid, and it returns a pair in both versions without an exception, but observable mutation and return order change.
- Reproduction sketch:
  Build `MultiDict([("a", "1"), ("b", "2")])`, call `popitem()`, and print the returned pair plus remaining items.
- Duplicate check:
  Similar to: no existing `multidict` card; `yarl` in this batch is also aio-libs but a different package/API.
  Different because: this is mutable multi-value mapping pop order, not URL normalization or HTTP client behavior.
- Risk notes:
  Use exact `6.2.0 -> 6.3.0`; avoid the yanked `6.5.0` release and avoid C-extension-specific performance claims.
- Next action:
  Try local reproduction in pure Python client code and promote if both wheels install cleanly.

## IDEA-20260520-013: yarl URL.join keeps empty URL path segments

- Package: `yarl`
- API surface: `yarl.URL.join`, `yarl.URL.joinpath`, `/` operator string output
- Candidate versions: old `1.9.9`, new `1.9.10`
- Source:
  - URL: https://yarl.aio-libs.org/en/stable/changes/
  - Release/changelog section: `1.9.10` / `Bug fixes`
  - Quote or paraphrase: The changelog says URL joining with empty segments changed to match RFC 3986 and align URL joining helpers.
- Behavior hypothesis:
  Joining a base URL whose path intentionally contains empty segments may produce a different resulting URL string after the upgrade.
- Why this may be silent drift:
  The same `URL(...).join(...)` call returns a `URL` object in both versions and stringification succeeds, but path normalization changes.
- Reproduction sketch:
  Compare `str(URL("https://web.archive.org/web/").join(URL("https://github.com/")))` or an equivalent empty-segment path case under both versions.
- Duplicate check:
  Similar to: no existing `yarl` card; `urllib3` rejection and `httpx` idea are adjacent URL/HTTP areas.
  Different because: this is pure URL object joining semantics, not TLS defaults or HTTP request JSON serialization.
- Risk notes:
  Earlier `1.9.5`/`1.9.6` notes mention a reverted empty-segment change, so pin the later stable `1.9.9 -> 1.9.10` pair first.
- Next action:
  Find the smallest documented empty-segment URL fixture and reproduce without network calls.

## IDEA-20260520-014: python-json-logger default encodes bytes as URL-safe base64

- Package: `python-json-logger`
- API surface: `pythonjsonlogger.json.JsonFormatter`, `pythonjsonlogger.jsonlogger.JsonFormatter`
- Candidate versions: old `3.0.1`, new `3.1.0`
- Source:
  - URL: https://nhairs.github.io/python-json-logger/latest/changelog/
  - Release/changelog section: `3.1.0` / `Changed`
  - Quote or paraphrase: The changelog says default JSON formatter encodings changed, including bytes and several object categories.
- Behavior hypothesis:
  A log record carrying `extra={"payload": b"abc"}` may serialize the bytes field differently after upgrade.
- Why this may be silent drift:
  The formatter API and logging call remain valid; the handler emits JSON in both versions, but encoded field values can change.
- Reproduction sketch:
  Attach `JsonFormatter("%(message)s %(payload)s")` to an in-memory stream handler, log a record with bytes in `extra`, and print the JSON line.
- Duplicate check:
  Similar to: no existing logging/JSON formatter card; `requests` and `httpx` cards touch JSON but not log-record formatting.
  Different because: this is local logging serialization behavior in a distinct package.
- Risk notes:
  The package reorganized modules in `3.1.0`; choose an import path that remains compatible, or reject if only renamed import paths reproduce.
- Next action:
  Prototype with `python-json-logger==3.0.1` and `==3.1.0`, checking that no import rewrite is needed.

## IDEA-20260520-015: dateparser stops trying previous locales by default

- Package: `dateparser`
- API surface: `dateparser.DateDataParser.get_date_data`, `dateparser.parse`
- Candidate versions: old `1.0.0`, new `1.1.0`
- Source:
  - URL: https://dateparser.readthedocs.io/_/downloads/en/v1.1.0/pdf/
  - Release/changelog section: `1.1.0` changelog
  - Quote or paraphrase: The changelog says parsing is deterministic and no longer tries previous locales by default.
- Behavior hypothesis:
  A parser instance used on two inputs in sequence may stop carrying locale guesses from the first parse into the second parse.
- Why this may be silent drift:
  The parser calls still return date data without requiring a new argument, but the inferred language/locale and parsed result can change.
- Reproduction sketch:
  Create one `DateDataParser`, parse a locale-specific date string, then parse an ambiguous numeric/string date and print the returned `date_obj` and locale metadata.
- Duplicate check:
  Similar to: no existing `dateparser` card; `arrow` and `django` timezone cards are temporal but different packages and APIs.
  Different because: this is date parsing locale-memory behavior, not timezone object implementation.
- Risk notes:
  Avoid current-date-relative phrases such as "yesterday"; use fixed absolute date strings and a single parser instance.
- Next action:
  Search tests or release PRs for a minimal locale carry-over fixture, then reproduce `1.0.0 -> 1.1.0`.

## IDEA-20260520-016: Pillow resize default resampling switches to BICUBIC

- Package: `pillow`
- API surface: `PIL.Image.Image.resize`
- Candidate versions: old `6.2.2`, new `7.0.0`
- Source:
  - URL: https://pillow.readthedocs.io/en/stable/releasenotes/7.0.0.html
  - Release/changelog section: `7.0.0` release notes / resampling filter default
  - Quote or paraphrase: Pillow's release notes describe changing the default resize resampling filter to BICUBIC.
- Behavior hypothesis:
  Resizing the same small generated image without passing `resample=` may produce different pixel values after upgrade.
- Why this may be silent drift:
  `Image.resize(size)` remains a valid public call and returns an image in both versions, but default interpolation changes output.
- Reproduction sketch:
  Create a deterministic RGB image in memory, call `resize((larger_width, larger_height))` without `resample`, and print a stable sample of output pixels.
- Duplicate check:
  Similar to: no existing `pillow` card; `matplotlib` idea is image-adjacent but about colormap registry object copying.
  Different because: this is pixel interpolation default behavior in Pillow.
- Risk notes:
  Older Pillow wheels may not install on the current Python; use the oldest locally installable version before `7.0.0` if `6.2.2` is unavailable.
- Next action:
  Try isolated install with exact versions; if old wheels fail, record install-risk rejection rather than widening the version range blindly.

## IDEA-20260520-017: packaging SpecifierSet adapts prerelease matching

- Package: `packaging`
- API surface: `packaging.specifiers.Specifier.contains`, `SpecifierSet.contains`, `SpecifierSet.filter`
- Candidate versions: old `25.0`, new `26.0`
- Source:
  - URL: https://packaging.pypa.io/en/stable/changelog.html
  - Release/changelog section: `26.0` / `Behavior adaptations`
  - Quote or paraphrase: The changelog records PEP 440 prerelease handling changes for specifier `contains` and `filter` methods.
- Behavior hypothesis:
  The same specifier set and candidate version list involving prereleases may include or exclude different versions after upgrade.
- Why this may be silent drift:
  The specifier APIs and arguments remain valid and return booleans or filtered iterables in both versions, but dependency selection semantics can change.
- Reproduction sketch:
  Evaluate `SpecifierSet` with prerelease and final version candidates, print `contains(...)` results and `list(filter(...))` under both versions.
- Duplicate check:
  Similar to: no existing `packaging` card.
  Different because: this is dependency-version specifier semantics, not application-library parsing, validation, or rendering.
- Risk notes:
  The changelog entry is terse; find the exact PEP 440 edge input from PR or tests before promotion.
- Next action:
  Inspect packaging PR/test cases for the minimal prerelease fixture and reproduce `25.0 -> 26.0`.

## IDEA-20260520-018: structlog default configuration adds log level processing

- Package: `structlog`
- API surface: `structlog.get_logger`, default processors, default bound logger
- Candidate versions: old `20.1.0`, new `20.2.0`
- Source:
  - URL: https://www.structlog.org/en/22.1.0/changelog.html
  - Release/changelog section: `20.2.0` / `Added` and `Changed`
  - Quote or paraphrase: The changelog says `add_log_level` became part of the default configuration and the default bound logger changed.
- Behavior hypothesis:
  Calling `structlog.get_logger().info("event")` with no explicit configuration may print or return event data with different default fields after upgrade.
- Why this may be silent drift:
  The old public call shape remains valid and logging succeeds, but default emitted event structure can change for users relying on unconfigured structlog.
- Reproduction sketch:
  Capture stdout from a process that imports structlog, calls `structlog.get_logger().info("hello")`, and prints the captured output.
- Duplicate check:
  Similar to: no existing `structlog` card; `python-json-logger` in this batch is also logging-related.
  Different because: this is structlog default processor/bound-logger behavior, not JSON formatter encoding.
- Risk notes:
  The docs state default configuration is not covered by full backward-compatibility policy, making this borderline but still local and deterministic.
- Next action:
  Try exact versions and reject if the observable difference is only a removed uncommon method rather than successful default logging output.

## REJECTED-20260520-019: simplejson allow_nan default now raises on NaN

- Package: `simplejson`
- API surface: `simplejson.dumps`, `simplejson.loads`, `JSONEncoder`, `JSONDecoder`
- Source: https://simplejson.readthedocs.io/
- Tried because:
  The docs for `3.19.0` indicate `allow_nan` was changed or added so default behavior better follows the JSON spec.
- Rejected because:
  - the most direct observable case is `dumps(float("nan"))` or `loads("NaN")`
  - the new default raises instead of returning a different successful output
  - that violates the no-exception happy-path requirement for silent drift
- What future runs should avoid: Avoid simplejson `3.18.x -> 3.19.x` `allow_nan` default changes as benchmark candidates.
- What future runs may still try: A simplejson serialization change where both versions successfully emit different JSON for the same valid input.

## REJECTED-20260520-020: PyMongo JSONMode default is prominent migration-guide behavior

- Package: `pymongo`
- API surface: `bson.json_util.dumps`, `bson.json_util.JSONOptions`
- Source: https://pymongo.readthedocs.io/en/4.0.1/migrate-to-pymongo4.html
- Tried because:
  `bson.json_util.dumps` is local, deterministic, and PyMongo 4 changes the default JSON mode from legacy to relaxed.
- Rejected because:
  - the change is under the PyMongo 4 migration guide and framed with backward-breaking migration context
  - the same guide groups it with many other major-version breaking changes
  - using it would weaken the silent-drift requirement even though no MongoDB server is needed
- What future runs should avoid: Do not use PyMongo 3.x -> 4.x default JSONMode, UUID representation, or DBRef decoding migration-guide entries as silent-drift candidates.
- What future runs may still try: A PyMongo or `bson` minor-release local serialization bugfix not under the major migration guide and not requiring a MongoDB server.

## IDEA-20260520-021: Pygments HtmlFormatter table filename row changes

- Package: `pygments`
- API surface: `pygments.highlight with HtmlFormatter(linenos='table', filename=...)`
- Candidate versions: old 2.8.1, new 2.9.0
- Source:
  - URL: https://pygments.org/docs/changelog/#version-2-9-0
  - Release/changelog section: Version 2.9.0 / Updated filename handling in HTML formatter
  - Quote or paraphrase: The changelog describes moving the filename into a separate table row when HTML table line numbers are used.
- Behavior hypothesis: The same highlight call may emit different HTML structure around line-number tables and filename spans after the formatter change.
- Why this may be silent drift: The formatter constructor and highlight call remain valid and return HTML in both versions, but snapshot HTML or CSS selectors can observe different markup without an exception.
- Reproduction sketch: Call highlight('print(1)\n', PythonLexer(), HtmlFormatter(linenos='table', filename='demo.py')) and print a compacted fragment containing filename and table rows.
- Duplicate check:
  - Similar to: No existing pygments card; markdown and mistune-like rendering areas are separate packages.
  - Different because: This targets syntax highlighter HTML table markup, not Markdown footnote ordering or SQL formatter whitespace.
- Risk notes:
- Use exact 2.8.1 -> 2.9.0; avoid lexer-token changes and compare only the documented formatter filename/table fragment.
- Next action: Try isolated reproduction and keep if both versions install cleanly.

## IDEA-20260520-022: sqlparse strip_comments preserves different whitespace

- Package: `sqlparse`
- API surface: `sqlparse.format(..., strip_comments=True)`
- Candidate versions: old 0.5.0, new 0.5.1
- Source:
  - URL: https://sqlparse.readthedocs.io/en/stable/changes.html#release-0-5-1-jul-15-2024
  - Release/changelog section: Release 0.5.1 / Bug Fixes
  - Quote or paraphrase: The changelog says strip_comments had been too greedy and removed too much whitespace; users may need strip_whitespace=True for prior behavior.
- Behavior hypothesis: Formatting the same SQL containing comments may keep line breaks or spaces that older sqlparse removed.
- Why this may be silent drift: The public format call and option name are unchanged and return strings in both versions, but formatted SQL text can differ.
- Reproduction sketch: Print sqlparse.format('select 1 -- note\nfrom t', strip_comments=True) under both versions and compare normalized repr output.
- Duplicate check:
  - Similar to: No existing sqlparse card; existing parsing/formatting cards are for markdown, yarl, json, and logging packages.
  - Different because: This is SQL comment-stripping whitespace behavior in sqlparse, not Python-Markdown footnote ordering or python-json-logger encoding.
- Risk notes:
- Stay on 0.5.0 -> 0.5.1 and avoid the 0.5.5 DoS error behavior because that introduces exceptions.
- Next action: Reproduce with a minimal SQL snippet from issue 772 behavior.

## IDEA-20260520-023: Docutils HTML5 footnotes move into aside

- Package: `docutils`
- API surface: `docutils.core.publish_parts(..., writer_name='html5')`
- Candidate versions: old 0.18.1, new 0.19
- Source:
  - URL: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-19-2022-07-05
  - Release/changelog section: Release 0.19 / Output changes / HTML5
  - Quote or paraphrase: The release notes describe HTML5 output changing to wrap footnotes and related blocks in semantic aside/nav elements.
- Behavior hypothesis: Publishing the same reStructuredText with a footnote to HTML5 may emit a different element tree around the footnote list.
- Why this may be silent drift: The publisher API and writer name remain valid and return HTML parts in both versions, but downstream snapshots or CSS selectors can see different markup.
- Reproduction sketch: Call publish_parts on a tiny document with 'Text [1]_\n\n.. [1] note' and print the body fragment containing the footnote container.
- Duplicate check:
  - Similar to: No existing docutils card; markdown and mistune are adjacent markup-rendering packages only.
  - Different because: This is reStructuredText HTML5 writer semantics, not Markdown extension ordering or template grouping.
- Risk notes:
- HTML output changes are documented under output changes, not breaking changes; verify installability of old 0.18.1 on current Python.
- Next action: Try local reproduction and keep if the fragment is stable without depending on current dates or stylesheet files.

## REJECTED-20260520-024: Mistune raw HTML escaping belongs to explicit breaking change

- Package: `mistune`
- API surface: `mistune.markdown(text)`, renderer `escape` option
- Source: https://mistune.lepture.com/en/v0.8.4/
- Tried because:
  Mistune's old documentation mentions a default `escape=True` behavior for raw HTML rendering, which initially looked like a local deterministic Markdown output drift.
- Rejected because:
  - the relevant changelog entry is for `0.7`, not `0.8.4`
  - the same entry explicitly says it includes a breaking change around HTML parsing options
  - using raw HTML escaping from this range would duplicate a prominent security/breaking-change migration rather than a silent drift
- What future runs should avoid: Avoid Mistune `0.6 -> 0.7` raw HTML parsing and `escape` default behavior as silent-drift candidates.
- What future runs may still try: A later Mistune 2.x or 3.x renderer/output bugfix where the same public call succeeds with different deterministic output and no breaking-change label.

## IDEA-20260520-025: jsonpickle make_refs False serializes repeats differently

- Package: `jsonpickle`
- API surface: `jsonpickle.encode(obj, make_refs=False)`
- Candidate versions: old 1.4.2, new 1.5.0
- Source:
  - URL: https://jsonpickle.github.io/history.html#v1-5-0
  - Release/changelog section: v1.5.0
  - Quote or paraphrase: The history says make_refs=False used to emit null for repeated objects and now serializes all instances; it calls this a minor-level behavior change.
- Behavior hypothesis: Encoding a list containing the same dict object twice with make_refs=False may produce a different JSON payload after the change.
- Why this may be silent drift: The encode function and make_refs option remain available and return JSON text in both versions, but repeated-object serialization semantics differ.
- Reproduction sketch: Create d={'x': 1}; print jsonpickle.encode([d, d], make_refs=False, unpicklable=False) under both versions.
- Duplicate check:
  - Similar to: No existing jsonpickle card; python-json-logger and simplejson cards concern logging JSON and NaN exception behavior.
  - Different because: This is object graph serialization with jsonpickle's make_refs option, not formatter JSON encoding or simplejson strictness.
- Risk notes:
- Avoid pandas/numpy extension paths and keep the object graph to built-in dict/list values.
- Next action: Reproduce exact output and confirm both versions install on the current Python.

## IDEA-20260520-026: filelock logger default level stops forcing warning

- Package: `filelock`
- API surface: `import filelock; logging.getLogger('filelock')`
- Candidate versions: old 3.3.0, new 3.3.1
- Source:
  - URL: https://py-filelock.readthedocs.io/en/latest/changelog.html#v3-3-1-2021-10-15
  - Release/changelog section: v3.3.1
  - Quote or paraphrase: The changelog says the filelock logger is left unset, whereas it was previously set to warning.
- Behavior hypothesis: Importing filelock and inspecting or using the package logger may show a different effective logging configuration under the same client code.
- Why this may be silent drift: Importing the package and using the public logging namespace succeeds in both versions, but observed logger level or emitted log filtering changes.
- Reproduction sketch: Before importing filelock, configure root logging; after import, print logging.getLogger('filelock').level and getEffectiveLevel().
- Duplicate check:
  - Similar to: No existing filelock card; structlog and python-json-logger are logging-adjacent but different packages and APIs.
  - Different because: This targets import-time package logger configuration, not structlog default processors or JSON log record serialization.
- Risk notes:
- Logger side effects are somewhat infrastructure-shaped; prefer a deterministic introspection output rather than timing lock acquisition.
- Next action: Try 3.3.0 -> 3.3.1 and decide whether logger-level drift is benchmark-worthy.

## IDEA-20260520-027: python-dotenv set_key quote output changes

- Package: `python-dotenv`
- API surface: `dotenv.set_key(..., quote_mode='auto')`
- Candidate versions: old 0.17.1, new 0.18.0
- Source:
  - URL: https://bbc2.github.io/python-dotenv/changelog/#0180-2021-06-20
  - Release/changelog section: 0.18.0 / Changed
  - Quote or paraphrase: The changelog says set_key and dotenv set switched quoting behavior, including single quotes and auto mode no longer quoting alphanumeric values.
- Behavior hypothesis: Writing the same key and value to a temporary .env file with quote_mode='auto' may produce different file text after upgrade.
- Why this may be silent drift: The set_key call remains valid and returns normally in both versions, but the persisted .env text changes under identical inputs.
- Reproduction sketch: Create a temporary .env file, call set_key(path, 'TOKEN', 'abc123', quote_mode='auto'), then print the file contents.
- Duplicate check:
  - Similar to: No existing python-dotenv card; requests and python-json-logger cover decoding/JSON formatting, not .env mutation.
  - Different because: This is local environment-file serialization behavior in python-dotenv.
- Risk notes:
- Use a temporary local file only; avoid symlink/mode behavior from 1.2.2 because those are explicitly breaking changes.
- Next action: Reproduce 0.17.1 -> 0.18.0 and keep if output differs without platform-specific filesystem details.

## IDEA-20260520-028: pathspec gitwildmatch dir star matches descendants

- Package: `pathspec`
- API surface: `PathSpec.from_lines('gitwildmatch', patterns).match_file(path)`
- Candidate versions: old 0.9.0, new 0.10.0
- Source:
  - URL: https://pypi.org/project/pathspec/0.10.0/
  - Release/changelog section: 0.10.0 / Major changes
  - Quote or paraphrase: The 0.10.0 changelog says gitwildmatch pattern dir/* is now handled the same as dir/, matching all descendants rather than only direct children.
- Behavior hypothesis: The same gitwildmatch pattern list may start matching nested descendant paths that were previously not matched.
- Why this may be silent drift: The PathSpec.from_lines and match_file calls remain valid and return booleans, but match semantics for an existing pattern change.
- Reproduction sketch: Build PathSpec.from_lines('gitwildmatch', ['dir/*']) and print match_file('dir/a.txt') and match_file('dir/sub/a.txt').
- Duplicate check:
  - Similar to: No existing pathspec card; yarl URL joining is adjacent path-ish semantics but a different package and domain.
  - Different because: This is filesystem ignore pattern matching, not URL path normalization or HTTP behavior.
- Risk notes:
- This is listed under major changes, so silent-policy fit is borderline; reject later if the project treats major-change headings as too prominent.
- Next action: Try exact versions and review whether the major-changes heading disqualifies it.

## REJECTED-20260520-029: Celery 4.0 default serializer is prominent upgrade guidance

- Package: `celery`
- API surface: `Celery app default task_serializer/result_serializer and message serialization`
- Source: https://docs.celeryq.dev/en/4.0/whatsnew-4.0.html#json-is-now-the-default-serializer
- Tried because: Celery 4.0 changed defaults from pickle to JSON, and default configuration can be inspected or exercised locally without a real broker in some eager/unit-test paths.
- Rejected because:
- Reject for this batch because the serializer change is called out in the Celery 4.0 important upgrade notes and was announced ahead of time; a meaningful task-message behavior reproduction also risks drifting into broker/task-queue setup instead of a simple local package API.
- What future runs should avoid: Do not spend another silent-drift attempt on Celery 3.1 -> 4.0 default task_serializer, result_serializer, accept_content, or task message protocol defaults.
- What future runs may still try: A minor Celery utility or canvas serialization bugfix that is local, deterministic, not under important upgrade notes, and does not require a broker.

## REJECTED-20260520-030: cattrs sequence structuring migrations are explicit

- Package: `cattrs`
- API surface: `Converter.structure for Sequence and abstract Set annotations`
- Source: https://catt.rs/en/stable/migrations.html
- Tried because: cattrs migration notes list deterministic local behavior changes such as sequences structuring into tuples and abstract sets structuring into frozensets.
- Rejected because:
- Reject because these items are documented on the official Migrations page as backwards-incompatible behavior with restoration recipes, so they are not silent enough for this discovery policy.
- What future runs should avoid: Avoid cattrs 25.1.0 through 25.3.0 migration-page default structuring behavior as silent-drift candidates.
- What future runs may still try: A cattrs minor bugfix outside the Migrations page where the same Converter.structure or unstructure call returns different successful data without a prominent compatibility warning.

## IDEA-20260520-031: Black 2024 stable style changes formatted output

- Package: `black`
- API surface: `black.format_str, black.FileMode, black CLI formatting output`
- Candidate versions: old 23.12.1, new 24.1.0
- Source:
  - URL: https://black.readthedocs.io/en/stable/change_log.html
  - Release/changelog section: 24.1.0 / Highlights / Stable style
  - Quote or paraphrase: The Black changelog says 24.1.0 introduces the 2024 stable style and lists output-affecting formatting changes such as wrapping if-else expressions and standardizing Unicode escape hex case.
- Behavior hypothesis: The same Python source passed through black.format_str may produce different formatted text after the stable-style rollover.
- Why this may be silent drift: The public formatter API and CLI invocation remain valid and return formatted text in both versions; code snapshots or formatting checks can observe changed output without an exception.
- Reproduction sketch: Call black.format_str on a short snippet using an if-else expression or uppercase Unicode escape hex sequence with black.FileMode(), then print the formatted result.
- Duplicate check:
  - Similar to: No existing black card; pytest and Pygments are tool-output adjacent but different packages and APIs.
  - Different because: This targets Python source formatter stable-style output, not pytest reporting or syntax-highlighter HTML markup.
- Risk notes:
- Formatter output changes are expected for Black yearly style releases, so silent-policy fit needs review; still local and deterministic.
- Next action: Try exact versions 23.12.1 -> 24.1.0 and pick one minimal stable-style fixture.

## IDEA-20260520-032: Loguru serialized JSON stops escaping non-ASCII

- Package: `loguru`
- API surface: `loguru.logger.add(..., serialize=True), logger.info`
- Candidate versions: old 0.5.3, new 0.6.0
- Source:
  - URL: https://loguru.readthedocs.io/en/latest/project/changelog.html
  - Release/changelog section: 0.6.0 (2022-01-29)
  - Quote or paraphrase: The 0.6.0 changelog says Loguru prevents non-ASCII characters from being escaped when logging JSON messages with serialize=True.
- Behavior hypothesis: The same serialized log event containing a non-ASCII message may write a different raw JSON string, escaping in old versions and preserving the character in the new version.
- Why this may be silent drift: The logger.add and logger.info calls remain valid and logging succeeds in both versions, while the raw serialized output changes.
- Reproduction sketch: Attach an io.StringIO sink with serialize=True, log a fixed non-ASCII message, then print whether the raw buffer contains a Unicode escape sequence.
- Duplicate check:
  - Similar to: structlog and python-json-logger cards are logging-adjacent.
  - Different because: This is Loguru serialized JSON escaping behavior, not structlog default processors or python-json-logger bytes encoding.
- Risk notes:
- Avoid comparing timestamps in the serialized record; inspect only the raw escaping marker around a deterministic message.
- Next action: Try 0.5.3 -> 0.6.0 in isolated environments and normalize away timestamp fields.

## IDEA-20260520-033: Hypothesis creates gitignore in example database directory

- Package: `hypothesis`
- API surface: `hypothesis settings example database, DirectoryBasedExampleDatabase side effects`
- Candidate versions: old 6.151.14, new 6.152.0
- Source:
  - URL: https://hypothesis.readthedocs.io/en/latest/changelog.html
  - Release/changelog section: 6.152.0 - 2026-04-14
  - Quote or paraphrase: The Hypothesis changelog says it now automatically creates a .gitignore containing * inside the .hypothesis directory.
- Behavior hypothesis: Running the same local Hypothesis test or database-touching code may leave an extra .hypothesis/.gitignore file after upgrade.
- Why this may be silent drift: The public test/decorator API still succeeds, but deterministic filesystem side effects in the local project directory change.
- Reproduction sketch: In a temporary working directory, run a tiny @given test or explicit DirectoryBasedExampleDatabase usage, then print whether .hypothesis/.gitignore exists and its contents.
- Duplicate check:
  - Similar to: No existing Hypothesis card; pytest card is test-tool adjacent only.
  - Different because: This is Hypothesis local example-database filesystem behavior, not pytest terminal reporting.
- Risk notes:
- Keep the reproduction in a temporary directory and avoid relying on random generated values; only inspect the database directory side effect.
- Next action: Prototype 6.151.14 -> 6.152.0 and confirm which minimal public call triggers database creation.

## IDEA-20260520-034: lxml addnext preserves moved tail text

- Package: `lxml`
- API surface: `lxml.etree._Element.addnext, lxml.etree.tostring`
- Candidate versions: old 4.4.3, new 4.5.0
- Source:
  - URL: https://lxml.de/6.0/changes-6.0.4.html
  - Release/changelog section: 4.5.0 (2020-01-29) / Bugs fixed
  - Quote or paraphrase: The lxml changelog says tail text of nodes removed from a document using item deletion disappeared silently instead of staying with the removed node.
- Behavior hypothesis: The same element deletion or sibling-move operation may serialize different tail text around the affected node after the bug fix.
- Why this may be silent drift: Element manipulation and serialization APIs remain valid and return normally, while serialized XML/HTML text can change deterministically.
- Reproduction sketch: Build a small tree with an element carrying tail text, remove or move that child with the documented operation, then print etree.tostring(root, encoding=str).
- Duplicate check:
  - Similar to: No existing lxml card; docutils and Bleach-adjacent rejected leads concern markup output but not lxml tree mutation.
  - Different because: This is XML element tail-text retention during local tree mutation, not Markdown/reStructuredText rendering or HTML sanitizing.
- Risk notes:
- Old lxml wheels for current Python may be a problem; if 4.4.3 cannot install locally, try the nearest installable pre-4.5 version or reject for install risk.
- Next action: Try isolated 4.4.3 -> 4.5.0 and verify a minimal tree mutation that succeeds in both versions.

## IDEA-20260520-035: RDFLib GROUP_CONCAT empty separator changes output

- Package: `rdflib`
- API surface: `rdflib.Graph.query` with SPARQL `GROUP_CONCAT(...; separator="")`
- Candidate versions: old 6.3.2, new 7.0.0
- Source:
  - URL: https://rdflib.readthedocs.io/en/stable/changelog/
  - Release/changelog section: 2023-08-02 RELEASE 7.0.0 / fix: GROUP_CONCAT handling of empty separator
  - Quote or paraphrase: The RDFLib changelog says GROUP_CONCAT previously treated an empty separator like it was not set, effectively using a single space; the fix makes an empty separator concatenate with nothing between values.
- Behavior hypothesis: The same in-memory SPARQL query using `GROUP_CONCAT(...; separator="")` may return a different literal string after upgrade.
- Why this may be silent drift: Graph construction and Graph.query call shape remain valid and the query completes locally, but aggregate output changes.
- Reproduction sketch: Create an in-memory Graph with two values for one subject, run `SELECT (GROUP_CONCAT(?v; separator="") AS ?out)`, and print the returned literal.
- Duplicate check:
  - Similar to: No existing RDFLib card; sqlparse and docutils cards are text-output adjacent only.
  - Different because: This targets SPARQL aggregate semantics in RDFLib, not SQL formatting or markup rendering.
- Risk notes:
- RDFLib 7.0.0 is a major release with explicit breaking sections; this specific fix is not labeled breaking but silent-policy fit is borderline.
- Next action: Try 6.3.2 -> 7.0.0 locally and reject if the major-release context is considered too prominent.

## IDEA-20260520-036: odfdo Paragraph formats whitespace by default

- Package: `odfdo`
- API surface: `odfdo.text.Paragraph, Paragraph.append, Header, Span text construction`
- Candidate versions: old 3.7.7, new 3.8.0
- Source:
  - URL: https://jdum.github.io/odfdo/CHANGES.html
  - Release/changelog section: 3.8.0 - 2024-08-25 / Changed
  - Quote or paraphrase: The odfdo changelog says Paragraph text appending now defaults to formatted handling that converts line breaks, tabs, and repeated spaces to ODF tags.
- Behavior hypothesis: Constructing the same Paragraph from text containing newlines, tabs, or repeated spaces may produce different XML text after upgrade.
- Why this may be silent drift: The constructor and append APIs still succeed with the same inputs, but deterministic serialized ODF/XML content changes.
- Reproduction sketch: Create Paragraph(word1\nword2) or Paragraph with repeated spaces, serialize the element XML, and print the compact XML fragment.
- Duplicate check:
  - Similar to: No existing odfdo card; docutils and python-dotenv cards both concern local text serialization but different packages and surfaces.
  - Different because: This is ODF XML paragraph whitespace serialization, not reStructuredText HTML5 output or .env quoting.
- Risk notes:
- Package is less common than prior targets; confirm PyPI installability and public import paths before promoting.
- Next action: Try 3.7.7 -> 3.8.0 with a minimal Paragraph XML serialization fixture.

## REJECTED-20260520-037: natsort default numeric parsing is explicit legacy incompatibility

- Package: `natsort`
- API surface: `natsort.natsorted default alg behavior`
- Source: https://natsort.readthedocs.io/en/8.2.0/changelog.html#id33
- Tried because: natsort 4.0.0 changed default sorting from signed floats to unsigned integers, which could produce deterministic local output differences for strings with signed numbers.
- Rejected because:
- Reject for this batch because the changelog explicitly calls the default change backwards-incompatible, the version range is from 2015, and the project documentation already frames it as a major semantic switch.
- What future runs should avoid: Avoid natsort 3.x -> 4.0 default signed-float versus unsigned-int sorting as a silent-drift candidate.
- What future runs may still try: A later natsort minor bugfix where natsorted returns a different successful order without an explicit backwards-incompatible heading.

## REJECTED-20260520-038: Bleach sanitizer rewrites are explicit incompatible output changes

- Package: `bleach`
- API surface: `bleach.clean, bleach.Cleaner.clean, bleach.linkify`
- Source: https://bleach.readthedocs.io/en/stable/changes.html and https://bleach.readthedocs.io/en/v5.0.0/changes.html
- Tried because: Bleach has deterministic local HTML sanitizing output changes, including a 2.0 clean rewrite and 5.0 attribute-order preservation.
- Rejected because:
- Reject because the clearest output drifts are under Backwards incompatible changes, security-driven rewrites, or major sanitizer migration notes; this is too prominently announced for the silent policy.
- What future runs should avoid: Do not reuse Bleach 2.0 clean rewrite, attribute callable arity, CSS sanitizer rewrite, or 5.0 attribute-order preservation as silent-drift candidates.
- What future runs may still try: A narrow Bleach patch-level rendering bugfix where bleach.clean succeeds in both versions and the source is not under backward-incompatible or security sections.

## REJECTED-20260520-039: xlrd 2.0 encoding default is buried inside major removal release

- Package: `xlrd`
- API surface: `xlrd.open_workbook default CODEPAGE fallback encoding`
- Source: https://xlrd.readthedocs.io/en/latest/changes.html
- Tried because: xlrd 2.0.0 changed the default encoding used when no CODEPAGE record is present from ascii to iso-8859-1, which could be locally observable with a crafted .xls fixture.
- Rejected because:
- Reject because the same 2.0.0 entry prominently removes all non-.xls support and is a major compatibility release; a valid reproduction also requires a binary workbook fixture with a missing CODEPAGE record, adding fixture fragility.
- What future runs should avoid: Avoid xlrd 1.x -> 2.0.0 CODEPAGE fallback encoding and .xlsx removal as silent-drift candidates.
- What future runs may still try: A smaller xlrd parsing or formatting bugfix with a simple checked-in .xls fixture, no major removal context, and successful behavior in both versions.

## REJECTED-20260520-040: pyparsing empty-string parse action fix is exception-path only

- Package: `pyparsing`
- API surface: `pyparsing.Literal.add_parse_action, ParseResults named access`
- Source: https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_1.html
- Tried because: Pyparsing 3.1 notes that parse actions returning an empty string for a named expression now preserve the result name instead of later raising KeyError.
- Rejected because:
- Reject because the observable difference is that old code raises KeyError when accessing the named result while the new version succeeds; this violates the no-exception happy-path requirement for silent drift.
- What future runs should avoid: Avoid pyparsing 3.0 -> 3.1 named empty-string parse-action behavior as a benchmark candidate.
- What future runs may still try: A pyparsing fix where parse_string and subsequent public result inspection both succeed in old and new versions but produce different deterministic tokens or dumps.

## IDEA-20260520-041: Beautiful Soup script get_text semantics change

- Package: `beautifulsoup4`
- API surface: `bs4.BeautifulSoup(...).script.get_text()`, `.strings`, `.stripped_strings`
- Candidate versions: old `4.9.3`, new `4.10.0`
- Source:
  - URL: https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.html?highlight=select#get-text
  - Release/changelog section: Documentation notes for `get_text()` behavior as of `4.9.0` and `4.10.0`
  - Quote or paraphrase: The docs say script/style/template contents were generally not treated as document text from `4.9.0`, while `4.10.0` changed direct tag-level text handling so calling `script.get_text()` uses a tag-specific notion of text.
- Behavior hypothesis:
  Same code parsing a local HTML string and calling `soup.script.get_text()` may return different text around JavaScript contents after upgrading.
- Why this may be silent drift:
  The constructor, parser name, and `get_text()` call remain valid and local; the output text can change without exceptions or network access.
- Reproduction sketch:
  Parse `"<html><script>var x = 1;</script><p>visible</p></html>"` with `html.parser`, then print `soup.get_text("|")`, `soup.script.get_text("|")`, and `list(soup.script.strings)`.
- Duplicate check:
  Similar to: No existing `beautifulsoup4` card; `bleach`, `docutils`, and `lxml` are markup-adjacent but different packages and APIs.
  Different because: This targets Beautiful Soup tree text extraction, not sanitizing, HTML5 writer output, or lxml tail text mutation.
- Risk notes:
  Keep parser fixed to built-in `html.parser`; avoid `lxml` or `html5lib` parser variation.
- Next action:
  Try `4.9.3 -> 4.10.0` in isolated environments and keep if direct script tag output differs while both calls succeed.

## IDEA-20260520-042: fsspec default file cache strategy changes

- Package: `fsspec`
- API surface: `fsspec.open`, `fsspec.spec.AbstractBufferedFile`, default cache type for buffered reads
- Candidate versions: old `0.8.7`, new `0.9.0`
- Source:
  - URL: https://filesystem-spec.readthedocs.io/en/stable/changelog.html#id61
  - Release/changelog section: `0.9.0`
  - Quote or paraphrase: The changelog says the default file caching strategy changed to `fsspec.caching.ReadAheadCache`.
- Behavior hypothesis:
  Opening the same local or memory-backed file through fsspec without specifying `cache_type` may expose a different cache implementation and read-ahead behavior.
- Why this may be silent drift:
  The public `fsspec.open(...).open()` call still returns a readable file object, but cache object type and seek/read side effects can change.
- Reproduction sketch:
  Create a temporary local file, open it with `fsspec.open(path, mode="rb").open()`, read a few bytes, and print `type(file.cache).__name__` plus deterministic read/seek observations.
- Duplicate check:
  Similar to: No existing `fsspec` card.
  Different because: This is file abstraction cache behavior, not package manager, HTTP, URL, or pathlib-like path matching.
- Risk notes:
  Avoid HTTP filesystems or cloud backends; keep the test on a temporary local file.
- Next action:
  Prototype `0.8.7 -> 0.9.0`; reject if the cache type is not public enough or local file paths bypass the changed cache layer.

## IDEA-20260520-043: coverage JSON report stops counting module docstrings as executed

- Package: `coverage`
- API surface: `coverage.Coverage`, `Coverage.json_report`, `coverage json`
- Candidate versions: old `7.13.0`, new `7.13.1`
- Source:
  - URL: https://coverage.readthedocs.io/en/latest/changes.html#version-7-13-1-2025-12-28
  - Release/changelog section: `Version 7.13.1`
  - Quote or paraphrase: The changelog says JSON reports used to include module docstrings as executed lines, and that this was fixed to match other reports.
- Behavior hypothesis:
  Running the same one-file local script under coverage and producing JSON may change the reported executed line numbers for a module-level docstring.
- Why this may be silent drift:
  Coverage collection and JSON reporting succeed in both versions, but downstream tools reading the JSON report can observe different executed line data.
- Reproduction sketch:
  Write a temporary module whose first statement is a module docstring and a simple assignment, run it through `coverage run`, then print the JSON report entry's executed lines.
- Duplicate check:
  Similar to: `pytest` and `pytest-cov` territory only in broad test-tool category; no existing `coverage` card.
  Different because: This targets coverage.py JSON report semantics, not pytest terminal summary output.
- Risk notes:
  Avoid combining with pytest; use `coverage.Coverage` or `python -m coverage` directly on a temporary file.
- Next action:
  Try exact versions `7.13.0` and `7.13.1`, then decide whether JSON report side effects are acceptable benchmark outputs.

## IDEA-20260520-044: mypy default cache format switches to binary and SQLite

- Package: `mypy`
- API surface: `mypy.api.run`, `python -m mypy`, default incremental cache files
- Candidate versions: old `1.19.0`, new `2.0.0`
- Source:
  - URL: https://mypy.readthedocs.io/en/stable/changelog.html
  - Release/changelog section: `Mypy 2.0` / Performance Improvements
  - Quote or paraphrase: The release notes say mypy now uses fixed-format cache by default, and SQLite cache is enabled by default.
- Behavior hypothesis:
  Running mypy on the same tiny local module with default incremental cache settings may create different cache file names and formats.
- Why this may be silent drift:
  The CLI and `mypy.api.run` invocation remain valid and return normal type-check output, but the local `.mypy_cache` side effects change.
- Reproduction sketch:
  In a temporary directory, write `x: int = 1`, run `mypy.api.run([path])`, and print selected `.mypy_cache` file suffixes or whether SQLite/fixed-format cache artifacts exist.
- Duplicate check:
  Similar to: `black`, `ruff`, and `pytest` are tool-output adjacent.
  Different because: This targets mypy cache side effects, not Python source formatting, lint target-version selection, or test-runner reporting.
- Risk notes:
  The cache implementation is a tool side effect; prefer artifact names or documented flags over parsing binary content.
- Next action:
  Try `1.19.0 -> 2.0.0`; reject if the environment does not support current mypy wheels or if cache artifacts are too implementation-shaped.

## IDEA-20260520-045: Ruff default Python target version advances to 3.9

- Package: `ruff`
- API surface: `ruff check` default target version inference, Python syntax diagnostics
- Candidate versions: old `0.7.4`, new `0.8.0`
- Source:
  - URL: https://github.com/astral-sh/ruff/releases/tag/0.8.0
  - Release/changelog section: `0.8.0` release notes
  - Quote or paraphrase: The release notes say Ruff defaults to Python 3.9 instead of 3.8 when no explicit target version or `requires-python` is configured.
- Behavior hypothesis:
  Running `ruff check` on the same local source file without configuration may stop reporting a Python-3.8-only syntax issue after the default target moves to 3.9.
- Why this may be silent drift:
  The CLI command and input file are unchanged, but diagnostic output changes because the implicit language target changed.
- Reproduction sketch:
  In an empty temp project with no config, run `ruff check` on a file using a Python 3.9 syntax feature such as built-in generic annotations, and print the diagnostic count or output.
- Duplicate check:
  Similar to: `black` stable style and `mypy` tool-output/cache cards.
  Different because: This is linter target-version inference, not formatter output or type-check cache artifacts.
- Risk notes:
  Ruff's minor releases intentionally carry breaking changes by project policy, so silent-policy fit is borderline; pin exact versions and avoid config files.
- Next action:
  Try `0.7.4 -> 0.8.0`; reject if the release note is judged too prominent or if chosen input depends on host Python parsing.

## IDEA-20260520-046: Rich empty color environment variables no longer disable color

- Package: `rich`
- API surface: `rich.console.Console.print`, `NO_COLOR`, `FORCE_COLOR` environment handling
- Candidate versions: old `13.9.4`, new `14.0.0`
- Source:
  - URL: https://github.com/Textualize/rich/releases/tag/v14.0.0
  - Release/changelog section: `14.0.0` / Changed
  - Quote or paraphrase: The release notes say empty `NO_COLOR` and `FORCE_COLOR` environment variables are now treated as disabled.
- Behavior hypothesis:
  With `NO_COLOR` set to an empty string, the same `Console(force_terminal=True).print("[red]x[/red]")` code may emit ANSI color in the new version but not in the old version.
- Why this may be silent drift:
  The print call succeeds locally in both versions, while captured console output bytes can change under the same environment.
- Reproduction sketch:
  Set `os.environ["NO_COLOR"] = ""`, print styled text to an `io.StringIO` console with `force_terminal=True`, and print whether ANSI escape sequences are present.
- Duplicate check:
  Similar to: No existing `rich` card; `loguru`, `structlog`, and `python-json-logger` are terminal/log-output adjacent only.
  Different because: This is terminal styling environment semantics, not logging serialization or default processors.
- Risk notes:
  The release text says this drove the major version bump, so the candidate is borderline for silent delivery even though it is local and deterministic.
- Next action:
  Prototype exact versions and decide whether the major-bump prominence disqualifies it.

## IDEA-20260520-047: json5 custom encoder output indentation is fixed

- Package: `json5`
- API surface: `json5.dumps`, `json5.dump` with custom encoder / `cls`-style object conversion
- Candidate versions: old `0.12.0`, new `0.12.1`
- Source:
  - URL: https://pypi.org/project/json5/
  - Release/changelog section: `v0.12.1`
  - Quote or paraphrase: The release history says `v0.12.1` fixes a case where objects returned from a custom encoder were not indented properly.
- Behavior hypothesis:
  The same `json5.dumps(..., indent=2, cls=...)` or custom-encoder path may produce differently indented JSON5 text after the bug fix.
- Why this may be silent drift:
  Serialization completes in both versions with the same call shape, but text output can change in a deterministic local fixture.
- Reproduction sketch:
  Define a tiny custom encoder that converts a custom object to a nested dict/list, call `json5.dumps(obj, indent=2, cls=Encoder)`, and print the formatted output.
- Duplicate check:
  Similar to: `simplejson`, `jsonpickle`, `python-json-logger`, and `requests` have JSON-adjacent cards.
  Different because: This is JSON5 custom encoder formatting, not NaN policy, object reference handling, logging JSON, or response decoding.
- Risk notes:
  Need to inspect the package's current custom-encoder API because `cls` typing was also mentioned near this release; reject if the old call path raises.
- Next action:
  Try `0.12.0 -> 0.12.1` with the issue-backed encoder shape and keep only if both versions serialize successfully.

## REJECTED-20260520-048: PyJWT 2.0 encode return type is too prominent

- Package: `pyjwt`
- API surface: `jwt.encode`
- Source: https://pyjwt.readthedocs.io/en/stable/changelog.html#v2-0-0
- Tried because:
  PyJWT 2.0 says `jwt.encode(...)` returns a string instead of bytes, which is a deterministic local return-value change with the same public function.
- Rejected because:
  - the behavior is listed directly in the major `v2.0.0` changed section
  - nearby 2.0 entries include removed CLI/deprecated APIs and required algorithm changes
  - using it would make the benchmark look like a major-version migration check, not silent drift
- What future runs should avoid: Avoid PyJWT `1.7.1 -> 2.0.0` `jwt.encode` bytes-to-string behavior and decode algorithm requirement changes.
- What future runs may still try: A later patch/minor PyJWT claim formatting or header parsing fix where encode/decode succeeds in both versions and the source is not a prominent migration item.

## REJECTED-20260520-049: Invoke MockContext repeat default is explicitly incompatible

- Package: `invoke`
- API surface: `invoke.context.MockContext(..., repeat=...)`
- Source: https://www.pyinvoke.org/changelog.html#id62
- Tried because:
  Invoke 2.0 notes that `MockContext` changed the default for its `repeat` init keyword from `False` to `True`, which could alter local test helper behavior without external dependencies.
- Rejected because:
  - the same changelog section explicitly warns that the scenario is backwards incompatible
  - the affected API is a testing/mock helper rather than a normal runtime behavior path
  - the release bundles several prominent 2.0 compatibility warnings
- What future runs should avoid: Do not use Invoke 1.x -> 2.0 `MockContext.repeat`, `Task.argspec`, or `Config` compatibility changes as silent-drift candidates.
- What future runs may still try: A non-warning Invoke bugfix where `Context.run` or parser output succeeds in both versions and changes deterministic stdout/stderr.

## REJECTED-20260520-050: platformdirs directory moves are labeled BREAKING

- Package: `platformdirs`
- API surface: `platformdirs.user_config_dir`, `platformdirs.user_log_dir`, `platformdirs.site_cache_dir`
- Source: https://platformdirs.readthedocs.io/en/latest/changelog.html
- Tried because:
  platformdirs has local deterministic path-returning APIs and several versioned directory changes on macOS and Unix.
- Rejected because:
  - the relevant macOS config and Unix log-directory changes are explicitly prefixed `BREAKING`
  - some outputs are OS-specific, adding platform qualification to a case that is already too prominent
  - later directory changes are either additive API or reversions under clear changelog headings
- What future runs should avoid: Avoid platformdirs `2.0.0`, `2.6.0`, `3.0.1`, and `3.2.0` config/log directory path changes as silent-drift candidates.
- What future runs may still try: A narrow platformdirs bugfix not labeled breaking, ideally on a deterministic non-OS-specific path helper or with a clearly controlled platform fixture.

## ACCEPTED-20260519-001: httpx_json_request_body_compact

- Case id: `httpx_json_request_body_compact`
- Package: `httpx`
- API surface: `httpx.Request(json=...)`
- Versions: old 0.27.2, new 0.28.0
- Source: https://github.com/encode/httpx/blob/master/CHANGELOG.md
- Reproduction path: data\reproductions\httpx-json-request-body-compact\attempt_001\result.json
- Oracle path: data\oracle\httpx_json_request_body_compact\oracle_spec.yaml
- Package path: data\packages\httpx_json_request_body_compact
- Audit path: data\audit\httpx_json_request_body_compact.json
- Why it is non-duplicate: Promotes IDEA-20260519-001; this covers local HTTP request JSON serialization, not the existing pandas, pydantic, or scikit-learn anchors.
- Follow-up ideas nearby:
- Try IDEA-20260519-002: Jinja groupby default case-insensitive behavior.

## RUN-20260520-RAW-LANGUAGE-PYTHON: independent Python agent batch

- Target: 10 Python-language candidates.
- Result: 10/10 candidates returned by the independent Python agent.
- Language judgment: Python has abundant candidate material; no exhaustion judgment.
- Important de-dupe note:
  - This is a raw language-agent batch, not a promoted fresh discovery batch.
  - Several rows overlap with existing accepted cases, curated local anchors, rejected lessons, or previously explored package families.
  - Before promotion, run a duplicate check against the entire Python idea bank and existing `data/curated`, `data/packages`, and `cases` directories.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| PY-SD-001 | NumPy | Scalar and array dtype promotion | 1.26.x -> 2.0.0 | https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html#changes-to-numpy-data-type-promotion | NEP 50 changes mixed-dtype promotion, so identical arithmetic can return different dtypes and lower/higher precision results. | Expressions still succeed; only dtype, rounding, overflow, or downstream branch behavior changes. | Compare `np.float32(3) + 3.` and `np.array([3], dtype=np.float32) + np.float64(3)`; print dtype and value repr. | High |
| PY-SD-002 | pandas | `DataFrame.groupby(..., sort=False)` with ordered categorical grouper | 1.5.x -> 2.0.0 | https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.groupby.html | Ordered categoricals no longer force category-order sorting when `sort=False`, so aggregation index order follows input observation order. | Aggregated values are valid; only row/index order drifts. | Build ordered categorical categories `["low", "med", "high"]` with rows `["high", "low"]`; compare groupby index order. | High |
| PY-SD-003 | SciPy | `scipy.stats.mode` with omitted `keepdims` | 1.10.x -> 1.11.0 | https://docs.scipy.org/doc/scipy-1.10.1/reference/generated/scipy.stats.mode.html | Default `keepdims` changes from legacy axis-retaining behavior to `False`, changing result shape. | `ModeResult` returns normally; broadcasting or indexing may silently target different dimensions. | Run `stats.mode(np.array([[1,2],[1,3]]), axis=0).mode.shape` across versions. | High |
| PY-SD-004 | scikit-learn | `sklearn.cluster.KMeans(n_init omitted)` | 1.3.x -> 1.4.0 | https://scikit-learn.org/1.4/modules/generated/sklearn.cluster.KMeans.html | Default `n_init` changes from `10` to `"auto"`; with `init="k-means++"` this reduces runs to 1. | Model fitting succeeds and returns plausible clusters; only model output quality/assignment drifts. | Fit `KMeans(n_clusters=3, random_state=0)` on a dataset with local minima; compare `inertia_` and labels. | High |
| PY-SD-005 | Polars | `DataFrame.join` null-key matching | 0.19.x -> 0.20.0 | https://docs.pola.rs/releases/upgrade/0.20/ | Default joins stop matching null keys, so null-null matches disappear unless null matching is explicitly enabled. | Query succeeds; result has fewer rows with no warning at call site. | Join two frames on a nullable key using `how="inner"`; compare row count. | High |
| PY-SD-006 | Dask | Dask DataFrame string dtype inference/conversion | before 2023.7.1 -> 2023.7.1 with pandas>=2 and pyarrow>=12 | https://docs.dask.org/en/stable/changelog.html#v2023-7-1 | Text columns using pandas `object` dtype auto-convert to `string[pyarrow]`, changing dtypes and null/string backend behavior. | Lazy computations still run; schema and null semantics shift based on installed optional dependencies. | Compare `dd.from_pandas(pd.DataFrame({"s":["a", None]}), npartitions=1).dtypes` with pyarrow installed. | High |
| PY-SD-007 | Pydantic | `BaseModel.model_dump` / nested subclass serialization | 1.10.x -> 2.0.0 | https://docs.pydantic.dev/2.0/migration/ | Nested fields annotated as a base model now dump only fields declared on the annotated type, omitting subclass-only fields. | Serialization succeeds; JSON/dict payload silently loses fields. | Define `Base(a)`, `Sub(Base, b)`, wrapper field `x: Base`; compare dumping `Wrap(x=Sub(a=1,b=2))`. | High |
| PY-SD-008 | SQLAlchemy | Core `Connection.execute` DML without explicit commit | 1.4 legacy behavior -> 2.0.0 | https://docs.sqlalchemy.org/20/changelog/migration_20.html#library-level-but-not-driver-level-autocommit-removed-from-both-core-and-orm | Library-level autocommit is removed, so inserts/updates that used to persist may be rolled back when the connection closes. | `execute` returns successfully; missing write is observed only on a later read. | Insert into SQLite without explicit `begin` or `commit`, close connection, then query from a new connection. | High |
| PY-SD-009 | Cython | Compiler default `language_level` for `.pyx` files | 0.29.x -> 3.0.0 | https://docs.cython.org/en/latest/src/userguide/migrating_to_cy30.html#python-3-syntax-semantics | Files without explicit `language_level` now use Python 3 semantics by default, changing division and other language-level behavior. | Extension can build and import; numeric results differ at runtime. | Compile `.pyx` containing `def div(a, b): return a / b` with no directive; call `div(3, 2)`. | Medium-high |
| PY-SD-010 | attrs | Generated equality method for `attrs.define` / `attr.s` classes | <24.1.0 -> 24.1.0 | https://www.attrs.org/en/24.1.0/changelog.html | Generated `__eq__` changed from tuple comparison to chained attribute comparisons, affecting values equal by identity but not by value, such as shared `float("nan")`. | Equality returns a boolean either way; cache keys, dedupe, or tests can silently flip. | `nan=float("nan")`; define `@attrs.define class A: x: float`; compare `A(nan) == A(nan)`. | High |

### Verification updates for raw Python batch

| Date | ID | Status | Evidence |
|---|---|---|---|
| 2026-05-20 | PY-SD-010 | Verified by Python reproduction pipeline | Source checked against attrs 24.1.0 changelog. Reproduction result: `data\verification\python_attrs_nan_equality\attempt_002\result.json`. Old `attrs==23.2.0` returns equality `true` for two boxes sharing the same `nan`; new `attrs==24.1.0` returns `false`. Both install and run successfully; stdout differs. |
| 2026-05-21 | PY-SD-010 | Re-verified in current environment | Reproduction result: `data\verification\python_attrs_nan_equality\attempt_003\result.json`; keep=true. |
