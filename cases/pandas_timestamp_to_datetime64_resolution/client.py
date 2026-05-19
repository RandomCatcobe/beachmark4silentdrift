"""Client for pandas Timestamp.to_datetime64 resolution drift."""
from __future__ import annotations

import json

import pandas as pd


def main() -> None:
    value = pd.Timestamp("2023-01-01").to_datetime64()
    print(
        json.dumps(
            {
                "pandas_version": pd.__version__,
                "dtype": str(value.dtype),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
