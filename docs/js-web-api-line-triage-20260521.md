# JavaScript Web/API Line Triage - 2026-05-21

Source draft: `C:/Users/canglan/Downloads/javascript.md`

This artifact line-manages the 26 JavaScript/web API drift leads from the external draft. Each entry keeps its original source line, evidence URL, triage decision, and route into the next artifact queue.

## Output Summary

| Bucket | Count | Entries |
|---|---:|---|
| Promotion-ready leads | 6 | A1, A3, A4, A5, B1, B2 |
| Boundary / needs reproduction or stronger evidence | 8 | A2, A6, A7, A9, A12, B3, B6, B9 |
| Historical / control examples | 2 | A10, A11 |
| Low-confidence leads | 4 | A8, B11, B13, B14 |
| Exclude from silent-drift core | 6 | B4, B5, B7, B8, B10, B12 |

Primary promotion queue:

| Candidate | Source line | Route | Why it stays |
|---|---:|---|---|
| JS-WEB-01 Gemini alias retargeting drops grounding behavior | 11 | Promote to candidate write-up; reproduce if API access is available. | Same alias/config succeeds, but reported output loses grounding metadata and expected search behavior. |
| JS-WEB-02 Office.js Outlook body HTML attribute omission | 34 | Promote to Office.js web-service candidate; reproduction may require Outlook Web fixture. | `body.getAsync` still returns HTML, but class/data attributes disappear. |
| JS-WEB-03 Twitter/X hosted `widgets.js` deleted-tweet fallback change | 46 | Promote as hosted JavaScript embed drift. | Same page markup and hosted script path continue running, but embedded deleted content rendering changes. |
| JS-WEB-04 Office.js Outlook dialog z-order/iframe behavior change | 58 | Promote to UI API semantics candidate. | `displayDialogAsync` succeeds, but dialog placement/modal behavior changes. |
| JS-WEB-05 Mapbox GL JS language config silent no-op | 151 | Promote as no-op lead; confirm whether older version/config path worked. | `setConfigProperty` call does not error, but labels do not change and getter reports `null`. |
| JS-WEB-06 Apollo `useLazyQuery` fetch-policy/cache semantics shift | 162 | Promote as package-level repro candidate. | Query still succeeds, but reported behavior returns cache rather than network results after upgrade. |

## Line Ledger

| Line | ID | Decision | Route | Evidence | Note |
|---:|---|---|---|---|---|
| 11 | A1 | Promotion-ready | Candidate write-up | [HN](https://news.ycombinator.com/item?id=47271099), [Gemini changelog](https://ai.google.dev/gemini-api/docs/changelog) | Keep as alias/default-tool behavior drift; evidence is developer report plus official model/alias change context. |
| 23 | A2 | Boundary | Needs reproduction | [HN](https://news.ycombinator.com/item?id=47271099), [Google AI forum](https://discuss.ai.google.dev/t/why-is-using-a-response-schema-not-supported-when-using-grounded-search/92327) | Report says search was ignored when JSON mode and Search were combined, but current evidence also shows unsupported/hard-error behavior. |
| 34 | A3 | Promotion-ready | Candidate write-up | [OfficeDev issue 5296](https://github.com/OfficeDev/office-js/issues/5296), [Office.js open letter issue 6513](https://github.com/OfficeDev/office-js/issues/6513) | Strong silent content-inclusion drift: returned HTML omits attributes relied on by add-ins. |
| 46 | A4 | Promotion-ready | Candidate write-up | [Kevin Marks](https://www.kevinmarks.com/twittereditsyou.html), [HN](https://news.ycombinator.com/item?id=30928217) | Strong hosted-script example; not a package API, but directly JavaScript/web-surface relevant. |
| 58 | A5 | Promotion-ready | Candidate write-up | [OfficeDev issue 6242](https://github.com/OfficeDev/office-js/issues/6242), [Office.js open letter issue 6513](https://github.com/OfficeDev/office-js/issues/6513) | UI API call still succeeds, but foreground/modal semantics change. |
| 70 | A6 | Boundary | Capability-detection backlog | [OfficeDev issue 5610](https://github.com/OfficeDev/office-js/issues/5610), [Office.js open letter issue 6513](https://github.com/OfficeDev/office-js/issues/6513) | Good false-positive capability-detection case; classify as platform/API inconsistency until repro is clearer. |
| 82 | A7 | Boundary | Platform-inclusion backlog | [OfficeDev issue 6492](https://github.com/OfficeDev/office-js/issues/6492), [Office.js open letter issue 6513](https://github.com/OfficeDev/office-js/issues/6513) | Mac/Windows hidden-bookmark inclusion differs; needs old/new drift proof before promotion. |
| 94 | A8 | Low-confidence | Evidence search only | [Reddit](https://www.reddit.com/r/node/comments/1ru0joz/whats_your_worst_story_of_a_thirdparty_api/) | Fits the wrong-result shape, but current evidence is a single anecdote without vendor or secondary confirmation. |
| 105 | A9 | Boundary | Capability-detection backlog | [OfficeDev issue 5701](https://github.com/OfficeDev/office-js/issues/5701) | `isSetSupported` and actual API availability disagree; needs tighter version/platform details. |
| 116 | A10 | Historical / control | Do not promote as modern JS case | [HN](https://news.ycombinator.com/item?id=8347310) | Strong precedent for batch-accounting semantics, but too old for the current modern-corpus target. |
| 127 | A11 | Historical / control | Do not promote as modern JS case | [StackOverflow](https://stackoverflow.com/questions/15388495/tolocalestring-format-changed-in-chrome) | Useful browser-runtime drift example, but 2013 and outside current priority window. |
| 138 | A12 | Boundary | Security/auth-scope backlog | [lepro.dev](https://www.lepro.dev/en/google-api-keys-gemini-exposure), [Paniam](https://blog.paniam.cloud/posts/google-api-keys-are-now-secrets) | Auth-scope/billing exposure drift; important but not response-value silent drift. |
| 151 | B1 | Promotion-ready | Candidate write-up | [Mapbox issue 13630](https://github.com/mapbox/mapbox-gl-js/issues/13630), [Mapbox language docs](https://docs.mapbox.com/help/dive-deeper/change-language/) | Silent no-op is strong; still mark old-version support as a confirmation task. |
| 162 | B2 | Promotion-ready | Candidate write-up | [Apollo issue 10285](https://github.com/apollographql/apollo-client/issues/10285), [useLazyQuery docs](https://www.apollographql.com/docs/react/api/react/useLazyQuery) | Cache/network semantics shift gives stale but successful results; changelog/docs make silence partial rather than absolute. |
| 173 | B3 | Boundary | Documented-default-control backlog | [Mongoose issue 11861](https://github.com/Automattic/mongoose/issues/11861), [Mongoose 7 migration](https://mongoosejs.com/docs/migrating_to_7.html) | Query result-set drift is real, but migration docs and warnings are explicit. |
| 185 | B4 | Exclude core | Documented-control only | [Firebase release notes](https://firebase.google.com/support/release-notes/js), [StackOverflow](https://stackoverflow.com/questions/54744979/getting-the-timestampsinsnapshots-setting-now-defaults-to-true-firestore-error) | Timestamp field-type default changed with clear warning/release notes. |
| 197 | B5 | Exclude core | Auth-migration control only | [StackOverflow](https://stackoverflow.com/questions/73357232/why-is-my-messagecreate-event-not-working-discord-js), [AnswerOverflow](https://www.answeroverflow.com/m/1329554466524889178) | Discord privileged intent migration is explicit and usually fails visibly. |
| 209 | B6 | Boundary | Runtime-misconfig backlog | [Next issue 38743](https://github.com/vercel/next.js/issues/38743) | Edge/Node runtime mismatch is close to silent runtime drift, but issue also includes hard-error characteristics. |
| 220 | B7 | Exclude core | Hard-break control only | [whatwg-url issue 166](https://github.com/jsdom/whatwg-url/issues/166) | Dependency upgrade causes TypeError; not a continuing wrong-result case. |
| 231 | B8 | Exclude core | Browser-defect control only | [Esri community](https://community.esri.com/t5/arcgis-online-questions/map-error-in-new-chrome-update-128-0-6613-85/td-p/1525829), [Esri support](https://support.esri.com/en-us/knowledge-base/problem-defective-chromium-128-update-and-arcgis-maps-s-000033499) | Chromium 128 rendering defect; useful as outage/browser-bug control, not API drift. |
| 243 | B9 | Boundary | Default-region backlog | [Maps JavaScript API release notes](https://developers.google.com/maps/documentation/javascript/releases) | Correct date is 2022-11-17; strong default-region shape, but needs developer complaint or deterministic repro. |
| 254 | B10 | Exclude core | Framework-migration control only | [React 18 blog](https://react.dev/blog/2022/03/29/react-v18), [BigBinary](https://www.bigbinary.com/blog/react-18-introduces-automatic-batching) | React 18 batching is documented major-version framework behavior, not external silent API drift. |
| 266 | B11 | Low-confidence | Evidence search only | [Puppeteer changelog](https://pptr.dev/CHANGELOG) | Changelog-level timeout default clue only; no wrong-result complaint found. |
| 277 | B12 | Exclude core | Hard-break control only | [Node v15 release](https://nodejs.org/en/blog/release/v15.0.0), [Reddit](https://www.reddit.com/r/node/comments/jipk9c/icymi_in_node_v15_unhandled_rejected_promises/) | Process-exit behavior is hard break and officially announced. |
| 288 | B13 | Low-confidence | Evidence search only | [Optimizely changelog](https://github.com/optimizely/javascript-sdk/blob/master/CHANGELOG.md) | Event retry/default processing clues exist, but no production wrong-result report was found. |
| 299 | B14 | Low-confidence | Evidence search only | [Mapbox changelog](https://raw.githubusercontent.com/mapbox/mapbox-gl-js/main/CHANGELOG.md) | Fontstack compositing default clue only; no user-side silent failure evidence yet. |

## Next Artifact Routes

Promotion-ready entries should move first into case write-ups or reproduction specs:

| New ID | Draft ID | Minimal next artifact |
|---|---|---|
| JS-WEB-01 | A1 | Evidence-backed candidate note; API repro gated on Gemini access. |
| JS-WEB-02 | A3 | Office.js candidate note with HTML-before/after expectation. |
| JS-WEB-03 | A4 | Hosted JavaScript embed case note; likely documentation-only because remote behavior was rolled back. |
| JS-WEB-04 | A5 | Office.js UI-semantics candidate note with z-order/modal oracle. |
| JS-WEB-05 | B1 | Mapbox GL JS minimal map repro and old-version/documentation confirmation. |
| JS-WEB-06 | B2 | Apollo package repro comparing `useLazyQuery` behavior across 3.5.x and 3.6.x. |

Boundary entries stay in the backlog until their missing proof is supplied:

| Draft ID | Missing proof |
|---|---|
| A2 | Current or archived repro proving successful request while Search is silently skipped. |
| A6 | Exact iOS host/version matrix and failed API call after positive `isSetSupported`. |
| A7 | Whether hidden-bookmark inclusion changed over time or is only platform divergence. |
| A9 | Exact Word host/version and whether the support check reports true in the failing environment. |
| A12 | Framing as security/auth-scope drift rather than response-value drift. |
| B3 | Decide whether documented default changes belong in the silent-drift corpus. |
| B6 | Separate genuine silent fallback from misconfiguration/hard error. |
| B9 | Add developer report or deterministic address fixture showing changed geocode result after 2022-11-17. |

Corrections to apply to the source draft if it is edited later:

- B9 date should be `2022-11-17`, not an unverified placeholder.
- A8 should be downgraded from boundary to low-confidence until non-Reddit evidence is found.
- B4, B5, B7, B8, B10, and B12 should not be counted as silent-drift candidates in corpus statistics.
- B11, B13, and B14 should be marked as changelog-only leads, not vetted candidates.
