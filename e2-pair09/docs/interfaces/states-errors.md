# 状态机与错误码

| 项 | 值 |
|---|---|
| 负责人 | B1 |
| 版本 | v0.1（草案，待 A1 与 A3 联合评审） |
| 依据 | 《E2 需求与接口契约》第 8、9、10、25 页 |
| 单一事实来源 | 枚举取值定义在 `task.schema.json`，本文说明迁移规则与语义 |

## 1. 状态枚举

| 状态 | 含义 | 终态 |
|---|---|---|
| `QUEUED` | 任务已接受，等待执行 | 否 |
| `RUNNING` | 后台执行中 | 否 |
| `SUCCEEDED` | 任务正常跑完，结果可用。结果里可能带 MD 或 RD | 是 |
| `FAILED` | 任务因系统错误终止 | 是 |
| `TIMED_OUT` | 任务超过时间限制被终止 | 是 |
| `CANCELLED` | 任务被取消 | 是 |

## 2. 状态迁移

| 起始状态 | 事件 | 目标状态 | 附带字段 |
|---|---|---|---|
| `QUEUED` | 执行器领取任务 | `RUNNING` | `execution.started_at` |
| `QUEUED` | 队列中取消 | `CANCELLED` | 无 |
| `QUEUED` | 受理后环境准备失败 | `FAILED` | `error.code = ENV_3002` |
| `RUNNING` | 分析正常结束 | `SUCCEEDED` | `output` |
| `RUNNING` | 分析器自身崩溃 | `FAILED` | `error.code = ANALYSIS_5001` |
| `RUNNING` | 超过 `timeout_seconds` | `TIMED_OUT` | `error.code = EXEC_4002` |
| `RUNNING` | 执行中取消 | `CANCELLED` | 可保留部分产物 |

终态不可再迁移。同一 `job_id` 的状态只能沿上表前进，不回退。

## 3. 关键判定：检测发现不等于任务失败

这是第 9 页与第 25 页第 04 条的答案，也是本组最容易写错的一条。

| 场景 | `status` | `output` | `error` |
|---|---|---|---|
| 分析完成，未发现 MD/RD | `SUCCEEDED` | 图与空报告 | 无 |
| 分析完成，发现 MD 或 RD | `SUCCEEDED` | 图、MD/RD 报告、findings | 无 |
| 镜像构建失败，分析未开始 | `FAILED` | 可无 | `ENV_3002` |
| 任务超时 | `TIMED_OUT` | 可保留已产生日志 | `EXEC_4002` |
| 分析器进程崩溃 | `FAILED` | 可无 | `ANALYSIS_5001` |
| 被取消 | `CANCELLED` | 可保留部分产物 | 无 |

判断依据是"工具是否跑完"，不是"有没有检出问题"。跑完了并且有发现，仍然是 `SUCCEEDED`。

## 4. 系统错误码

| 码 | 触发条件 | 通常由哪个服务产生 | 写入位置 |
|---|---|---|---|
| `ENV_3002` | 镜像构建失败，无法获得可运行环境 | DRAFT | `job.error` |
| `EXEC_4002` | 任务超过时间限制被终止 | 四类服务的执行器 | `job.error` |
| `ANALYSIS_5001` | 分析器自身失败，未产出可用结果 | BuildChecker、EChecker | `job.error` |

本文档定义本组的错误码命名规则，作为后续扩展依据：领域前缀加四位数字。`ENV_` 表示环境与镜像，`EXEC_` 表示执行与调度，`ANALYSIS_` 表示分析。千位段沿用现有分布，3xxx 归环境类，4xxx 归执行类，5xxx 归分析类。

新增错误码属于可兼容变更，需要递增契约 MINOR 版本并双方同步。修改已有码的含义属于破坏性变更，见 `../versioning.md`。

## 5. 检测发现的字段与来源

检测发现写在 `ERROR_REPORT` 产物的 `findings` 数组里，小规模报告可以直接内联在 `output.findings`，这一点由本组决定并记录在 `../CHANGELOG.md`。

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | `MISSING` 表示实际需要但声明缺失，`REDUNDANT` 表示已声明但本配置未用 |
| `target` | 是 | 目标，例如 `main.o` |
| `dependency` | 是 | 依赖，例如 `config.h` |
| `commit` | 是 | 完整提交 SHA |
| `detector` | 是 | 发现来源。人工样本必须能识别为人工来源，例如 `INSTRUCTOR_ORACLE` |
| `location` | 完整报告必填 | 文件与行号 |
| `evidence` | 完整报告必填 | 证据说明 |

schema 层面只强制前五项，`location` 与 `evidence` 由评审把关，原因是人工样本在课堂阶段可能还没有稳定行号。

## 6. 扩展与变更

| 动作 | 兼容性 |
|---|---|
| 新增错误码 | 可兼容，MINOR 递增 |
| 新增可选字段 | 可兼容，MINOR 递增 |
| 新增状态枚举值 | 破坏性，MAJOR 递增，必须先与消费者确认 |
| 删除或改名状态值、错误码 | 破坏性，MAJOR 递增 |
| 修改已有码或状态的语义 | 破坏性，MAJOR 递增 |
| 取消 `additionalProperties: false` | 放宽校验，属于可兼容，但要说明原因 |
