# 契约变更记录

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 本文件由 B1（李秉轩）维护

记录 `docs/interfaces/` 下公共契约的每一次变更。版本规则与递增依据见 `versioning.md`。
第 26 页要求「改字段之前先考虑消费者」，因此每条变更都必须写清影响面。

## [Unreleased]

### 待处理

| # | 事项 | 需要谁给结论 | 影响 |
|---|---|---|---|
| 1 | `artifact://pair09/{job_id}/{name}` 用完整 `job_id` 是对第 24 页样例的有意偏离 | 教师确认 | 若被驳回，`artifact_uri` 模式、样例与校验器三处要同步改 |
| 2 | 错误码注册表 `VALIDATION_2xxx` 命名空间为 A09/B09 自行扩展，非第 9 页给定 | 教师或助教确认 | 影响创建期拒绝的表示方式 |
| 3 | `execution` 字段在第 19 页被列为公共字段但全篇未定义，现定义由 A1 给出 | A2、A3、B2、B3 确认可用 | 若服务侧需要更多计时字段，属可兼容扩展 |
| 4 | `input` / `output` 内部字段由四个服务负责人最终确认 | A2、A3、B2、B3 | 见 Issue #1 第三节 |
| 5 | 产物读取接口在 E2 不部署，E3 是否需要落地实现 | 全组 | 见 `interfaces/endpoints.md` 第四节 |

## [1.0.0] - 2026-09-21

契约首次冻结。由 A1（谢浩天）建立，B1（李秉轩）复核后定稿。

### 新增

| 文件 | 内容 |
|---|---|
| `interfaces/task.schema.json` | 统一任务模型，三类顶层对象 `create_request` / `job` / `artifact_record`，34 个 `$defs` |
| `interfaces/errors.md` | 错误与检测发现的双通道约定，含错误码注册表 |
| `interfaces/endpoints.md` | 四个创建端点、一个查询端点、一个产物读取端点 |
| `interfaces/samples/**` | 16 个正例、18 个负例 |
| `tools/validate.py`、`tests/test_validate.py` | 零依赖校验器与运行期断言 |
| `adr/ADR-001..006` | 六份架构决策记录 |
| `BACKLOG.md`、`VALIDATION.md`、`AI_USAGE.md`、`CONTRIBUTIONS.md` | 第 12、14、15 页要求的流程文档 |

### B1 复核结论

逐条回应 Issue #1 第二节的七项待确认。结论已落实到对应文件。

| # | 事项 | B1 结论 | 落点 |
|---|---|---|---|
| 1 | 产物读取端点 | 接受 `GET /v1/artifacts/{artifact_id}`，用 `artifact_id` 寻址、用 `sha256` 校验本体 | `interfaces/endpoints.md` 第四节 |
| 2 | `VALIDATION_2xxx` 命名空间 | 接受，但限定为创建期同步拒绝，只出现在 HTTP 4xx 响应体，不写入 `job.error` | `interfaces/errors.md` 第二节 |
| 3 | 信封严格 / 载荷可扩展 | 接受这条分界，并写进版本兼容规则 | `versioning.md` 第三节 |
| 4 | `execution` 定义 | 接受 `{attempt, queued_at, started_at, finished_at, duration_ms?, worker_id?}` | `interfaces/task.schema.json` |
| 5 | artifact URI 用完整 `job_id` | 接受，但标记为对课件样例的有意偏离，需教师确认 | `interfaces/endpoints.md` 第四节 |
| 6 | 五个端点路径 | 沿用第 27 页参考命名，不做改动 | `interfaces/endpoints.md` 第一节 |
| 7 | 错误码注册表维护权 | 归 B1。错误码变更属版本与兼容性范畴，走 `versioning.md` 第五节的流程 | `interfaces/errors.md` |

### 本组自行决定的部分

课件未规定、由 A09/B09 确定的内容集中列在这里，便于对方组与助教核对。

| 决定 | 内容 | 记录位置 |
|---|---|---|
| 端点命名 | 沿用第 27 页参考命名，端点名等于 `job_type` 的 kebab-case 加 `-jobs` | `interfaces/endpoints.md` 第一节 |
| 错误码命名空间 | `VALIDATION_2xxx` 请求期、`ENV_3xxx` 环境与基线、`EXEC_4xxx` 执行、`ANALYSIS_5xxx` 分析器 | `interfaces/errors.md` 第二节 |
| 严格程度分界 | 信封严格、载荷可扩展 | `adr/ADR-004`、`versioning.md` 第三节 |
| 创建期拒绝与运行期失败 | 结构性违规返回 HTTP 400 且不产生 Job，语义性违规落 `FAILED` | `adr/ADR-005` |
| 产物寻址 | 用 `artifact_id` 而非 URI 字符串 | `interfaces/endpoints.md` 第四节 |
| 契约版本号形式 | 三段式 `MAJOR.MINOR.PATCH`，两段式被拒 | `versioning.md` 第一节 |
| 校验器依赖 | 零第三方依赖，从 schema 读常量而非硬编码 | `adr/ADR-006` |

### 变更影响

初版，尚无既有消费者受影响。E3 若修改本版任何字段，按 `versioning.md` 第四节的流程处理。
