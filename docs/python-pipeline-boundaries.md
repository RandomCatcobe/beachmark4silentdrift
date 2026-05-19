# Python Pipeline Boundaries

This project currently validates one specific pipeline:

```text
Python package candidate
  -> old/new pip-installable versions
  -> hand-authored local client
  -> deterministic old/new behavior comparison
  -> curated case
  -> pytest oracle
  -> benchmark package
  -> audit
  -> python status
```

## In Scope

A case is in scope only when all of these are true:

- It is a Python package/library case.
- Both old and new versions are identifiable and installable in local isolated Python environments.
- The same client code can run against both versions.
- The behavior difference is deterministic and locally observable.
- The benchmark can be packaged with public files separated from hidden oracle files.

## Out of Scope Unless Explicitly Commanded

Agents must not expand the pipeline into any of the following areas unless the user gives an explicit command to do so:

- Cloud service alias or service behavior drift, such as Gemini model aliases or AWS S3 service defaults.
- Current-version bugs or parameter semantics issues without a clean old/new version pair, such as a single-version LangChain or NumPy bug report.
- CUDA/GPU-dependent reproductions or hardware-specific behavior.
- Legacy drift outside the active date/version policy that still affects modern migrations.
- Complex semantic oracles beyond deterministic local behavior diffs, such as statistical stability, performance regression, probabilistic distributions, or long-running reliability behavior.

## Agent Rule

When a candidate falls outside the current boundary:

1. Do not build a new adapter, harness, oracle family, cloud fixture system, GPU path, or statistical evaluator.
2. Record the boundary reason in the relevant report or triage notes.
3. Stop at the existing pipeline boundary.
4. Continue only if the user explicitly commands that boundary to be opened.

The correct default action is to preserve the working Python package pipeline, not to broaden the project.

## Reserved Interface Exception

The user has explicitly allowed reserving interfaces for future ecosystems. This exception permits
contract files, registry entries, CLI inspection commands, tests, and handoff documentation only. It
does not permit implementing a non-Python runner, cloud harness, GPU path, or complex oracle without
a separate explicit command.

## JVM, JS, PHP, Ruby, .NET, And Go Adapter Exceptions

On 2026-05-19 the user explicitly opened the boundary for JVM special cases.
JVM is now allowed to have an active adapter, local deterministic old/new
execution, and JVM-specific execution details such as multiple source roots,
classpath/JAR entries, resource directories, JVM arguments, and program
arguments.

The user then asked to adapt additional languages gradually, one at a time. JS
is now allowed to have an active adapter for local deterministic Node package
root reproductions.

PHP is now allowed to have an active adapter for local deterministic PHP CLI
package-root reproductions.

Continuing the one-language-at-a-time expansion, Ruby is now allowed to have an
active adapter for local deterministic Ruby CLI package-root reproductions.

Continuing the one-language-at-a-time expansion, .NET is now allowed to have an
active adapter for local deterministic .NET CLI project-root reproductions.

Continuing the one-language-at-a-time expansion, Go is now allowed to have an
active adapter for local deterministic Go CLI package-root reproductions.

These exceptions are limited to JVM, JS, PHP, Ruby, .NET, and Go. They do not
open cloud harnesses, GPU paths, current-version bug tracks without old/new
pairs, statistical or performance oracles, or any other ecosystem. The detailed
boundaries are in `docs/jvm-special-case-boundary.md`,
`docs/js-adapter-boundary.md`, `docs/php-adapter-boundary.md`,
`docs/ruby-adapter-boundary.md`, `docs/dotnet-adapter-boundary.md`, and
`docs/go-adapter-boundary.md`.

## Parallel Adapter Work Boundary

When future adapter work is split across multiple agents, each agent must stay inside its owned
ecosystem directory and avoid shared refactors. The detailed collaboration protocol is in
`docs/ecosystem-adapter-handoff.md`.

If an adapter task looks larger than an isolated directory-level implementation, the agent must stop,
record the blocker, and ask the user or coordinator before changing shared project structure.

Currently reserved ecosystems include `rust`. JVM, JS, PHP, Ruby, .NET, and Go
have separate active exceptions. Reservation is not implementation permission.
