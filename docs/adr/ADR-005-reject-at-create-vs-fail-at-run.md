# ADR-005：创建期拒绝 vs 运行期失败

- 状态：**已接受**（A1 谢浩天，A09；创建期错误码边界经 B1 复核；相关判据修订见待评审 ADR-010）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 5、7、8、9、12、16、22、25 页；ADR-002；`docs/interfaces/errors.md` 第四节

## Context

第 25 页检查 03 要求「删除增量任务的 `baseline`，应被拒绝」，
第 12 页把「缺 baseline 被拒绝」列为 A 侧 Backlog 的验收条件。
但两处都**没有说在哪里被拒绝**。异步 Job 模型下有两个候选时机：

- **创建期**：`POST /v1/incremental-check-jobs` 直接返回 `HTTP 400`，不产生 Job。
- **运行期**：POST 返回 202 受理，EChecker 后台跑起来才发现基线有问题，
  Job 落为 `FAILED` + `job.error`。

这个选择会同时改变 schema、`validate.py` 的行为、以及 A3 与 B1 的对接方式，
所以必须在冻结契约时定下来。第 16 页第三轮练习「加入一个失败输入，
讨论状态与错误码」讨论的正是这一类问题。

难点在于「基线有问题」不是一种情况，而是**两类**：

| 情况 | 例子 | 何时能发现 |
| --- | --- | --- |
| 结构性违规 | `input` 里根本没有 `baseline` 键；`baseline` 缺 `commit`；`commit` 是 7 位短 SHA | 解析请求体即可，不需要任何外部资源 |
| 语义性违规 | `baseline.commit` ≠ `input.base_commit`；`baseline.configuration_id` 与环境不符；`actual_graph_uri` 指向的产物已被清理或 sha256 不符 | 必须去读产物、比对提交，只能在执行期 |

第 22 页把这两类混在一句话里：「检查基线提交和配置是否匹配」——
既要检查字段在不在（结构），又要检查值对不对（语义）。

## Decision

**按「发现时机」切分，而不是按「严重程度」切分。**

### 1. 结构性违规 → 创建期同步拒绝，不产生 Job

```http
POST /v1/incremental-check-jobs
→ HTTP/1.1 400 Bad Request
  { "error": { "code": "VALIDATION_2001",
               "message": "input 缺少 INCREMENTAL_CHECK 的必填字段: baseline" } }
```

`task.schema.json` 把 `baseline` 列为 `INCREMENTAL_CHECK` 的 `input` 必填项，
所以 `tools/validate.py` 对缺 baseline 的文档直接判不合格——
这就是第 25 页检查 03 的落地形式。

关键推论：**这类请求根本不会进入 Job 状态机**，因此不存在「`FAILED` 的
缺 baseline 任务」这种东西。调用方拿到 400 就知道是自己的请求写错了，
改完重发即可，不需要轮询。

### 2. 语义性违规 → 受理，然后 `FAILED` + `job.error`

```json
{
  "status": "FAILED",
  "output": {},
  "error": {
    "code": "ENV_3003",
    "message": "基线不匹配：baseline.commit=ffff... 与 input.base_commit=a1b2c3d4... 不一致",
    "retryable": false
  }
}
```

字段都在、格式都对，所以 POST 通过；值对不对只有真正去读基线产物才知道。
落为 `FAILED` 而不是 400，因为任务确实被受理并消耗了资源，
调用方需要能通过 `job_id` 查到失败原因。

### 3. 校验器**故意不**做语义交叉检查

`tools/validate.py` 不校验 `base_commit == baseline.commit`。
这不是遗漏，是本 ADR 的直接结论：契约校验器管形状，不管跨字段语义真值。
若校验器也去比对这两个值，就会与运行期职责重叠，且 `samples/job.baseline-mismatch-failed.json`
这个**合法**样例反而会被判不合格。

因此本仓库有两个互补的样例，专门用来展示这条边界：

| 样例 | `baseline` | 校验结果 | 真实系统行为 |
| --- | --- | --- | --- |
| `samples/invalid/missing-baseline.json` | **缺失** | 被拒 | HTTP 400，不产生 Job |
| `samples/job.baseline-mismatch-failed.json` | 齐全但 `commit` 对不上 | **通过** | 202 受理 → `FAILED` + `ENV_3003` |

### 4. 判据：能不能只看请求体就判定

一句话规则，供四组自行套用：

> **只读请求体就能判定的错误 → 400 + `VALIDATION_2xxx`；**
> **需要访问外部资源（仓库、镜像、产物、基线图）才能判定的错误 → 受理 + `FAILED` + `ENV_3xxx`/`EXEC_4xxx`/`ANALYSIS_5xxx`。**

按这条规则分类四个服务的典型失败：

| 失败 | 分类 | 码 |
| --- | --- | --- |
| `INCREMENTAL_CHECK` 缺 `baseline` | 创建期 | `VALIDATION_2001` |
| `commit` 不是 40 位完整 SHA | 创建期 | `VALIDATION_2001` |
| `job_type` 写成 `ABC` | 创建期 | `VALIDATION_2001` |
| `REPAIR` 的 `md_report.type` 不是 `ERROR_REPORT` | 创建期 | `VALIDATION_2001` |
| `DRAFT` 缺 `limits.timeout_seconds` | 创建期 | `VALIDATION_2001` |
| 幂等键重复但请求体不同 | 创建期 | `VALIDATION_2002` |
| `baseline.commit` ≠ `base_commit` | 运行期 | `ENV_3003` |
| `actual_graph_uri` 指向的产物已不存在 | 运行期 | `ENV_3003` |
| 镜像拉取/构建失败 | 运行期 | `ENV_3002` |
| 超过 `limits.timeout_seconds` | 运行期 | `EXEC_4002` |
| 依赖图提取器崩溃 | 运行期 | `ANALYSIS_5001` |

注意 `REPAIR` 的 `md_report.type` 被归为**创建期**：类型是请求体里的字面值，
不需要读产物就能判定。而「那份报告的内容是否真的只含 MD」需要下载才知道，
属运行期。

## Alternatives

### 全部走运行期：POST 一律 202，任何问题都落 `FAILED`

实现最简单，服务端只有一条路径。但代价很大：调用方写错一个字段名，
也要先拿到 `job_id`、轮询、等到终态，才知道自己请求体拼错了——
把同步可判定的错误变成异步，纯粹是浪费。而且 `FAILED` 会混进真正的
环境/执行故障统计里，让「我们的服务稳不稳」这个指标失真。**否决。**

### 全部走创建期：POST 时把所有能查的都查了，包括读基线产物

调用方体验最好，400 就说明请求一定跑得起来。但 POST 会变成一个耗时操作
（要拉产物、比对 SHA），直接违反第 6、7 页「耗时任务先受理，再后台执行」
的立论基础；而且创建期查过不代表运行期还成立（产物可能刚好被清理），
所以运行期检查一个都省不掉，等于做两遍。**否决。**

### 按严重程度分：轻的 400，重的 `FAILED`

直觉合理，但「严重程度」没有客观判据，四个人会给出四种分法，
而且同一个错误在不同服务里严重程度不同。换成「发现时机」这条客观判据后，
分类结果唯一。**否决。**

### 让校验器也做语义交叉检查，把 `base_commit` ≠ `baseline.commit` 也判为不合格

能让 `validate.py` 更强。但这样 `samples/job.baseline-mismatch-failed.json`
这个合法且重要的样例就没法存在了——而它恰恰是用来向 B 组解释
「为什么这个 FAILED 是正常契约行为」的教学材料。校验器的职责是形状，
语义真值属运行期。**否决。**

## Consequences

**得到的：**

- 第 25 页检查 03 有了确定的实现形式，A3 的验收条件「删掉 baseline 被拒」
  可以直接由 `make check` 演示。
- 调用方错误处理变简单：400 → 改请求重发；`FAILED` → 按 `retryable` 决定重试。
  两种动作截然不同，现在由错误码命名空间直接区分。
- 四个服务能各自套用同一条判据归类自己的失败，不必逐一与 A1 协商。
- `VALIDATION_2xxx` 与 `ENV_3xxx` 的分界让「契约 bug」和「环境故障」
  在统计上分开。

**付出的：**

- 多了一个错误码命名空间（`VALIDATION_2xxx`），且它不出现在第 9 页的
  三个码里，属 A09/B09 扩展，需 B1 认可。
- 服务端要实现两条错误路径（HTTP 4xx 与 Job 终态），比单一路径复杂。
  E2 不部署所以暂时无成本，但 E3/E12 要落地。
- 「只看请求体就能判定」这条判据在边界情形下需要判断力。
  例如 `md_report.type` 是字面值（创建期），但 `md_report.sha256` 是否与
  实际文件相符要下载才知道（运行期）——同一个对象的不同字段落在不同侧。
  已在 `errors.md` 第四节的表格里逐个列明。
- 校验器**不**保证请求一定能跑成功。通过 `validate.py` 只说明形状合规，
  这一点必须在联调时向 B 组讲清楚，否则会产生「校验过了为什么还 FAILED」的误解。

**验证：**

- `samples/invalid/missing-baseline.json` —— 缺 `baseline` → 被拒（检查 03）
- `samples/invalid/short-commit-sha.json` —— 短 SHA → 被拒
- `samples/invalid/repair-wrong-report-type.json` —— `md_report.type=ACTUAL_GRAPH` → 被拒
- `samples/job.baseline-mismatch-failed.json` —— 语义不匹配 → **通过校验**，
  以 `FAILED` + `ENV_3003` 表达
- `tests/…TestSlide25Check03MissingBaseline` —— 现场 `del input["baseline"]`、
  置空 `baseline`、删 `configuration_id`、改短 SHA，四种变异全部断言被拒

**B1 已确认：** `VALIDATION_2xxx` 只用于创建期 HTTP 4xx 响应体，不产生 Job，
也不写入 `job.error`。请求结构与运行期语义的判据由 ADR-010 第四节修正，
该修正仍待 B1 评审。
