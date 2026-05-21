# E-Commerce API Online Line Triage - 2026-05-21

Run ID: `ONLINE-20260521-001`

This artifact line-manages seven online platform/API drift leads supplied in the
current batch. The output deliberately does not create or update an idea bank.
Every retained case is routed only to `online/case-library/` and is marked as
not reproducible offline.

## Output Summary

| Bucket | Count | Entries |
|---|---:|---|
| Accepted online-only cases | 2 | OL-ECOM-001, OL-ECOM-007 |
| Boundary / needs stronger source | 3 | OL-ECOM-002, OL-ECOM-003, OL-ECOM-006 |
| Operational constraint, not yet drift | 1 | OL-ECOM-004 |
| Rejected as core drift | 1 | OL-ECOM-005 |

## Primary Online Case Queue

| Case ID | Candidate | Route | Why it stays online-only |
|---|---|---|---|
| OL-ECOM-001 | JD Union item ID moved from static numeric SKU-like ID to dynamic string itemId | `online/case-library/cases/ol-ecom-001-jd-union-dynamic-itemid.md` | Requires JD Union account policy, sceneId permission, and live JD API behavior. |
| OL-ECOM-007 | Amazon SP-API `OrderItemId` mismatch across Orders and Finances endpoints | `online/case-library/cases/ol-ecom-007-amazon-spapi-orderitemid-mismatch.md` | Requires SP-API credentials and a real historical order with financial events. |

## Line Ledger

| ID | Platform/API | Decision | Evidence strength | Offline reproduction | Note |
|---|---|---|---|---|---|
| OL-ECOM-001 | JD Union / goods APIs | `accept_online_case` | high for documented service-contract change | `not_possible` | JD Union notice mirrors state that Union item IDs became dynamic strings with A/B segments, were introduced from 2024-03-06, and later became required for all media APIs by 2024-09-30. |
| OL-ECOM-002 | JD order API | `boundary_needs_source` | medium-low | `not_possible` | Current evidence is a practical article/search result about time-window and 90-day constraints. No primary JD order doc was confirmed in this pass. |
| OL-ECOM-003 | Taobao `taobao.trades.sold.get` | `boundary_needs_source` | medium-low | `not_possible` | Developer article claims a 30-minute query-window trap, but the official API page checked here confirms 3-month access, fields, status/type defaults, and pagination details, not the 30-minute limit. |
| OL-ECOM-004 | Taobao callback / order-status push | `operational_constraint` | medium-low | `not_possible` | Developer article claims a 5-second callback timeout and three retries. Official message-service pages found in this pass describe retry behavior in other contexts but did not confirm this exact rule. |
| OL-ECOM-005 | Taobao order status `TRADE_CLOSED` | `reject_client_mapping_only` | medium for client-risk, low for drift | `not_possible` | Official docs list `TRADE_CLOSED`; failure is incomplete client mapping, not a verified platform drift. |
| OL-ECOM-006 | Taobao order number / `tid` format | `boundary_needs_source` | medium-low | `not_possible` | Developer article claims order IDs expanded beyond 18 numeric digits. Current official docs still present `tid` as a number in examples, so this needs primary confirmation or production evidence. |
| OL-ECOM-007 | Amazon SP-API Orders/Finances | `accept_online_case` | high | `not_possible` | GitHub issue reports same-order `OrderItemId` mismatch beginning 2023-01-08; official docs confirm the two live endpoints and successful response surfaces. |

## Checked Sources

- JD developer article: https://cloud.tencent.com/developer/article/2566489
- JD Union 2024-03 notice mirror: https://www.taokeshow.com/55048.html
- JD Union 2024-08 notice mirror: https://www.taokeshow.com/60150.html
- JD Union notice mirror with itemId details: https://www.dingdanxia.com/article/231.html
- JD order time-window lead: https://juejin.cn/post/7637372855349968932
- JD order time-window secondary article: https://www.sohu.com/a/1019932956_122400414
- Taobao order article corrected URL: https://cloud.tencent.com/developer/article/2566440
- Taobao official order sync guide: https://developer.alibaba.com/docs/doc.htm?articleId=1029&docType=1&source=search&treeId=1
- Taobao official `taobao.trades.sold.get` docs: https://developer.alibaba.com/docs/api.htm?apiId=46&source=search
- Taobao official status docs: https://open.fliggy.com/docs/doc.htm?articleId=102856&docType=1&treeId=780
- Amazon SP-API issue: https://github.com/amzn/selling-partner-api-models/issues/427
- Amazon `getOrderItems` docs: https://developer-docs.amazon.com/sp-api/lang-en_US/reference/getorderitems
- Amazon `listFinancialEventsByOrderId` docs: https://developer-docs.amazon.com/sp-api/lang-en_US/reference/listfinancialeventsbyorderid

## Corrections From Source Batch

- The supplied Tencent Cloud URL `https://cloud.tencent.com/developer/article/2531819`
  opens as an unrelated Linux process-control article. The matching Taobao
  order article found during this pass is
  `https://cloud.tencent.com/developer/article/2566440`.
- The Amazon issue URL supplied under the old
  `selling-partner-api-docs/issues/427` path redirects through repository
  migration. The checked canonical issue is
  `https://github.com/amzn/selling-partner-api-models/issues/427`.

