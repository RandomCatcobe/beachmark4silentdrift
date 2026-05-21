# JavaScript Drift Idea Bank

Independent language idea bank for local, deterministic JavaScript/Node silent-drift candidates.

## RUN-20260520-001: Independent JS Agent Batch

- Target: 10 candidates.
- Result: 10/10 candidates found.
- Language judgment: JavaScript/Node has abundant candidate material; no exhaustion judgment.
- Promotion note: validate each item against the JS adapter boundary before reproduction. Avoid browser-only or network-install assumptions.

| ID | Package / Tool | API Surface | Version Boundary | Source | Behavior Hypothesis | Why Silent | Reproduction Sketch | Confidence |
|---|---|---|---|---|---|---|---|---|
| JS-01 | Node.js | `Intl.DateTimeFormat`, locale/date output | Node 12 official binaries -> Node 13+ official binaries | https://nodejs.org/en/blog/release/v13.0.0 | Full ICU became the default, so non-English locale formatting can change from fallback/English-like output to localized output. | Same `Intl` calls succeed; only formatted strings and snapshots drift. | Compare `new Intl.DateTimeFormat("es", { month: "long", timeZone: "UTC" }).format(new Date(Date.UTC(1970, 0, 1)))` on Node 12 vs 13+. | High |
| JS-02 | npm CLI | `npm install`, `package-lock.json` generation | npm 6 -> npm 7 | https://blog.npmjs.org/post/626173315965468672/npm-v7-series-beta-release-and-semver-major.html | Same install can write lockfile format `lockfileVersion: 1` vs `2`. | Command exits successfully and public CLI shape is unchanged; drift appears as lockfile or parser behavior. | In an empty local package, run `npm install --package-lock-only`; compare generated `package-lock.json`. | High |
| JS-03 | Prettier | `prettier.format` / CLI default formatting | Prettier 2.8 -> 3.0 | https://prettier.io/blog/2023/07/05/3.0.0.html | Default `trailingComma` changed from `es5` to `all`, adding trailing commas in multiline function calls. | Formatting succeeds with same omitted options; only emitted text changes. | Format a multiline `foo(longArg1, longArg2)` call with default options. | High |
| JS-04 | Jest | Snapshot serialization, `snapshotFormat` default | Jest 28 -> 29 | https://jestjs.io/blog/2022/08/25/jest-29 | Default snapshot format changed to `escapeString: false` and `printBasicPrototype: false`. | Tests can pass after snapshot update; matcher API is unchanged. | Snapshot `expect({ a: 1 }).toMatchSnapshot()` and compare text. | High |
| JS-05 | Mongoose | Query casting/filtering, `strictQuery` default | Mongoose 6 -> 7 | https://mongoosejs.com/docs/migrating_to_7.html#strictquery | Unknown query keys are no longer stripped by default, so `{ notInSchema: 1 }` can query differently. | `Model.find()` still succeeds; result set changes. | Define schema `{ field: Number }`, insert docs, run `Model.find({ notInSchema: 1 })`. | High |
| JS-06 | Zod | `z.object`, optional fields with defaults | Zod 3 -> 4 | https://zod.dev/v4/changelog | Defaults inside optional object fields are now applied, changing parse output from missing key to populated key. | `.parse()` succeeds in both versions; returned object shape drifts. | `z.object({ a: z.string().default("tuna").optional() }).parse({})`; compare `{}` vs `{ a: "tuna" }`. | High |
| JS-07 | Tailwind CSS | Utility CSS defaults for `border`, `divide`, `ring` | Tailwind CSS 3 -> 4 | https://tailwindcss.com/docs/upgrade-guide#default-border-color | Default border/divide color changed from configured `gray-200` to `currentColor`; default ring behavior also changed. | Same class names compile; CSS and visual output change. | Compile markup with `class="border"` and `class="ring"` and compare emitted CSS. | High |
| JS-08 | Marked | `marked.parse` markdown-to-HTML defaults | Marked 7 -> 8 | https://marked.js.org/using_advanced#old-options | Built-in heading IDs and email mangling options were removed; default HTML for headings/mail links can change. | `marked.parse()` succeeds; generated HTML loses attributes or escaping unless extensions are added. | Run `marked.parse("# Hello")`; compare heading HTML. | High |
| JS-09 | dotenv | `.env` parser, `dotenv.parse` / `config` | dotenv 14.x -> 15.x | https://github.com/motdotla/dotenv#comments | Inline `#` starts a comment unless the value is quoted, so unquoted secret values containing `#` are truncated. | Parsing succeeds and env vars are set; only parsed value changes. | Parse `SECRET=abc#def`; compare preserved vs truncated value. | High |
| JS-10 | Handlebars | Template property/method resolution | Handlebars 4.5.3 -> 4.6.0+ | https://handlebarsjs.com/api-reference/runtime-options.html#options-to-control-prototype-access | Prototype property/method access is forbidden by default, changing templates that read class or built-in prototype members. | Template rendering often completes with blank output or warning rather than a compile-time break. | Render `start{{aString.trim}}end` with `{ aString: "  abc  " }`; compare output. | High |

## RUN-20260521-001: Web/API Line Triage

- Source draft: `C:/Users/canglan/Downloads/javascript.md`.
- Full artifact: [js-web-api-line-triage-20260521.md](js-web-api-line-triage-20260521.md).
- Scope: 26 JavaScript/web API drift leads from draft lines 11-299.
- Result: 6 promotion-ready leads, 8 boundary leads, 2 historical controls, 4 low-confidence leads, and 6 excludes.
- Promotion queue: A1 Gemini alias grounding behavior, A3 Office.js HTML attribute omission, A4 Twitter/X `widgets.js` fallback change, A5 Office.js dialog behavior, B1 Mapbox GL JS language config no-op, and B2 Apollo `useLazyQuery` cache/network semantics.
- Important correction: B9 Google Maps JavaScript API Geocoder default-region release note date is 2022-11-17.

## Verification Log

| Date | ID | Status | Evidence |
|---|---|---|---|
| 2026-05-20 | JS-06 | Verified by JS adapter pipeline | Source checked against Zod 4 migration guide. Reproduction result: `data\verification\js_zod_optional_defaults\attempt_001\result.json`. Old `zod@3.25.76` parses `{}` to `{}`; new `zod@4.1.12` parses `{}` to `{"a":"tuna"}`. Both exit 0; stdout differs. |
| 2026-05-20 | JS-09 | Verified by JS adapter pipeline | Source checked against dotenv README comments section. Reproduction result: `data\verification\js_dotenv_hash_comments\attempt_001\result.json`. Old `dotenv@14.3.2` parses `SECRET=abc#def` as `abc#def`; new `dotenv@15.0.1` parses it as `abc`. Both exit 0; stdout differs. |
| 2026-05-21 | JS-06 | Re-verified in current environment | Reproduction result: `data\verification\js_zod_optional_defaults\attempt_002\result.json`; keep=true. |
| 2026-05-21 | JS-09 | Re-verified in current environment | Reproduction result: `data\verification\js_dotenv_hash_comments\attempt_002\result.json`; keep=true. |
