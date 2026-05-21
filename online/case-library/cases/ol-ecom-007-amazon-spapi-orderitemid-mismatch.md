# OL-ECOM-007: Amazon SP-API `OrderItemId` Cross-Endpoint Mismatch

Status: accepted

Decision: `accept_online_case`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: Amazon Selling Partner API
- API surface: Orders v0 and Finances v0
- Endpoints: `getOrderItems`, `listFinancialEventsByOrderId`
- Field: `OrderItemId`

## Drift Category

Cross-endpoint ID semantics drift.

## Checked Situation

The GitHub issue reports that, starting around 2023-01-08, the same shipped
order item could return different `OrderItemId` values from Orders and Finances
endpoints while other fields such as SKU still lined up. The API calls remain
successful, so clients that join order items to financial events by
`OrderItemId` can silently fail reconciliation or fall back to weaker matching.

Official Amazon docs confirm that `getOrderItems` returns detailed order-item
information and that `listFinancialEventsByOrderId` returns financial events
for a specified order. The mismatch itself is from the GitHub bug report, not an
official changelog.

## Why Offline Reproduction Is Not Possible

The proof requires Amazon SP-API credentials, a seller account, a real order,
and financial events for that order. Sandbox examples cannot prove the reported
production cross-endpoint mismatch.

## Evidence URLs

- https://github.com/amzn/selling-partner-api-models/issues/427
- https://developer-docs.amazon.com/sp-api/lang-en_US/reference/getorderitems
- https://developer-docs.amazon.com/sp-api/lang-en_US/reference/listfinancialeventsbyorderid

