# pandas_str_replace_regex_default

Real Python silent-drift candidate for `pandas.Series.str.replace`.

Source: https://pandas.pydata.org/pandas-docs/version/2.0/whatsnew/v2.0.0.html

The release note says: "Change the default argument of regex for Series.str.replace() from True to False."

The hand-authored client calls:

```python
values.str.replace(r"\W", "_")
```

Expected reproduction command:

```bash
silent-drift-miner reproduce plan --candidate-id pandas-str-replace-regex-default --library pandas --old-version 1.5.3 --new-version 2.0.3 --client-file cases/pandas_str_replace_regex_default/client.py --out data/reproductions/pandas-str-replace-regex-default/spec.json
```

This case is deterministic: no network, clock, randomness, or filesystem input is used by the client.
