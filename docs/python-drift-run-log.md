# Python Drift Run Log

Append-only batch notes for model-guided Python silent-drift discovery.

## 2026-05-19: v0.11.0 pre-run preparation

- Model/operator: Codex
- Search budget: not started
- Packages searched: none
- Ideas added: 0
- Ideas rejected: 0
- Cases promoted: 0
- Cases accepted: 0
- Notes:
  - Markdown memory helpers were implemented and pushed in `v0.11.0`.
  - Readiness and next-run brief files were generated.
  - The real discovery/search loop is intentionally still unopened.

## 2026-05-19: Python autodiscovery pilot batch 001

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched: `httpx`, `jinja2`, `werkzeug`, `starlette`, `babel`, `click`, `networkx`, `attrs`, `urllib3`, `fastapi`
- Ideas added:
  - `IDEA-20260519-001`: `httpx` JSON request body compact serialization
  - `IDEA-20260519-002`: `jinja2` `groupby` default becomes case-insensitive
  - `IDEA-20260519-003`: `werkzeug.http.dump_cookie` path default transiently drops slash
  - `IDEA-20260519-004`: `starlette.responses.FileResponse` chunk size default increases
  - `IDEA-20260519-005`: `babel.core.Locale.number_symbols` gains numbering-system layer
  - `IDEA-20260519-006`: `click.option` flag default preservation changes callback value
- Ideas rejected:
  - `REJECTED-20260519-007`: NetworkX 3.0 matrix-to-array migration is too prominently announced
  - `REJECTED-20260519-008`: attrs `@define` on-setattr converters are explicit breaking change
  - `REJECTED-20260519-009`: urllib3 TLS minimum default needs network-like SSL context and is prominent
  - `REJECTED-20260519-010`: FastAPI `strict_content_type` is explicitly marked breaking
- Cases promoted: 0
- Cases accepted: 0
- Notes:
  - No code files were changed.
  - Search stayed inside Python package/library drift discovery.
  - Existing repository anchors for pandas, pydantic, scikit-learn, polars, and numpy were avoided.
  - Best next reproduction candidates are `httpx`, `jinja2`, `werkzeug`, and `click`; `babel` is borderline because the changelog says "possibly backwards incompatible".


## RUN-20260519: 2026-05-20: Python autodiscovery pilot batch 002

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched:
- matplotlib
- requests
- pytest
- django
- flask
- arrow
- sqlalchemy
- pyyaml
- marshmallow
- aiohttp
- Ideas added:
- IDEA-20260520-001: matplotlib get_cmap returns a copy
- IDEA-20260520-002: requests application/json defaults to UTF-8 decoding
- IDEA-20260520-003: pytest default -r short summary reports failures/errors
- IDEA-20260520-004: Django default timezone object switches to zoneinfo
- IDEA-20260520-005: Flask session cookie domain stops using SERVER_NAME
- IDEA-20260520-006: Arrow timezone objects migrate from pytz to ZoneInfo
- Ideas rejected:
- REJECTED-20260520-007: SQLAlchemy Row containment is prominent 2.0 migration behavior
- REJECTED-20260520-008: PyYAML default loader and flow-style changes are explicit incompatibilities
- REJECTED-20260520-009: marshmallow TimeDelta float preservation is explicitly backward-incompatible
- REJECTED-20260520-010: aiohttp ClientTimeout sock_connect default is under breaking-change heading
- Cases promoted to reproduction:
- 0
- Cases accepted into benchmark:
- 0
- Notes:
- No code files were changed; search stayed inside Python package/library drift discovery.
- Avoided prior idea-bank packages plus local case anchors for pandas, pydantic, scikit-learn, numpy, and polars.
- Best next reproduction candidates: matplotlib, requests, Flask, Arrow; Django is plausible but has Python-version/setup risk; pytest needs policy review because the deterministic run returns a failing test exit code.

## RUN-20260520: Python autodiscovery pilot batch 003

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched:
  - `markdown`
  - `multidict`
  - `yarl`
  - `python-json-logger`
  - `dateparser`
  - `pillow`
  - `packaging`
  - `structlog`
  - `simplejson`
  - `pymongo`
- Ideas added:
  - `IDEA-20260520-011`: Python-Markdown footnotes order by reference occurrence
  - `IDEA-20260520-012`: multidict `popitem` removes latest entry
  - `IDEA-20260520-013`: yarl `URL.join` keeps empty URL path segments
  - `IDEA-20260520-014`: python-json-logger default encodes bytes as URL-safe base64
  - `IDEA-20260520-015`: dateparser stops trying previous locales by default
  - `IDEA-20260520-016`: Pillow resize default resampling switches to BICUBIC
  - `IDEA-20260520-017`: packaging `SpecifierSet` adapts prerelease matching
  - `IDEA-20260520-018`: structlog default configuration adds log level processing
- Ideas rejected:
  - `REJECTED-20260520-019`: simplejson `allow_nan` default now raises on NaN
  - `REJECTED-20260520-020`: PyMongo JSONMode default is prominent migration-guide behavior
- Cases promoted to reproduction: 0
- Cases accepted into benchmark: 0
- Notes:
  - No code files were changed; this batch only appended Python drift discovery Markdown.
  - Avoided all previously mentioned packages and APIs from batches 001 and 002.
  - Best next reproduction candidates are `multidict`, `yarl`, `python-json-logger`, and `markdown`; `pillow` and `dateparser` need install/input-fixture checks; `packaging` needs exact PEP 440 edge input from tests or PRs.

## RUN-20260520: Python autodiscovery pilot batch 004

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched:
- pygments
- sqlparse
- docutils
- mistune
- jsonpickle
- filelock
- python-dotenv
- pathspec
- celery
- cattrs
- Ideas added:
- IDEA-20260520-021: Pygments HtmlFormatter table filename row changes
- IDEA-20260520-022: sqlparse strip_comments preserves different whitespace
- IDEA-20260520-023: Docutils HTML5 footnotes move into aside
- IDEA-20260520-025: jsonpickle make_refs False serializes repeats differently
- IDEA-20260520-026: filelock logger default level stops forcing warning
- IDEA-20260520-027: python-dotenv set_key quote output changes
- IDEA-20260520-028: pathspec gitwildmatch dir star matches descendants
- Ideas rejected:
- REJECTED-20260520-024: Mistune raw HTML escaping belongs to explicit breaking change
- REJECTED-20260520-029: Celery 4.0 default serializer is prominent upgrade guidance
- REJECTED-20260520-030: cattrs sequence structuring migrations are explicit
- Cases promoted to reproduction:
- 0
- Cases accepted into benchmark:
- 0
- Notes:
- No code files were changed; this batch only appended Python drift discovery Markdown.
- Avoided all packages and APIs already mentioned in previous idea/rejection cards.
- Best next reproduction candidates are sqlparse, jsonpickle, python-dotenv, and Pygments; pathspec needs silent-policy review because the source calls it a major change.

## RUN-20260520: Python autodiscovery pilot batch 005

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched:
- black
- loguru
- hypothesis
- lxml
- rdflib
- odfdo
- natsort
- bleach
- xlrd
- pyparsing
- Ideas added:
- IDEA-20260520-031: Black 2024 stable style changes formatted output
- IDEA-20260520-032: Loguru serialized JSON stops escaping non-ASCII
- IDEA-20260520-033: Hypothesis creates gitignore in example database directory
- IDEA-20260520-034: lxml addnext preserves moved tail text
- IDEA-20260520-035: RDFLib GROUP_CONCAT empty separator changes output
- IDEA-20260520-036: odfdo Paragraph formats whitespace by default
- Ideas rejected:
- REJECTED-20260520-037: natsort default numeric parsing is explicit legacy incompatibility
- REJECTED-20260520-038: Bleach sanitizer rewrites are explicit incompatible output changes
- REJECTED-20260520-039: xlrd 2.0 encoding default is buried inside major removal release
- REJECTED-20260520-040: pyparsing empty-string parse action fix is exception-path only
- Cases promoted to reproduction:
- 0
- Cases accepted into benchmark:
- 0
- Notes:
- No code files were changed; this batch only appended Python drift discovery Markdown.
- Avoided all packages and APIs already mentioned in previous idea/rejection cards plus local anchors pandas, pydantic, scikit-learn, numpy, and polars.
- Best next reproduction candidates are Loguru, Hypothesis, odfdo, and RDFLib; Black and lxml need policy/install-risk review.

## RUN-20260520: Python autodiscovery pilot batch 006

- Model/operator: Codex
- Search budget: 10 discovery attempts, then stop
- Packages searched:
  - `beautifulsoup4`
  - `fsspec`
  - `coverage`
  - `mypy`
  - `ruff`
  - `rich`
  - `json5`
  - `pyjwt`
  - `invoke`
  - `platformdirs`
- Ideas added:
  - `IDEA-20260520-041`: Beautiful Soup script `get_text` semantics change
  - `IDEA-20260520-042`: fsspec default file cache strategy changes
  - `IDEA-20260520-043`: coverage JSON report stops counting module docstrings as executed
  - `IDEA-20260520-044`: mypy default cache format switches to binary and SQLite
  - `IDEA-20260520-045`: Ruff default Python target version advances to 3.9
  - `IDEA-20260520-046`: Rich empty color environment variables no longer disable color
  - `IDEA-20260520-047`: json5 custom encoder output indentation is fixed
- Ideas rejected:
  - `REJECTED-20260520-048`: PyJWT 2.0 encode return type is too prominent
  - `REJECTED-20260520-049`: Invoke `MockContext.repeat` default is explicitly incompatible
  - `REJECTED-20260520-050`: platformdirs directory moves are labeled `BREAKING`
- Cases promoted to reproduction: 0
- Cases accepted into benchmark: 0
- Notes:
  - No code files were changed; this batch only appended Python drift discovery Markdown.
  - Avoided all previously mentioned packages/APIs plus local anchors `pandas`, `pydantic`, `scikit-learn`, `numpy`, and `polars`.
  - Best next reproduction candidates are `coverage`, `beautifulsoup4`, `json5`, and `fsspec`; `ruff`, `rich`, and `mypy` need policy review because their differences are tool defaults or side effects.

## RUN-20260519: Python autodiscovery promotion batch 001

- Model/operator: Codex
- Search budget: 1 promoted reproduction from existing IDEA card
- Packages searched:
- httpx
- Ideas added:
- None
- Ideas rejected:
- None
- Cases promoted to reproduction:
- IDEA-20260519-001 -> httpx-json-request-body-compact
- Cases accepted into benchmark:
- ACCEPTED-20260519-001: httpx_json_request_body_compact
- Notes:
- No new search; closed the markdown memory loop for the previously reproduced httpx case.
- Counts: promoted=1, accepted=1, rejected=0.
- Reproduction keep=true and package audit pass=true with no findings.
