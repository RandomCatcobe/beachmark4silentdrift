# 暂缓事项（Deferred Work）

## 2026-05-19 Update

JVM, JS, PHP, Ruby, .NET, and Go are no longer deferred after explicit
one-language-at-a-time user requests. They are active only for local
deterministic adapter/reproduction paths. Rust, cloud-service harnesses,
distributed systems, statistical oracles, and large-scale benchmark collection
remain deferred.

以下事项在 `candidate -> reproduction -> curation -> oracle -> package -> audit` 链路稳定前，全部暂缓。

## 暂缓工程项（Deferred Engineering）

- Rust 支持（Rust Support）。
- L4 盲操作任务（Blind Operation Tasks）。
- 统计性漂移判定器（Statistical Drift Oracle）。
- 分布式系统复现工具（Distributed-System Reproduction Harness）。
- 多 agent 评测器（Multi-Agent Evaluator）。
- 面向 benchmark agent 的 release-note 检索工具（Release-Note Retrieval Tools）。
- 大规模 benchmark 收集（Large-Scale Benchmark Collection）。

## 暂缓研究和论文项（Deferred Research and Paper Work）

- 会场定位（Venue Framing）。
- 论文实验矩阵（Paper Experiment Matrix）。
- 模型比较（Model Comparison）。
- 成本感知评测（Cost-Aware Evaluation）。
- Agent 轨迹分析（Agent Trace Analysis）。
- 多工具设置消融（Multi-Tool Setting Ablations）。
- 四生态覆盖目标（Four-Ecosystem Coverage Targets）。
- 30-50 条案例这类样本数目标（Sample-Count Targets）。

## 重新启用规则（Reactivation Rule）

只有当某个暂缓项能直接改善已验证案例生命周期（Verified Case Lifecycle），或核心 Python 流水线已有已审计真实案例（Audited Real Cases）后，才把它重新纳入路线图。
