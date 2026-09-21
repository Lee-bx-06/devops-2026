# ADR-007：DRAFT 与 BuildChecker 的环境交接契约

- 状态：**Proposed**（B2 已落实 A2/B2 v0.1 约定，待 A2 在 PR 中接受）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：课件第 5、20、21、24 页；`task.schema.json` 的 `input_draft` / `output_draft`

## Context

DRAFT 从固定仓库提交生成可构建环境，BuildChecker 在同一环境中执行全量依赖检测。
课件第 20 页要求 DRAFT 输出 Dockerfile、镜像引用、每轮日志与选择理由，
第 21 页要求 BuildChecker 获得镜像、`configuration_id`、构建命令和项目根目录。

旧样例把 `environment` 放在未约束扩展区，没有 `output.build`，且使用包含 commit 的
`configuration_id`、相对 `project_root` 和兼做构建的 `clean_command`。A2 无法在不写
转换逻辑的情况下消费这些结果。另外，仓库同时存在点号和连字符命名的两套
DRAFT 请求/成功响应，会让契约真源不唯一。

## Decision

### 1. 只保留一套 canonical 链路

标准端到端样例为：

```text
draft.request.json
-> draft.job-succeeded.json
-> full-check.request.json
```

DRAFT 响应原样回显请求 `input` 和 `trace_id`。删除重复的
`draft-request.json` 与 `draft-response.json`。失败、超时仍保留独立状态样例，
但不得形成第二套成功链路。

### 2. DRAFT 成功输出正式包含环境与最终命令

`output_draft` 在 `task.schema.json` 中必填：

- `environment.image_uri` 和 `environment.configuration_id`；
- `build.command`、`build.clean_command`、`build.verify_command` 和 `build.project_root`；
- `build_result`、`rounds` 与 `artifacts`。

A2 使用唯一的无损映射：

```text
FULL_CHECK.input.environment = DRAFT.output.environment
FULL_CHECK.input.build       = DRAFT.output.build
```

专项测试比较两个 JSON 对象全等，避免字段重命名或语义转换。

### 3. 镜像引用与 `configuration_id`

- 字段名统一为 `image_uri`，不使用 `image_reference`，也不再输出冗余 `image_ref`。
- `image_uri` 必须是 OCI/Docker reference，禁止 `latest`。canonical 样例使用 digest。
- `configuration_id` 由 DRAFT 产生，A2 只原样消费。它是 opaque 非空字符串，
  只随基础镜像、工具链、依赖集或构建参数变化。
- `configuration_id` 不得包含 commit、Job ID 或随机 UUID。样例使用
  `cc-gcc13-release-6f12a4c8`。
- 所有 DRAFT artifact 的 `configuration_id` 必须与 `environment` 一致。

### 4. 构建命令的语义不重叠

```text
clean_command  = make clean
command        = make all
verify_command = make test
project_root   = /workspace/project
```

A2 依次执行 clean、build、verify。`clean_command` 不得使用 `&&`、`||` 或 `;`
串联构建命令。`project_root` 是容器内仓库根目录，必须是绝对 POSIX 路径，
不接受 `.`、Windows 路径或宿主路径。

### 5. 成功、失败与迭代次数

`build_result.iterations` 定义为“环境配置发生修改的轮数”，必须等于
`rounds` 长度。DRAFT 只有在下列条件全部成立时返回 `SUCCEEDED`：

- clean、build、verify 退出码均为 0；
- 镜像可拉取、可运行；
- 最后一轮没有新的环境修改；
- `build_succeeded=true` 且 `verify_succeeded=true`。

达到 `max_iterations` 仍未成功时返回 `FAILED + ENV_3002`；超时返回
`TIMED_OUT + EXEC_4002`。两种情况的 `output` 都必须是 `{}`，不交接半成品环境。

### 6. artifact 与每轮日志一一对应

`rounds[].log_uri` 必须指向 `output.artifacts[]` 中 `type=BUILD_LOG` 的记录。
成功输出至少包含一个 `DOCKERFILE`、每轮日志与最终验证日志。每条 artifact
都必须携带与请求相同的 40 位 commit 及与环境相同的 `configuration_id`。

样例 artifact 本体保存在 `docs/interfaces/artifacts/job-draft09/`。测试会重新计算
文件大小和 SHA-256，避免只校验“64 位形式正确”却指向不存在的内容。
读取方式仍按 ADR-003：用 `artifact_id` 调用 `GET /v1/artifacts/{artifact_id}`，
下载后用 `sha256` 验证。

## Alternatives

### 让 A2 从 Dockerfile 重建环境

违反“A2 直接消费 DRAFT 环境”的边界，也可能得到不同镜像。否决。

### 把 `environment` 保留为未约束扩展字段

样例能通过宽松载荷，但缺字段、改名或类型错误都无法被拒绝。A2 明确要求
进入正式 schema。否决。

### 保留 `build_result.image_ref`

会与 `environment.image_uri` 表达同一事物，必须再增加一条相等性规则。只保留
`environment.image_uri`，避免两个真源。否决。

### `configuration_id` 包含 commit

看似便于追溯，但同一构建配置每次换 commit 都会获得新 ID，破坏跨 Job 复用和
基线比较。commit 已由仓库字段和 artifact 单独记录。否决。

## Consequences

- A2 可将 DRAFT 的 `environment` 与 `build` 对象直接放入 FULL_CHECK 请求。
- schema 和校验器会拒绝缺环境、缺配置 ID、命令缺失、相对项目路径及语义重叠的
  `clean_command`。
- 校验器会拒绝 artifact 的 commit/configuration 不一致、轮次日志无对应产物、
  浮动 `latest` 镜像与绑定 commit/Job/UUID 的 `configuration_id`。
- 仓库增加四个小型 artifact fixture，用于校验样例中的大小与 SHA-256。
- ADR 保持 Proposed，直到 A2 在 Issue/PR 中复核并改为 Accepted。

验证命令：

```bash
make check
```
