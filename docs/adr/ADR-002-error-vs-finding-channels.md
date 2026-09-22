# ADR-002：错误与检测发现走两条独立通道

- 状态：**已接受**（A1 谢浩天，A09；错误码命名空间及注册表归属经 B1 复核）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 8、9、10、25 页；`docs/interfaces/errors.md`；ADR-005

## Context

BuildChecker 与 EChecker 的**正常工作结果**就是「报告存在缺失依赖（MD）和
冗余依赖（RD）」。也就是说，一次完全成功的检测，其产出很可能是「发现了问题」。

这与「工具没跑完」是两件完全不同的事，但如果契约不强制区分，二者极易被写进
同一个字段——最自然的误写就是把 MD 当成错误，于是 `status` 变成 `FAILED`。

后果是连锁的：

- MDFixer（B3）的输入是 MD 报告（第 12、23 页：「只消费 MD」）。
  若 MD 被写成 `FAILED` + `job.error`，B3 按「失败任务不消费」的规则就会**永远收不到待修复项**。
- 「项目很干净，零发现」和「分析器崩了，什么都没查」在数据上变成同一种形状，
  无法区分。
- 重试策略错位：MD 不该重试，环境故障该重试。

第 9 页专门用一整页讲这件事，第 25 页又把「解释 MD 为什么不等于工具执行失败」
列为四条最小检查之一。第 8 页在 `SUCCEEDED` 旁边直接标注「可能报告 MD/RD」。

## Decision

**两条通道，物理隔离，由 schema 的状态矩阵强制。**

| | 通道 A：系统执行错误 | 通道 B：正常分析发现 |
| --- | --- | --- |
| 载体 | `job.error` | `output.findings[]` + `ERROR_REPORT` artifact |
| 出现的 `status` | `FAILED` / `TIMED_OUT` | `SUCCEEDED` |
| 取值 | `ENV_3xxx` / `EXEC_4xxx` / `ANALYSIS_5xxx` / `VALIDATION_2xxx` | `MISSING` / `REDUNDANT` |
| 另一侧必须为 | `output` = `{}` | `error` = `null` |

具体约束写进 `task.schema.json` 的 `status_matrix`：

- `SUCCEEDED` → `error` 必须是 `null`（`{"const": null}`），`output` 可含 findings
- `FAILED` / `TIMED_OUT` → `error` 必须是合法 error 对象，`output` 必须 `maxProperties: 0`
- `QUEUED` / `RUNNING` / `CANCELLED` → `error` 必须 `null`，`output` 必须 `{}`

并且 **`error.code` 的命名空间正则不接受 `MISSING` / `REDUNDANT`**：

```
^(VALIDATION_2[0-9]{3}|ENV_3[0-9]{3}|EXEC_4[0-9]{3}|ANALYSIS_5[0-9]{3})$
```

所以「把 MD 写进 error」这条路在类型层面就走不通，不靠人自觉。

反向也封死：`FAILED` 的 `output` 必须为空，所以「任务失败了但顺便带出半截 findings」
也不合法——要么跑完给结论，要么没跑完给错误码。

### finding 的完整形状

第 10 页给了五个字段的样例（`type` / `target` / `dependency` / `commit` / `detector`），
并注明「完整报告还要有位置和证据」「人工样本标明人工来源」。
第 5 页从接收方视角要求同一件事：修复交接时接收方要能核对
「目标、缺失文件、位置与证据」。

因此 A1 把 finding 定为九个必填字段：

```
id, type, target, dependency, commit, detector, location, evidence[], message
```

- `location` = `{path, line?, column?}`，让 B3 知道改哪个文件哪一行
- `evidence[]` 非空数组，`kind ∈ {PROCESS_TRACE, FILE_ACCESS, DECLARATION, INSTRUCTOR_SAMPLE}`
  对应第 21 页「进程、文件和声明位置证据」
- `detector = INSTRUCTOR_ORACLE` 即第 10 页的「人工样本标明人工来源」
- `commit` 必须完整 40 位 SHA，这是第 5 页「报告属于当前源码版本」的机器可验证形式

**缺位置或证据的 finding 会被校验器拒绝**，因为 B3 拿它无法定位到要修改的声明。

## Alternatives

### 单一 `error` 字段，用 `severity` 区分严重程度

只需一个字段，看起来更简洁。但「严重度」是连续谱，而这里需要的是**二元互斥**：
分析器有没有得出结论。用 severity 表达会让「SUCCEEDED 但有 error」这种
自相矛盾的文档合法化，B3 仍要自己猜该不该消费。**否决。**

### MD 也判 `FAILED`，另加 `error.code = "MISSING_DEPENDENCY"`

直觉上「发现问题=失败」。但这正是第 9 页要纠正的误解，且直接违反第 8 页
「`SUCCEEDED` … 可能报告 MD/RD」。后果见 Context：B3 收不到输入，
零发现和没检出无法区分。**否决。**

### finding 只保留第 10 页样例的五个字段，位置和证据留给服务自己扩展

契约更小、各组更自由。但第 5 页明确把「位置与证据」列为**接收方的检查项**，
第 12 页 B 侧「修复报告输入」的验收条件是「只消费 MD」——消费的前提是报告够用。
若位置与证据可选，B3 会在联调时才发现拿到的报告改不动文件，
而那时已经是 E3/E12 了。**否决**，改为九个字段全必填。

### `error.code` 写成封闭枚举（只允许第 9 页那三个码）

最严格。但任何一组新增错误码都构成第 26 页所说的枚举改变，属破坏性变更，
六个人被锁死在一次同步升级里。改用命名空间正则 + `errors.md` 注册表，
各组可在自己的段内增码而不动 schema。详见 ADR-004。**否决。**

## Consequences

**得到的：**

- 第 25 页检查 04 有了书面答案（`errors.md` 第一节）**和**可执行断言
  （`tests/…Check04MdIsNotExecutionFailure`：MD 进 findings 合法，
  同一条 MD 进 `error.code` 被拒）。
- B3 的消费规则变得极简：只看 `status == SUCCEEDED` 且 `output.findings[].type == MISSING`。
- 「干净项目」与「分析器崩溃」在数据上彻底分开：前者 `SUCCEEDED` + `findings: []`，
  后者 `FAILED` + `ANALYSIS_5001`。
- 重试策略可以直接由 `error.code` 的命名空间推导，不必解析 `message` 文本。

**付出的：**

- finding 九个字段全必填，对 A2/A3 是负担：即使工具拿不到行号，
  也得显式写 `line: null` 而不是省略。这是刻意的——省略和「查过了但没有」
  必须可区分。
- `evidence` 必须非空，意味着检测服务得真的留下证据文件（进程 trace、声明图）。
  第 21 页本来就把这些列为 BuildChecker 的输出，所以不是新增负担，只是提前强制。
- 六个状态 × 三条通道规则的组合较多，样例量随之上升。负例逐条覆盖，
  清单见 `../VALIDATION.md` 第五节。

**验证：**

- `samples/full-check.job-succeeded.json` —— `SUCCEEDED` + `error: null` + 一条 MD、一条 RD
- `samples/invalid/md-reported-as-error.json` —— 同一条 MD 写进 `error` → 被拒
- `samples/invalid/succeeded-with-error.json` —— `SUCCEEDED` 带 error → 被拒
- `samples/invalid/failed-without-error.json` —— `FAILED` 无 error → 被拒
- `samples/invalid/timed-out-with-output.json` —— `TIMED_OUT` 带 output → 被拒
- `samples/invalid/finding-missing-evidence.json` —— finding 缺位置与证据 → 被拒
- `samples/job.failed.json` / `job.analysis-failed.json` —— `ENV_3002` 与 `ANALYSIS_5001` 的区分

**B1 已确认：** `VALIDATION_2xxx` 仅用于创建期同步拒绝，不写入 `job.error`；
错误码注册表由 B1 维护。`retryable` 的服务侧建议值仍由各服务负责人确认。
