# CSV Case Coverage Audit

Date: 2026-05-20

Source CSV: `C:/Users/canglan/Downloads/cases (1).csv`

Scope: checked the current repository only. I counted coverage from packaged cases,
audit artifacts, reproduction attempts, markdown memory, and tests. I did not treat
generic package mentions or generic pipeline tests as evidence that a specific CSV
behavior is covered.

## Summary

- CSV rows checked: 28
- Exact accepted/audited cases: 1
- Adjacent accepted case, not the same CSV behavior: 1
- Existing probe or reproduction that did not become accepted: 1
- Existing blocked/rejected report related to the row: 1
- Documentation guidance only, no artifact: 1
- Duplicate CSV row: 1
- Rows with no exact repo coverage: 22
- Direct tests for these CSV behaviors: 0

The main bookkeeping gap is that `sklearn_kmeans_n_init_auto` is a real packaged
and audited case, but it is not represented in `docs/python-drift-idea-bank.md`.
The idea bank currently records only `httpx_json_request_body_compact` as an
accepted promotion.

## What Counts

- Exact accepted: `data/packages/<case_id>/` exists, `data/audit/<case_id>.json`
  passes, and the API/version/source match the CSV row closely.
- Adjacent accepted: an accepted case is in the same problem family, but the API,
  source, or version pair differs.
- Probe/dropped: a reproduction was attempted, but it did not produce an accepted
  drift case.
- Blocked/rejected: an existing report already records why the candidate did not
  fit the local package harness or acceptance policy.
- Test coverage: a test names or exercises this specific behavior. Generic tests
  for packaging, audit, status, or reproduction infrastructure are listed only as
  generic support.

## Row-by-row Check

| # | CSV item | Current status | Repo evidence | Test coverage | Action |
| --- | --- | --- | --- | --- | --- |
| 1 | scikit-learn `LogisticRegression` default solver and `multi_class` change | Uncovered | No exact case, reproduction, package, idea-bank card, or test found. | None | Triage first. It is an old, documented default shift, so it likely needs policy review before promotion. |
| 2 | scikit-learn `SVC`/`SVR` `gamma` default change | Uncovered | No exact repo evidence found. | None | Triage first. Same concern: old and documented default shift. |
| 3 | scikit-learn `KMeans n_init='auto'` default | Exact accepted/audited | `data/packages/sklearn_kmeans_n_init_auto/`, `data/audit/sklearn_kmeans_n_init_auto.json`, `data/reports/python_status.json`; candidate-flow status is `pass_uncertain_silence`. | No direct behavior test. It is covered by generic status/audit gates only. | Backfill markdown memory in `docs/python-drift-idea-bank.md`. |
| 4 | pandas string dtype default becomes `str` | Uncovered | No exact repo evidence found. | None | Good future candidate if it can be reproduced locally without pyarrow ambiguity. |
| 5 | pandas `DataFrame.groupby(group_keys=...)` default becomes `True` | Uncovered | No exact repo evidence found. | None | Candidate, but source/version should be checked because it is a documented default shift. |
| 6 | pandas `groupby(observed=...)` default becomes `True` | Documentation guidance only | Mentioned in `docs/guide-for-agents.md` as an example, but no case, reproduction, package, idea-bank card, or test exists. | None | Promote only after a real reproduction. |
| 7 | pandas timestamp/string time parsing precision change | Adjacent accepted only | Accepted case `pandas_timestamp_to_datetime64_resolution` covers `pandas.Timestamp.to_datetime64` from 1.5.3 to 2.0.3, not the CSV's pandas 3.0 string parsing behavior. | No direct CSV behavior test. | Do not count as exact coverage. Create a separate candidate if this CSV behavior matters. |
| 8 | pandas `value_counts(sort=False)` ordering/stability change | Uncovered | No exact repo evidence found. | None | Candidate. Row 21 duplicates this. |
| 9 | NumPy random generator algorithm update | Probe/dropped, not accepted | Existing `numpy_choice_shuffle_with_p` probe has `data/reproductions/numpy-choice-shuffle-with-p/attempt_001/result.json` with `drop_reason: no_behavior_diff`; it is not the same broad NumPy 1.17 `Generator` migration case. | None | Do not count as accepted. Needs a new, versioned reproducer or a rejected card. |
| 10 | PyTorch cross-version or hardware reproducibility | Blocked related report | `data/reports/python_candidate_flow_report.json` records a related PyTorch CUDA candidate as blocked because it has no clean local CPU old/new drift pair. | None | Keep blocked unless a deterministic CPU-only package/version pair is found. |
| 11 | scikit-learn `OrthogonalMatchingPursuit normalize` default | Uncovered | No exact repo evidence found. | None | Triage first. Likely old/documented/deprecated boundary. |
| 12 | scikit-learn `quantile_transform copy` default | Uncovered | No exact repo evidence found. | None | Triage first; may be locally reproducible if old versions install cleanly. |
| 13 | scikit-learn `FunctionTransformer validate` default | Uncovered | No exact repo evidence found. | None | Triage first; likely locally reproducible. |
| 14 | scikit-learn `validation_curve`/`learning_curve cv` default folds | Uncovered | No exact repo evidence found. | None | Triage first; deterministic client may be possible but old version support matters. |
| 15 | scikit-learn `r2_score multioutput` default | Uncovered | No exact repo evidence found. | None | Triage first; old version and explicit documentation need policy review. |
| 16 | scikit-learn `normalized_mutual_info_score average_method` default | Uncovered | No exact repo evidence found. | None | Triage first; likely small local reproducer. |
| 17 | scikit-learn `power_transform method` default | Uncovered | No exact repo evidence found. | None | Triage first; check whether old version is installable in the sandbox. |
| 18 | scikit-learn `SVC decision_function_shape` default | Uncovered | No exact repo evidence found. | None | Triage first; old/documented default shift. |
| 19 | pandas `resample(group_keys=...)` default becomes `False` | Uncovered | No exact repo evidence found. | None | Candidate. Pure local pandas reproducer should be possible. |
| 20 | pandas `concat` DatetimeIndex sort behavior | Uncovered | No exact repo evidence found. | None | Candidate. Needs a minimal deterministic input. |
| 21 | pandas `DataFrame.value_counts(sort=False)` order change | Duplicate of row 8 | No exact repo evidence found beyond row 8. | None | Deduplicate with row 8 before promoting. |
| 22 | pandas `Day` offset becomes calendar day | Uncovered | No exact repo evidence found. | None | Candidate, likely good if timezone/DST input is deterministic. |
| 23 | pandas Copy-on-Write default enabled | Uncovered | No exact repo evidence found. | None | Triage carefully. It is a major default behavior change and may be too explicitly breaking for silent-drift acceptance. |
| 24 | SciPy `stats.mode keepdims` default becomes `False` | Uncovered | No exact repo evidence found. | None | Candidate. Small pure-local SciPy reproducer is likely. |
| 25 | SciPy `special.comb legacy` default becomes `False` | Uncovered | No exact repo evidence found. | None | Triage first. Verify the parameter exists and can show visible output change across installable versions. |
| 26 | PyTorch `torch.load(weights_only=True)` default | Uncovered | No exact repo evidence found. | None | Likely reject or defer because the cited source explicitly frames it as BC-breaking and it may involve security-sensitive pickle behavior. |
| 27 | Transformers `AutoTokenizer` defaults to fast tokenizers | Uncovered | No exact repo evidence found. | None | Defer unless a local tokenizer fixture can avoid network/model downloads. |
| 28 | Transformers `return_dict=True` default | Uncovered | No exact repo evidence found. | None | Candidate only if a no-download config/model path is found; otherwise defer. |

## Test Inventory

Current test inventory adds infrastructure confidence, but it does not add exact
coverage for any CSV row beyond the accepted KMeans package artifacts.

- `python -m pytest --collect-only -q` collected 108 tests.
- The latest full suite run in this sandbox was `103 passed, 5 skipped`.
- `silent_drift_miner/tests/test_real_cases.py` directly checks only
  `pandas_str_replace_regex_default`, `pydantic_optional_field_required`, and
  `pydantic_field_alias_none`.
- `silent_drift_miner/tests/test_python_status.py`,
  `silent_drift_miner/tests/test_bench_audit.py`, and related ecosystem tests
  validate generic package/status/audit mechanics, not these CSV behaviors.
- `silent_drift_miner/tests/test_autodiscovery.py` exercises autodiscovery report
  mechanics using `pandas_read_csv_uint8_overflow`; it does not cover the CSV rows.

## Recommended Next Moves

1. Backfill `sklearn_kmeans_n_init_auto` into markdown memory as an accepted case,
   because the artifacts already exist and pass audit.
2. Pick the next CSV candidates from pure-local, low-dependency items:
   `SciPy stats.mode keepdims`, pandas `resample group_keys`, pandas
   `value_counts(sort=False)`, or pandas `Day` offset.
3. Keep PyTorch hardware reproducibility, `torch.load(weights_only=True)`, and
   Transformers tokenizer behavior out of the immediate queue until policy and
   fixture boundaries are clearer.
