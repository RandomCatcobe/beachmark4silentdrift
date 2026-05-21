# beachmark4silentdrift

SilentDrift is a case discovery and reproduction library for silent behavioral
drift: old and new versions both run successfully, but the observable behavior
changes in a way that can silently affect callers.

This repository is not yet a polished paper benchmark. It is the artifact
factory that turns leads into reproducible, reviewable, and eventually packaged
case-bank entries.

## Current Status (2026-05-21)

- Complete case-bank packages: 11 under `docs/case-bank/cases/**`.
- Python package pipeline: 7 audited package-style cases under `data/packages/`.
- Sequential verification run: 30 candidates checked in source order, with
  16 `verified_keep`, 3 `no_behavior_diff`, and 11 blocked with first blocker
  recorded.
- Reverse verification run: 50 candidates checked from the other end of the
  queue, with 7 new `verified_keep`, 5 existing/deduplicated records, and the
  remaining entries recorded as offline, source, dependency, or runtime blocks.
- Online service drift has a separate lane under `online/`; those cases are
  useful evidence but are not counted as offline-reproducible case-bank packages.

The active goal is to migrate every packageable `verified_keep` case from the
`sequential_30` and `reverse_50` runs into full case-bank folders, then build an
eval package from every complete case that exists at that point.

## What Counts As Complete

A complete case-bank entry lives at:

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

and contains:

```text
case.md
evidence.md
env.md
metadata.json
client/
hidden/
```

The public files explain the task, environment, and source evidence. The
`hidden/` directory contains the oracle and expected assertions, and is stripped
when an eval package is built.

## Main Commands

Build generated case-bank indexes:

```powershell
python -m case_bank index build --out docs/case-bank/indexes/
```

Build an eval package from all complete case folders:

```powershell
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

Run the case-bank tests:

```powershell
python -m pytest silent_drift_miner/tests/test_case_bank.py
```

Run the broader test suite when touching shared tooling:

```powershell
python -m pytest
```

## Important Paths

- `docs/case-bank/` - canonical case-bank layout, indexes, and packaging prompt.
- `docs/case-bank/cases/` - complete packaged cases.
- `docs/case-bank-restructure/final-plan.md` - schema, folder contract, status
  meanings, and packaging rules.
- `docs/verification-runs/` - human-readable ledgers for the 30/50 verification
  runs.
- `data/verification/sequential_30/` - artifacts from the forward 30-case run.
- `data/verification/reverse_50/` - artifacts from the reverse 50-case run.
- `data/packages/` - older Python package-style artifacts.
- `online/` - online-only platform/API drift records.
- `silent_drift_miner/` - miner, reproduction, oracle, audit, and adapter code.

## Current Packaging Work

Use this prompt when spawning or instructing other instances:

```text
docs/case-bank/package-30-50-agent-prompt.md
```

Recommended shards:

- `sequential_30` .NET + Go
- `sequential_30` JavaScript
- `sequential_30` JVM
- `reverse_50` Ruby + PHP
- `reverse_50` Python
- blocked/no-diff/source-check ledger and opportunistic promotions

If not every case can be completed, still run the package command after moving
invalid drafts out of `docs/case-bank/cases/`. The final package should include
every valid complete case available at that moment.

## Non-Negotiables

- Do not claim a case is complete unless the folder exists, metadata validates,
  indexes regenerate, and packaging succeeds with it included.
- Do not put raw dependency caches, virtual environments, `node_modules`,
  `vendor`, `bin`, `obj`, jars, or generated build products into new case
  folders.
- Public task files must not reveal hidden oracle conditions or exact expected
  outputs.
- Work with existing user or agent changes; do not revert unrelated edits.

## Older Roadmap Docs

The phase docs still describe how the project got here:

- `docs/phase-0-ground-rules.md`
- `docs/phase-1-pipeline-skeleton.md`
- `docs/phase-2-python-reproduction.md`
- `docs/phase-3-oracle-package-audit.md`
- `docs/phase-4-real-python-cases.md`
- `docs/phase-5-llm-client-generation.md`
- `docs/phase-6-ecosystem-expansion.md`

Treat them as historical context unless they conflict with the current
case-bank contract in `docs/case-bank-restructure/final-plan.md`.

---

# 中文版

SilentDrift 是一个用于收集、复现和打包“静默行为漂移”的案例库。这里的
“静默”指 old/new 两个版本都能正常运行，但可观察行为发生变化，调用方可能在
没有硬错误的情况下被影响。

这个仓库目前还不是一套最终论文基准，而是一个产物工厂：把线索推进成可复现、
可人审、最终可打包的 case-bank 案例。

## 当前状态（2026-05-21）

- 完整 case-bank 包：`docs/case-bank/cases/**` 下已有 11 个。
- Python 旧流水线包：`data/packages/` 下有 7 个已审计 package-style 案例。
- 顺序 30 个候选验证：按来源顺序验证 30 个，其中 16 个 `verified_keep`，
  3 个 `no_behavior_diff`，11 个记录了精确首个阻塞点。
- 反向 50 个候选验证：从队列另一端验证 50 个，其中新增 7 个
  `verified_keep`，5 个已有/去重记录，其余按离线不可复现、来源阻塞、依赖
  或运行时阻塞记录。
- 在线服务漂移有独立通道：`online/`。这些案例是有价值证据，但不计入离线可
  复现 case-bank 包。

当前核心目标：把 `sequential_30` 和 `reverse_50` 中所有可打包的
`verified_keep` 案例迁移为完整 case-bank 文件夹，然后用当时所有已完成案例
构建 eval package。

## 完整案例的标准

完整 case-bank entry 位于：

```text
docs/case-bank/cases/<primary-scenario>/<case-id-slug>/
```

并包含：

```text
case.md
evidence.md
env.md
metadata.json
client/
hidden/
```

公开文件说明任务、环境和来源证据。`hidden/` 放 oracle 与 expected
assertions，在构建 eval package 时会被剥离。

## 常用命令

生成 case-bank 索引：

```powershell
python -m case_bank index build --out docs/case-bank/indexes/
```

从所有完整 case 文件夹构建 eval package：

```powershell
python -m case_bank pack --src docs/case-bank/cases/ --out eval_package/
```

运行 case-bank 测试：

```powershell
python -m pytest silent_drift_miner/tests/test_case_bank.py
```

改共享工具时运行更完整测试：

```powershell
python -m pytest
```

## 关键路径

- `docs/case-bank/` - 规范 case-bank 布局、索引和打包提示词。
- `docs/case-bank/cases/` - 已完成的打包案例。
- `docs/case-bank-restructure/final-plan.md` - schema、文件夹契约、状态含义
  和打包规则。
- `docs/verification-runs/` - 30/50 验证运行的人类可读 ledger。
- `data/verification/sequential_30/` - 正向 30 个验证运行的产物。
- `data/verification/reverse_50/` - 反向 50 个验证运行的产物。
- `data/packages/` - 旧 Python package-style 产物。
- `online/` - online-only 平台/API 漂移记录。
- `silent_drift_miner/` - miner、reproduction、oracle、audit 和 adapter 代码。

## 当前打包工作

给其他实例使用这份提示词：

```text
docs/case-bank/package-30-50-agent-prompt.md
```

推荐分片：

- `sequential_30` .NET + Go
- `sequential_30` JavaScript
- `sequential_30` JVM
- `reverse_50` Ruby + PHP
- `reverse_50` Python
- blocked/no-diff/source-check ledger 与可顺手推进的案例

如果不是所有案例都能完成，也要在把无效草稿移出 `docs/case-bank/cases/` 后运行
打包命令。最终 package 应包含当时所有有效完整案例。

## 硬规则

- 不要声称案例已完成，除非 case 文件夹存在、metadata 可校验、索引可重建，
  且打包命令成功把它包含进去。
- 新 case 文件夹里不要放原始依赖缓存、虚拟环境、`node_modules`、`vendor`、
  `bin`、`obj`、jar 或生成产物。
- 公开任务文件不能泄露 hidden oracle 条件或精确 expected outputs。
- 尊重已有用户或其他 agent 的修改；不要回滚无关改动。

## 旧路线图文档

这些 phase 文档记录了项目演进过程：

- `docs/phase-0-ground-rules.md`
- `docs/phase-1-pipeline-skeleton.md`
- `docs/phase-2-python-reproduction.md`
- `docs/phase-3-oracle-package-audit.md`
- `docs/phase-4-real-python-cases.md`
- `docs/phase-5-llm-client-generation.md`
- `docs/phase-6-ecosystem-expansion.md`

如果它们与 `docs/case-bank-restructure/final-plan.md` 中当前 case-bank 契约冲突，
以后者为准。
