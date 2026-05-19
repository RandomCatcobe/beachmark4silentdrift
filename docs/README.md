# SilentDrift 路线图（Roadmap）

SilentDrift 当前不是一套已经成型的论文基准（Paper Benchmark），而是一个案例发现与复现库（Case Discovery and Reproduction Library）。近期目标是搭建可靠的产物工厂（Artifact Factory），让每条候选案例（Candidate）都能从来源证据（Source Evidence）推进到可复现、可人审、可打包、可审计的案例（Case）。

核心生命周期（Lifecycle）如下：

```text
raw_note
  -> mined_candidate
  -> triaged_candidate
  -> reproduction_attempted
  -> behavior_diff_observed
  -> human_verified
  -> oracle_packaged
  -> benchmark_ready
```

所有阶段都必须保留文件化输入输出（File-Based Inputs and Outputs），这样每一步都可以重跑（Rerun）、审计（Audit）和调试（Debug）。

## 术语入口（Terminology）

先阅读 [术语表（Terminology）](terminology.md)。架构文档中的关键概念统一使用“中文术语（English Term）”形式，避免后续 Claude/Codex 在候选、复现、判定器、打包、审计之间混用词汇。

## 阶段索引（Phase Index）

| 阶段 | 版本 | 目标 | 退出标准 |
| --- | --- | --- | --- |
| [阶段 0](phase-0-ground-rules.md) | Setup | 固定工程约束（Ground Rules）和防泄漏规则（Leakage Rules） | 贡献者和 agent 明确哪些事不能改、不能泄漏 |
| [阶段 1](phase-1-pipeline-skeleton.md) | v0.1 | 稳定模式（Schema）、产物路径（Artifact Paths）、第 1 层 CLI、分诊队列（Triage Queue）、合成演示（Synthetic Demo） | 候选 JSONL（Candidate JSONL）和分诊产物（Triage Artifacts）可确定、可测试 |
| [阶段 2](phase-2-python-reproduction.md) | v0.2 | 建立 Python-only 复现层（Reproduction Layer），只使用人工客户端（Hand-Authored Client） | 旧/新版本运行（Old/New Runs）能捕获输出和保留/丢弃原因（Keep/Drop Reasons） |
| [阶段 3](phase-3-oracle-package-audit.md) | v0.3 | 生成 pytest 判定器（Oracle）、打包 L1/L2/L3 任务（Task Package）、审计泄漏与溯源 | 隐藏/公开分离（Hidden/Public Split）被强制检查 |
| [阶段 4](phase-4-real-python-cases.md) | v0.4 | 加入第一个真实 Python 案例（Real Python Case） | 真实案例能从干净检出（Clean Checkout）重新构建 |
| [阶段 5](phase-5-llm-client-generation.md) | v0.5 | 加入受控的 LLM 客户端生成（LLM Client Generation） | 提示词（Prompt）经过脱敏（Redaction），且测试不依赖真实 API |
| [阶段 6](phase-6-ecosystem-expansion.md) | v0.6 | Python 稳定后再做生态扩展（Ecosystem Expansion） | 新适配器（Adapter）满足与 Python 相同的生命周期门槛 |

暂缓项见 [暂缓事项（Deferred Work）](deferred.md)。

## 总执行原则（Implementation Rule）

在 `candidate -> reproduction -> curation -> oracle -> package -> audit` 链路打通前，不要提前追论文评测（Paper Evaluation）、多语言覆盖（Multi-Ecosystem Coverage）或大规模样本数（Large-Scale Sample Count）。
