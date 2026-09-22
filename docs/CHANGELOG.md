# 契约变更记录

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 本文件由 B1（李秉轩）维护

记录 `docs/interfaces/` 下公共契约的每一次变更。版本规则与递增依据见 `versioning.md`。
第 26 页要求「改字段之前先考虑消费者」，因此每条变更都必须写清影响面。

## [Unreleased]

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

| # | 事项 | 需要谁给结论 | 影响 |
|---|---|---|---|
| 1 | `artifact://pair09/{job_id}/{name}` 用完整 `job_id` 是对第 24 页样例的有意偏离 | 教师确认 | 若被驳回，`artifact_uri` 模式、样例与校验器三处要同步改 |
| 2 | 错误码注册表 `VALIDATION_2xxx` 命名空间为 A09/B09 自行扩展，非第 9 页给定 | 教师或助教确认 | 影响创建期拒绝的表示方式 |
| 3 | `execution` 字段在第 19 页被列为公共字段但全篇未定义，现定义由 A1 给出 | A2、A3、B2、B3 确认可用 | 若服务侧需要更多计时字段，属可兼容扩展 |
| 4 | `input` / `output` 内部字段由四个服务负责人最终确认 | A2、A3、B2、B3 | 见 Issue #1 第三节 |
| 5 | 产物读取接口在 E2 不部署，E3 是否需要落地实现 | 全组 | 见 `interfaces/endpoints.md` 第四节 |
| 6 | 收紧 `job.error.code`（上表 A1 变更第 1 项）是否需要递增 `schema_version` | **B1 裁定** | A1 判断不递增：1.0.0 的 `errors.md` 从未允许 `VALIDATION_2xxx` 进 `job.error`，是 schema 正则写宽了，本次是让 schema 符合已定稿规范。但 `versioning.md` 第二节把「改动 `error.code`」列在破坏兼容栏。若 B1 判定需递增，A1 将同步改 `const`、全部 38 个样例与测试。论证见 ADR-010 第五节 |
| 7 | `endpoints.md`「状态迁移」硬规则 2 与迁移表第三行冲突（`QUEUED→FAILED` vs「`RUNNING` 不可跳过」） | **B1 修订** | A1 建议收窄硬规则 2 为「`SUCCEEDED` 与 `TIMED_OUT` 不可跳过 `RUNNING`」，保留 `QUEUED→FAILED` 路径。规则本意（超时归属可判定）不受影响。见 ADR-010 第二节 |
| 8 | `configuration_id` 取值两组不一致：A1 用第 22 页原文的 `cc-MODE0`，B2 用 `draft-gcc13-release-9f8e7d6c` | B2 定格式、A2 定消费方式 | 该值必须全组统一，否则 DRAFT → BuildChecker 的环境交接对不上（第 21、22 页）。见 `interfaces/samples/README.md` 第四节 |
| 9 | DRAFT 样例两套并存、命名规范不统一 | **B2 执行** | A1 未擅自改名，因三个文件被 B2 的 `ADR-007` 与 `CONTRIBUTIONS.md` 引用。方案见 `interfaces/samples/README.md` 第五节 |

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
