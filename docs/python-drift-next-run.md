# Python Drift Next-Run Brief

This brief prepares the next model-guided discovery batch. It does not start the batch.

Release context: `v0.11.0` includes the Markdown memory helpers and this
pre-run brief. The next action is still waiting for an explicit instruction to
begin searching.

## Batch Budget
- Target discovery attempts: 10
- Start only when explicitly asked to begin searching.
- Append every useful idea or useful failure back to Markdown.

## Package Focus
- None

## Operating Rules
- Read the idea bank before searching.
- Prefer a new package, API surface, version range, or drift category.
- Do not clone accepted cases or rejected dead ends.
- Record rejections when they teach future runs what to avoid.
- Promote only evidence-backed, deterministic, local Python behavior changes.
- Keep source quotes short and paraphrase where possible.

## Avoid Summary
# Python Drift Avoid Summary

## Packages Already Mentioned
- None yet

## API Surfaces Already Mentioned
- None yet

## Accepted Case Anchors
- None

## Rejection Lessons
- None

## Append Commands
```bash
silent-drift-miner autodiscovery idea ...
silent-drift-miner autodiscovery reject ...
silent-drift-miner autodiscovery accept ...
silent-drift-miner autodiscovery log ...
```

## Current Idea Bank
# Python Drift Idea Bank

Append-only memory for Python silent-drift discovery ideas, rejected leads, duplicate warnings, and accepted cases.

## Current Run Log
# Python Drift Run Log

Append-only batch notes for model-guided Python silent-drift discovery.

