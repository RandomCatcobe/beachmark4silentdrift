# httpx_json_request_body_compact

Real Python silent-drift candidate for `httpx.Request(json=...)`.

Source: https://github.com/encode/httpx/blob/master/CHANGELOG.md

The changelog for `0.28.0` says JSON request bodies now use a compact
representation by default. The hand-authored client constructs a request
locally and prints the serialized body, so the reproduction does not perform a
network call.

Run the reproduction with:

```powershell
.\.sandbox\sdm.cmd reproduce run --spec data\reproductions\httpx-json-request-body-compact\spec.json --out data\reproductions\httpx-json-request-body-compact --install --venv-root .repro_venvs --build-timeout 300 --timeout 60
```

This case is deterministic: no network, clock, randomness, or filesystem input
is used by the client.
