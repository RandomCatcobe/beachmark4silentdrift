# 术语表（Terminology）

本文档用于统一架构文档中的中文术语和英语术语，后续 Claude/Codex 修改文档或代码时应优先沿用这里的写法。

## 项目定位（Project Positioning）

| 中文术语 | English Term | 用法 |
| --- | --- | --- |
| 静默行为漂移 | Silent Behavioral Drift | API 调用形状不变，但行为结果发生变化 |
| 案例发现与复现库 | Case Discovery and Reproduction Library | 当前项目定位 |
| 产物流水线 | Artifact Pipeline | 从候选到可审计任务包的工程链路 |
| 产物工厂 | Artifact Factory | 稳定地产生可追溯、可复现、可打包案例的系统 |
| 论文基准 | Paper Benchmark | 后续可能形成的研究产物，不是当前目标 |
| 路线图 | Roadmap | 分阶段实现计划 |

## 生命周期（Lifecycle）

| 中文术语 | English Term | 用法 |
| --- | --- | --- |
| 原始笔记 | Raw Note | release note、CHANGELOG、migration guide 等原始文本 |
| 候选案例 | Candidate | 从文本中挖出的潜在 drift |
| 已挖掘候选 | Mined Candidate | 第 1 层输出的候选 |
| 已分诊候选 | Triaged Candidate | 人审或规则分诊后的候选 |
| 复现尝试 | Reproduction Attempt | 对候选进行 old/new 运行的尝试 |
| 行为差异 | Behavior Diff | old/new 输出差异 |
| 人工验证 | Human Verification | 人确认是否可入库 |
| 判定器打包 | Oracle Packaging | 生成隐藏测试和公开任务材料 |
| 可入基准 | Benchmark Ready | 通过审计并可作为任务发布 |

## 核心模块（Core Modules）

| 中文术语 | English Term | 用法 |
| --- | --- | --- |
| 模式 | Schema | 数据结构契约 |
| 产物 | Artifact | 每阶段落盘文件 |
| 产物存储器 | ArtifactStore | 统一管理产物路径的对象 |
| 分诊队列 | Triage Queue | 候选进入复现前的人审/粗筛队列 |
| 复现工具 | Reproduction Harness | old/new 环境中运行同一 client 的工具 |
| 人工客户端 | Hand-Authored Client | 人写的最小复现 client |
| 生成客户端 | Generated Client | LLM 或工具生成的 client |
| 判定器 | Oracle | 隐藏测试或判断逻辑 |
| 任务包 | Task Package | 面向 benchmark/agent 的 public + hidden 包 |
| 审计 | Audit | 检查泄漏、复现、溯源和包结构 |

## 安全与质量（Safety and Quality）

| 中文术语 | English Term | 用法 |
| --- | --- | --- |
| 隐藏/公开分离 | Hidden/Public Split | hidden oracle 不能泄漏到 public task |
| 判定器泄漏 | Oracle Leakage | expected output、hidden test、repair hint 泄漏 |
| 溯源 | Provenance | URL、excerpt、retrieved_at、version pair 等证据链 |
| 离线夹具 | Offline Fixture | 测试用本地数据，不依赖网络 |
| 确定性 | Deterministic | 重跑结果稳定 |
| 保留/丢弃决策 | Keep/Drop Decision | 复现结果是否进入下一阶段 |
| 失败模式 | Failure Mode | install_failed、no_behavior_diff 等可解释失败原因 |

## 文档约定（Documentation Convention）

- 架构文档使用中文主叙述。
- 关键术语首次出现时写成“中文术语（English Term）”。
- CLI 命令、路径、枚举值、JSON/YAML 字段名保持英文原样。
- 如果新增术语，先更新本文件，再更新阶段文档。
