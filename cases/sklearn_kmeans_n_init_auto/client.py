"""Client for scikit-learn KMeans n_init default drift."""
from __future__ import annotations

import json

from sklearn.cluster import KMeans


def main() -> None:
    points = [
        [0.0, 0.0],
        [0.0, 0.2],
        [0.2, 0.0],
        [8.0, 8.0],
        [8.1, 8.2],
        [7.9, 8.1],
        [3.0, 10.0],
        [3.2, 10.1],
        [2.9, 9.8],
    ]
    model = KMeans(n_clusters=3, random_state=7, init="k-means++")
    model.fit(points)
    payload = {
        "sklearn_version": __import__("sklearn").__version__,
        "n_init_param": model.get_params()["n_init"],
        "actual_n_init": getattr(model, "_n_init", None),
        "inertia": round(float(model.inertia_), 8),
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
