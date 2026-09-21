# 端点约定

小组 A09 / 配对组 B09 ｜ 契约版本 1.0.0
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

## 五、待 B1 确认

- [ ] 五个端点路径是否沿用第 27 页参考命名
- [ ] `GET /v1/artifacts/{artifact_id}` 是否作为产物读取接口（A1 提案）
- [ ] 认证、分页、批量查询是否需要（E2 不涉及，E3 可能需要）
- [ ] 端点与 `job_type` 不一致时的错误码归属
