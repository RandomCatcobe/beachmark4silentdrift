# Tag Taxonomy

The folder path gives one primary browse path. Tags provide all other views.

## Primary Scenario Tags

Use one as `primary_scenario` for the case folder path.

- `validation-and-policy`: validators, business-rule checks, allow/reject changes.
- `parsing-and-ingestion`: CSV, query strings, dotenv, XML/JSON parsing, imports.
- `serialization-and-binding`: serializers, config binders, object mapping, shape changes.
- `time-and-localization`: timezones, timestamps, locale, charset, calendars, ICU.
- `state-and-lifecycle`: async ordering, callbacks, webhook delivery, object lifecycle.
- `routing-and-identity`: path matching, entity IDs, SKU/store IDs, identity resolution.
- `commerce-order-flow`: order sync, refund, shipment, payment, ERP state propagation.
- `inventory-and-fulfillment`: stock updates, warehouse routing, oversell prevention.
- `observability-and-logging`: log format, tracing, monitoring, silent success signals.
- `runtime-semantics`: language/runtime behavior not tied to one business domain.

## Ecosystem And Language Tags

Use both when useful:

- `ecosystems`: `python`, `js`, `go`, `ruby`, `php`, `jvm`, `dotnet`, `api-platform`
- `languages`: `python`, `javascript`, `typescript`, `go`, `ruby`, `php`, `java`,
  `kotlin`, `scala`, `csharp`, `fsharp`, `vb`

For platform API cases, the ecosystem can be `api-platform` and the platform can
be recorded separately, for example `platforms: ["taobao", "jd", "shopify"]`.

## API Surface Tags

- `library-api`
- `runtime-api`
- `framework-api`
- `cli`
- `config-file`
- `webhook`
- `message-service`
- `rest-api`
- `graphql-api`
- `database-orm`
- `validator`
- `parser`
- `serializer`
- `router`
- `logger`

## Drift Pattern Tags

- `default-changed`
- `default-policy-changed`
- `field-semantics-changed`
- `field-removed-or-masked`
- `type-or-shape-changed`
- `parser-rule-changed`
- `ordering-changed`
- `bundled-data-changed`
- `runtime-locale-changed`
- `validation-relaxed`
- `validation-strictness-increased`
- `success-but-no-effect`
- `out-of-order-event`
- `old-state-overwrite`

## Failure Mode Tags

- `silent-value-change`
- `silent-acceptance-change`
- `silent-rejection-change`
- `wrong-entity`
- `wrong-route`
- `stale-state`
- `missing-field`
- `wrong-type`
- `wrong-order`
- `wrong-timezone`
- `wrong-locale`
- `wrong-inventory`
- `wrong-fulfillment`
- `wrong-refund-or-payment-state`

## Benchmark Construction Tags

- `local-deterministic`: no network/service needed during reproduction.
- `package-cache`: needs locally installed package versions.
- `runtime-pair`: needs old/new runtime versions.
- `service-contract`: source is a platform or SaaS API contract.
- `mockable-service`: can be reproduced with mocks/history capture.
- `requires-live-credential`: not suitable until reduced or mocked.

## Example Classification

```json
{
  "case_id": "PHP-07",
  "primary_scenario": "time-and-localization",
  "application_scenarios": ["time-and-localization", "runtime-semantics"],
  "ecosystems": ["php"],
  "languages": ["php"],
  "api_surfaces": ["library-api", "runtime-api"],
  "drift_patterns": ["default-changed"],
  "failure_modes": ["wrong-timezone", "silent-value-change"],
  "benchmark_construction": ["local-deterministic", "package-cache"]
}
```
