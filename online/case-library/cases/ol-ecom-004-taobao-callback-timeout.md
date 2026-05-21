# OL-ECOM-004: Taobao Callback Timeout And Retry Behavior

Status: boundary

Decision: `operational_constraint`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: Taobao Open Platform
- API surface: order-status callback / `trade_status_changed` style messages
- Fields/concepts: callback response deadline, retry count, order-status push

## Drift Category

Callback timeout and retry semantics.

## Checked Situation

The corrected Tencent Cloud article claims Taobao callbacks time out after five
seconds, then retry three times before no longer pushing that order-status
change. That is a useful online integration risk, especially for clients that
perform slow ERP sync or SMS work inline before returning success.

This pass did not find a primary Taobao document confirming the exact five
second / three retry rule for this specific order callback path. Some official
message-service pages describe retry behavior in other contexts, which means
the rule may be product-specific or outdated.

## Why Offline Reproduction Is Not Possible

The behavior depends on live callback delivery, vendor retry scheduling, and a
registered public callback endpoint. Local tests can only validate the client
architecture, not the vendor retry semantics.

## Evidence URLs

- https://cloud.tencent.com/developer/article/2566440

## Next Source Task

Find the official Taobao message-service page for the exact order-status
callback channel, or obtain a production callback log with retry timestamps.

