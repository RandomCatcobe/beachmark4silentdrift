# 阶段 5：LLM 客户端生成（LLM Client Generation）

## 目标（Goal）

交付 v0.5：加入可选、受控、防泄漏的 LLM 客户端生成（Leak-Controlled LLM Client Generation）。LLM 可以帮助编写复现客户端（Reproducer Client），但不能成为判定器（Oracle）或预期行为（Expected Behavior）的真相来源（Source of Truth）。

## TODO

- 增加脱敏客户端生成提示词构建器（Redacted Client-Generation Prompt Builder）。✓
- 提示词只允许使用公开复现上下文（Public Reproduction Context）。✓
- 保存提示词（Prompt）、模型元数据（Model Metadata）和生成客户端（Generated Client）以便审计。✓
- API key 缺失时优雅失败（Graceful Failure）。✓
- LLM 生成保持可选（Optional），不能成为默认路径（Default Path）。✓
- 增加不调用真实 API 的提示词检查测试（Prompt Inspection Tests）。✓

## CLI/API 形状（CLI/API Shape）

```bash
silent-drift-miner reproduce generate-client \
  --candidate cases/pandas_str_replace_regex_default/candidate.json \
  --candidate-id pandas-str-replace-regex-default \
  --redacted \
  --dry-run \
  --out data/reproductions/pandas-str-replace-regex-default/generated_client.py
```

该命令会写出：

```text
data/reproductions/<candidate_id>/generated_client.py
data/reproductions/<candidate_id>/generated_client.py.prompt.md
data/reproductions/<candidate_id>/generated_client.py.metadata.json
```

允许进入提示词的输入（Allowed Prompt Inputs）：

```text
library
ecosystem
version_old
version_new
api_surface
public_intent
allowed_imports
forbidden_terms
```

禁止进入提示词的输入（Forbidden Prompt Inputs）：

```text
expected_old_output
expected_new_output
oracle
hidden_oracle_path
repair_hint
observed_diff
curated_truth
```

## 验收标准（Acceptance Criteria）

- 提示词脱敏测试（Prompt Redaction Tests）证明禁止字段不存在。✓
- 生成客户端和提示词元数据一起保存。✓
- 测试不需要真实 LLM 调用（Live LLM Call）。✓
- API key 缺失时给出清晰、非崩溃错误。✓
- 生成客户端仍必须经过与人工客户端相同的复现工具（Reproduction Harness）。

## 非目标（Non-Goals）

- 不让 LLM 决定漂移是否真实。
- 不让 LLM 编写权威判定器（Authoritative Oracle）。
- 不把旧/新预期输出放进生成提示词。
- 不让生成客户端成为 CI 或测试的必要条件。
