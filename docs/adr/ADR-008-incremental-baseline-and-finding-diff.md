# ADR-008：增量检测的基线可比性与 finding 差集语义

| 项 | 值 |
|---|---|
| 状态 | Accepted |
| 日期 | 2026-09-22 |
| 提议人 | A3 朱鸣涛（241250048） |
| 评审人 | B3、B1 |
| 关联文件 | `interfaces/echecker-contract.md`、`interfaces/task.schema.json`、`tests/test_echecker_contract.py` |

## Context

第 22 页要求 `INCREMENTAL_CHECK` 接收旧提交依赖图并输出当前、新增和消除的
finding，但原契约没有回答三个问题：

1. 只有 C0 的实际图时，如何知道某条 finding 是新增还是消除？
2. finding 的 ID、证据或描述改变时，是否算成新的依赖错误？
3. 更新后的图怎样保证能成为下一次检测的基线？

ISSTA 2024 EChecker 使用历史 clean build 实际依赖图，在新提交上结合增量构建观察、
预处理指令变化和 Makefile 构建命令变化，推导新的完整实际依赖图。课程 E2 不实现
算法，但必须把算法需要的输入和可供下游消费的输出定义完整。

## Decision

### 1. 基线同时引用 C0 实际图和 C0 ERROR_REPORT

`baseline` 必填四个字段：

```text
actual_graph_uri
error_report_uri
commit
configuration_id
```

实际图用于推导 C1 更新图；历史 ERROR_REPORT 提供 C0 finding 集合。没有历史报告就
无法准确计算 `resolved`，因此不能只给实际图。

字段缺失是创建期格式错误；字段值或下载后 artifact 不匹配是 EChecker 的运行期
接收方检查，失败时使用 `FAILED + ENV_3003`。这一职责边界沿用 ADR-010。

### 2. C0 必须是 C1 的祖先，但不限定为直接父提交

直接父提交适合逐提交检测，但契约允许一次比较跨越多个提交。此时
`introduced` / `resolved` 表示“从 C0 到 C1”这整个区间的净变化。若 C0 不是 C1
的祖先，变化方向不明确，运行期以 `ENV_3003` 失败。

### 3. finding 身份是 `(type, target, dependency)`

`id` 是一次报告中的追踪标识，`detector`、`location`、`evidence` 和 `message` 可能因
重新检测而变化；把它们纳入身份会把同一个持续存在的问题误报为“一条消除加一条
新增”。因此集合比较只使用依赖错误本身的三个字段，并按上游 ERROR_REPORT 中的
字面值比较，不自行猜测或改写路径。

设 C0 与 C1 的集合分别为 `F0`、`F1`：

```text
findings   = F1
introduced = F1 - F0
resolved   = F0 - F1
```

当前与新增 finding 的 `commit` 属于 C1；已消除 finding 保留 C0 的 commit，以便
追溯它最后一次存在的基线报告。

### 4. 更新图必须是完整、可继续消费的 C1 ACTUAL_GRAPH

`updated_graph` 必须由当前 Job 产生，属于 C1 和当前 `configuration_id`，并出现在
`output.artifacts[]`。其本体保留与输入相同的 `project_root`，内容是更新后的完整图，
而不是本次增量构建观察到的局部子图。

### 5. B3 只消费 C1 当前 ERROR_REPORT

EChecker 产生一份 C1 ERROR_REPORT，其 findings 与 `output.findings` 一致。B3 只处理
其中当前仍存在的 MISSING；`introduced` 可用于排序或说明，`resolved` 不进入修复。

### 6. E2 不定义“无基线时自动 clean build”

论文允许首次检测时执行 clean build 并保存历史图。本组已有 BuildChecker 专门负责
全量检测，因此基线缺失时走 A2，而不是让 A3 隐式承担第二套 clean build 职责。

## Alternatives

### 只传 C0 实际图，由 EChecker 猜测历史 findings

实际图没有声明图，也没有历史 MD/RD 集合，无法确定某个历史 finding 是否已经消除。
否决。

### 使用 finding.id 做集合身份

不同检测器或不同运行可以为同一错误生成不同 ID，会制造假的新增/消除。否决。

### 要求 C0 必须是 C1 的直接父提交

语义最简单，但会拒绝合法的批量比较和漏检补跑。祖先关系已经足够定义变化方向，
因此不增加这项限制。

### 把增量构建观察到的局部图直接当作 updated_graph

未重建 target 会从图中消失，下一轮以此为基线会不断丢边。否决。

### 没有基线时由 EChecker 自动执行 clean build

符合论文原型，但与本组 BuildChecker 的服务边界重复，也使 A3 请求的成本和语义不
稳定。E2 选择显式调用 A2 后再调用 A3。

## Consequences

**好处：**

- C0/C1 和新增/消除的含义可由样例和测试精确验证。
- 更新后的图能成为下一轮真实基线，形成连续检测闭环。
- B3 获得的是当前可修复 MD，不会误修已经消除的问题。
- 不把 E2 扩展成另一套全量构建服务。

**代价：**

- A3 请求比课件最小字段多一个 `baseline.error_report_uri`。
- EChecker 运行期需要读取两个历史 artifact，并检查祖先关系与元数据。
- finding 的路径规范依赖上游报告保持稳定；上游改变身份语义时必须走兼容性评审。

**新增工作：**

- schema、校验器和所有增量正例补齐历史报告 URI。
- 提供 C1 ACTUAL_GRAPH 与 ERROR_REPORT 本体样例。
- 用专项测试固定集合差、commit 归属、artifact 归属与哈希。

## 验证方式

- `python tools/validate.py`
- `python -m unittest tests.test_echecker_contract -v`
- `samples/incremental-check.request.json`
- `samples/incremental-check.job-succeeded.json`
- `samples/job.baseline-mismatch-failed.json`
- `samples/artifact.incremental-actual-graph.json`
- `samples/artifact.incremental-error-report-body.json`
