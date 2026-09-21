# ADR-001 长耗时任务采用异步 Job 与 202 受理

| 项 | 值 |
|---|---|
| 状态 | Accepted |
| 日期 | 2026-09-20 |
| 提议人 | B1 |
| 评审人 | 待 A1、A2、A3、B2、B3 确认 |
| 关联文件 | `interfaces/endpoints.md`、`interfaces/task.schema.json`、`interfaces/states-errors.md` |

## Context

四类任务都是长耗时操作。生成 Dockerfile 需要反复构建并验证，全量检测需要跑 clean build 并采集依赖，增量检测需要比对历史图，修复需要改 Makefile 后重新构建和重检。这些操作的耗时超过一次 HTTP 请求能可靠持有的时间。

同时有三条课程约束：

1. E2 只定义契约，不要求部署 API
2. 另一组必须能查询进度并取结果，因为下游服务要消费上游产物
3. 大日志不能塞进每个响应

## Decision

采用异步 Job 模型。创建端点接受请求后立即返回 HTTP 202，响应体只给 `job_id` 与 `status: "QUEUED"`。执行结果由查询端点 `GET /v1/jobs/{job_id}` 提供，任务状态按 `QUEUED`、`RUNNING`、终态推进。

四类任务共用同一份 Job 模型，差异只在 `input`。公共字段为 `schema_version`、`job_id`、`trace_id`、`job_type`、`status`、`execution`、`input`、`output`、`error`。

产物通过 `artifact.uri` 引用交接，不内嵌到响应里。

## Alternatives

| 替代方案 | 未采用的理由 |
|---|---|
| 同步等待，一次请求返回全部结果 | 实现简单，但客户端与执行过程强耦合。构建可能迭代多次，请求会超时或长时间占用连接，也无法中途查询进度 |
| 无状态的一次性 HTTP 接口，由调用方轮询重试 | 无法表达"任务已受理但未执行"，重试与重复执行难以区分，幂等性无处安放 |
| 服务端主动回调下游地址 | E2 不部署服务，回调地址无法约定。回调还需要下游暴露端点，超出本学期范围 |

## Consequences

好处：

1. 执行与查询解耦，上游可以先提交任务再处理别的事
2. 任务状态可查询，便于定位卡在哪一环
3. 大产物走引用，响应体保持小

代价：

1. 必须引入任务存储与状态查询，比同步实现多一层
2. 必须定义状态机与终态语义，其中"检出 MD 仍然算 SUCCEEDED"容易理解错
3. 客户端需要处理"受理成功但执行失败"与"请求本身不合法"两种不同失败

需要新增的工作：

1. 状态机与错误码文档，见 `interfaces/states-errors.md`
2. 创建请求的幂等键约定，避免重复提交产生两个任务
3. 产物引用的解析方式，需要双方各自验证一次真的能读到

## 验证方式

用 `interfaces/samples/` 下的样例验证：

1. `samples/job-full-check-succeeded.example.json` 证明有 MD 发现时状态仍为 `SUCCEEDED`
2. `samples/job-timed-out.example.json` 证明执行失败时原因写在 `job.error`
3. `samples/invalid/` 下两个反例证明不合法的创建请求在入口被拒绝，不会产生任务
