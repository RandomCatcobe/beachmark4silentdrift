# 阶段 4：真实 Python 案例（Real Python Cases）

## 目标（Goal）

交付 v0.4：先加入第一个真实 Python 静默漂移案例（Real Python Silent Drift Case），确认能干净重建后，再扩展到 3-5 个真实案例。

## TODO

- 选择一个旧/新版本稳定的真实 Python 候选（Real Python Candidate）。
- 编写人工客户端（Hand-Authored `client.py`）。
- 运行旧/新复现（Old/New Reproduction），记录观察到的差异（Observed Diff）。
- 用明确溯源（Provenance）和审阅笔记（Review Notes）整理案例（Curate Case）。
- 生成并验证 pytest 判定器（Pytest Oracle）。
- 打包 L1/L2/L3 任务（Task Package）。
- 运行审计（Audit）并保存报告。
- 在 README 或案例清单（Case Manifest）中记录精确复现命令（Reproduction Command）。

## CLI/API 形状（CLI/API Shape）

```bash
silent-drift reproduce plan \
  --candidate-id CANDIDATE_ID \
  --library pandas \
  --old-version OLD_VERSION \
  --new-version NEW_VERSION \
  --client-file cases/source_clients/CANDIDATE_ID/client.py \
  --out data/reproductions/CANDIDATE_ID/spec.json

silent-drift reproduce run \
  --spec data/reproductions/CANDIDATE_ID/spec.json \
  --out data/reproductions/CANDIDATE_ID/attempt_001/

silent-drift curate create \
  --reproduction-result data/reproductions/CANDIDATE_ID/attempt_001/result.json \
  --decision accept \
  --case-id CASE_ID \
  --out data/curated/CASE_ID.yaml

silent-drift oracle generate --case data/curated/CASE_ID.yaml --template pytest --out data/oracle/CASE_ID/
silent-drift bench package --case data/curated/CASE_ID.yaml --oracle data/oracle/CASE_ID/oracle_spec.yaml --levels L1,L2,L3 --out data/packages/
silent-drift audit case --package data/packages/TASK_ID/ --out data/audit/TASK_ID.json
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

- 至少一个真实案例包（Real Case Package）存在于 `cases/` 或 `data/packages/`。
- 该案例能从干净检出（Clean Checkout）重新构建。
- 该案例包含来源 URL（Source URL）、原文摘录（Excerpt）、抓取时间（Retrieved Timestamp）、版本对（Version Pair）、API 表面（API Surface）、复现结果、判定器规格（Oracle Spec）、任务包和审计报告。
- README 或案例清单包含精确复现命令。
- 第一个案例使用确定性行为（Deterministic Behavior）和稳定依赖版本（Stable Dependency Versions）。

## 非目标（Non-Goals）

- 不从 Kafka、Spark、分布式系统（Distributed Systems）或依赖系统时钟的时区行为开始。
- Python 生命周期（Python Lifecycle）稳定前，不扩展到 JVM/Go/Rust。
- 不在一个真实案例完整复现前追样本数（Sample Count）。
- 不加入论文实验矩阵（Paper Experiment Matrix）。
