# Ruby Drift Idea Bank

Independent language idea bank for local, deterministic Ruby silent-drift candidates.

## RUN-20260520-001: Independent Ruby Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: Ruby has enough core Rails/Rack/gem material; no exhaustion judgment.
- Promotion note: prefer pure Ruby/gem calls. Rails app-level defaults may need careful minimization to fit the Ruby adapter boundary without a server/database.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| RB-AS-001 | Rails ActiveSupport | `ActiveSupport::TimeWithZone#to_time` | Rails <8.1 -> 8.1 | https://github.com/rails/rails/releases/tag/v8.1.0 | `to_time` no longer returns system-local time; it preserves the receiver timezone. | Same method returns a `Time`; offsets or serialized strings drift. | Set `Time.zone = "Tokyo"`, parse a zoned time, call `to_time`, compare `utc_offset`. | High |
| RB-AS-002 | Rails ActiveSupport | `Enumerable#sole` on tuple-yielding enumerables | Rails <8.1 -> 8.1 | https://github.com/rails/rails/releases/tag/v8.1.0 | For a one-entry hash, `sole` may change from returning only the key to returning the full key/value tuple. | The call succeeds and still returns one object, but object shape/content changes. | Run `{ a: 1 }.sole.inspect` across Rails 8.0 and 8.1. | High |
| RB-AS-003 | Rails ActiveSupport | `ActiveSupport::Digest` defaults | `config.load_defaults` before 7.0 -> 7.0+ | https://guides.rubyonrails.org/configuring.html#config-active-support-hash-digest-class | Default digest class changes from SHA1 to SHA256. | Same digest API returns a string, but length/content changes and cache keys/checksums drift. | Compare `ActiveSupport::Digest.hexdigest("abc")` with `load_defaults 6.1` vs `7.0`. | High |
| RB-AS-004 | Rails ActiveSupport | `ActiveSupport::Cache` serialization format | `config.load_defaults` before 7.1 -> 7.1+ | https://guides.rubyonrails.org/configuring.html#config-active-support-cache-format-version | Default cache format version changes, altering stored bytes for the same key/value. | Reads/writes work in one runtime; persisted cache entries or byte-level tests drift. | Write same object to a cache store and inspect raw entry encoding under `load_defaults 7.0` vs `7.1`. | High |
| RB-RACK-005 | Rack | `Rack::Utils.parse_nested_query` | Rack 2.2 -> 3.x | https://rack.github.io/rack/3.1/CHANGELOG_md.html | Semicolon stops acting as a GET parameter separator. | Parsing succeeds but returns a different params hash. | Compare `Rack::Utils.parse_nested_query("a=1;b=2")`. | High |
| RB-RACK-006 | Rack | Response header hashes | Rack 2.x -> 3.x | https://rack.github.io/rack/main/UPGRADE-GUIDE_md.html | Header names become lower-case in Rack 3-compatible response handling. | HTTP remains valid; string-key lookups or snapshots using original case drift. | Build a small Rack response and inspect `headers.keys` before/after Rack 3 middleware. | Medium-high |
| RB-FAR-007 | Faraday | Query-string encoding | Faraday 1.0.0 -> 1.0.1 | https://github.com/lostisland/faraday/blob/main/CHANGELOG.md | Spaces in query strings encode as `%20` instead of `+`. | Request succeeds with the same params API; URL string and signatures differ. | Compare `Faraday::Utils.build_query(q: "a b")`. | High |
| RB-SKQ-008 | Sidekiq | Job payload timestamps | Sidekiq 7.x -> 8.0 | https://github.com/sidekiq/sidekiq/blob/main/Changes.md | `created_at`, `enqueued_at`, `failed_at`, and `retried_at` store epoch milliseconds instead of epoch float seconds. | Jobs enqueue and run; payload inspection, middleware, and metrics see different numeric units. | Freeze time, enqueue a job, inspect payload JSON timestamp units. | High |
| RB-RSP-009 | RSpec expectations | `aggregate_failures` return value | rspec-expectations 3.10 -> 3.11 | https://github.com/rspec/rspec-expectations/blob/main/Changelog.md | `aggregate_failures` returns `true` when no exception occurs. | Specs still pass; helper code using the return value observes `nil` vs `true`. | Print `aggregate_failures { expect(1).to eq(1) }` under 3.10 and 3.11. | High |
| RB-NOK-010 | Nokogiri | XML/HTML4 SAX entity handling | Nokogiri <1.17 -> 1.17 | https://nokogiri.org/CHANGELOG.html | External entity references no longer register SAX errors; parsed entities may surface through `reference` callback. | SAX parse can complete, but handler event/error streams differ. | Implement a SAX handler recording `error` and `reference`; parse XML with an external entity and compare callbacks. | Medium |

## Verification Log

| Date | ID | Status | Evidence |
|---|---|---|---|
| 2026-05-21 | RB-FAR-007 | Rejected by local check | Installed `faraday` 1.0.0 and 1.0.1 into isolated gem dirs. Both `Faraday::Utils.build_query(q: "a b")` returned `q=a+b`; the claimed `%20` drift did not reproduce. |
| 2026-05-21 | RB-RACK-005 | Verified by Ruby adapter pipeline | Source checked against Rack 3.x changelog/upgrade notes. Reproduction result: `data\verification\ruby_rack_semicolon_query\attempt_001\result.json`. Old `rack-2.2.9` parses `a=1;b=2&c=3` as `{"a":"1","b":"2","c":"3"}`; new `rack-3.1.0` parses it as `{"a":"1;b=2","c":"3"}`. Both exit 0; stdout differs. |
