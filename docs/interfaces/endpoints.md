# 端点约定

小组 A09 / 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0
**负责人：B1** ｜ 本页由 A1 依第 7、27 页起草，供 B1 复核后定稿
**E2 只定义契约，不要求部署 API（第 7 页）**——本页描述的是协议形状，不是已运行的服务。

## 一、四个创建端点 + 一个查询端点（第 27 页）

| 操作 | 服务 | 负责组 | 参考端点 | `job_type` |
| --- | --- | --- | --- | --- |
| 生成构建环境 | DRAFT | B2 | `POST /v1/dockerfile-jobs` | `DRAFT` |
| 全量检测 | BuildChecker | A2 | `POST /v1/full-check-jobs` | `FULL_CHECK` |
| 增量检测 | EChecker | A3 | `POST /v1/incremental-check-jobs` | `INCREMENTAL_CHECK` |
| 修复缺失依赖 | MDFixer | B3 | `POST /v1/repair-jobs` | `REPAIR` |
| 查询任务 | 公共 | A1 / B1 | `GET /v1/jobs/{job_id}` | —— |

第 27 页注明「端点命名是参考，配对组可协商修改」。A09/B09 沿用参考命名，
理由是下游只需记一套规则：**端点名 = `job_type` 的 kebab-case + `-jobs`**。

### 冗余设计说明

四个创建端点已经隐含了 `job_type`，但请求体里仍**必须**再写一次 `job_type`。
这不是冗余失误：Job 文档会被单独存储、转发、离线校验（`tools/validate.py` 就是
脱离 HTTP 直接校验 JSON 文件的），离开端点上下文后 `job_type` 必须自解释。
校验器会检查二者一致；不一致时以请求体为准并返回 `VALIDATION_2001`。

## 二、创建任务的交互（第 7 页）

```http
POST /v1/full-check-jobs
Content-Type: application/json

{
  "kind": "create_request",
  "schema_version": "1.0.0",
  "trace_id": "trace-a09-e2-001",
  "job_type": "FULL_CHECK",
  "idempotency_key": "a09-full-9f8e7d6c-cc-MODE0",
  "input": { ... }
}
```

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "kind": "job",
  "schema_version": "1.0.0",
  "job_id": "job-full09",
  "status": "QUEUED",
  "http_status": 202,
  ...
}
```

三条硬约定：

1. **返回 202，不返回 200。** 202 表示「已受理、尚未完成」。返回 200 会让调用方
   误以为拿到了最终结果。见 `samples/invalid/queued-http-200.json`。
2. **`job_id` 由服务端产生。** `create_request` 里出现 `job_id` 或 `status` 一律拒绝。
   见 `samples/invalid/create-request-with-job-id.json`。
3. **`idempotency_key` 必填。** 网络重试时用同一个键重放，服务端必须返回同一个
   `job_id`，不得重复起任务。键相同但请求体不同 → `VALIDATION_2002`。

请求体完整样例：`samples/draft.request.json`、`samples/full-check.request.json`、
`samples/incremental-check.request.json`、`samples/repair.request.json`。
受理响应样例：`samples/job.accepted-queued.json`。

FULL_CHECK 的服务专有输出、实际图/声明图和 ERROR_REPORT 本体见
`buildchecker-contract.md`；对应 schema 定义位于 `task.schema.json`。

## 三、查询任务

```http
GET /v1/jobs/job-full09
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{ "kind": "job", "job_id": "job-full09", "status": "SUCCEEDED", ... }
```

- 查询返回**完整 Job 文档**，含 `status`、`execution`、`output`、`error`。
- 查询响应里**不带** `http_status` 字段——该字段只用于表达创建时的 202 受理语义。
  schema 的 `status_matrix` 强制：`http_status` 只允许出现在 `QUEUED` 文档中。
- 第 6 页：「不必把大日志塞进每个响应」。查询响应只给 `output.artifacts[]` 里的
  **引用**（URI + sha256 + media_type），大文件本体走第四节的产物接口。
- 轮询建议：指数退避，起始 2s，上限 30s；终态为
  `SUCCEEDED / FAILED / TIMED_OUT / CANCELLED`，到达终态后停止轮询。

### 状态迁移（B1 补充）

第 8 页给出六个状态，`status_matrix` 约束了每个状态下哪些字段合法，但两者都没有约定
状态之间怎么走。下表补齐迁移规则，供四个服务的执行器对齐。B1 于 2026-09-21 补入。

| 起始状态 | 事件 | 目标状态 | 必须写入 |
| --- | --- | --- | --- |
| `QUEUED` | 执行器领取任务 | `RUNNING` | `execution.started_at` |
| `QUEUED` | 队列中取消 | `CANCELLED` | —— |
| `QUEUED` | 受理后环境准备失败 | `FAILED` | `error.code = ENV_3002` |
| `RUNNING` | 分析正常结束 | `SUCCEEDED` | `output`，`error: null` |
| `RUNNING` | 分析器自身崩溃 | `FAILED` | `error.code = ANALYSIS_5001` 或 `ANALYSIS_5002` |
| `RUNNING` | 超过时间限制 | `TIMED_OUT` | `error.code = EXEC_4002` |
| `RUNNING` | 执行中取消 | `CANCELLED` | —— |

三条硬规则：

1. **终态不可再迁移。** 同一 `job_id` 的状态只沿上表前进，不回退，也不从终态回到非终态。
2. **`RUNNING` 不可跳过。** 任务是长耗时操作，从 `QUEUED` 直达终态意味着执行器没有记录开始时间，
   `execution.started_at` 会缺失，而它是判断超时归属的凭据。
3. **`retryable` 为 `true` 时重试产生新的 `attempt`，不产生新 `job_id`。** 见
   `task.schema.json` 的 `execution.attempt`。客户端重试则用同一个 `idempotency_key` 重放创建请求。

状态流转样例：`samples/job.accepted-queued.json` → `samples/job.running.json` →
`samples/full-check.job-succeeded.json`；失败路径见 `samples/job.failed.json`、
`samples/job.timed-out.json`、`samples/job.analysis-failed.json`、
`samples/job.baseline-mismatch-failed.json`；取消见 `samples/job.cancelled.json`。

## 四、产物读取（第 24 页，翻车点 #3）

**只给 `artifact://` URI 而不给读取方式，联调时两边都读不出来。** 因此本节约定解析器。

URI 文法：

```
artifact://pair09/{job_id}/{name}
         └─┬──┘ └───┬───┘ └─┬─┘
      配对组命名空间  生产任务   文件名
```

`pair09` = A09 与 B09 的共享命名空间（第 15 页要求接口文件写明配对组编号）。
写成其他命名空间会被校验器拒绝，见 `samples/invalid/foreign-artifact-uri.json`。

解析方式（A1 提案，**待 B1 复核**）：

```http
GET /v1/artifacts/{artifact_id}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json          # 取自 artifact 记录的 media_type
Content-Length: 6712
ETag: "4e5f6071...a1b2c3d"              # 取自 artifact 记录的 sha256

<文件本体>
```

约定：

| 项 | 约定 |
| --- | --- |
| 寻址键 | `artifact_id`（全局唯一），不是 URI 字符串——URI 只是给人看的定位提示 |
| 响应类型 | 必须等于 artifact 记录里的 `media_type` |
| 完整性 | 下载方**必须**用记录里的 `sha256` 校验本体；不符即视为传输损坏，重新下载 |
| 不存在 | `404`，响应体为 `{"error": {"code": "VALIDATION_2001", ...}}` |
| 鉴权 | E2 不要求；若 E3/E12 需要，由 B1 在此追加 |
| 保留期 | 至少覆盖本轮 E2 + E3；`producer_job_id` 与 `commit` 保证可追溯 |

第 24 页要求「E12 必须证明另一组能读取文件」。本节的 `GET /v1/artifacts/{artifact_id}`
就是为此预留的接口；A09/B09 在 E2 阶段**不部署**它，但契约已冻结，
E12 时任何一方实现都能对接。

产物记录样例：`samples/artifact.error-report.json`；
内联在 `output.artifacts[]` 里的形态见 `samples/full-check.job-succeeded.json`。

## 五、B1 定稿结论

本页由 A1 依第 7、27 页起草，B1 于 2026-09-21 复核定稿。逐条回应起草时留下的四个待确认项。

| # | 待确认项 | B1 结论 | 理由 |
| --- | --- | --- | --- |
| 1 | 五个端点路径是否沿用第 27 页参考命名 | **沿用，不做改动** | 第 27 页注明命名可协商。沿用的收益是下游只需记一条规则：端点名等于 `job_type` 的 kebab-case 加 `-jobs`。改名会让四份样例、校验器与既有文档同时返工 |
| 2 | `GET /v1/artifacts/{artifact_id}` 是否作为产物读取接口 | **接受** | 第 24 页要求「约定解析器或实际下载接口」二选一。用 `artifact_id` 寻址比用 URI 字符串稳定，改动 URI 文法不会破坏已发出的下载链接；配合 `sha256` 校验满足第 24 页「需要核验完整性时使用」 |
| 3 | 认证、分页、批量查询是否需要 | **E2 不做，E3 再定** | 第 7 页明确 E2 不部署 API。这三项属于部署期问题，现在约定会凭空增加四组的实现负担。E3 需要时按 `../versioning.md` 第四节走 MINOR 变更补入 |
| 4 | 端点与 `job_type` 不一致时的错误码归属 | **归 `VALIDATION_2001`** | 端点与请求体不一致属于请求结构性违规，按 ADR-005 走创建期同步拒绝，返回 HTTP 400 且不产生 Job，因此不属于 `job.error` 的范畴。`VALIDATION_2xxx` 的适用范围见 `errors.md` 第二节 |

### 一条需要教师确认的有意偏离

第 24 页的样例是 `artifact://pair01/full01/actual.json`，其中 `full01` 不是合法 `job_id`
（本契约的 `job_id` 形如 `job-full09`）。若沿用课件写法，URI 与 `job_id` 无法用同一条正则校验，
`artifact_record.producer_job_id` 与 URI 也对不上号。

本组改为 `artifact://pair09/job-full09/actual.json`，属**对课件样例的有意偏离**，
已记入 `../CHANGELOG.md` 的待处理表，请教师在课上确认。若被驳回，需要同步修改
`task.schema.json` 的 `artifact_uri` 模式、相关样例与 `tools/validate.py`。

### 第 5 页的交接验收清单

第 5 页给出四个交接环节，右侧一列是接收方的检查项。这四行是三轮交换（第 16 页）时
双方面对面要过的内容，比「双方理解一致」这种说法可验证。

| 交接 | 发送方提供 | 接收方检查 | 对应端点 |
| --- | --- | --- | --- |
| 环境交接 | 仓库版本、镜像或构建方案 | 环境能用，构建命令明确 | `POST /v1/dockerfile-jobs` |
| 增量检测 | 旧提交的依赖图、配置与新提交 | 基线版本和配置匹配 | `POST /v1/incremental-check-jobs` |
| 修复交接 | 目标、缺失文件、位置与证据 | 报告属于当前源码版本 | `POST /v1/repair-jobs` |
| 验证交接 | Patch、日志、构建测试结果 | 修改生效，无效候选被拒绝 | 重新验证环节 |

四个创建端点的请求体字段与右侧检查项一一对应：接收方检查「基线版本和配置匹配」，
落到字段上就是 `input.baseline.commit` 必须等于 `input.base_commit`，
且 `input.baseline.configuration_id` 必须等于 `input.environment.configuration_id`。
