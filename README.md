# beachmark4silentdrift

## Current Status (2026-05-19)

- Latest pushed package release: `v0.11.0`.
- Python package lifecycle is the mature path, with six audited real Python cases.
- JVM, JS, PHP, Ruby, .NET, and Go adapters are active for local deterministic
  toy/reproduction cases; Rust remains reserved.
- Python autodiscovery now has Markdown memory helpers for idea cards,
  rejection lessons, accepted-case anchors, readiness checks, and next-run
  briefs. The real 200-attempt discovery run has not been started.

SilentDrift 当前定位为静默行为漂移（Silent Behavioral Drift）的案例发现与复现库（Case Discovery and Reproduction Library）。本仓库目前包含第 1 层挖掘器（Layer 1 Miner），以及把它逐步扩展成可复现产物流水线（Reproducible Artifact Pipeline）的阶段路线图（Roadmap）。

## Claude / Codex 路线图（Roadmap）

- [文档索引（Docs Index）](docs/README.md)
- [术语表（Terminology）](docs/terminology.md)
- [阶段 0：工程约束（Ground Rules）](docs/phase-0-ground-rules.md)
- [阶段 1：流水线骨架（Pipeline Skeleton）](docs/phase-1-pipeline-skeleton.md)
- [阶段 2：Python 复现（Python Reproduction）](docs/phase-2-python-reproduction.md)
- [阶段 3：判定器、打包、审计（Oracle, Package, Audit）](docs/phase-3-oracle-package-audit.md)
- [阶段 4：真实 Python 案例（Real Python Cases）](docs/phase-4-real-python-cases.md)
- [阶段 5：LLM 客户端生成（LLM Client Generation）](docs/phase-5-llm-client-generation.md)
- [阶段 6：生态扩展（Ecosystem Expansion）](docs/phase-6-ecosystem-expansion.md)
- [暂缓事项（Deferred Work）](docs/deferred.md)

## 当前代码（Current Code）

当前 Python 工程位于 [`silent_drift_miner/`](silent_drift_miner/)。扩展流水线前，先从上面的路线图（Roadmap）和术语表（Terminology）开始。
