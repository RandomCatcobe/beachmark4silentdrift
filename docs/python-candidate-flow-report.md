# Python Candidate Flow Report

This report tests the user-provided silent API drift list against the Python-only benchmark flow:

`reproduce plan/run -> curate create -> oracle generate/validate -> bench package -> audit -> python status`

## Results

- Full new pass: 3 cases
  - `pandas_timestamp_to_datetime64_resolution`
  - `pandas_read_csv_uint8_overflow`
  - `sklearn_kmeans_n_init_auto` as `uncertain_silence`
- Existing pass retained: `pandas_str_replace_regex_default`
- Dropped after reproduction: 2 cases
  - `numpy_choice_shuffle_with_p`: no old/new behavior diff after ignoring version metadata
  - `polars_cast_strict_float_to_int`: no old/new behavior diff after ignoring version metadata
- Blocked or rejected before reproduction: 12 rows
- Duplicate row: pandas timestamp duplicate

The machine-readable report is `data/reports/python_candidate_flow_report.json`.

## Engineering Fix

While testing NumPy, the pipeline exposed a false positive: JSON stdout containing only a version field difference was treated as a behavior diff. The reproduction diff now strips keys named `version` or ending with `_version` before deciding whether structured JSON stdout changed.

Regression test:

```bash
python -m pytest tests/test_reproduction_run.py
```

## Algorithm Decisions Needed

- Whether warning-backed default shifts, like sklearn KMeans, stay accepted as `uncertain_silence`.
- Whether legacy cases outside 2022-2026 can be admitted when they still affect modern migrations.
- Whether current-version bugs without old/new version pairs need a separate benchmark track.
- Whether cloud/service alias drifts need a recorded-fixture harness separate from the pip package harness.
