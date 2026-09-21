# ADR-001：采用异步 Job 模型与单一公共信封

- 状态：**已接受**（A1 谢浩天，A09）；待 B1 复核
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 6、7、8、19 页；ADR-004、ADR-006

## Context

四个服务（DRAFT / BuildChecker / EChecker / MDFixer）都要做耗时操作：
生成 Dockerfile 要多轮迭代构建，全量检测要跑完整 clean build，修复要构建+测试+重检。
第 6 页给出的判断是「耗时任务先受理，再后台执行」，第 13 页把这条写成了 ADR 模板：
耗时操作可能超过 HTTP 生命周期。

同时第 19 页要求「一份 Job 表达四类耗时任务」，公共字段固定为九个：
`schema_version`、`job_id`、`trace_id`、`job_type`、`status`、`execution`、
`input`、`output`、`error`。

A09 有六个人、四个服务，如果每组各写一份 schema，字段名与必填性必然分叉
（这是本次作业最典型的失败模式）。公共部分必须只有一份。

另有两处第 19 页没说清的细节需要 A1 定：

1. 第 7 页写明「`job_id` 由服务端产生」，但第 19 页把 `job_id` 列为公共字段。
   那么创建请求里到底有没有 `job_id`？
2. `execution` 被列为公共字段，但全套 27 页没有任何一页解释它是什么。

## Decision

### 1. 异步 Job：POST 返回 202，GET 查询状态

创建任务立即返回 `HTTP 202` 与一个 `status: "QUEUED"` 的 Job 文档，
调用方保存 `job_id` 后轮询 `GET /v1/jobs/{job_id}` 直到终态。
状态机为 `QUEUED → RUNNING → {SUCCEEDED | FAILED | TIMED_OUT | CANCELLED}`（第 8 页）。

### 2. 用 `kind` 判别式区分三种文档，而不是把请求和响应塞进同一个形状

一份 `task.schema.json`，顶层 `oneOf` 三个互斥分支，由必填的 `kind` 字段判别：

| `kind` | 用途 | 有无 `job_id` / `status` |
| --- | --- | --- |
| `create_request` | 客户端 POST 的请求体 | **无**（服务端产生） |
| `job` | 受理响应与查询响应，即「一张可查询的任务单」（第 6 页） | 有 |
| `artifact_record` | 第 24 页的产物记录，可独立交接 | 无 |

`create_request` 额外必填 `idempotency_key`（第 7 页：「创建请求携带输入与幂等键」），
且 `additionalProperties: false`，所以客户端塞 `job_id` 会被直接拒绝。

### 3. `http_status` 只在受理响应里出现

`job` 有一个可选字段 `http_status`，`status_matrix` 规定它**只能**与 `QUEUED`
共存且值必须是 202。这样「受理响应」和「查询一个仍在排队的任务」两种文档
能用同一个形状表达而不混淆——查询响应不带 `http_status`。

### 4. `execution` 定义为计时与重试元数据

第 19 页列了 `execution` 但没解释。A1 定义它为：

```json
{
  "attempt": 1,
  "queued_at": "2026-09-20T09:20:00Z",
  "started_at": "2026-09-20T09:20:03Z",
  "finished_at": null,
  "duration_ms": null,
  "worker_id": "a09-buildchecker-worker-1"
}
```

`attempt` / `queued_at` / `started_at` / `finished_at` 必填（未开始时后三者为 `null`），
`duration_ms` / `worker_id` 可选。理由：第 6 页要求「另一组能查询进度」并
「不必把大日志塞进每个响应」，那么进度就得由轻量的计时字段承载；
`EXEC_4002`（超时）与 `retryable` 的判断也需要 `attempt` 和时间戳作为依据。

**这是 A1 的定义，不是课程给定内容**，B1 与四个服务负责人都可以提出异议。

## Alternatives

### 同步等待（POST 直到任务完成才返回）

实现最简单，无需任务存储和查询端点。但客户端与执行完全耦合：
一次全量检测可能跑十几分钟，HTTP 连接、网关超时、浏览器刷新都会打断它，
且中断后无法恢复也无法知道跑到哪了。第 13 页已明确指出这个代价。**否决。**

### 请求与响应共用一个 schema，`job_id` 设为可选

少一个 `kind` 分支。但「可选」意味着客户端也能填 `job_id`，
服务端产生的标识就可能被客户端覆盖，幂等键语义随之崩坏；
而且校验器无法区分「受理响应」和「查询响应」，202 规则也就无从强制。
第 7 页特意点出「`job_id` 由服务端产生」，说明这里需要结构性区分。**否决。**

### 每个服务各写一份 schema，公共字段靠约定对齐

短期看各组自由度最高。但第 12 页把「统一任务模型」的责任方写成「A/B 共同」、
产物写成单一的 `task.schema.json`，验收条件是「四类对象可表达」——
课程要的就是一份。六份 schema 在联调时必然对不上，全组返工。**否决。**

### `execution` 留空不定，交给各服务自己填

最省事，也最危险：四个服务会给出四种互不兼容的执行元数据，
而 `trace_id` 串联平台流程（第 6 页）依赖统一的计时口径。**否决。**

## Consequences

**得到的：**

- 四类 job 由同一份 schema 表达，`tools/validate.py` 一次校验四对请求/响应
  （第 25 页检查 01，也是 A1 的验收条件）。
- 「受理响应」与「查询响应」可区分，202 语义可被机器校验。
- `execution` 有了统一口径，`trace_id` 能真正串起跨服务流程。

**付出的：**

- 需要任务存储与查询能力（第 13 页已预见）。E2 阶段**不实现**——第 7 页明确
  「E2 先定义，不要求部署 API」——但契约已经把它需要的字段固定下来了。
- 调用方必须实现轮询与终态判断，比同步调用复杂。
- 三种 `kind` 意味着样例数量翻倍：每类 job 至少要一对请求/响应。
  本仓库已备齐 16 个正例 + 18 个负例。
- `execution` 是 A1 自行定义的，存在被 B1 或教师否掉的风险；若推翻，
  属第 26 页的破坏性变更，需升 `schema_version` 并同步四组样例。

**验证：** `tests/test_validate.py::TestSlide25Check01FourJobTypes` 断言四类
请求/响应都能通过校验，且响应回显请求的 `input`；
`TestEnvelopeIsFrozen` 断言 `create_request` 带 `job_id` 会被拒。
