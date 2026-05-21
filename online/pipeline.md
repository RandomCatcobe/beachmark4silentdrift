# Online Pipeline Contract

## Purpose

The online pipeline preserves service/API drift evidence that cannot be made
locally deterministic. It borrows the offline pipeline's discipline around
stable artifacts, source ledgers, and explicit triage decisions, but stops
before reproduction packaging.

## Evidence Ladder

| Level | Meaning | Typical sources |
|---|---|---|
| S0 | Unchecked lead | Search hit, draft note, SEO article |
| S1 | Developer report | Blog, forum post, support thread |
| S2 | Vendor-notice mirror | Third-party mirror of signed vendor notice |
| S3 | Primary source | Official docs, official issue tracker, vendor changelog |
| S4 | Live proof | Fresh credentialed probe or user-supplied production log |

## Triage Decisions

| Decision | Use when |
|---|---|
| `accept_online_case` | The evidence supports a live-service behavior or contract change, but offline reproduction is blocked. |
| `boundary_needs_source` | The shape is plausible, but current evidence is mostly secondary or contradictory. |
| `operational_constraint` | The lead is an integration rule, timeout, pagination, or retry constraint rather than a clear drift. |
| `reject_client_mapping_only` | The platform behavior is documented and the failure is mainly incomplete client-side mapping. |
| `exclude_hard_break` | The endpoint clearly errors or stops working rather than continuing with wrong results. |

## Routing Rules

All accepted or boundary online cases remain under `online/case-library/`.

They must not be copied into:

- `docs/*idea-bank*.md`
- `docs/case-bank/`
- `data/packages/`
- offline oracle or benchmark packaging outputs

## Required Case Fields

Each online case record should include:

- case id and slug
- status and triage decision
- platform/API surface
- endpoint/function/field, if known
- drift category
- evidence strength
- checked source URLs
- what changed
- why offline reproduction is not possible
- whether the case is silent, documented, or only operational

## Offline Reproduction Policy

Set `offline_reproduction: not_possible` unless the case can be converted into a
deterministic local package-version, runtime-version, or mockable-service case.

Typical blockers:

- live platform credentials
- account-segment rollout or permissions
- production historical orders
- live callback retries or hosted push behavior
- vendor-side mutable state that cannot be pinned

