# OL-ECOM-002: JD Order Query Time Window

Status: boundary

Decision: `boundary_needs_source`

Offline reproduction: `not_possible`

Idea-bank route: forbidden

## Platform And Surface

- Platform: JD Open Platform
- API surface: `jd.order.search` / `jingdong.pop.order.search`
- Fields/concepts: `startTime`, `endTime`, `timeType`

## Drift Category

Time-window and incremental-sync semantics.

## Checked Situation

The current lead says JD order query windows must use precise timestamps, stay
within a bounded range, and avoid querying too far back, or clients can receive
empty or unstable results. The shape is relevant for ERP missed-order failures:
old clients may keep polling with wide windows and silently interpret an empty
result as "no orders."

The evidence found in this pass is still secondary. The Juejin source did not
render useful content through the available browser view, and the matching
search/source trail is a practical article rather than primary JD docs.

## Why Offline Reproduction Is Not Possible

The failure depends on live JD order data, account permissions, endpoint policy,
and possibly production pagination/latency. A local mock would only model the
risk.

## Evidence URLs

- https://juejin.cn/post/7637372855349968932
- https://www.sohu.com/a/1019932956_122400414

## Next Source Task

Find primary JD documentation or a developer ticket confirming exact query
window, historical range, and empty-result behavior.

