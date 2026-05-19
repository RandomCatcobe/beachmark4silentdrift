# 阶段 2：Python 复现（Python Reproduction）

## 目标（Goal）

交付 v0.2 的 Python-only 复现工具（Reproduction Harness）。它只使用人工编写客户端（Hand-Authored Client），在旧版本和新版本依赖（Old/New Dependency Versions）上运行同一份 `client.py`，捕获输出（Output）、总结差异（Diff），并分类保留/丢弃决策（Keep/Drop Decision）。

## TODO

- 增加 Python 复现模式（Reproduction Schema），覆盖规格（Spec）、运行（Run）、结果（Result）和差异（Diff）。✓
- 从已接受候选（Accepted Candidate）和人工 `client.py` 生成复现计划（Reproduction Plan）。✓
- 为同一库与版本对（Version Pair）生成旧/新环境定义（Old/New Environment Definitions）。✓
- 分别捕获 stdout、stderr、退出码（Exit Code）、运行日志（Run Logs）和构建日志（Build Logs）。✓
- 为 stdout/stderr/退出码差异生成摘要（Diff Summary）。✓
- 运行多次时创建 `attempt_001`、`attempt_002`，不能覆盖旧尝试（Attempt）。✓
- 记录结构化丢弃原因（Drop Reasons）。✓

## CLI/API 形状（CLI/API Shape）

```bash
silent-drift reproduce plan \
  --candidate-id CANDIDATE_ID \
  --library pandas \
  --old-version 1.5.3 \
  --new-version 2.0.0 \
  --client-file examples/reproducers/CANDIDATE_ID/client.py \
  --out data/reproductions/CANDIDATE_ID/spec.json

silent-drift reproduce run \
  --spec data/reproductions/CANDIDATE_ID/spec.json \
  --out data/reproductions/CANDIDATE_ID/attempt_001/ \
  --install \
  --venv-root .repro_venvs/

silent-drift reproduce summarize \
  --result data/reproductions/CANDIDATE_ID/attempt_001/result.json
```

预期产物布局（Artifact Layout）：

```text
data/reproductions/<candidate_id>/attempt_001/
  spec.json
  old/
    Dockerfile
    stdout.txt
    stderr.txt
    exit_code.txt
    run.log
    build.log
  new/
    Dockerfile
    stdout.txt
    stderr.txt
    exit_code.txt
    run.log
    build.log
  diff.json
  result.json
```

丢弃原因（Drop Reasons）：

```text
install_failed
import_failed
client_generation_failed
client_runtime_error
no_behavior_diff
hard_break
flaky_output
timeout
```

## 验收标准（Acceptance Criteria）

- 一个玩具 Python 包版本夹具（Toy Python Package Fixture）可以离线复现。
- 旧版本运行（Old Run）和新版本运行（New Run）使用同一份客户端文件（Client File）。
- stdout、stderr、退出码和日志分别存储。
- `result.json` 写明保留/丢弃（Keep/Drop）及原因。
- 重跑同一规格（Spec）会创建新的尝试目录（Attempt Directory）。
- Docker 相关测试在必要时使用 mock。

## 非目标（Non-Goals）

- 不支持 JVM、Go、Rust 或多语言抽象（Multi-Language Abstraction）。
- 本阶段不使用 LLM 生成客户端。
- 安装失败（Install Failed）或导入路径变化（Import Path Changed）不能算静默漂移（Silent Drift）。
- 不打包 benchmark 任务（Benchmark Tasks）。
