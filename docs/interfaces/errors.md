# 错误与检测发现：两条独立通道

小组 A09 / 配对组 B09 ｜ 契约版本 1.0.0 ｜ 负责人 A1（谢浩天），B1 复核

本页是 E2 第 9 页的落地约定，也是第 25 页最小检查第 04 条的书面答案。

## 一、核心规则：MD 不等于工具执行失败

> **第 25 页检查 04：解释 MD 为什么不等于工具执行失败。**

「发现缺失依赖」（Missing Dependency, MD）是**分析器正常工作后得出的结论**，
「工具没跑完」是**分析器根本没得出任何结论**。二者在契约里必须走不同的字段：

| | 检出 MD | 工具执行失败 |
| --- | --- | --- |
| 分析器是否跑完 | 跑完了 | 没跑完（崩溃/超时/环境不可用） |
| 有没有结论 | 有，且结论就是「存在缺失声明」 | 没有任何结论 |
| `status` | `SUCCEEDED`（第 8 页：结果可用，可能报告 MD/RD） | `FAILED` 或 `TIMED_OUT` |
| 写在哪 | `output.findings[]`，`type: "MISSING"` | `job.error`，`code: ENV_3xxx / EXEC_4xxx / ANALYSIS_5xxx` |
| `output` | 非空，携带 findings 与 artifacts | **必须为空对象 `{}`** |
| `error` | **必须为 `null`** | 必须是含 `code` + `message` 的对象 |
| 下游该怎么办 | MDFixer (B3) 消费 MD 并尝试修复 | 调用方按 `retryable` 决定重试或换环境，**不得**送进 MDFixer |

一句话：**MD 是产品的输出，不是产品的故障。** 把 MD 写成 `FAILED` 会让 B3 永远收不到
待修复的报告，也会让「零缺陷」和「没检出」在数据上无法区分。

这条规则由 `task.schema.json` 的 `status_matrix` 强制，并由
`samples/invalid/md-reported-as-error.json` 与
`tests/test_validate.py::TestSlide25Check04MdIsNotExecutionFailure` 校验。
对照正例见 `samples/full-check.job-succeeded.json`：状态 `SUCCEEDED`、`error: null`、
`output.findings` 里带一条 `MISSING`。

## 二、通道 A：系统执行错误 → `job.error`

仅在 `status` 为 `FAILED` 或 `TIMED_OUT` 时出现，其他状态必须 `error: null`。

```json
"error": {
  "code": "ENV_3002",
  "message": "镜像构建失败：registry.pair09.local/draft:broken-tag 无法拉取",
  "retryable": true,
  "detail": "可选的自由文本补充，不承载机器可判断的语义"
}
```

`code` 与 `message` 必填；`retryable` 与 `detail` 可选。
`error` 对象 `additionalProperties: false` —— 它是 A1 冻结的公共形状，
机器判断只允许依赖 `code`，不得解析 `message` 文本。

### 错误码注册表

命名空间按故障发生的阶段分段。**标注「第 9 页」的是课程给定码，不得改动语义；
标注「A09/B09 扩展」的是本配对组新增，需 B1 复核后生效。**

| 码 | 含义 | `retryable` 建议 | 来源 |
| --- | --- | --- | --- |
| `VALIDATION_2001` | 请求体不符合 `task.schema.json`（缺必填、类型错误、枚举越界） | false | A09/B09 扩展 |
| `VALIDATION_2002` | 幂等键重复但请求体与首次不一致 | false | A09/B09 扩展 |
| `ENV_3002` | 镜像构建失败 | true | **第 9 页** |
| `ENV_3003` | 基线不可读，或 `baseline.commit` / `configuration_id` 与请求不匹配 | false | A09/B09 扩展 |
| `EXEC_4001` | 工作进程崩溃或被外部终止 | true | A09/B09 扩展 |
| `EXEC_4002` | 任务超时 | false | **第 9 页** |
| `ANALYSIS_5001` | 分析器失败 | false | **第 9 页** |
| `ANALYSIS_5002` | 分析完成但产物写出失败 | true | A09/B09 扩展 |

命名空间规律：`VALIDATION_2xxx` 请求期 ｜ `ENV_3xxx` 环境与基线 ｜
`EXEC_4xxx` 执行 ｜ `ANALYSIS_5xxx` 分析器。

`task.schema.json` 用**正则**而非枚举约束 `error.code`：

```
^(VALIDATION_2[0-9]{3}|ENV_3[0-9]{3}|EXEC_4[0-9]{3}|ANALYSIS_5[0-9]{3})$
```

理由见 ADR-004：若写成封闭枚举，任何一组新增错误码都构成第 26 页所说的
「状态枚举改变」类破坏性变更，六个人会被锁死在一次同步升级里。用命名空间正则 +
本页注册表，各组可在自己的段内增码而不动 schema，同时自由文本码（如 `BOOM`）仍被拒绝。

### 新增错误码的流程

1. 在本页注册表加一行，写明含义、`retryable` 建议、来源。
2. 若需要新命名空间（如 `REPAIR_6xxx`），必须改 `task.schema.json` 的 `error_code` 正则，
   属破坏性变更，走 ADR + `schema_version` 升级（第 26 页）。
3. 在 `samples/invalid/` 或 `tests/` 补一条断言，然后 `make check`。

## 三、通道 B：正常分析发现 → `output.findings[]` 与 `ERROR_REPORT`

`status` 为 `SUCCEEDED` 时出现。两种 `type`（第 9 页）：

| type | 含义 | 谁消费 |
| --- | --- | --- |
| `MISSING` (MD) | 实际需要，但声明缺失 | MDFixer (B3) —— **只消费 MD**（第 12、23 页） |
| `REDUNDANT` (RD) | 声明了，但本构建配置未使用 | 人工评审；B3 不处理 |

finding 的完整形状（第 10 页原文五字段 + 「完整报告还要有位置和证据」）：

```json
{
  "id": "md-9f8e7d6c-001",
  "type": "MISSING",
  "target": "main.o",
  "dependency": "config.h",
  "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
  "detector": "INSTRUCTOR_ORACLE",
  "location": { "path": "src/Makefile", "line": 12, "column": null },
  "evidence": [
    { "kind": "INSTRUCTOR_SAMPLE", "detail": "教师提供的人工样本", "artifact_uri": null },
    { "kind": "FILE_ACCESS", "detail": "编译 main.c 时打开 config.h 失败", "artifact_uri": "artifact://pair09/job-full09/proc-trace-main-o.log" }
  ],
  "message": "main.o 实际需要 config.h，但 Makefile 第 12 行未声明该依赖"
}
```

字段约定：

- `commit` 必须是**完整 40 位 SHA**（第 10、21、22 页反复强调），短 SHA 一律拒绝。
  这是第 5 页「报告属于当前源码版本」的机器可验证形式。
- `detector` 标注发现来源。取值 `INSTRUCTOR_ORACLE` 表示**人工样本**
  （第 10 页：「人工样本标明人工来源」）；工具产生的发现用工具自己的标识
  （如 `BUILDCHECKER_DYNAMIC`、`ECHECKER_DIFF`）。
- `location` 给出可定位到行的位置，`evidence` 是非空数组，
  `kind` 取 `PROCESS_TRACE` / `FILE_ACCESS` / `DECLARATION` / `INSTRUCTOR_SAMPLE`
  （对应第 21 页「进程、文件和声明位置证据」）。
  缺位置或证据的 finding 会被校验器拒绝 —— 因为 B3 拿它没法改文件，
  这正是第 5 页「修复交接：接收方检查目标、缺失文件、位置与证据」的要求。
- finding 内部**允许**追加字段（第 26 页的可兼容变化），服务负责人可各自扩展；
  但上列九个字段是跨组共享的，删改属破坏性变更。

完整报告以 `type: "ERROR_REPORT"` 的 artifact 交接（第 9、24 页），
`output.findings` 内联同一批记录供快速阅读。二者不一致时以 artifact 为准。

## 四、边界情形

| 情形 | status | error | output |
| --- | --- | --- | --- |
| 检出 MD/RD | `SUCCEEDED` | `null` | 有 findings |
| 零发现（干净项目） | `SUCCEEDED` | `null` | `findings: []`，`counts` 全 0 |
| 镜像拉不下来 | `FAILED` | `ENV_3002` | `{}` |
| 分析器崩溃 | `FAILED` | `ANALYSIS_5001` | `{}` |
| 超时 | `TIMED_OUT` | `EXEC_4002` | `{}` |
| 基线 SHA 与 `base_commit` 不符 | `FAILED` | `ENV_3003` | `{}` |
| 请求缺 `baseline` 字段 | **不产生 Job** | HTTP 400 + `VALIDATION_2001` | —— |
| 人工取消 | `CANCELLED` | `null` | `{}` |

倒数第二行是 ADR-005 的决定：结构性违规在创建时同步拒绝，不占用 `job.error`；
语义性违规（字段都在但值对不上）只能在执行期发现，落为 `FAILED` + `job.error`。
两者的样例分别是 `samples/invalid/missing-baseline.json` 与
`samples/job.baseline-mismatch-failed.json`。

## 五、待 B1 复核

- [ ] `VALIDATION_2xxx` 命名空间是否接受，或改用 HTTP 4xx 状态码而不进注册表
- [ ] `ENV_3003`、`EXEC_4001`、`ANALYSIS_5002`、`VALIDATION_2002` 四个扩展码
- [ ] `retryable` 的建议值是否与 B 侧的重试策略一致
- [ ] 错误码注册表的维护权归 A1 还是 B1
