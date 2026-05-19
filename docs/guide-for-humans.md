# 傻瓜指南：怎么给 SilentDrift 找合适的案例

> 这份指南是给真实的人看的。不需要懂代码，也不需要懂机器学习。
> 读完之后，你能判断"这个案例能不能进去"，并且知道怎么把它交给工具处理。

---

## 第一步：先搞清楚我们在找什么

**一句话版本**：API 的调用方式没变，但结果悄悄变了。

想象一下你每天喝同一家咖啡店的拿铁。杯子一样，价格一样，你的点法一样——但某天开始，咖啡变甜了。没人通知你，收据上也没写。这就是"静默行为漂移"。

换成代码的说法：

```python
# 两年前的代码，到今天还是这样写的
result = df.groupby("city")["revenue"].sum()
```

函数名没变，参数没变，代码没变。但在 pandas 2.0 之后，这行代码返回的结果**排序可能不同**——因为 `sort` 参数的默认值悄悄变了。没有报错，没有警告，程序一直在跑，只是结果不一样了。

---

## 第二步：什么是"好案例"，什么是"坏案例"

### 好案例长这样

| 特征 | 说明 | 例子 |
|------|------|------|
| **调用方式没变** | 代码不用改 | `requests.get(url)` 还是那么写 |
| **结果悄悄变了** | 输出不一样，但没报错 | 返回的 Content-Type 默认值变了 |
| **用户不容易察觉** | 不细看测试很难发现 | 分页的起始页从 0 变成 1 |
| **有明确版本边界** | 能说清楚"从哪个版本开始变的" | pandas 1.5 → 2.0 |

### 坏案例长这样（这些进不来）

| 特征 | 为什么不行 | 例子 |
|------|-----------|------|
| **旧代码直接崩了** | 不是"静默"的，是显式的破坏性变更 | `foo()` 方法被删掉了 |
| **抛出了异常** | 程序会报错，用户马上就知道 | `TypeError: argument required` |
| **只是加了个警告** | 功能还在，只是`DeprecationWarning` | `applymap` 警告但还能用 |
| **文档里大写加粗写了** | 官方已经告知，不算"静默" | Migration Guide 第一段就写明了 |
| **结果完全随机** | 无法稳定复现，没法做成测试 | 依赖系统时间的行为 |

### 一个快速判断方法

问自己这三个问题：

> **1. 我把旧代码原封不动拿来用，程序还能跑起来吗？**
> （如果不能——这是破坏性变更，不要）
>
> **2. 程序跑起来之后，结果和之前不一样了吗？**
> （如果一样——没有漂移，不要）
>
> **3. 这个变化藏得够深，普通人升级版本后不容易立刻发现吗？**
> （如果很显眼——不够"静默"，优先级低）

三个问题都是"是"，就是好案例。

---

## 第三步：去哪里找案例

按照"效果最好"排序：

### 来源 1：Migration Guide（迁移指南）

这是最好的来源。库的作者升版本的时候会写迁移指南，其中**"默认值变更"**这类条目最容易是好案例。

搜索关键词（Google 或 GitHub）：
```
pandas migration guide "default" changed
requests 3.0 breaking changes defaults
pydantic v2 migration behavior
fastapi changelog defaults
```

重点看描述类似这样的句子：
- "The default value of X has changed from A to B"
- "X now defaults to Y instead of Z"
- "Previously, X was Y by default; now it is Z"

### 来源 2：CHANGELOG / Release Notes

几乎每个开源库都有 CHANGELOG 或 GitHub Releases 页面。重点看**大版本升级**（1.x → 2.x）。

好的信号词：
- `default` / `defaults to` / `default changed`
- `now returns` / `now produces`
- `previously` / `used to`
- `timezone` / `encoding` / `charset`
- `sort` / `order` / `pagination`

坏的信号词（看到就跳过）：
- `removed` / `deleted` / `dropped`
- `now raises` / `throws` / `exception`
- `breaking change` / `incompatible`
- `must now` / `required`

### 来源 3：Stack Overflow 和 GitHub Issues

搜索格式：
```
pandas 2.0 unexpected behavior
requests behavior changed
pydantic unexpected result after upgrade
```

看那些提问格式是"我的代码没变，但升级后结果不一样了"的帖子。这类帖子通常是真实踩坑案例，质量很高。

### 来源 4：你自己的血泪史

你或者你的团队在升级某个库之后，被某个神奇的 bug 整过吗？那很可能就是一个好案例。

---

## 第四步：发现案例之后，需要收集哪些信息

把下面这张表填完，就够了：

| 字段 | 说明 | 例子 |
|------|------|------|
| **库名** | 是哪个 Python 库 | `pandas` |
| **旧版本** | 漂移之前的版本 | `1.5.3` |
| **新版本** | 漂移之后的版本 | `2.0.0` |
| **标题** | 一句话说明变了什么 | "groupby 的 sort 参数默认值从 True 变为无效（行为实际不变但语义调整）" |
| **摘要** | 2-3 句话描述：旧行为是什么、新行为是什么、调用者不改代码会受什么影响 | 见下方示例 |
| **受影响的 API** | 哪个函数/方法/类 | `DataFrame.groupby()` |
| **来源 URL** | 在哪里看到这个信息的（changelog/issue/SO） | `https://pandas.pydata.org/docs/whatsnew/v2.0.0.html` |
| **原文摘录** | 截取最相关的那段原文（不超过 400 字） | "The default value of observed..." |

**摘要示例（写成这样就够了）**：

> 在 pandas 1.x 中，`DataFrame.groupby()` 对含 NaN 的分组默认会忽略 NaN（observed=False 等效）。
> 升级到 pandas 2.0 之后，`observed` 参数的默认值语义发生变化，含 Categorical 列的 groupby 
> 行为可能产生更多分组行。调用者不修改代码就会得到行数更多的 DataFrame，且无任何报错或警告。

---

## 第五步：怎么把案例交给工具处理

### 方式 A：让工具自动挖掘（推荐新手）

如果你知道一个库"大概有问题"，可以让工具去自动扫描它的 changelog：

```bash
# 自动从 GitHub 获取 pandas 的发版记录并挖掘候选
silent-drift mine --library pandas --ecosystem python
```

运行完之后，工具会在 `data/candidates/pandas.jsonl` 里列出候选案例。你只需要逐条看一下，决定哪些值得继续处理。

### 方式 B：你已经找到了具体案例，直接喂给工具

```bash
# 把你找到的 changelog 片段保存到一个文本文件
# 比如 my_find.md，然后：
silent-drift mine \
  --library pandas \
  --source my_find.md \
  --source-url https://你找到这段文字的URL \
  --no-llm
```

### 方式 C：直接进入分诊队列（最快）

如果你已经手动确认了某个案例，可以直接在分诊队列里标记它：

```bash
# 查看分诊队列里有哪些候选在等待决策
silent-drift triage next --queue data/triage/pandas_queue.jsonl

# 标记一个候选为"接受，进入复现阶段"
silent-drift triage mark \
  --queue data/triage/pandas_queue.jsonl \
  --candidate-id abc123def456 \
  --decision accept_for_reproduction \
  --notes "pandas 1.5.3→2.0.0，groupby 默认行为变化，已在 changelog 确认"
```

---

## 第六步：常见误判和怎么避免

### 误判 1："这个警告算不算？"

`DeprecationWarning` 本身不算——但是：如果警告说"现在行为 X，将来会变成 Y"，然后在后续版本 Y 真的悄悄生效了，**那个生效的那一版才是我们要的案例**。

### 误判 2："这个是 bug fix，算不算？"

修了 bug 之后，旧的"错误行为"不见了，新的"正确行为"来了。如果：
- 调用者依赖了旧的错误行为（比如结果里多了个 None）
- 升级后那个 None 消失了，代码不报错但逻辑出问题

那这个 bug fix 就算。标题里可以注明"此前的错误行为被修复，导致依赖旧行为的代码结果改变"。

### 误判 3："这个库太冷门了要不要做"

优先选这些已知有丰富案例的库：
`pandas`、`requests`、`pydantic`、`fastapi`、`sqlalchemy`、`numpy`、`httpx`、`urllib3`

其他库也可以，但上面这几个历史版本稳定、案例密度高。

### 误判 4："我不确定旧版本的行为是什么"

这很正常。你只需要描述你**观察到**或**在文档里读到**的内容。工具会在复现阶段实际运行两个版本来确认。你不需要自己跑代码。

---

## 快速参考卡

```
好案例的三个必要条件
  ✓ 代码不改，程序还能跑
  ✓ 运行结果和以前不一样了
  ✓ 没有报错，没有异常

立刻排除的三个信号
  ✗ 函数/方法被删除了
  ✗ 会抛出异常
  ✗ 需要改代码才能用新版本

最好的来源
  → Migration Guide 里的 "default changed"
  → CHANGELOG 里的大版本说明
  → Stack Overflow 上"升级后行为不同"的帖子

需要提供的四件事
  → 库名 + 版本对（旧 → 新）
  → 受影响的函数/类名
  → 一句话标题 + 2-3 句摘要
  → 来源 URL
```

---

> 有疑问？把你发现的东西直接描述出来就行——工具会帮你过滤。
> 宁可提交一个"可能不对"的候选，也比什么都不提交强。
