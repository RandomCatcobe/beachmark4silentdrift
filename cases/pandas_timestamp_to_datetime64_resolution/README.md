# pandas_timestamp_to_datetime64_resolution

`pandas.Timestamp("2023-01-01").to_datetime64()` keeps the same public call shape across pandas 1.5.3 and 2.0.3, but the returned NumPy dtype changes from `datetime64[ns]` to `datetime64[s]`.

Run the reproduction with:

```bash
silent-drift-miner reproduce run --spec data/reproductions/pandas-timestamp-to-datetime64-resolution/spec.json --out data/reproductions/pandas-timestamp-to-datetime64-resolution --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```
