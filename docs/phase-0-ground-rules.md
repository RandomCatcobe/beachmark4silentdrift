# 阶段 0：工程约束（Ground Rules）

## 目标（Goal）

让仓库适合 Claude/Codex 逐步接手。这个阶段只固定工程规则（Engineering Rules）和安全边界（Safety Boundaries），不增加新的流水线行为（Pipeline Behavior）。

## TODO

- 新增根目录 agent 指令文件（Agent Instruction File），例如 `CLAUDE.md`。
- 明确项目定位：产物流水线（Artifact Pipeline），不是论文实验套件（Paper Experiment Suite）。
- 保留现有第 1 层挖掘行为（Layer 1 Mining Behavior），除非集成测试（Integration Test）需要兼容性修复。
- 要求每个阶段都有类型化模式（Typed Schema）、CLI 入口（CLI Entrypoint）、JSON/YAML 产物输出（Artifact Output）、测试（Tests）和失败模式（Failure Mode）。
- 要求测试离线运行（Offline Tests）。
- 要求所有联网功能（Network-Facing Functionality）都有离线夹具（Offline Fixtures）。
- 要求隐藏判定器（Hidden Oracle）与公开任务文件（Public Task Files）物理分离。

## CLI/API 形状（CLI/API Shape）

本阶段不新增运行时 CLI。开发者命令（Developer Command）为：

```bash
python -m pytest
```

如果仓库仍使用 `unittest`，先保留现有测试命令，直到阶段 1 接入 pytest。

## 验收标准（Acceptance Criteria）

- 仓库根目录记录项目约束（Project Constraints）。
- 现有第 1 层测试（Layer 1 Tests）通过。
- 现有离线 Spring Boot 演示（Offline Spring Boot Demo）仍可运行。
- 文档明确生命周期（Lifecycle）和防泄漏规则（Anti-Leakage Rules）。
- 不修改业务逻辑（Business Logic）。

## 非目标（Non-Goals）

- 不实现复现层（Reproduction）、判定器生成（Oracle Generation）、任务打包（Task Packaging）或多生态适配器（Multi-Ecosystem Adapters）。
- 不把 LLM 裁判（LLM Judge）作为主要判定器（Primary Oracle）。
- 不加入论文会场（Venue）、模型矩阵（Model Matrix）或样本规模（Sample Size）判断。
