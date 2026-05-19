# pandas_read_csv_uint8_overflow

`pandas.read_csv(..., dtype={"x": "UInt8"})` keeps the same public call shape across pandas 1.5.3 and 2.1.1. The old version rejects out-of-range integer input; the new version returns wrapped values such as `-1 -> 255` and `257 -> 1`.

Run the reproduction with:

```bash
silent-drift-miner reproduce run --spec data/reproductions/pandas-read-csv-uint8-overflow/spec.json --out data/reproductions/pandas-read-csv-uint8-overflow --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```
