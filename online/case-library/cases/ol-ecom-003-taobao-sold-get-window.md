# OL-ECOM-003: Taobao Sold-Order Query Window

Status: boundary

Decision: `boundary_needs_source`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: Taobao Open Platform
- API surface: `taobao.trades.sold.get`
- Fields/concepts: `start_created`, `end_created`, paging, order sync window

## Drift Category

Time-window and incremental-sync semantics.

## Checked Situation

The corrected Tencent Cloud article claims developers can miss orders when
polling `taobao.trades.sold.get` with a one-hour window because the effective
single-query range should be limited to 30 minutes.

The official API page checked here confirms that the endpoint searches sold
transactions within three months, returns partial trade data, uses creation-time
ordering, has paging controls, and has status/type defaults. It did not confirm
the claimed 30-minute hard limit in this pass. This keeps the lead in boundary
status rather than accepted online drift.

## Why Offline Reproduction Is Not Possible

The behavior depends on live Taobao order data and live endpoint handling of
wide windows. A mock can demonstrate missed-order logic, but not platform
behavior.

## Evidence URLs

- https://cloud.tencent.com/developer/article/2566440
- https://developer.alibaba.com/docs/api.htm?apiId=46&source=search
- https://developer.alibaba.com/docs/doc.htm?articleId=1029&docType=1&source=search&treeId=1

## Next Source Task

Find official docs, error responses, or production logs showing what happens
when the query window exceeds the alleged limit.

