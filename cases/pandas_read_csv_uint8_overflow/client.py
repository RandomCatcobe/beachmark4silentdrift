"""Client for pandas read_csv UInt8 overflow drift."""
from __future__ import annotations

from io import StringIO
import json

import pandas as pd


def main() -> None:
    data = StringIO("x\n-1\n257")
    try:
        df = pd.read_csv(data, dtype={"x": "UInt8"})
    except Exception as exc:
        payload = {
            "pandas_version": pd.__version__,
            "status": "raised",
            "error_type": type(exc).__name__,
            "error": str(exc).splitlines()[0],
        }
    else:
        payload = {
            "pandas_version": pd.__version__,
            "status": "returned",
            "values": [int(value) for value in df["x"].tolist()],
        }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
