# CLAUDE.md — beachmark4silentdrift Agent Instructions

## 项目定位（Project Positioning）

本仓库是**静默行为漂移（Silent Behavioral Drift）的案例发现与复现库（Case Discovery and Reproduction Library）**，不是论文基准（Paper Benchmark）。当前目标是搭建可靠的产物工厂（Artifact Factory），让每条候选案例从来源证据推进到可复现、可人审、可打包的案例。

## 当前阶段（Current Phase）

**阶段 0（Phase 0）**：工程约束已固定。**阶段 1（Phase 1）** 实施中：Layer 1 CLI 强化、ArtifactStore、分诊队列（Triage Queue）。

参见完整路线图：[docs/README.md](docs/README.md)

## 产物路径约定（Artifact Paths）

```
# 运行时产物（runtime artifacts，mine/triage/reproduce 等命令输出）
data/
  candidates/         # mine 命令输出的 JSONL 候选文件（--out 可覆盖）
  triage/             # triage 命令输出的分诊队列文件
  reproductions/      # reproduce 命令输出
  oracle/             # oracle 生成产物（hidden/ 与 public/ 物理分离）
  packages/           # bench 打包产物
  audit/              # audit 报告
  raw_changelogs/     # GitHub API 缓存（不提交到 git）

# 测试夹具（test fixtures，提交到 git，供离线测试使用）
silent_drift_miner/data/
  candidates/         # 测试用预置候选文件（如 spring-boot.jsonl）
  fixtures/           # 离线 changelog 夹具（如 pandas_changelog.md）
```

**所有产物必须写到配置的产物根目录（Artifact Root）之内，不能随意写到任意路径。**

## 防泄漏规则（Anti-Leakage Rules）

以下内容**绝对不能**进入 LLM 提示词（Prompt）或公开任务文件（Public Task Files）：

- 预期旧/新输出（Expected old/new outputs）
- 隐藏测试（Hidden Tests）
- 修复提示（Repair Hints）
- 判定器细节（Oracle Details）

隐藏判定器文件（Hidden Oracle Files）必须与公开任务文件（Public Task Files）物理分离。

## 核心生命周期（Lifecycle）

```text
raw_note
  -> mined_candidate       (Layer 1 mine 命令)
  -> triaged_candidate     (triage build/mark 命令)
  -> reproduction_attempted (Layer 2 harness, Phase 2)
  -> behavior_diff_observed
  -> human_verified
  -> oracle_packaged        (Phase 3)
  -> benchmark_ready
```

## CLI 入口（CLI Entrypoints）

```bash
# 离线规则挖掘（不调用 LLM，不联网）
python -m silent_drift_miner.cli mine \
  --library pandas --source data/fixtures/pandas_changelog.md \
  --no-llm --out data/candidates/pandas.jsonl

# 带 LLM 精炼（需要 ANTHROPIC_API_KEY）
python -m silent_drift_miner.cli mine --library requests --use-llm

# 统计和查看
python -m silent_drift_miner.cli stats
python -m silent_drift_miner.cli show pandas
python -m silent_drift_miner.cli validate-candidates data/candidates/pandas.jsonl

# 分诊队列（Phase 1）
python -m silent_drift_miner.cli triage build \
  --candidates data/candidates/pandas.jsonl \
  --out data/triage/pandas_queue.jsonl
python -m silent_drift_miner.cli triage mark \
  --queue data/triage/pandas_queue.jsonl \
  --candidate-id CANDIDATE_ID \
  --decision accept_for_reproduction

# 运行测试
python -m pytest
```

## 工程规则（Engineering Rules）

1. **每阶段都必须有**：类型化模式（Typed Schema）、CLI 入口、JSON/YAML 产物输出、测试（Tests）、失败模式（Failure Mode）
2. **测试必须离线运行**（无网络、无 LLM API 依赖）
3. **所有联网功能必须有离线夹具（Offline Fixtures）**
4. **不修改业务逻辑**，除非集成测试需要兼容性修复
5. **Python stable before multi-ecosystem**：JVM、Go、Rust 生态的复现支持推迟到 Python 流水线稳定

## 暂缓项（Deferred）

参见 [docs/deferred.md](docs/deferred.md)。在 `candidate -> oracle -> package -> audit` 链路打通前，不推进 JVM/Go/Rust 复现、多 agent 评测、论文实验矩阵。

## 术语约定

使用"中文术语（English Term）"形式。详见 [docs/terminology.md](docs/terminology.md)。
