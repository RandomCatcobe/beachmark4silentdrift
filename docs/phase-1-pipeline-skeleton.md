# 阶段 1：流水线骨架（Pipeline Skeleton）

## 目标（Goal）

交付 v0.1 工程骨架（Engineering Skeleton）：稳定产物（Artifacts）、候选模式（Candidate Schema）、第 1 层 CLI 强化（Layer 1 CLI Hardening）、分诊队列（Triage Queue）和离线合成演示（Offline Synthetic Demo）。

## TODO

- 增加共享产物模式（Shared Artifact Schema），覆盖候选（Candidate）、分诊（Triage）、复现（Reproduction）、整理（Curation）、判定器（Oracle）、任务包（Benchmark Package）和审计报告（Audit Report）。✓
- 增加产物存储器（ArtifactStore），把所有输出映射到配置的产物根目录（Artifact Root）下。✓
- 保持候选 ID（Candidate ID）稳定且确定。✓
- 增加或确认第 1 层命令：`mine`、`stats`、`show`、`validate-candidates`。✓
- 增加离线夹具模式（Offline Fixture Mode）：`--no-llm` 和 `--llm-filter`。✓
- 对畸形 JSONL（Malformed JSONL）给出清晰错误。✓（`validate-candidates` 已处理）
- 增加分诊命令（Triage Commands）：`build`、`next`、`mark`、`export`。✓
- 增加不依赖网络或 LLM API 的合成端到端演示（Synthetic End-to-End Demo）占位。✓
- 将现有 `unittest` 测试迁移至 `pytest`（本阶段验收标准要求使用 `tmp_path` fixture）。✓

## CLI/API 形状（CLI/API Shape）

```bash
silent-drift mine \
  --library pandas \
  --ecosystem python \
  --source data/fixtures/pandas_changelog.md \
  --out data/candidates/pandas.jsonl \
  --no-llm

silent-drift stats data/candidates/pandas.jsonl
silent-drift show data/candidates/pandas.jsonl --candidate-id CANDIDATE_ID
silent-drift validate-candidates data/candidates/pandas.jsonl

silent-drift triage build \
  --candidates data/candidates/pandas.jsonl \
  --out data/triage/pandas_queue.jsonl

silent-drift triage mark \
  --queue data/triage/pandas_queue.jsonl \
  --candidate-id CANDIDATE_ID \
  --decision accept_for_reproduction \
  --notes "looks like default behavior drift"
```

核心分诊决策（Triage Decisions）：

```text
accept_for_reproduction
reject_hard_break
reject_additive_feature
reject_bugfix_only
reject_not_silent
borderline
needs_more_context
```

## 验收标准（Acceptance Criteria）

- 候选 JSONL（Candidate JSONL）能通过模式往返（Schema Round Trip）。
- 产物路径（Artifact Paths）确定，并且不能写出产物根目录（Artifact Root）。
- `stats` 输出类别（Category）、置信度（Confidence）、生态（Ecosystem）和来源（Source）统计。
- 分诊队列（Triage Queue）保留所有候选，每个候选默认只能有一个决策，除非显式覆盖（Overwrite）。
- 测试使用临时目录（Temporary Directory），例如 `tmp_path`。
- 现有第 1 层行为保持兼容。

## 非目标（Non-Goals）

- 不加入 Docker 复现（Docker Reproduction）。
- 不加入 LLM 客户端生成（LLM Client Generation）。
- 不加入判定器生成（Oracle Generation）或任务打包（Task Packaging）。
- 不把流水线做成只能一次跑完的黑盒（Black-Box Pipeline）。
