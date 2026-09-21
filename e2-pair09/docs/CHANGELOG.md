# 契约变更记录

本文件记录 `interfaces/` 下契约的每一次变更。版本规则见 `versioning.md`。

## [Unreleased]

### 待处理

1. `finding.detector` 目前是自由字符串，取值集合需要 A2 与 A3 确认后收敛
2. `ERROR_REPORT` 产物的文件结构尚未定稿，需要 A2 提供一份完整报告样例
3. `artifact.uri` 的下载接口 `GET /v1/artifacts/{artifact_id}` 是备用方案，需要确认 E3 是否真的需要
4. ADR-003、ADR-004、ADR-005 尚未认领

## [0.1.0] - 2026-09-20

### 新增

1. `interfaces/task.schema.json` 初稿。一份 Job 表达 DRAFT、FULL_CHECK、INCREMENTAL_CHECK、REPAIR 四类任务，公共字段为 `schema_version`、`job_id`、`trace_id`、`job_type`、`status`、`execution`、`input`、`output`、`error`
2. `interfaces/endpoints.md`。四个创建端点与一个查询端点，采用第 27 页的参考命名，未做修改
3. `interfaces/states-errors.md`。六个状态、迁移规则、三个系统错误码，以及检测发现与系统错误的分离规则
4. `interfaces/samples/` 下三个有效样例与两个反例
5. `adr/` 目录、四段式模板、ADR-001 与 ADR-002
6. `versioning.md` 与消费者清单

### 本组决定（课件允许协商、但必须记录的部分）

这些内容课件没有规定，由本组确定。列在这里便于对方组核对。

| 决定 | 内容 | 记录位置 |
|---|---|---|
| 端点命名 | 完全采用第 27 页参考命名 | `interfaces/endpoints.md` 第 2 节 |
| 错误码命名规则 | 领域前缀加四位数字，3xxx 环境、4xxx 执行、5xxx 分析 | `interfaces/states-errors.md` 第 4 节 |
| 严格模式 | 所有对象使用 `additionalProperties: false` | ADR-002 |
| 小报告内联 | 少量 findings 可内联在 `output.findings`，完整报告以 `ERROR_REPORT` 产物为准 | `interfaces/states-errors.md` 第 5 节 |
| 校验错误与执行错误的分工 | 契约不合法返回 400 且不创建任务，执行失败返回 200 并在 `job.error` 说明 | `interfaces/endpoints.md` 第 5 节 |
| 产物读取方式 | 引用解析与下载接口两条路径，验收时要由对方真实读取一次 | `interfaces/endpoints.md` 第 4 节 |

### 变更影响

初版，尚无消费者受影响。
