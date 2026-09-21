# ADR-007：DRAFT 与 BuildChecker 的环境交接契约

- 状态：**Proposed**（B2 zrh，待 A2 确认）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：课件第 5、20、21、24 页；`task.schema.json` 的 `input_draft` / `output_draft`

## Context

DRAFT 负责从固定的仓库提交生成可构建环境，BuildChecker 需要复用这个环境
执行全量依赖检测。课件第 20 页要求 DRAFT 输入包含仓库、构建命令、最大迭代次数
与时间限制，输出包含 Dockerfile、镜像引用、每轮日志、修改及选择理由、
最终构建和验证结果。第 21 页又要求 BuildChecker 能使用镜像、`configuration_id`、
clean build 命令和项目根目录。

E2 只冻结契约，不部署 API。因此本决策的核心是让 B2 的 DRAFT 样例与 A1/B1
已冻结的公共信封一致，同时让 A2 能从结果中唯一确定要读取的环境。

## Decision

### 1. DRAFT 请求沿用公共创建信封

`draft-request.json` 使用 `kind=create_request`、`schema_version=1.0.0`、`trace_id`、
`job_type=DRAFT`、`idempotency_key` 和 `input`。`input` 固定为：

- `repository`：仓库 URL、40 位完整 commit SHA，可选 branch；
- `build`：`command`、`verify_command`、`clean_command` 和 `project_root`；
- `limits`：`max_iterations` 与 `timeout_seconds`。

`limits` 保留在 DRAFT 专有输入中，不再误放到 `execution`。`execution` 只用于 Job
的排队、执行和完成时间。

### 2. 成功结果显式给出成功判据

`draft-response.json` 使用 `status=SUCCEEDED`、`error=null`，并在 `output.build_result`
中必填：

- `build_succeeded`：clean build 是否成功；
- `verify_succeeded`：验证命令是否成功；
- `iterations`：实际迭代次数；
- `image_ref`：可供下游拉取的镜像引用；
- `success_criteria`：可供人和下游共同核对的成功判据。

本组将成功判据定为：`clean_command + command` 与 `verify_command` 的退出码均为 0，
且最后一轮没有新的环境修改。`build_succeeded=true` 但 `verify_succeeded=false`
不算 DRAFT 成功。

### 3. 环境与 `configuration_id` 必须一致

`output.environment` 作为 B2 在宽松载荷区的可兼容扩展，提供 `image_uri`、
`configuration_id`、`project_root` 与 `clean_command`。其中：

- `environment.image_uri` 必须与 `build_result.image_ref` 相同；
- Dockerfile 和每轮日志的 artifact 必须携带相同的 `configuration_id`；
- BuildChecker 创建请求应原样使用这个 `image_uri` 和 `configuration_id`，
  不得自行重新命名配置。

样例中 `configuration_id=draft-gcc13-release-9f8e7d6c`。它同时出现在环境描述和
所有 DRAFT artifact 记录中，供 A2 交叉检查。

### 4. 每轮日志与选择理由可追溯

`output.rounds[]` 的每项包含 `index`、`change`、`rationale` 和 `log_uri`。日志本体
不内联到 Job 响应，而是按 ADR-003 通过 `artifact://pair09/{job_id}/{name}` 引用，
并在 `output.artifacts[]` 中保留媒体类型、生产 Job、commit、配置及 `sha256`。

### 5. 失败结果不交接部分环境

`draft-failed-response.json` 使用 `status=FAILED`、`output={}` 和 `ENV_3002`。根据公共
状态矩阵，FAILED 必须有 `job.error`，且 `output` 必须是空对象。失败轮次产生的
临时镜像或日志不得被宣称为可供 BuildChecker 消费的有效产物。

## Alternatives

### 只交付 Dockerfile

BuildChecker 仍需要自行构建环境，不能直接复用 DRAFT 的构建结果，也无法与
`configuration_id` 保持一致。否决。

### 只交付镜像引用

下游可以运行环境，但缺少 Dockerfile、每轮修改理由和日志，无法解释环境如何
得到，也不符合第 20 页。否决。

### 失败时返回部分 `output`

看似便于调试，但下游无法判断这些产物是否可用，且直接违反已冻结的公共
状态矩阵。调试信息应放在 `error.detail` 或工作器侧日志中。否决。

### 另起一套 DRAFT 顶层信封

这会与 `task.schema.json` 中已冻结的 `create_request` / `job` 重复，并导致三份
样例无法通过公共校验器。否决。

## Consequences

- A2 可以从一份成功 Job 中同时获得镜像、`configuration_id`、项目根目录和
  clean build 命令，并用 artifact 记录核对来源。
- `build_result` 把“进程跑完”与“构建且验证成功”分开，避免将半成品交给下游。
- 每轮修改均有理由和日志 URI，可以审查 DRAFT 是否引入不必要的环境变更。
- `output.environment` 是载荷区的可兼容扩展，当前校验器只保证公共必填字段；
  `image_uri` 与 `configuration_id` 的跨字段一致性暂由 A2/B2 交叉复核。
- A2 确认后可将本 ADR 从 Proposed 更新为 Accepted。如果 A2 需要删除、改名或改变
  已有字段语义，必须按 ADR-004 走破坏性变更流程。

验证命令：

```bash
make check
```
