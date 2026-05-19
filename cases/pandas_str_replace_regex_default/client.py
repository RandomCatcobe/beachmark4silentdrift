"""Client for pandas Series.str.replace regex default drift."""
from __future__ import annotations

import json

import pandas as pd


def main() -> None:
    values = pd.Series(["a.b", "a?b", "abc"])
    result = values.str.replace(r"\W", "_").tolist()
    print(json.dumps({"pandas_version": pd.__version__, "result": result}, sort_keys=True))


if __name__ == "__main__":
    main()
