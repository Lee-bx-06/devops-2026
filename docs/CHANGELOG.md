# 契约变更记录

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 本文件由 B1（李秉轩）维护

记录 `docs/interfaces/` 下公共契约的每一次变更。版本规则与递增依据见 `versioning.md`。
第 26 页要求「改字段之前先考虑消费者」，因此每条变更都必须写清影响面。

## [Unreleased]

### B1 版本裁定与复核（2026-09-22）

B1 按 `versioning.md` 完成 Issue #1 指定的版本裁定，修订 `endpoints.md` 硬规则 2，
并关闭 `errors.md` 与 ADR 上挂在自己名下的待复核项。本仓库的约定是「版本号归 B1 维护」，
本节即该职权的行使记录。

**裁定：三处变更均维持 `schema_version = 1.0.0`，不递增。**

| # | 变更 | 来源 | 按 `versioning.md` 第一节的字面归类 | 裁定 |
| --- | --- | --- | --- | --- |
| 1 | `error.code` 收紧为 `job_error_code` / `request_error_code` 两个正则 | A1，ADR-010 | 改动 `error.code`，列为可能破坏兼容 | **不递增** |
| 2 | `output_repair.rejected_candidates[].reason_code` 与 `output_repair.findings[].status` 引入封闭 enum | B3，ADR-009 / PR #20 | 取值集由开放收紧为封闭 | **不递增** |
| 3 | 新增三种 artifact 本体 `kind`：`actual_graph` / `declared_graph` / `error_report` | A2，ADR-011 / PR #6 | 新增产物类型，列为 MINOR | **不递增** |

共同理由：三处都落在**契约尚无任何消费者**的窗口内。第 7 页明确 E2 不部署 API，
仓库外没有任何一方按 1.0.0 解析过这些文档，因此不存在「旧版本被解析之后语义改变」的场景。
逐条补充：

- 变更 1 是让 schema 符合 1.0.0 内 `errors.md` 已定稿的规则，规范本身没变（ADR-010 第五节）。
- 变更 2 落在 B3 自己所有的 `output` 载荷内（ADR-004 第三节），消费者是 MDFixer 一方，
  封闭取值同时写进 `task.schema.json` 与 `tools/validate.py`，没有跨组破坏。
- 变更 3 只新增 `kind` 取值，不改既有取值的含义，属第 26 页「可兼容变化」一侧。

**首次有服务按 1.0.0 消费之后，同样性质的变更必须按 `versioning.md` 第一节递增。**
本判据、三条裁定的完整论证，以及「若日后改判为递增需要同步修改的五个位置」，
见 `versioning.md` 第七节。

本节落点：

| 文件 | 变更 |
| --- | --- |
| `interfaces/endpoints.md` | 硬规则 2 收窄为「`SUCCEEDED` 与 `TIMED_OUT` 不可跳过 `RUNNING`」，并留修订记录；第四节去掉「待 B1 复核」标注 |
| `adr/ADR-010-…md` | 状态 `Proposed` → `Accepted`，四条待评审项逐条给出结论 |
| `adr/ADR-011-…md` | 「待复核」改为复核状态表；B1 的版本影响项已定，其余三项待本人确认 |
| `adr/README.md` | 索引中 010 状态更新；011 注明 B1 项已完成 |
| `interfaces/errors.md` | 第五节「待 B1 复核」四条全部关闭，注册表定稿为八个码 |
| `interfaces/samples/job.failed-before-start.json` | 新增正例：`QUEUED→FAILED`，`started_at` 与 `duration_ms` 为 `null` |
| `VALIDATION.md`、`README.md` | 正例数随之更新为 25 |

### 修复：A3 artifact 在 Windows 下的完整性校验

- 修复 Issue #19：EChecker 的两份文本 artifact 在 Windows 检出为 CRLF 时，
  工作区字节数与仓库中的 LF blob 不同，导致 `size_bytes` / `sha256` 测试失败。
- 在 `.gitattributes` 中将两份 artifact 固定为 LF，并让专项测试按 UTF-8/LF
  规范字节计算大小与 SHA-256；样例中原有的规范元数据保持不变。
- `echecker-contract.md` 明确记录完整性字段的计算口径。

### 新增：B3 MDFixer 候选补丁拒绝判据

| 文件 | 内容 |
|---|---|
| `interfaces/samples/repair.job-succeeded-rejected.json` | 消费 1 条 C1 MISSING，全部候选被拒，任务仍为 SUCCEEDED |
| `adr/ADR-009-patch-acceptance-criteria.md` | 接受判据 7 条、拒绝原因码 8 个、字段追加 3+1 个；回答 `configuration_id` 相等语义 |
| `interfaces/task.schema.json` | `output_repair.rejected_candidates[].reason_code` 与 `output_repair.findings[].status` 加入封闭 enum |
| `tools/validate.py` | `Schema` 类从 schema 读两个 enum；REPAIR 分支新增两条取值校验 |
| `interfaces/samples/README.md` | 用途枚举登记 `job-succeeded-rejected` |

状态：已合并（PR #20，内容提交 `feadb30`，合并提交 `877e7c4`）。
ADR-009 状态为 Accepted。`schema_version` 是否因新增封闭 enum 而递增，
待 B1 按 `versioning.md` 第二节裁定。

后续：A3 在 PR #21（合并提交 `182de4d`）修复了 Windows CRLF 导致的 artifact
`size_bytes` 偏差，`make check` 在 Windows 与 Unix 上均全绿。

### 新增：A3 EChecker 增量检测契约

- 新增 `interfaces/echecker-contract.md` 与 `ADR-008`，定义 C0/C1、基线运行期
  匹配、finding 集合身份、`introduced` / `resolved` 差集和 B3 交接语义。
- `baseline` 新增必填 `error_report_uri`，使 EChecker 能从 C0/C1 两份报告精确
  计算新增与消除；旧的三字段增量请求需要补字段。
- 成功响应中的 `updated_graph` 必须是当前 Job 生成的 C1 ACTUAL_GRAPH，并同时列入
  `artifacts[]`；新增 C1 实际图与 ERROR_REPORT 两份可下载本体样例。
- 校验器增加 introduced/resolved 集合关系、finding commit 归属和更新图归属检查；
  新增 12 项 A3 专项测试。

状态：B3/B1 已完成评审，ADR-008 已接受；PR #8 已合并，最终内容提交为
`a45c3b7`，合并提交为 `f1d3dbb`。

### A1 第三轮：修复交接链断裂并补跨文档一致性守卫（2026-09-21）

| # | 变更 | 类型 | 影响面 |
|---|---|---|---|
| 1 | 6 个 A1 负责的样例迁移到规范环境值：`configuration_id` 由退役的 `cc-MODE0` 改为 `cc-gcc13-release-6f12a4c8`，`image_uri` 由 `draft:9f8e7d6c-iter3` 改为 digest 形式，`build.clean_command` 与 `project_root` 对齐 DRAFT 输出 | 样例修正 | `artifact.error-report.json`、`job.accepted-queued.json`、`job.analysis-failed.json`、`job.cancelled.json`、`repair.request.json`、`repair.job-succeeded.json`。无 schema 变更 |
| 2 | 新增 `tests/test_cross_document_consistency.py` | 新增 | 断言同一 `artifact_id` 记录逐字段一致、记录与本体一致、REPAIR 的 `md_report` 与 FULL_CHECK 实际产出一致、环境链一致 |
| 3 | `README.md` 不再写死测试总数 | 修正 | 该数字随每次新增测试过时，且 A1/A2/A3 三份 PR 必然在同一行冲突。改为断言「任何文档不得写死测试总数」 |

**动因**：`artifact-full09-error-report` 的 `configuration_id` 曾在 5 个样例里
出现两种取值，而 `make check` 全绿。A2 迁移了 DRAFT → FULL_CHECK 那半条链，
FULL_CHECK → MDFixer 那半没动。`VALIDATION.md` 第四节原有「跨文档一致性未覆盖」
一条，A2 补上 DRAFT → FULL_CHECK 的断言后把整条删掉了——但交接链不止一段。

**已知偏差登记表**（`KNOWN_ENV_DEVIATIONS`，守卫只拦表外新违规，不阻塞他人 PR）：

| 文件 | 负责人 | 原因 |
|---|---|---|
| `full-check.clean-project.json` | A2 | `image_uri` 用 `iter4` tag 却配规范 `configuration_id`，按 A2 自己的 `$defs.configuration_id` 定义二者不自洽，需裁定 |

A3 的四项偏差已在 PR #8 中完成迁移，并由提交 `a45c3b7` 从
`KNOWN_ENV_DEVIATIONS` 移除。

### 新增：A2 BuildChecker 输出与 artifact 本体

| 文件 | 内容 |
|---|---|
| `interfaces/buildchecker-contract.md` | FULL_CHECK 请求、成功输出、MD/RD、失败路径与下游交接 |
| `interfaces/task.schema.json` | 新增 `actual_graph` / `declared_graph` / `error_report` 三种本体定义 |
| `adr/ADR-011-buildchecker-output-contract.md` | A2 对本体和跨字段一致性的架构决策（原编号 010，与 A1 的 ADR-010 冲突后改号） |
| `interfaces/samples/artifact.*.json` | 三份 artifact 本体正例 |
| `interfaces/samples/full-check.clean-project.json` | 零发现成功样例 |
| `interfaces/samples/invalid/…` | counts 不一致、缺图、非法 observation、报告本体不一致、相对 project_root 五个负例 |
| `tests/test_buildchecker_contract.py` | A2 的 artifact 与跨字段一致性测试 |
| `tools/validate.py` | 增加 counts/findings、核心 artifact 类型和三种本体的校验 |

状态：A2 已起草，A3 已按其冻结产物完成基线接入；待 B3、B1 复核。
是否提升 `schema_version` 由 B1 按 `versioning.md` 判定。
### A1 变更（2026-09-21，待 B1 评审）

对应 ADR-010。三项改动，其中第 1 项涉及 `error.code`，版本号处理见下方待处理表第 6 项。

| # | 变更 | 类型 | 影响面 |
|---|---|---|---|
| 1 | `error_code` 拆为 `job_error_code`（`ENV_3xxx`/`EXEC_4xxx`/`ANALYSIS_5xxx`）与 `request_error_code`（`VALIDATION_2xxx`）；`job.error` 只引前者 | 收紧 | 落实 B1 在 `errors.md` 第二节已定稿的规则。此前 schema 正则四段全允许，即文档禁止的事契约放行。**仓库内无任何合法样例受影响**，仅 A1 一条测试断言过旧行为，已改正 |
| 2 | `status_matrix` 增加 `execution.started_at` / `finished_at` 的计时约束 | 收紧 | 把 B1 在 `endpoints.md`「状态迁移」一节的规则形式化。全部 19 个正例已符合，无需改样例 |
| 3 | 新增 `$defs.produced_environment`，挂到 `output_draft.environment`（**可选**） | 新增 | 依 B2 的 `draft-response.json` 补入，使该字段可被校验。第 21、22 页要求下游消费的 `configuration_id` 此前在 DRAFT 输出里没有定义来源。是否升为必填由 B2 决定 |

新增负例 `samples/invalid/validation-code-in-job-error.json`；
`draft.job-succeeded.json` 补入 `output.environment`；
测试由 27 项增至 41 项（含两项防文档腐烂的断言，见下）。

数量类陈述的单一来源是 `VALIDATION.md` 第五节；ADR 与 BACKLOG 不再各自写死样例数，
改为指向该节，并由 `tests/…TestDocsDoNotRot` 断言其与实际文件数一致。
起因是本轮自检发现三个 ADR 里的样例计数在 B2 补样例后已全部过时。

同时更正 `BACKLOG.md` 第四节关于 `origin/e2b2`「不可直接合并、三个样例通不过校验」
的判断：实测 `e2b2` 已完全并入 main，提交 `38f6694` 在仓库内不存在，
三个样例单独校验全部通过。原文保留在 `git show 8eb7b4c`，更正附证据表。
### B2：落实 A2–B2 环境交接约定

- 将 DRAFT 成功输出的 `environment`、`build`、`build_result`、`rounds` 与
  `artifacts` 纳入正式 schema；FULL_CHECK 输入同步要求清理、构建、验证三条命令
  和绝对 POSIX `project_root`
- 规范镜像为 OCI/Docker 引用并拒绝 `:latest`；`configuration_id` 定义为稳定、
  不绑定提交、任务或 UUID 的不透明标识
- DRAFT 成功输出可逐字段直接映射到 FULL_CHECK 输入；校验器会拒绝两侧漂移、
  非连续迭代轮次、日志与制品不对应以及错误的提交/配置归属
- 删除三份重复命名的旧 DRAFT 样例，保留唯一规范请求/成功链，新增构建失败样例，
  并明确任务超时和达到最大迭代次数的终态
- 新增一组 Dockerfile/轮次日志/最终验证日志测试制品，样例记录其真实 SHA-256
  与字节数；新增 7 项 A2–B2 专项单元测试
- 本变更只涉及 B2 所属的 DRAFT 契约及其与 A2 的明确交接边界，提交到 `e2b2`
  并通过 PR 请求合入，不直接推送 `main`
### A2 复核 B2 的 DRAFT 交接并接受 ADR-007（2026-09-21）

- 逐条复核 `Issue #4` / `PR #5`：`output_draft` 已进 schema、canonical DRAFT 链唯一、
  `configuration_id` 不再绑定 commit、`clean_command` 与 `project_root` 语义统一、
  Issue + PR 追溯齐备。B2 待确认的五项前置条件全部满足，`ADR-007` 由 `Proposed` 改为 `Accepted`。
- 复核发现并修正一处数据不一致：`draft.job-succeeded.json` 中 Dockerfile 制品的
  `size_bytes` / `sha256` 取自 CRLF 工作副本（318 字节），与仓库内 LF blob
  （308 字节）不符，`TestA2B2DraftHandoff` 在干净检出上必然失败。已按 blob 实际字节改正。
- 原 `ADR-010-buildchecker-output-contract.md` 与 A1 已合并的 `ADR-010` 编号冲突，
  已在 `a2-full-check-contract` 分支改号为 `ADR-011` 并登记进 `adr/README.md`。

### 待处理

| # | 事项 | 需要谁给结论 | 状态与影响 |
|---|---|---|---|
| 1 | `artifact://pair09/{job_id}/{name}` 用完整 `job_id` 是对第 24 页样例的有意偏离 | 教师（知情项，不阻塞） | 组内已定案：A1 与 B1 于 2026-09-22 认可为组内协议（Issue #1）。若教师在课上驳回，`artifact_uri` 模式、样例与校验器三处同步改，见 `interfaces/endpoints.md` 第五节 |
| 2 | 错误码注册表 `VALIDATION_2xxx` 命名空间为 A09/B09 自行扩展，非第 9 页给定 | 教师或助教（知情项） | B1 已把适用边界限死为创建期拒绝，不写入 `job.error`；见 `interfaces/errors.md` 第二节与第五节 |
| 3 | ADR-011 的消费侧复核 | A2、B3、B2 | 三方的复核项内容均已由各自 PR 落实（#6 / #20 / #5），本人在 Issue #1 确认后 ADR-011 由 `Proposed` 改 `Accepted` |
| 4 | `full-check.clean-project.json` 的 `image_uri`（iter4 tag）与 `configuration_id`（规范值）是否自洽 | A2 裁定 | `KNOWN_ENV_DEVIATIONS` 中唯一未消除的偏差，二者必居其一 |
| 5 | 产物读取接口 `GET /v1/artifacts/{artifact_id}` 是否在 E3 落地实现 | 全组（E3 决定） | E2 不部署（第 7 页）；契约已冻结，见 `interfaces/endpoints.md` 第四节 |

原表的第 3 项（`execution` 定义）、第 4 项（`input` / `output` 内部字段）由四组在各自样例与
PR 中落实；第 6 项（`schema_version`）、第 7 项（硬规则 2）已由 B1 于 2026-09-22 裁定；
第 8 项（`configuration_id` 取值）已由 A1/A2/A3/B2 完成迁移，仅余 A2 的 `clean-project`
一处偏差（上表第 4 项）；第 9 项（DRAFT 样例重复命名）已由 B2 完成。

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
