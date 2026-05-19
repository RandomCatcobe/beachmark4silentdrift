# Python Autodiscovery Handoff

Last updated: 2026-05-20.

This note hands off the current Python autodiscovery work. It is about the
autodiscovery idea bank itself. The repository also contains six manually found
Python cases; the idea bank has now produced one additional accepted case.

## Current State

- Idea bank: `docs/python-drift-idea-bank.md`
- Run log: `docs/python-drift-run-log.md`
- Next-run brief: `docs/python-drift-next-run.md`
- Current idea-bank counts:
  - `IDEA`: 40
  - `REJECTED`: 20
  - `ACCEPTED`: 1
- `IDEA-20260519-001` has been promoted and accepted as
  `ACCEPTED-20260519-001` / `httpx_json_request_body_compact`.
- The six older audited Python cases were found before the Markdown
  autodiscovery memory loop and should be treated as historical anchors, not
  idea-bank output, unless explicitly backfilled.

## Original Root Cause Of Zero Accepted Cards

The `autodiscovery` command set is currently a Markdown memory helper, not a
full autonomous experiment runner.

Evidence:

- `docs/python-autodiscovery-plan.md` says the `v0.11.0` local implementation is
  intentionally small and only helps the model write and reread Markdown memory.
- `silent_drift_miner/src/silent_drift_miner/autodiscovery.py` builds readiness
  and next-run briefs; it does not start discovery or reproduction.
- `docs/python-drift-run-log.md` records each pilot batch as "10 discovery
  attempts, then stop".
- Those run-log batches say no code files were changed or only Markdown was
  appended.
- Before the `httpx` promotion, a local check found 40 unique idea packages and
  0 matching reproduction directories for those idea packages.

The missing bridge is:

```text
IDEA card
  -> promoted candidate
  -> hand-authored minimal client
  -> reproduce plan
  -> reproduce run
  -> curate accept/reject
  -> oracle/package/audit
  -> ACCEPTED or REJECTED card update
```

## Local Sandbox

A local control sandbox has been created under:

```text
D:\myproject\beach\.sandbox\autodiscovery
```

Properties:

- Python: `3.12.3`
- Base executable: `C:\ProgramData\anaconda3\python.exe`
- `include-system-site-packages = false`
- Installed packages: only `pip 24.0`
- `silent-drift-miner` is not installed into the venv.
- The wrapper runs the project from source with `PYTHONPATH`.

Use this wrapper from the repository root:

```powershell
.\.sandbox\sdm.cmd autodiscovery readiness
.\.sandbox\sdm.cmd python status --cases cases --packages data\packages --min-cases 0
```

The PowerShell wrapper `.sandbox\sdm.ps1` also exists, but the local Windows
execution policy blocks direct `.ps1` execution. Prefer `.sandbox\sdm.cmd`.

`.sandbox/` is ignored in `.gitignore`.

## Important Working Tree Notes

At the time of this handoff, the working tree already had local Markdown changes:

- `docs/python-drift-idea-bank.md`
- `docs/python-drift-next-run.md`
- `docs/python-drift-run-log.md`

The current sandbox setup also changed:

- `.gitignore` to ignore `.sandbox/`

There is also an untracked file from an earlier failed `uv run` attempt:

- `silent_drift_miner/uv.lock`

Do not delete or revert unrelated local changes without explicit user approval.

## Recommended First Promotion Batch

Start with one or two low-dependency, pure-local ideas. Current sequence:

1. Done: `IDEA-20260519-001` / `httpx` JSON request body compact serialization
2. Next: `IDEA-20260519-002` / `jinja2` `groupby` default becomes case-insensitive

Why these first:

- no live network
- no database or service
- small dependency footprint
- short deterministic client
- clear public source evidence
- same public call shape

Avoid starting with heavy or policy-borderline ideas such as `matplotlib`,
`pytest`, `django`, `ruff`, `mypy`, or side-effect/tooling defaults until the
promotion loop is proven.

## Completed First Candidate: httpx

Create:

```text
cases/httpx_json_request_body_compact/
  client.py
  candidate.json
  README.md
```

Minimal client shape:

```python
from __future__ import annotations

import json
import httpx


def main() -> None:
    request = httpx.Request(
        "POST",
        "https://example.test/submit",
        json={"a": 1, "b": 2},
    )
    print(
        json.dumps(
            {
                "httpx_version": httpx.__version__,
                "content": request.content.decode("utf-8"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
```

Expected old/new hypothesis:

- old `httpx==0.27.2`: JSON content likely includes spaces after separators.
- new `httpx==0.28.0`: JSON content should be compact.

Run from repo root:

```powershell
.\.sandbox\sdm.cmd reproduce plan `
  --candidate-id httpx-json-request-body-compact `
  --library httpx `
  --old-version 0.27.2 `
  --new-version 0.28.0 `
  --client-file cases\httpx_json_request_body_compact\client.py `
  --out data\reproductions\httpx-json-request-body-compact\spec.json

.\.sandbox\sdm.cmd reproduce run `
  --spec data\reproductions\httpx-json-request-body-compact\spec.json `
  --out data\reproductions\httpx-json-request-body-compact `
  --install `
  --venv-root .repro_venvs `
  --build-timeout 300 `
  --timeout 60
```

Network note: the run does not call the network, but `--install` needs package
installation unless the package wheels are already cached locally.

## After Reproduction

Inspect:

```text
data/reproductions/<candidate-id>/attempt_001/result.json
data/reproductions/<candidate-id>/attempt_001/diff.json
data/reproductions/<candidate-id>/attempt_001/old/stdout.txt
data/reproductions/<candidate-id>/attempt_001/new/stdout.txt
```

If `keep: true` and the diff is a genuine behavior diff:

1. Create a curated case with `curate create`.
2. Generate an oracle with `oracle generate`.
3. Package with `bench package`.
4. Audit with `audit case`.
5. Append an `ACCEPTED-*` card to `docs/python-drift-idea-bank.md`.
6. Append a run-log entry with the promoted and accepted case.
7. Refresh `docs/python-drift-next-run.md` with `autodiscovery brief`.

If the result is not usable:

1. Append a `REJECTED-*` card explaining the failed reproduction.
2. Add the failure lesson to the run log.
3. Refresh the next-run brief so the avoid list learns from it.

## Acceptance Bar

Use the same standard as `docs/guide-for-agents.md`:

- same call shape
- deterministic local behavior
- output differs between old and new
- no live service dependency
- not just a removed import, signature break, or canonical exception path
- not prominently labeled as breaking in the primary source

Cases that pass mechanically but are warning-backed or prominently announced
should be marked as uncertain or rejected unless the user explicitly accepts
borderline policy cases.

## Open Engineering Gap

The next durable code improvement is a small promotion command, for example:

```text
silent-drift-miner autodiscovery promote ...
```

It should not try to solve client synthesis fully at first. A practical first
version can:

- read an `IDEA-*` card id
- require an existing hand-authored client path
- create candidate metadata
- run `reproduce plan`
- run `reproduce run`
- append promoted/rejected/accepted notes to Markdown

This would close the current process gap without pretending the idea bank can
automatically synthesize every client.
