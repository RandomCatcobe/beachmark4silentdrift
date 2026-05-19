# 阶段 3：判定器、打包、审计（Oracle, Package, Audit）

## 目标（Goal）

交付 v0.3：生成 pytest 判定器（Pytest Oracle）、打包 L1/L2/L3 任务（Task Package），并对泄漏（Leakage）、可复现性（Reproducibility）和溯源（Provenance）做全量审计（Full Audit）。

## TODO

- 增加整理命令（Curation Commands），把复现结果（Reproduction Result）变成接受或拒绝的案例清单（Case Manifest）。✓
- 为 Python 案例生成 pytest 判定器（Pytest Oracle）。✓
- 在判定器目录中强制隐藏/公开分离（Hidden/Public Split）。✓
- 只生成 L1、L2、L3 benchmark 任务包（Task Packages）。✓
- 增加审计检查（Audit Checks）：判定器泄漏（Oracle Leakage）、复现状态（Reproducibility Status）、溯源（Provenance）和包结构（Package Structure）。✓
- 保存 JSON 审计报告（Audit Report）。✓

## CLI/API 形状（CLI/API Shape）

```bash
silent-drift curate create \
  --reproduction-result data/reproductions/CANDIDATE_ID/attempt_001/result.json \
  --decision accept \
  --case-id pandas_timezone_001 \
  --out data/curated/pandas_timezone_001.yaml

silent-drift oracle generate \
  --case data/curated/pandas_timezone_001.yaml \
  --template pytest \
  --out data/oracle/pandas_timezone_001/

silent-drift oracle validate \
  --oracle data/oracle/pandas_timezone_001/oracle_spec.yaml \
  --mode old

silent-drift bench package \
  --case data/curated/pandas_timezone_001.yaml \
  --oracle data/oracle/pandas_timezone_001/oracle_spec.yaml \
  --levels L1,L2,L3 \
  --out data/packages/

silent-drift audit case \
  --package data/packages/TASK_ID/ \
  --out data/audit/TASK_ID.json
```

`oracle validate` 会运行隐藏 pytest 判定器（Hidden Pytest Oracle），并把日志写入 `validation/<mode>_pass.log` 或 `validation/<mode>_fail.log`。

预期判定器布局（Oracle Layout）：

```text
data/oracle/<case_id>/
  oracle_spec.yaml
  hidden/
    test_behavior.py
    expected.json
  public/
    README.md
    starter_client.py
  validation/
    old_pass.log
    new_fail.log
    fixed_pass.log
```

## 验收标准（Acceptance Criteria）

- 已接受案例 YAML（Accepted Case YAML）能校验，并链接回复现结果。
- 被拒绝案例（Rejected Cases）会记录，不能删除。
- 公开文件（Public Files）不包含旧/新预期输出（Expected Old/New Output）。
- 公开文件不命名隐藏判定器文件（Hidden Oracle Files）。
- 旧版本校验（Old Validation）通过，新版本校验（New Validation）因预期原因失败。
- 生成的任务包不会把隐藏判定器复制到公开启动仓库（Public Starter Repo）。
- 审计能对故意泄漏（Intentional Leakage）明确失败，并输出 JSON 报告。

## 非目标（Non-Goals）

- 不实现 L4 盲操作任务（Blind Operation Tasks）。
- 不生成 JUnit、Go test 或 Rust test 判定器。
- 不使用 LLM 裁判作为主要判定器（Primary Oracle）。
- 不做抽样审计（Sampled Audit）；每个打包案例都必须审计。
