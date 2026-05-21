# Ecommerce API Silent Drift Idea Bank

Append-only memory for ecommerce/open-platform API silent-drift evidence, candidate scenarios, search patterns, and batch notes.

## Seed Context From User - Not Counted

The following user-provided leads are preserved as background evidence only. They do not count toward the follow-up discovery target.

| Seed ID | Name | API / Surface | Silent drift pattern | Source |
|---|---|---|---|---|
| SEED-20260520-001 | Taobao order detail field semantics | `taobao.trade.fullinfo.get` | Detail query succeeds, but shipping, printing, inventory, or settlement logic can silently use the wrong parent/suborder, payment, or status scope. | [Taobao Open Platform](https://developer.alibaba.com/docs/api.htm?apiId=54) |
| SEED-20260520-002 | Taobao receiver address field semantics | `taobao.trade.fullinfo.get` | `receiver_city` / `receiver_district` are not stable city/district business concepts, so ERP/WMS routing keyed only on city can pick the wrong logistics rule. | [Taobao Open Platform](https://developer.alibaba.com/docs/api.htm?apiId=54) |
| SEED-20260520-003 | Taobao message ordering | Message service for product, order, and reverse-order messages | Old state can arrive after newer state and overwrite local order, refund, stock, or customer-service state unless consumers query authoritative detail APIs. | [Taobao message docs](https://developer.alibaba.com/docs/doc.htm?articleId=121426&docType=1&treeId=735) |
| SEED-20260520-004 | JD order status callback silently discarded | `/common/notify/orderstatus` | If `orderId` does not match, the callback can return success while the order system discards the event, leaving the order stuck. | [JD operator interface docs](https://opendoc.jd.com/isp_all/api/interfacelist/014-commonnotifyorderstatus.html) |
| SEED-20260520-005 | Meituan merchant ID is unstable | `waimai.poi.food` and merchant-food APIs | Numeric `wm_poi_id` can change dynamically; old caches can silently point cart, menu, store, or order operations at the wrong object. | [Meituan enterprise waimai API](https://h5.dianping.com/app/bep-docs/sky-doc/canyinopenapi/waimai_api.html) |
| SEED-20260520-006 | Pinduoduo order field openness retrofit | Kuaimai Pinduoduo order information openness retrofit | Fields stop returning or are replaced by system fields, shifting order, refund, SKU, and payment logic into stale/fallback paths. | [Kuaimai Open Platform](https://open.kuaimai.com/docs/question/%E7%B3%BB%E7%BB%9F%E5%85%AC%E5%91%8A/%E6%8B%BC%E5%A4%9A%E5%A4%9A%E8%AE%A2%E5%8D%95%E4%BF%A1%E6%81%AF%E5%BC%80%E6%94%BE%E6%94%B9%E9%80%A0%E5%85%AC%E5%91%8A/) |
| SEED-20260520-007 | Generic integration silent failure evidence | MuleSoft / sync flows | HTTP status and logs can look successful while CRM, ERP, or inventory data remains missing, stale, or partially updated. | [Stacksync silent failures](https://www.stacksync.com/blog/detect-silent-failures-mulesoft) |
| SEED-20260520-008 | Ecommerce order-to-ERP sync chain evidence | Platform orders synced into ERP | Order pull, cleaning, SKU mapping, warehouse routing, and status writeback create natural cascade paths for silent field/status drift. | [AI Indeed order sync architecture](https://www.ai-indeed.com/encyclopedia/20019.html) |

## RUN-20260520-001: Follow-up Discovery Batch - 10 New Items

- Operator: Codex plus two parallel research agents.
- Target: 10 new evidence-backed ideas, excluding all user-provided seed items.
- Result: 10/10 new items found and recorded.
- Duplicate handling:
  - The Kuaimai/Pinduoduo openness retrofit was returned by a helper agent but is excluded from the new count because it duplicates `SEED-20260520-006`.
  - Shopify, eBay, and Kuaishou remain useful overflow leads, but the run stops at 10 counted items.

| New ID | Name | API / Surface | Evidence | Silent drift pattern | Source |
|---|---|---|---|---|---|
| NEW-20260520-001 | Douyin order sync returns success but order center is empty | Douyin mini-app guarantee-payment order sync `/api/apps/order/v2/push` | Official FAQ says order sync can return success while the order center cannot show the order; causes include missing order-display whitelist, empty `item_list`, or the user not granting order-display authorization. | Developer-side API call is successful, but user/order-center business state is absent. | [Douyin Open Platform order sync](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/payment/ecpay/order/order-sync) |
| NEW-20260520-002 | Amazon feed status hides per-record business failures | Amazon SP-API Feeds API | `processingStatus=DONE` means feed processing completed; developers must retrieve the processing report to see successful records and records with errors. | Feed/task status looks complete while SKU, listing, inventory, refund, or adjustment records may not have taken effect. | [Submit a feed](https://developer-docs.amazon.com/sp-api/docs/submit-a-feed), [Listings workflow guide](https://developer-docs.amazon.com/sp-api/docs/building-listings-management-workflows-guide) |
| NEW-20260520-003 | Walmart processed feed does not imply element success | Walmart Marketplace Feeds | `feedStatus=PROCESSED` only means the feed finished processing; it does not imply individual element success, and object statuses can still be `DATA_ERROR`, `SYSTEM_ERROR`, or `TIMEOUT_ERROR`. | SKU-level item, price, or inventory updates can fail while the feed-level terminal state looks green. | [Walmart Marketplace feeds overview](https://developer.walmart.com/cl-marketplace/docs/feeds-overview) |
| NEW-20260520-004 | Adobe Commerce bulk API accepts queue entries that later fail | Adobe Commerce / Magento REST bulk and async APIs | Bulk responses can show `errors:false` and per-request `status:"accepted"` because records were only queued; docs show accepted duplicate customer creates that later fail and require operation-status polling. | Transport/queue acceptance is mistaken for business success unless the integration reconciles per-operation failure status. | [Bulk endpoints](https://developer.adobe.com/commerce/webapi/rest/use-rest/bulk-endpoints/), [Operation status endpoints](https://developer.adobe.com/commerce/webapi/rest/use-rest/operation-status-endpoints/) |
| NEW-20260520-005 | BigCommerce webhook delivery can duplicate lightweight events | BigCommerce store/order/product webhooks | Webhook payloads are lightweight and often contain IDs; docs warn duplicate callbacks can occur from retries or network issues and apps must use idempotency. | A delivered webhook can cause duplicate processing or stale fetch-and-overwrite behavior unless the app dedupes and re-queries authoritative state. | [BigCommerce webhooks](https://docs.bigcommerce.com/developer/docs/integrations/webhooks/overview) |
| NEW-20260520-006 | Mercado Libre notifications require ACK plus resource refetch | Mercado Libre Global Selling notifications | Docs describe retries if HTTP 200 is not returned promptly, advise acknowledging before fetching resource state, and provide missed-feed recovery. | Duplicate, delayed, or missed notifications can silently corrupt local order, inventory, or shipment state if consumers treat event delivery as final state. | [Mercado Libre receive notifications](https://global-selling.mercadolibre.com/devsite/api-docs/receive-notifications) |
| NEW-20260520-007 | Taobao online logistics send can create flow without changing trade status | `taobao.logistics.online.send` | Service docs note that when no waybill number is provided, the call can start online shipment flow but the trade state will not become seller-shipped until `taobao.logistics.online.confirm` is called. | ERP can record "shipment API succeeded" while the platform trade is still not actually marked shipped. | [Taobao logistics online send](https://open.fliggy.com/docs/doc.htm?articleId=10687&docType=2&treeId=568) |
| NEW-20260520-008 | Taobao sensitive order data changes to masked/OAID-dependent data | Taobao order APIs and order push under consumer-sensitive-information protection | Platform docs describe receiver name, mobile, phone, and detailed address data becoming masked; OAID generation depends on specific fields. | Fields remain present but become masked or unusable for downstream ERP/WMS, merge-shipment, address matching, or waybill workflows unless OAID handling is implemented. | [Taobao sensitive information protection / OAID](https://developer.alibaba.com/docs/doc.htm?articleId=120175&docType=1&source=search&treeId=796) |
| NEW-20260520-009 | Etsy webhooks carry resource pointers and may replay | Etsy Open API webhooks | Order events provide a resource URL rather than full authoritative state; retry/recovery behavior means webhook IDs and timestamps are needed for duplicate/replay handling. | Event delivery is not enough to update order state safely; consumers must idempotently fetch and reconcile current resource state. | [Etsy webhooks](https://developer.etsy.com/documentation/essentials/webhooks/) |
| NEW-20260520-010 | Google Merchant product input success is not product approval | Google Merchant Center Merchant API `productInputs.insert` and product status | A successful product input write can later process into a product with normalized attributes, disapproved destinations, or item-level issues visible only through status APIs. | Product upload/update succeeds, but listing eligibility and final persisted product state diverge after asynchronous processing. | [Merchant API add and manage products](https://developers.google.com/merchant/api/guides/products/add-manage) |

## Overflow Candidates Not Counted In This Ten-Item Run

- Shopify webhooks: useful for duplicate/out-of-order/missed webhook state drift. Source: [Shopify webhooks docs](https://shopify.dev/docs/apps/build/webhooks).
- eBay Sell Feed API: useful for completed or completed-with-error feed tasks whose result files contain per-record listing/fulfillment/order-ack failures. Sources: [Sell Feed API overview](https://developer.ebay.com/api-docs/sell/static/feed/fx-feeds-overview.html), [General feed tasks](https://developer.ebay.com/api-docs/sell/static/feed/general-feed-tasks.html).
- Kuaishou privacy encryption and e-waybill transition: service-provider notes and reports describe order privacy data encryption and WMS/e-waybill routing failures, but it needs stronger official-open-platform confirmation before promotion.

## Handoff Search Instructions

Do not search for generic "API bug" reports. Search for integration semantics where transport success and business success diverge.

High-value query shapes:

```text
返回成功 但是 没有生效 订单
接口成功 订单状态 未更新
订单同步 成功 ERP 不一致
退款状态 同步 异常 发货
消息 顺序性 反查 订单状态
字段 不返回 改造 订单 拼多多
SKU 映射 错发 ERP
库存同步 成功 超卖
回调 返回成功 丢弃 卡单
状态回写 成功 未生效
平台状态 子订单状态 不返回
商家编码 替换 系统SKU
```

```text
ecommerce API returns 200 but order not updated
silent sync failure inventory ecommerce
order webhook out of order status overwritten
Shopify webhook order status stale
WooCommerce API success but stock not updated
ERP order sync mismatch refund status
SKU mapping wrong item shipped
webhook delivered but business state unchanged
silent failure API integration ecommerce
inventory sync green but overselling
feed processing report errors status done inventory
```

Priority sites:

- Official docs: Taobao/Alibaba Open Platform, JD Zeus/Jingmai/Tianmu docs, Pinduoduo Open Platform, Meituan/Dianping Open Platform, Ele.me Open Platform, Douyin Shop Open Platform, Kuaishou Shop Open Platform, Shopify, Amazon SP-API, eBay, Walmart Marketplace, Adobe Commerce, BigCommerce, Etsy, Google Merchant Center, WooCommerce, Magento.
- Service-provider docs: Kuaimai, Jushuitan, Wangdian, Guanyi, Mabang ERP, Dianxiaomi, Saihe, Shopify/WooCommerce/Magento connector docs.
- Secondary discussions: official platform forums, merchant communities, CSDN, cnblogs, Juejin, SegmentFault, GitHub issues, Stack Overflow, Shopify Community, Amazon Seller Forums, Reddit `r/shopify`.

Prefer official "notes", "compatibility retrofit", "FAQ", "field description", "webhook retry/idempotency", and "processing report" docs over merchant complaints because they are easier to cite in papers and to turn into dataset construction rules.
