# ADR-010：状态迁移规则的形式化，兼修正 ADR-005 的判据表述

- 状态：**Accepted**（A1 谢浩天，A09 提出；B1 李秉轩于 2026-09-22 评审通过）
- 日期：2026-09-21
- 契约版本：1.0.0（未递增，理由见第五节）
- 相关：第 5、8 页；ADR-001、ADR-005；`endpoints.md`「状态迁移（B1 补充）」一节
- 编号说明：008 / 009 已由 `adr/README.md` 预留给 A3 与 B3，故本篇取 010

## Context

B1 于 2026-09-21 在 `endpoints.md` 补入「状态迁移」一节，给出七行迁移表和三条硬规则：

1. 终态不可再迁移
2. **`RUNNING` 不可跳过** —— 原文理由是「从 `QUEUED` 直达终态意味着执行器没有记录开始时间，`execution.started_at` 会缺失，而它是判断超时归属的凭据」
3. `retryable` 为 `true` 时重试产生新的 `attempt`，不产生新 `job_id`

但迁移表第三行写的是：

| 起始状态 | 事件 | 目标状态 | 必须写入 |
| --- | --- | --- | --- |
| `QUEUED` | 受理后环境准备失败 | `FAILED` | `error.code = ENV_3002` |

**这一行与硬规则 2 直接冲突。** 任务在队列里就因为镜像拉不下来而失败，
它从未被执行器领取，`started_at` 只能是 `null`——而这正是硬规则 2 说「不可以」的情形。
同一行里 `QUEUED → CANCELLED`（队列中取消）也是同样的问题。

这个冲突不是文字瑕疵。它决定了 `execution.started_at` 到底能不能为 `null`，
而这会落到 schema、校验器和四个服务的执行器实现上。

同时，B1 在同一份文档末尾补了另一条规则：

> 接收方检查「基线版本和配置匹配」，落到字段上就是 `input.baseline.commit` 必须等于
> `input.base_commit`，且 `input.baseline.configuration_id` 必须等于
> `input.environment.configuration_id`。

这条规则该由谁在什么时候执行，ADR-005 没有说清，且 ADR-005 的判据表述本身有问题
（见第四节）。

## Decision

### 1. 迁移规则不在文档里靠自觉，而是形式化为**单文档可校验的计时约束**

迁移本身是「文档序列」上的性质，单个 Job 文档看不到自己的前驱。
但每一次迁移都会在 `execution` 上留下必然痕迹，而痕迹是单文档可校验的：

| `status` | `started_at` | `finished_at` | 含义 |
| --- | --- | --- | --- |
| `QUEUED` | 必须 `null` | 必须 `null` | 尚未被执行器领取 |
| `RUNNING` | 必须是时间戳 | 必须 `null` | 已领取，未结束 |
| `SUCCEEDED` | 必须是时间戳 | 必须是时间戳 | 确实跑过并跑完了 |
| `TIMED_OUT` | 必须是时间戳 | 必须是时间戳 | 确实跑过，跑到超时 |
| `FAILED` | **允许 `null`** | 必须是时间戳 | 可能从未被领取（环境准备失败） |
| `CANCELLED` | **允许 `null`** | 必须是时间戳 | 可能在队列中就被取消 |

这套约束同时落实了 B1 的三条硬规则里可单文档验证的两条：

- 「终态不可再迁移」→ 终态必须有 `finished_at`，非终态必须没有
- 「`RUNNING` 不可跳过」→ `SUCCEEDED` 与 `TIMED_OUT` 必须有 `started_at`

### 2. 冲突的解法：**收窄硬规则 2，而不是删掉迁移表那一行**

`QUEUED → FAILED`（环境准备失败）是真实且必须支持的路径：镜像拉不下来时，
让执行器先「领取」任务再立刻失败，只是为了满足一条文档规则而伪造一次
`started_at`，那会让「任务真正跑了多久」这个指标失真。

因此硬规则 2 应改述为：

> **`SUCCEEDED` 与 `TIMED_OUT` 不可跳过 `RUNNING`**（必须有 `started_at`）；
> `FAILED` 与 `CANCELLED` 允许从 `QUEUED` 直达，此时 `started_at` 为 `null`。

B1 给出的原始理由——「`started_at` 是判断超时归属的凭据」——在收窄后依然成立：
超时只可能是 `TIMED_OUT`，而 `TIMED_OUT` 必须有 `started_at`。**规则的本意被完整保留，
只是适用范围从「所有终态」收窄到「确实运行过的终态」。**

建议 B1 据此修订 `endpoints.md` 的硬规则 2 表述。迁移表本身无需改动——表是对的。

### 3. 基线一致性属**运行期的接收方检查**，契约校验器故意不强制

第 5 页的表格右列标题是「**接收方检查**」：

| 交接 | 发送方提供 | 接收方检查 |
| --- | --- | --- |
| 增量检测 | 旧提交的依赖图、配置与新提交 | 基线版本和配置匹配 |

接收方是 EChecker（A3），检查发生在它拿到请求之后，即运行期。B1 自己的表述
「接收方检查『基线版本和配置匹配』」也是这个意思。

因此：

- `input.baseline.commit == input.base_commit` → **运行期**，不符则 `FAILED` + `ENV_3003`
- `input.baseline.configuration_id == input.environment.configuration_id` → **运行期**，同上
- `tools/validate.py` **不**做这两项交叉比对

样例 `job.baseline-mismatch-failed.json` 因此是**合法**文档：它记录的正是一次
通过了创建期校验、在运行期因基线不匹配而失败的任务。

`tests/test_validate.py::TestBaselineConsistencyIsRuntimeNotContract` 用三条断言
把这层边界钉住，防止后来者误把它收紧成创建期拒绝——收紧会导致该样例变为非法，
并让 A3 失去表达「基线不匹配」这一真实故障的手段。

**但字段形状仍然强制**：`baseline` 必填，四个子字段必填，`commit` 必须是完整
40 位 SHA，`actual_graph_uri` 与 `error_report_uri` 必须落在 `pair09` 命名空间。
不比对值，不等于不校验形状。新增历史报告的理由见 ADR-008。

## Alternatives

### 删掉迁移表的 `QUEUED → FAILED` 行，严格维持「`RUNNING` 不可跳过」

文档自洽了。但代价是执行器必须在环境准备失败时伪造一次 `started_at`，
或者把「镜像拉不下来」硬塞进 `RUNNING` 之后再失败——两种做法都污染了
「任务实际运行时长」这个指标，而 `EXEC_4002` 超时归属恰恰依赖它。**否决。**

### 把迁移规则留在文档里，不进 schema 和校验器

最省事。但 `execution.started_at` 能否为 `null` 是个会直接影响四个服务实现的
硬约束，只写在文档里等于靠人自觉；等到 E3 联调时才发现某一组的执行器
在 `QUEUED` 状态就填了 `started_at`，返工成本远高于现在加六条断言。**否决。**

### 用一个独立的状态机校验器，接收 Job 文档序列做校验

理论上最完整，能真正验证「终态不可再迁移」。但 E2 不部署服务、没有任务存储，
不存在可供校验的文档序列；造一个只能喂假数据的序列校验器没有意义。
单文档计时约束已经覆盖了可验证的部分。**否决**（E3 若有了任务存储可重新评估）。

### 把基线一致性也放进 `validate.py`

能让校验器「更强」。但直接违反第 5 页把它列为「接收方检查」的定位，
且会让 `job.baseline-mismatch-failed.json` 这个教学样例变成非法文档。
更实际的问题是：A3 需要一个合法的方式表达「基线不匹配」这种真实故障，
如果创建期就拒了，运行期的 `ENV_3003` 就没有存在的余地。**否决。**

### 递增 `schema_version` 到 1.1.0

见第五节。**本次不递增**，但已提交 B1 裁定。

## 四、对 ADR-005 判据表述的修正

ADR-005 给出的判据是「能不能只看请求体就判定」，并把
`baseline.commit ≠ base_commit` 归为「必须去读产物、比对提交，只能在执行期」。

**这个理由是错的。** 比对请求体里两个字面量字符串不需要读任何产物。
`baseline.configuration_id` 与 `environment.configuration_id` 同理。

结论没错，理由错了——而这种错误理由会误导后来者：按「需不需要 I/O」判断，
所有文档内交叉比对都会被划到创建期，正是上文否决的第四种方案。

正确的判据应当是**职责归属**，而非技术可行性：

> **形状与格式违规** → 创建期拒绝，HTTP 400 + `VALIDATION_2xxx`，不产生 Job。
> **第 5 页列为「接收方检查」的语义一致性** → 运行期，由接收方服务判定，
> 落为 `FAILED` + 相应 `job.error` 码。
> **需要外部资源才能确认的真值**（产物是否存在、sha256 是否相符、镜像能否拉取）
> → 运行期。

按 B1 在 `adr/README.md` 第一节的规则（「撤销或修正了前面已写下的某个决定」需写 ADR，
「同一主题的后续决定新建一篇并标注替代关系，不修改原文」），
本篇不改动 ADR-005 原文，仅在此标注：**ADR-005 第三节的判据表述由本篇第四节修正，
其分类结论仍然有效。**

## 五、版本号：本次不递增，请 B1 裁定

本篇同时收紧了 `error.code`（拆出 `job_error_code`，排除 `VALIDATION_2xxx`）。
按 `versioning.md` 第二节，「改动 `error.code`」列在「可能破坏兼容」栏，似乎应当 MAJOR 加一。

A1 的判断是**不递增**，理由：

`errors.md` 第二节（B1 于 2026-09-21 定稿，属 1.0.0 契约的组成部分）已经明文规定
`job.error.code` 只取三段、`VALIDATION_2xxx` 不写入 `job.error`。
也就是说 **1.0.0 的规范从未允许过 `VALIDATION_2xxx` 出现在 `job.error`**，
是 `task.schema.json` 的正则写宽了，与已定稿的规范不一致。
本次改动是让 schema 符合 1.0.0 规范，不是改变规范。

按 `versioning.md` 第一节，这更接近「契约形状不变」的修正。
且实际影响面为零：仓库内没有任何合法样例在 `job.error` 里用过 `VALIDATION_2xxx`
（只有 A1 自己的一条测试断言过它会被接受，该断言已随本篇改正）。

**但版本号归 B1 维护，本判断需 B1 确认。** 若 B1 认为应收紧为 MINOR 或 MAJOR，
A1 将同步修改 `schema_version` 的 `const`、全部 38 个样例与相关测试。
已记入 `CHANGELOG.md` 待处理表与 `BACKLOG.md`。

## Consequences

**得到的：**

- B1 迁移表里那处自相矛盾有了明确解法，且解法保留了他规则的**本意**
  （超时归属仍可判定），不是简单删掉了事。
- `execution.started_at` 能否为 `null` 有了确定答案，四个服务的执行器实现有据可依。
- 六条计时约束进了 schema 与校验器，不再靠人自觉。
- 基线一致性的职责归属被三条测试钉住，后来者不会误收紧。
- ADR-005 那个错误的理由被公开修正，避免「按 I/O 判断」这个错误判据扩散。

**付出的：**

- `FAILED` / `CANCELLED` 的 `started_at` 变成「可 null 也可非 null」，
  消费方不能用「`started_at` 非空」来判断任务是否跑过，必须结合 `status`。
- 单文档约束**不能**证明「终态不可再迁移」——那需要文档序列。
  本 ADR 只覆盖了可验证的部分，剩下的仍靠执行器自律，已在 `VALIDATION.md` 的
  未覆盖清单里写明。
- 修改了 B1 定稿文档所依赖的一条硬规则表述，需要 B1 认可；
  若 B1 坚持原表述，则 `QUEUED → FAILED` 路径必须从迁移表删除，
  并另行定义环境准备失败的表示方式。
- `job.failed.json` 等现有样例都带 `started_at`，未覆盖「`FAILED` 且 `started_at` 为 null」
  这一新合法形态。已用测试覆盖（`test_failed_without_started_at_is_allowed`），
  但是否补一个独立正例样例，留待 B1 决定。

**验证：**

```
$ make check
A09/B09 公共契约校验通过：…
Ran 39 tests in 0.019s
OK
```

- `tests/…TestTransitionTiming` 七条：QUEUED/RUNNING 的 null 约束、
  非终态不得有 `finished_at`、`SUCCEEDED` 不得跳过 `RUNNING`、
  六个终态样例都有 `finished_at`、`FAILED`/`CANCELLED` 允许 `started_at` 为 null
- `tests/…TestBaselineConsistencyIsRuntimeNotContract` 三条：
  值不匹配仍通过校验，但字段缺失仍被拒
- `samples/invalid/validation-code-in-job-error.json`：`VALIDATION_2001` 写进
  `job.error` → 被拒
- `tests/…::test_schema_splits_the_two_code_namespaces`：断言两个正则互斥且各自正确

**B1 评审结论（2026-09-22）：**

- [x] **硬规则 2 的收窄表述（第二节）——采纳。** `endpoints.md`「状态迁移」一节已按第二节
      改写，并留下修订记录；迁移表本身未改动。原表述与本组定义的状态样例不再冲突。
- [x] **`schema_version` 是否递增（第五节）——不递增，维持 `1.0.0`。**
      本次与 ADR-009 的两个封闭 enum、ADR-011 的三种 artifact 本体一并裁定，
      理由与落地清单见 `../versioning.md` 第七节，记录见 `../CHANGELOG.md`
      「B1 版本裁定与复核（2026-09-22）」。
- [x] **是否补一个「`FAILED` 且 `started_at` 为 null」的独立正例——补。**
      新增 `samples/job.failed-before-start.json`（`QUEUED→FAILED`，`ENV_3002`，
      `started_at` 与 `duration_ms` 均为 `null`），`VALIDATION.md` 第五节的正例数同步更新。
      在这之前该形态只有测试里的变异断言覆盖，其它组无法直接拿样例核对。
- [x] **基线一致性归运行期是否与 A3 的实现计划一致——一致。**
      A3 已合并的 `interfaces/echecker-contract.md` 第四节把 commit / `configuration_id`
      不匹配定义为**运行期接收方检查**，落为 `FAILED` + `ENV_3003`，与第三节结论相同；
      `tests/…TestBaselineConsistencyIsRuntimeNotContract` 的三条断言钉住这条边界。
      如 A3 对该表述有异议，在 Issue #1 提出即可，本 ADR 的状态随之回退为 `Proposed`。
