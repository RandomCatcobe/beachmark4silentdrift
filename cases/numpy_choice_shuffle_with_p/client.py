"""Client for NumPy Generator.choice shuffle parameter probe."""
from __future__ import annotations

import json

import numpy as np


def main() -> None:
    seed = 137
    n = 10_000
    k = 2_000
    p = np.ones(n) / n
    weighted_shuffle = np.random.default_rng(seed).choice(
        n, k, replace=False, p=p, shuffle=True
    )
    weighted_no_shuffle = np.random.default_rng(seed).choice(
        n, k, replace=False, p=p, shuffle=False
    )
    unweighted_shuffle = np.random.default_rng(seed).choice(
        n, k, replace=False, shuffle=True
    )
    unweighted_no_shuffle = np.random.default_rng(seed).choice(
        n, k, replace=False, shuffle=False
    )
    payload = {
        "numpy_version": np.__version__,
        "weighted_equal": bool(np.array_equal(weighted_shuffle, weighted_no_shuffle)),
        "unweighted_equal": bool(np.array_equal(unweighted_shuffle, unweighted_no_shuffle)),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
