# DOTNET-08: FluentValidation default EmailAddress behavior changed

## API Or Behavior Under Test

RuleFor(x => x.Email).EmailAddress() in FluentValidation.

## Version Boundary

FluentValidation 8.6.2 -> 9.0.0

## Old Behavior

The default email validator rejects borderline values that do not match the older regex-style policy.

## New Behavior

The same validator accepts values that satisfy the simpler ASP.NET Core-compatible policy.

## Why The Drift Is Silent

Validation returns a normal result object in both versions; only IsValid decisions change.

## Realistic Impact Scenario

Signup, account-update, or data-quality gates can silently accept email-like strings that were previously rejected.
