# Online Case Library

Standalone case library for online-only platform/API drift.

These records are deliberately not benchmark packages. They preserve checked
evidence, business impact, and the reason the case cannot be reproduced in the
repository's offline pipeline.

## Index

| Case ID | Status | Decision | Case file |
|---|---|---|---|
| OL-ECOM-001 | accepted | `accept_online_case` | `cases/ol-ecom-001-jd-union-dynamic-itemid.md` |
| OL-ECOM-002 | boundary | `boundary_needs_source` | `cases/ol-ecom-002-jd-order-time-window.md` |
| OL-ECOM-003 | boundary | `boundary_needs_source` | `cases/ol-ecom-003-taobao-sold-get-window.md` |
| OL-ECOM-004 | boundary | `operational_constraint` | `cases/ol-ecom-004-taobao-callback-timeout.md` |
| OL-ECOM-005 | rejected-core | `reject_client_mapping_only` | `cases/ol-ecom-005-taobao-trade-closed-mapping.md` |
| OL-ECOM-006 | boundary | `boundary_needs_source` | `cases/ol-ecom-006-taobao-order-id-format.md` |
| OL-ECOM-007 | accepted | `accept_online_case` | `cases/ol-ecom-007-amazon-spapi-orderitemid-mismatch.md` |

Machine-readable ledger: `cases.jsonl`.

## Shared Marker

Every record in this library has:

```yaml
offline_reproduction: not_possible
idea_bank_route: forbidden
offline_case_bank_route: forbidden
```

