# sklearn_kmeans_n_init_auto

`sklearn.cluster.KMeans(...).fit(...)` keeps the same public call shape across scikit-learn 1.3.2 and 1.5.2, but the default initialization count changes from 10 to 1 when `n_init` is left implicit. This case is tagged as uncertain-silence because scikit-learn 1.3.2 emits a FutureWarning and the default shift was announced in release notes.

Run the reproduction with:

```bash
silent-drift-miner reproduce run --spec data/reproductions/sklearn-kmeans-n-init-auto/spec.json --out data/reproductions/sklearn-kmeans-n-init-auto --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```
