# OL-ECOM-006: Taobao Order ID Format Expansion

Status: boundary

Decision: `boundary_needs_source`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: Taobao Open Platform
- API surface: order ID / `tid`
- Fields/concepts: transaction ID, order-number validation

## Drift Category

ID format drift.

## Checked Situation

The corrected Tencent Cloud article says older Taobao order IDs were treated as
18-digit numeric values by some client code, while later values could become
longer and include letters. That is a plausible silent loss mode: strict local
validators can filter valid platform orders while the API call itself succeeds.

This pass did not find primary Taobao documentation confirming that exact
format expansion. The current official `taobao.trades.sold.get` page still
shows `tid` as a number with numeric examples, which makes the claim worth
preserving but not yet accepted.

## Why Offline Reproduction Is Not Possible

The useful proof would be a real Taobao response containing a newer order ID
shape or an official field-format update. A local validator test can only model
the downstream failure.

## Evidence URLs

- https://cloud.tencent.com/developer/article/2566440
- https://developer.alibaba.com/docs/api.htm?apiId=46&source=search

## Next Source Task

Search for official field-format notices, SDK model changes, or anonymized
production responses showing non-18-digit or non-numeric `tid` values.

