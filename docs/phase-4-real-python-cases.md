# 阶段 4：真实 Python 案例（Real Python Cases）

## 目标（Goal）

交付 v0.4：先加入第一个真实 Python 静默漂移案例（Real Python Silent Drift Case），确认能干净重建后，再扩展到 3-5 个真实案例。

## TODO

- 选择一个旧/新版本稳定的真实 Python 候选（Real Python Candidate）。✓
- 编写人工客户端（Hand-Authored `client.py`）。✓
- 运行旧/新复现（Old/New Reproduction），记录观察到的差异（Observed Diff）。✓
- 用明确来源（Provenance）和审阅笔记（Review Notes）整理案例（Curate Case）。✓
- 生成并验证 pytest 判定器（Pytest Oracle）。✓
- 打包 L1/L2/L3 任务（Task Package）。✓
- 运行审计（Audit）并保存报告。✓
- 在 README 或案例清单（Case Manifest）中记录精确复现命令（Reproduction Command）。✓

## 已完成案例（Completed Case）

- `pandas_str_replace_regex_default`
- Source: https://pandas.pydata.org/pandas-docs/version/2.0/whatsnew/v2.0.0.html
- Version pair: `pandas==1.5.3` -> `pandas==2.0.3`
- Stabilizer: `Python 3.10` with `numpy==1.24.4`
- Observed diff:
  - old: `["a_b", "a_b", "abc"]`
  - new: `["a.b", "a?b", "abc"]`
- Result: `data/reproductions/pandas-str-replace-regex-default/attempt_001/result.json`
- Package: `data/packages/pandas_str_replace_regex_default/`
- Audit: `data/audit/pandas_str_replace_regex_default.json`

- `pydantic_optional_field_required`
- Source: https://pydantic.dev/docs/validation/2.11/get-started/migration/
- Version pair: `pydantic==1.10.15` -> `pydantic==2.7.4`
- Stabilizer: `Python 3.10`
- Observed diff:
  - old: model creation succeeds with `{"nickname": null}`
  - new: model creation fails with `nickname` missing
- Result: `data/reproductions/pydantic-optional-field-required/attempt_001/result.json`
- Package: `data/packages/pydantic_optional_field_required/`
- Audit: `data/audit/pydantic_optional_field_required.json`

- `pydantic_field_alias_none`
- Source: https://pydantic.dev/docs/validation/2.11/get-started/migration/
- Version pair: `pydantic==1.10.15` -> `pydantic==2.7.4`
- Stabilizer: `Python 3.10`
- Observed diff:
  - old: `field.alias == "name"`
  - new: `field.alias is None`
- Result: `data/reproductions/pydantic-field-alias-none/attempt_001/result.json`
- Package: `data/packages/pydantic_field_alias_none/`
- Audit: `data/audit/pydantic_field_alias_none.json`

## CLI/API 形状（CLI/API Shape）

```bash
py310="$(uv python find 3.10)"

silent-drift-miner reproduce plan \
  --candidate-id pandas-str-replace-regex-default \
  --library pandas \
  --old-version 1.5.3 \
  --new-version 2.0.3 \
  --client-file cases/pandas_str_replace_regex_default/client.py \
  --old-python-executable "$py310" \
  --new-python-executable "$py310" \
  --extra-package numpy==1.24.4 \
  --out data/reproductions/pandas-str-replace-regex-default/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/pandas-str-replace-regex-default/spec.json \
  --out data/reproductions/pandas-str-replace-regex-default \
  --install \
  --venv-root .repro_venvs \
  --build-timeout 300 \
  --timeout 60

silent-drift-miner curate create \
  --reproduction-result data/reproductions/pandas-str-replace-regex-default/attempt_001/result.json \
  --decision accept \
  --case-id pandas_str_replace_regex_default \
  --source-url https://pandas.pydata.org/pandas-docs/version/2.0/whatsnew/v2.0.0.html \
  --source-excerpt "Change the default argument of regex for Series.str.replace() from True to False." \
  --retrieved-at 2026-05-19 \
  --version-old 1.5.3 \
  --version-new 2.0.3 \
  --api-surface pandas.Series.str.replace \
  --review-notes "Accepted: isolated Python 3.10.20 reproduction with numpy==1.24.4 produced deterministic stdout diff and exit code 0 on both sides." \
  --out data/curated/pandas_str_replace_regex_default.yaml

silent-drift-miner oracle generate \
  --case data/curated/pandas_str_replace_regex_default.yaml \
  --template pytest \
  --out data/oracle/pandas_str_replace_regex_default/

silent-drift-miner oracle validate \
  --oracle data/oracle/pandas_str_replace_regex_default/oracle_spec.yaml \
  --mode old

silent-drift-miner oracle validate \
  --oracle data/oracle/pandas_str_replace_regex_default/oracle_spec.yaml \
  --mode new

silent-drift-miner bench package \
  --case data/curated/pandas_str_replace_regex_default.yaml \
  --oracle data/oracle/pandas_str_replace_regex_default/oracle_spec.yaml \
  --levels L1,L2,L3 \
  --out data/packages/

silent-drift-miner audit case \
  --package data/packages/pandas_str_replace_regex_default/ \
  --out data/audit/pandas_str_replace_regex_default.json
```

优先目标库（Preferred Targets）：

```text
pandas
requests
urllib3
pydantic
fastapi
starlette
numpy
```

## 验收标准（Acceptance Criteria）

- 至少一个真实案例包（Real Case Package）存在于 `cases/` 或 `data/packages/`。✓
- 该案例能从干净检出（Clean Checkout）重新构建。✓
- 该案例包含来源 URL、原文摘录、抓取时间、版本对、API 表面、复现结果、判定器规格、任务包和审计报告。✓
- README 或案例清单包含精确复现命令。✓
- 第一个案例使用确定性行为（Deterministic Behavior）和稳定依赖版本（Stable Dependency Versions）。✓

## 非目标（Non-Goals）

- 不从 Kafka、Spark、分布式系统（Distributed Systems）或依赖系统时钟的时区行为开始。
- Python 生命周期（Python Lifecycle）稳定前，不扩展到 JVM/Go/Rust。
- 不在一个真实案例完整复现前追样本数（Sample Count）。
- 不加入论文实验矩阵（Paper Experiment Matrix）。
