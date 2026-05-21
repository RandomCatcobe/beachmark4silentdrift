# Tag Taxonomy

Canonical reference: `final-plan.md`.

## Primary Scenario

Exactly one value becomes the case folder path segment:

- `validation-and-policy`
- `parsing-and-ingestion`
- `serialization-and-binding`
- `time-and-localization`
- `state-and-lifecycle`
- `routing-and-identity`
- `commerce-order-flow`
- `inventory-and-fulfillment`
- `observability-and-logging`
- `runtime-semantics`

## Ecosystem And Language

Recommended ecosystem values:

- `python`
- `js`
- `go`
- `ruby`
- `php`
- `jvm`
- `dotnet`
- `api-platform`

Recommended language values:

- `python`
- `javascript`
- `typescript`
- `go`
- `ruby`
- `php`
- `java`
- `kotlin`
- `scala`
- `csharp`
- `fsharp`
- `vb`

For platform API cases, use `api-platform` as an ecosystem and record platform
names separately when the schema adds a `platforms` field.

## Application Scenario Extensions

Application scenarios may include primary scenarios plus domain-oriented
secondary tags:

- `identity-and-contact-data`

## API Surface

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

## Drift Pattern

- `default-changed`
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

Do not use `default-policy-changed`; it is merged into `default-changed`.

## Failure Mode

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

## Determinism / Benchmark Construction

- `local-deterministic`
- `package-cache`
- `runtime-pair`
- `service-contract`
- `mockable-service`
- `requires-live-credential`
