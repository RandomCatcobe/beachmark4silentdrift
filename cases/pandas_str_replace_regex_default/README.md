# pandas_str_replace_regex_default

Real Python silent-drift candidate for `pandas.Series.str.replace`.

Source: https://pandas.pydata.org/pandas-docs/version/2.0/whatsnew/v2.0.0.html

The release note says: "Change the default argument of regex for Series.str.replace() from True to False."

The hand-authored client calls:

```python
values.str.replace(r"\W", "_")
```

Reproduction commands:

```bash
py310="$(uv python find 3.10)"
silent-drift-miner reproduce plan --candidate-id pandas-str-replace-regex-default --library pandas --old-version 1.5.3 --new-version 2.0.3 --client-file cases/pandas_str_replace_regex_default/client.py --old-python-executable "$py310" --new-python-executable "$py310" --extra-package numpy==1.24.4 --out data/reproductions/pandas-str-replace-regex-default/spec.json
silent-drift-miner reproduce run --spec data/reproductions/pandas-str-replace-regex-default/spec.json --out data/reproductions/pandas-str-replace-regex-default --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```

Observed diff from `attempt_001`:

- old `pandas==1.5.3`: `["a_b", "a_b", "abc"]`
- new `pandas==2.0.3`: `["a.b", "a?b", "abc"]`

This case is deterministic: no network, clock, randomness, or filesystem input is used by the client.
