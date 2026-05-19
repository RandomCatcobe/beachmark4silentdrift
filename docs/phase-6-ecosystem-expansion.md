# 阶段 6：生态扩展（Ecosystem Expansion）

## 目标（Goal）

交付 v0.6：只在 Python 生命周期（Python Lifecycle）稳定后扩展到其他生态（Ecosystems）。第一个扩展目标是 JVM；Go 和 Rust 只有在案例流水线确实需要时再加入。

## TODO

- 定义每个生态适配器（Ecosystem Adapter）必须满足的门槛（Adapter Gates）。✓
- 一次只增加一个生态适配器。
- 只有在 Python 已有多个已审计真实案例（Audited Real Cases）后，才开始 JVM。
- 复用同一生命周期：候选（Candidate）、分诊（Triage）、复现（Reproduction）、整理（Curation）、判定器（Oracle）、打包（Package）、审计（Audit）。
- 把生态特定环境逻辑（Ecosystem-Specific Environment Logic）限制在适配器边界（Adapter Boundary）内。

## 当前门槛状态（Current Gate Status）

```bash
silent-drift-miner ecosystem gates \
  --target jvm \
  --packages data/packages \
  --audit data/audit \
  --min-python-cases 3
```

当前有 3 个已审计真实 Python 案例，因此 JVM gate 已通过。不过当前执行范围仍是 Python-only；不要开始 JVM/Go/Rust adapter，除非用户明确重新打开多语言迁移。

本机 JVM 环境还需要单独检查：

```bash
silent-drift-miner ecosystem env-check \
  --target jvm \
  --out data/ecosystem_gates/jvm_env.json
```

如果 `java` 不存在，先记录 blocked 状态，不创建不可验证的 adapter。

## CLI/API 形状（CLI/API Shape）

外部 CLI 应保持一致：

Reserved adapter contracts can be inspected without executing a non-Python adapter:

```bash
silent-drift-miner ecosystem adapters
silent-drift-miner ecosystem adapters --target jvm
```

```bash
silent-drift-miner reproduce plan \
  --candidate-id CANDIDATE_ID \
  --ecosystem jvm \
  --library LIBRARY \
  --old-version OLD_VERSION \
  --new-version NEW_VERSION \
  --client-file examples/reproducers/CANDIDATE_ID/client \
  --out data/reproductions/CANDIDATE_ID/spec.json

silent-drift-miner reproduce run \
  --spec data/reproductions/CANDIDATE_ID/spec.json \
  --out data/reproductions/CANDIDATE_ID/attempt_001/
```

适配器契约（Adapter Contract）：

```text
create_old_env(case)
create_new_env(case)
install_dependency(version)
run_client(client_path)
classify_failure(run_logs)
generate_oracle_candidate(case)
```

## 验收标准（Acceptance Criteria）

- 新适配器输出与 Python 相同的复现结果模式（Reproduction Result Schema）。
- 新适配器尽量记录相同失败类别（Failure Categories）。
- 新适配器有离线玩具夹具（Offline Toy Fixtures）。
- 任何生态都不能绕过整理、判定器验证、打包和审计。
- JVM 先从一个最小、确定性案例（Minimal Deterministic Case）开始。

## 非目标（Non-Goals）

- 不在 Python 证明真实需求前创建空泛抽象适配器（Abstract Adapters）。
- 不在同一里程碑同时加入 Go/Rust。
- 第一次扩展不支持统计性或分布式漂移（Statistical or Distributed Drift）。
- 不把论文式模型比较（Model Comparison）放进生态扩展工作。
# 2026-05-19 JVM Boundary Update

The user explicitly opened the JVM special-case boundary. JVM is no longer only
reserved: it has an active adapter under `silent_drift_miner.adapters.jvm` for
local deterministic cases. Required real tools are now `java` and `javac`;
`mvn` and `gradle` remain optional. Other ecosystems remain reserved.

# 2026-05-19 JS Boundary Update

The user then asked to adapt additional languages gradually, one at a time. JS
is now active under `silent_drift_miner.adapters.js` for local deterministic
Node package-root cases. Required real tool: `node`; package managers remain
optional and are not part of the default execution path.

# 2026-05-19 PHP Boundary Update

Continuing the one-language-at-a-time expansion, PHP is now active under
`silent_drift_miner.adapters.php` for local deterministic PHP CLI include-path
cases. Required real tool: `php`; Composer remains optional and is not part of
the default execution path.

# 2026-05-19 Ruby Boundary Update

Continuing the one-language-at-a-time expansion, Ruby is now active under
`silent_drift_miner.adapters.ruby` for local deterministic Ruby CLI load-path
cases. Required real tool: `ruby`; Bundler remains optional and is not part of
the default execution path.

# 2026-05-19 .NET Boundary Update

Continuing the one-language-at-a-time expansion, .NET is now active under
`silent_drift_miner.adapters.dotnet` for local deterministic .NET CLI
project-root cases. Required real tool: `dotnet`; NuGet remains optional and is
not part of the default execution path.

# 2026-05-19 Go Boundary Update

Continuing the one-language-at-a-time expansion, Go is now active under
`silent_drift_miner.adapters.go` for local deterministic Go CLI package-root
cases. Required real tool: `go`; network module download is not part of the
default execution path.

# 2026-05-19 v0.11.0 Status Update

`v0.11.0` keeps Python as the mature production lifecycle and records the
current non-Python adapter state after the sequential expansion:

| Ecosystem | Status | Required real tool(s) | Default scope |
| --- | --- | --- | --- |
| Python | mature | `python`, `pip` | real audited package cases |
| JVM | active | `java`, `javac` | local deterministic Java source-root cases |
| JS | active | `node` | local deterministic Node package-root cases |
| PHP | active | `php` | local deterministic PHP CLI include-path cases |
| Ruby | active | `ruby` | local deterministic Ruby CLI load-path cases |
| .NET | active | `dotnet` | local deterministic .NET CLI project-root cases |
| Go | active | `go` | local deterministic Go CLI package-root cases |
| Rust | reserved | `cargo`, `rustc` | not opened yet |

Optional package managers remain outside the default path unless a concrete
future case justifies them.
