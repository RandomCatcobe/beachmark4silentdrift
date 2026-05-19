"""Client for Polars strict float-to-int cast probe."""
from __future__ import annotations

import json

import polars as pl


def main() -> None:
    df = pl.DataFrame({"x": [1.2, 5.8]})
    try:
        out = df.select(pl.col("x").cast(pl.Int32, strict=True).alias("x")).to_series()
    except Exception as exc:
        payload = {
            "polars_version": pl.__version__,
            "status": "raised",
            "error_type": type(exc).__name__,
            "error": str(exc).splitlines()[0],
        }
    else:
        payload = {
            "polars_version": pl.__version__,
            "status": "returned",
            "values": [int(value) for value in out.to_list()],
        }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
