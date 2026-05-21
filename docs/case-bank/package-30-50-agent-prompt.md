# Agent Prompt: Package 30/50 Verification Cases

Copy this prompt into any Codex/agent instance that should help convert the
2026-05-21 verification runs into complete SilentDrift case-bank packages.

## Prompt

You are working in `D:\myproject\bench2\beachmark4silentdrift`.

Goal: convert every case from the 2026-05-21 `sequential_30` and `reverse_50`
verification runs into complete `docs/case-bank/cases/...` packages whenever it
is genuinely possible. When not all cases can be completed, still build the
full eval package from every complete case folder that can be collected.

You are not alone in the codebase. Other instances may be packaging different
case IDs at the same time. Do not revert unrelated edits. Own only the case IDs
you are assigned, and do not edit another worker's case folder unless the user
explicitly asks.

### Ground Truth Inputs

Read these first:

- `docs/case-bank-restructure/final-plan.md`
- `docs/case-bank/README.md`
- `docs/case-bank/metadata.schema.json`
- `docs/verification-runs/run-20260521-sequential-30.md`
- `docs/verification-runs/run-20260521-reverse-50.md`
- `data/verification/sequential_30/summary.json`
- `data/verification/reverse_50/results.jsonl`
- Existing complete examples under `docs/case-bank/cases/**`

The existing complete case-bank packages are templates. Match their file layout
and tone.

### Scope

Process your assigned IDs. If no assignment is given, process all un-packaged
`verified_keep` IDs from both verification runs first, then try the blocked or
no-diff IDs only if time remains.

Known `sequential_30` verified IDs:

```text
DOTNET-05
DOTNET-09
GO-001
GO-003
GO-006
GO-007
JS-01
JS-02
JS-03
JS-04
JS-05
JS-10
JVM-JAVA-01
JVM-JAVA-02
JVM-JAVA-03
JVM-JAVA-04
```

Known `reverse_50` newly verified IDs:

```text
RB-RSP-009
RB-RACK-006
PY-SD-008
PY-SD-007
PY-SD-005
PY-SD-001
PHP-08
```

Existing/duplicate records from `reverse_50`:

```text
RB-RACK-005  already has a case-bank package
PY-SD-010    already has a case-bank package
PHP-07       already has a case-bank package
PHP-03       semantic duplicate of PHP-12
RB-FAR-007   rejected/no behavior diff in existing local check
```

Do not create duplicate case folders for existing or semantic-duplicate cases.
If a case already exists, only repair it if validation fails or requested.

### Case Package Contract

A case counts as package-complete only when this folder exists:

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

and contains:

```text
case.md
evidence.md
env.md
metadata.json
client/
  .gitignore
  probe.<language extension>
  package/build files if needed
hidden/
  oracle.md
  expected.json
```

Rules:

- `metadata.json` must validate against the schema and use `status:
  "verified_keep"` only when old and new runs both exit 0 and a meaningful
  silent drift is confirmed.
- `metadata.provenance.reproduction_result` must point to the verification
  artifact, for example `data/verification/sequential_30/JS-03` or
  `data/verification/reverse_50/details/PY-SD-005.json`.
- Public files (`case.md`, `evidence.md`, `env.md`) must not contain raw stdout
  dumps, hidden oracle conditions, or exact expected outputs.
- `hidden/expected.json` is the machine-readable assertion reduced from the
  raw verification output.
- `hidden/oracle.md` explains keep/reject/hard-break judgment, including allowed
  noise.
- `client/` must contain only minimal source/build files. Do not commit
  dependency caches, `node_modules`, `vendor`, virtualenvs, `bin`, `obj`, jars,
  or generated build products.

### Status Handling

Try to package every case in the two runs, but do not fake success.

- For `verified_keep`: migrate to a complete case package.
- For `skipped_existing_record`: verify that the existing package is present or
  record why no new package is needed.
- For `no_behavior_diff`: do not package as silent drift unless you find and run
  a corrected probe that produces a real old/new semantic difference.
- For `blocked`, `blocked_dependency_or_runtime`, `blocked_offline_reproduction`,
  and `source_check_blocked`: attempt promotion only when you can resolve the
  blocker locally and produce old/new successful runs. Otherwise, record the
  blocker in a conversion ledger and continue.

Keep incomplete drafts out of `docs/case-bank/cases/`. If a draft cannot be
made valid, move or keep it under a non-packaged work area such as
`docs/case-bank/work-in-progress/` or summarize it in a ledger. The final pack
command must still run over all valid collected packages.

### Suggested Parallel Shards

Use these shards if multiple instances are available:

```text
Shard A: sequential_30 DOTNET + GO
DOTNET-05 DOTNET-09 GO-001 GO-003 GO-006 GO-007

Shard B: sequential_30 JS
JS-01 JS-02 JS-03 JS-04 JS-05 JS-10

Shard C: sequential_30 JVM
JVM-JAVA-01 JVM-JAVA-02 JVM-JAVA-03 JVM-JAVA-04

Shard D: reverse_50 Ruby + PHP
RB-RSP-009 RB-RACK-006 PHP-08

Shard E: reverse_50 Python
PY-SD-001 PY-SD-005 PY-SD-007 PY-SD-008

Shard F: blocked/no-diff/source-check ledger and opportunistic promotions
all remaining IDs from sequential_30 and reverse_50
```

Each shard should finish by regenerating indexes if it changed case metadata.
The final coordinator should run the full package command after merging all
completed folders.

### Workflow

1. Check the working tree:

   ```powershell
   git status --short
   ```

2. Read existing examples in the same ecosystem before writing a new case.

3. For each assigned ID, inspect the verification artifact:

   ```powershell
   Get-ChildItem data\verification\sequential_30\<ID>
   Get-Content -Raw data\verification\reverse_50\details\<ID>.json
   ```

4. Recover the minimal probe from the verification artifact or reconstruct it
   from the run commands, source notes, and stdout/stderr. Keep the probe tiny.

5. Create the complete case folder under the best `primary_scenario` from the
   taxonomy in `final-plan.md`.

6. Reduce old/new behavior into `hidden/expected.json`. Prefer structured JSON
   assertions when the probe emits JSON; otherwise use stable stdout fragments
   or fields consistent with existing examples.

7. Regenerate indexes:

   ```powershell
   python -m case_bank index build --out docs/case-bank/indexes/
   ```

8. Run validation/tests that are relevant and available:

   ```powershell
   python -m pytest silent_drift_miner/tests/test_case_bank.py
   ```

9. Build the eval package even if some run IDs remain unpackaged:

   ```powershell
   python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
   ```

   If packaging fails because of an incomplete case folder, fix that folder or
   move the incomplete work out of `docs/case-bank/cases/`, then run the pack
   command again. The final eval package must contain all complete packages that
   exist at that point.

### Required Final Report

End with a concise report:

- case IDs packaged
- case IDs already covered or deduplicated
- case IDs still blocked and their first blocker
- exact package output path, usually `eval_package/`
- validation commands run and pass/fail result
- files changed

Do not claim a case is complete unless the case folder exists, metadata indexes
regenerate, and the eval package command succeeds with it included.
