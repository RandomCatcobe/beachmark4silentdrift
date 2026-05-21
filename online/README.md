# Online Service Drift Pipeline

This folder is the live-service counterpart to the local/offline reproduction
pipeline in the repository.

It is for platform APIs whose behavior depends on live vendor systems,
credentials, account policy, historical orders, or hosted callbacks. These
cases are useful evidence for silent behavioral drift, but they are not
eligible for the offline benchmark case bank.

## Hard Boundary

- Do not route these cases to any idea bank.
- Do not route these cases to `docs/case-bank/`.
- Do not package these cases as offline evaluation tasks.
- Keep even fully silent live-service drift in this folder.
- Mark every case with `offline_reproduction: not_possible`.

## Lifecycle

```text
raw_online_lead
  -> source_checked
  -> online_triaged
  -> online_case_recorded
  -> blocked_offline_reproduction
```

## Artifacts

- `pipeline.md`: the online-specific pipeline contract.
- `ecommerce-api-line-triage-20260521.md`: the checked ledger for the current
  e-commerce/API batch.
- `case-library/`: standalone case library for online-only cases.

## Current Run

Run ID: `ONLINE-20260521-001`

Scope: seven e-commerce platform/API drift leads covering JD Union, JD order
sync, Taobao order sync/callback/status/ID behavior, and Amazon SP-API.

Result: two accepted online-only cases, four boundary cases needing stronger
source or live proof, and one rejected-as-core-drift client mapping risk.

