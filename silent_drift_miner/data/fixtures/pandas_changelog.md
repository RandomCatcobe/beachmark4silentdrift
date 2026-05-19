# pandas Changelog Fixtures (Offline)

This file contains curated changelog excerpts for offline testing of the Layer 1 miner.
It is NOT a complete changelog — only sections that contain potential drift signals.

## Version 2.0.0 (2023-04-03)

- **Default dtype for integer columns changed**: Integer columns with missing values now default
  to nullable integer dtype (`Int64`) instead of `float64`. Code relying on the old default
  behavior may produce different results.
- `DataFrame.groupby` sort parameter now defaults to `True` consistently. Previously, sort
  defaulted differently depending on the groupby key type.
- The default value of `observed` in `groupby` changed from `False` to a warning, and will
  default to `True` in a future version.
- Copy-on-Write (CoW) behavior: In-place modification of a slice no longer silently modifies
  the parent DataFrame. Setting `pd.options.mode.copy_on_write = True` enables the new behavior.

## Version 1.5.0 (2022-09-19)

- `DataFrame.applymap` is deprecated; use `DataFrame.map` instead.
- The default value of `numeric_only` in many aggregation methods changed to `False`. Previously,
  non-numeric columns were silently dropped.

## Version 1.4.0 (2022-01-22)

- `concat` with empty or all-NA DataFrames: the default dtype inference changed. Empty frames
  now default to `object` dtype instead of `float64`.
- The `squeeze` parameter in `read_csv` now defaults to `False` and will be removed in a future
  version. Previously it defaulted to squeezing single-column DataFrames to a Series.
