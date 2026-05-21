# OL-ECOM-005: Taobao `TRADE_CLOSED` Client Mapping Risk

Status: rejected-core

Decision: `reject_client_mapping_only`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: Taobao Open Platform
- API surface: order status fields
- Fields/concepts: `TRADE_CLOSED`, `TRADE_NO_CREATE_PAY`, `TRADE_SUCCESS`

## Drift Category

Status-enum mapping risk, not verified platform drift.

## Checked Situation

The developer article describes clients that only handle `TRADE_SUCCESS` and
`TRADE_NO_CREATE_PAY`, then incorrectly treat `TRADE_CLOSED` as if no order was
created. Official Taobao status documentation lists `TRADE_CLOSED` as a real
transaction status, and the `taobao.trades.sold.get` docs include status values
and defaults.

This is a real integration risk, but current evidence points to incomplete
client-side state mapping rather than a silent platform behavior change.

## Why Offline Reproduction Is Not Possible

The original production impact depends on live orders and client mapping code.
The conceptual bug can be unit-tested locally, but that would not make it an
online drift case.

## Evidence URLs

- https://cloud.tencent.com/developer/article/2566440
- https://open.fliggy.com/docs/doc.htm?articleId=102856&docType=1&treeId=780
- https://developer.alibaba.com/docs/api.htm?apiId=46&source=search

