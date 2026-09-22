# 校验规则与运行方法

小组 A09 / 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0 ｜ 负责人 A1

## 一、怎么跑

```bash
make check          # 等价于下面两条
python3 tools/validate.py
python3 -m unittest discover -s tests -v
```

单文件校验（联调时用，校验对方给的文件）：

```bash
python3 tools/validate.py ../B09/their-response.json
```

**依赖：只需 Python 3 标准库。** 本机验证于 Python 3.14.6。
不依赖 `jsonschema` 是刻意的取舍，见 ADR-001 与下文第四节。

## 二、E2 第 25 页四条最小检查的落点

| # | 第 25 页要求 | 本仓库的实现 | 结果 |
| --- | --- | --- | --- |
| 01 | 运行 validate.py，检查四类请求与响应 | `tools/validate.py` + `check_coverage()` 强制四类 `job_type` 各有请求与成功响应样例、六种 `status` 各有样例；`tests/…Check01…` | 通过 |
| 02 | 将 `job_type` 改成 `ABC`，应被拒绝 | `samples/invalid/invalid-job-type.json`；`tests/…Check02…` 用**变异**方式现场改 `job_type` 断言被拒 | 通过 |
| 03 | 删除增量任务的 `baseline`，应被拒绝 | `samples/invalid/missing-baseline.json`；`tests/…Check03…` 现场 `del input["baseline"]` 断言被拒 | 通过 |
| 04 | 解释 MD 为什么不等于工具执行失败 | 文字：`docs/interfaces/errors.md` 第一节；代码：`tests/…Check04…` 断言「MD 进 findings 合法、同一条 MD 进 error 非法」 | 通过 |

第 24 页额外那条「让另一组真的把 artifact 读一次」在 E2 阶段以契约形式冻结
（`endpoints.md` 第四节），实际读取留到 E12 验证。

## 三、校验了什么

### 顶层信封（A1 冻结，`additionalProperties: false`）

六种 `kind`，互斥：三种 Job 封套
`create_request` / `job` / `artifact_record`，以及三种 artifact 本体
`actual_graph` / `declared_graph` / `error_report`。
顶层出现任何未定义字段一律拒绝——想加公共字段必须走 ADR + 版本升级（第 26 页）。

- `schema_version` 必须恰为 `1.0.0`
- `job_type` 封闭枚举：`DRAFT` / `FULL_CHECK` / `INCREMENTAL_CHECK` / `REPAIR`
- `status` 封闭枚举：`QUEUED` / `RUNNING` / `SUCCEEDED` / `FAILED` / `TIMED_OUT` / `CANCELLED`
  （注意课程规范用 `QUEUED`，不是 `PENDING`）
- `job_id` 匹配 `^job-[a-z0-9][a-z0-9-]*$`，且**不得**出现在 `create_request`
- `trace_id` 匹配 `^trace-[a-z0-9][a-z0-9-]*$`
- `commit` 一律 40 位小写十六进制（完整 SHA，第 10、21、22 页）
- `artifact uri` 一律 `artifact://pair09/{job_id}/{name}`（第 24 页 + 第 15 页配对组编号）
- `sha256` 一律 64 位小写十六进制

### 状态矩阵（第 8 页）

| `status` | `error` | `output` | `http_status` |
| --- | --- | --- | --- |
| `QUEUED` | 必须 `null` | 必须 `{}` | 可选，若出现必须 202 |
| `RUNNING` | 必须 `null` | 必须 `{}` | 禁止 |
| `SUCCEEDED` | 必须 `null` | 可含 findings / artifacts | 禁止 |
| `FAILED` | 必须是 error 对象 | 必须 `{}` | 禁止 |
| `TIMED_OUT` | 必须是 error 对象 | 必须 `{}` | 禁止 |
| `CANCELLED` | 必须 `null` | 必须 `{}` | 禁止 |

**检出 MD 仍是 `SUCCEEDED`**，findings 放 `output`，绝不放 `error`（第 8、9 页）。

### 状态迁移的计时痕迹（B1 迁移表 + ADR-010）

迁移本身是文档序列上的性质，单文档校验器看不到；但每次迁移都会在 `execution`
留下必然痕迹，这些痕迹可校验：

| `status` | `started_at` | `finished_at` |
| --- | --- | --- |
| `QUEUED` | 必须 `null` | 必须 `null` |
| `RUNNING` | 必须是时间戳 | 必须 `null` |
| `SUCCEEDED` | 必须是时间戳 | 必须是时间戳 |
| `TIMED_OUT` | 必须是时间戳 | 必须是时间戳 |
| `FAILED` | **允许 `null`** | 必须是时间戳 |
| `CANCELLED` | **允许 `null`** | 必须是时间戳 |

`FAILED` / `CANCELLED` 允许 `started_at` 为 `null`，对应 B1 迁移表里
`QUEUED → FAILED`（受理后环境准备失败）与 `QUEUED → CANCELLED`（队列中取消）
这两条从未进入 `RUNNING` 的路径。论证见 ADR-010 第二节。

### 错误码命名空间（第 9 页 + B1 于 2026-09-21 的边界限定）

`error.code` 拆成两个互斥的正则：

| 定义 | 正则 | 用在哪 |
| --- | --- | --- |
| `job_error_code` | `^(ENV_3[0-9]{3}\|EXEC_4[0-9]{3}\|ANALYSIS_5[0-9]{3})$` | `job.error`，即 `FAILED` / `TIMED_OUT` |
| `request_error_code` | `^VALIDATION_2[0-9]{3}$` | 创建期 HTTP 4xx 响应体，不产生 Job |

因此把 `VALIDATION_2001` 写进 `job.error` 会被拒（ADR-010、`errors.md` 第二节）。

### 服务专有 input（第 20–23 页，按 `job_type` 分叉）

| `job_type` | 必填 |
| --- | --- |
| `DRAFT` | `repository`、`build`、`limits.max_iterations`、`limits.timeout_seconds` |
| `FULL_CHECK` | `repository`、`environment`、`build`（含 `clean_command`、`project_root`） |
| `INCREMENTAL_CHECK` | `base_commit`、`repository`、`environment`、`build`、**`baseline`**（含 `actual_graph_uri`、`error_report_uri`、`commit`、`configuration_id`） |
| `REPAIR` | `repository`、`environment`、`build`、**`md_report`（`type` 必须为 `ERROR_REPORT`）**、`makefile_path` |

`REPAIR` 的 `md_report.type` 限制对应第 12、23 页「修复只消费 MD」。

### 服务专有 output（第 20–23 页）

| `job_type` | `SUCCEEDED` 时必填 |
| --- | --- |
| `DRAFT` | `environment`、`build`（clean/build/verify/绝对 project_root）、`build_result`、`rounds`、`artifacts` |
| `FULL_CHECK` | `counts`（`missing` / `redundant`） |
| `INCREMENTAL_CHECK` | `introduced`、`resolved`、`updated_graph` |
| `REPAIR` | `verification`（恰含 `build` / `test` / `recheck`）、`declaration_style` |

FULL_CHECK 还额外强制：

- `counts.missing` 等于 MISSING findings 数。
- `counts.redundant` 等于 REDUNDANT findings 数。
- `SUCCEEDED.output.artifacts[]` 同时包含 `ACTUAL_GRAPH`、`DECLARED_GRAPH`、
  `ERROR_REPORT`。

### artifact 本体（A2，第 21、22、23、24 页）

- `actual_graph`：target、实际文件访问、observation 和可选 evidence URI。
- `declared_graph`：target、Makefile prerequisite、声明位置。
- `error_report`：commit、configuration_id、counts、findings。
- `error_report.counts` 必须与自身 `findings` 一致。
- 三份本体都必须带相同的 `commit` 和 `configuration_id`。

定义见 `interfaces/buildchecker-contract.md` 与 `ADR-011`。

### A2/B2 环境交接专项校验

`tests/test_validate.py::TestA2B2DraftHandoff` 覆盖：

- 仓库只有一份 canonical DRAFT 请求和成功响应；
- `DRAFT.output.environment/build` 与 `FULL_CHECK.input.environment/build` 全等；
- 缺 `environment`、`configuration_id`、任一命令或 `project_root` 时被拒绝；
- 禁止 `latest`、相对 `project_root` 和串联构建的 `clean_command`；
- `configuration_id` 不包含 commit、Job ID 或随机 UUID；
- 每轮 `log_uri` 都有 `BUILD_LOG` artifact，所有 artifact 的 commit/configuration 一致；
- 对仓库内 DRAFT artifact fixture 重算文件大小和 SHA-256；
- `FAILED + ENV_3002`、`TIMED_OUT + EXEC_4002` 与迭代耗尽路径。

### A3 EChecker 专项校验

`tests/test_echecker_contract.py` 覆盖：

- C0 的 ACTUAL_GRAPH 与 ERROR_REPORT 都是必需基线；
- 请求中的 commit、configuration 和 project_root 与 A2 冻结的 artifact 一致；
- `findings=F1`、`introduced=F1-F0`、`resolved=F0-F1`；
- 当前/新增 finding 属于 C1，已消除 finding 可追溯到 C0；
- `updated_graph` 是当前 Job 生成并列入 artifacts 的 C1 ACTUAL_GRAPH；
- C1 ERROR_REPORT 与当前 findings 一致，可作为 B3 的修复输入；
- 两份 A3 artifact fixture 的大小和 SHA-256 与元数据一致。

### finding（第 10 页）

九个字段全必填：`id`、`type`、`target`、`dependency`、`commit`、`detector`、
`location`、`evidence`、`message`。`type` 只能是 `MISSING` / `REDUNDANT`；
`evidence` 必须非空，`kind` 取 `PROCESS_TRACE` / `FILE_ACCESS` / `DECLARATION` /
`INSTRUCTOR_SAMPLE`。缺位置或证据即拒绝——B3 拿它没法改文件（第 5 页）。

### error（第 9 页）

`code` 必须落在 `job_error_code` 的三段命名空间内（见 `errors.md`），`message` 必填。
`VALIDATION_2xxx` 属创建期 HTTP 4xx 码段，写进 `job.error` 会被拒。
`error` 对象严格封闭，不接受未定义字段。

## 四、已知边界：这不是通用 JSON Schema 引擎

`tools/validate.py` 是**手写镜像校验器**，不是 JSON Schema 实现。取舍理由：

- 课堂 150 分钟且与 E3 共享（第 2 页），现场 `pip install jsonschema` 不现实；
  评分环境也未必有网。第 25 页要求「运行 validate.py」必须当场可跑。
- 代价：schema 里少数纯声明性约束（如 `output_draft` 的 `allOf` 组合）
  由校验器以等价的手写逻辑覆盖，而非机械求解。

**防漂移措施**：校验器不硬编码常量，而是启动时从 `task.schema.json` 读取
枚举、正则、必填清单（见 `validate.py` 的 `Schema` 类）。改了 schema 里的
`job_type` 枚举，校验器立即跟着变。`tests/test_validate.py::TestSchemaAndValidatorAgree`
断言二者一致。

因此：**schema 是权威定义，validate.py 是它的可执行镜像。**
若两者出现分歧，以 schema 为准并修 validate.py。

尚未由校验器强制、需人工或运行期处理的约束：

- `base_commit` 与 `baseline.commit` 是否相等、`baseline.configuration_id` 与
  `environment.configuration_id` 是否相等——**故意不**在校验期比对。
  第 5 页把「基线版本和配置匹配」列为**接收方检查**，属运行期职责，
  由 EChecker 落为 `FAILED` + `ENV_3003`。
  `tests/…TestBaselineConsistencyIsRuntimeNotContract` 钉住这条边界，
  防止后来者误收紧。论证见 ADR-010 第三节；ADR-005 原来给的理由
  （「需要读产物才能比对」）不成立，已由 ADR-010 第四节修正。
- 「终态不可再迁移」需要 Job 文档**序列**才能验证，单文档校验器看不到。
  已覆盖的是它在每个状态上留下的计时痕迹（见第三节迁移表）。
- 任意 Job 内联 `output.findings` 与下载后的 `ERROR_REPORT` 文件本体是否一致：
  需要读取 artifact 才能比对，校验期只能检查两者各自的 counts 与形状。
  A2/A3 的专项测试用仓库内样例断言二者相等，
  但那是对样例的检查，不是对任意请求的校验。
- `trace_id` 在跨服务调用链上的实际串联。
- DRAFT canonical 样例与 A3 两份 artifact 的 `sha256` 已对仓库内 fixture 重算；
  其他说明性 artifact 仍需在真实下载后计算。

### 已覆盖：跨文档一致性（`tests/test_cross_document_consistency.py`）

单文档校验看不出「同一个 artifact 在两个文件里被描述成不同样子」。
这曾导致 `artifact-full09-error-report` 的 `configuration_id` 在 5 个样例里
出现两种取值而 `make check` 全绿：A2 迁移了 DRAFT → FULL_CHECK 那半条链，
FULL_CHECK → MDFixer 那半没动。现由该测试文件断言：

- 同一 `artifact_id` 在所有文件里的记录逐字段一致
- `artifact_record` 与它所描述的本体在 `commit`、`configuration_id` 上一致
- REPAIR 的 `input.md_report` 与 FULL_CHECK 实际产出的 `ERROR_REPORT` 记录逐字段一致
  （即第 5 页「修复交接」的接收方检查项，落到样例层面）
- `md_report.commit == repository.commit`、`md_report.configuration_id ==
  environment.configuration_id`（B3 的 ADR-009 判据，提前在样例层验证）
- 同一 commit 的检测/修复任务使用 DRAFT 为该 commit 产出的规范环境；
  环境准备失败（`ENV_3002`）的场景按**错误码**排除，不按文件名排除

已知偏差登记在该文件的 `KNOWN_ENV_DEVIATIONS`（含负责人与原因），
守卫只拦登记表**之外**的新违规，不强制登记表收缩，以免 A1 的测试卡住别人的 PR。
登记表的收缩记在 `BACKLOG.md`。

> 教训：本节原来有一条「DRAFT 输出的 `configuration_id` 与下游是否逐字一致——未覆盖」。
> A2 补上 DRAFT → FULL_CHECK 的断言后把整条删掉了，但交接链不止这一段，
> 删掉整条等于宣称问题已解决。**部分覆盖不等于覆盖。**

## 五、样例清单

正例 23 个（`docs/interfaces/samples/`）：四类 `job_type` 各一对请求/响应、
六种 `status` 各至少一个、独立 `artifact_record`、B2 的 DRAFT 请求/成功/失败链、
A2 的三种 artifact 本体和零发现路径，以及 A3 更新后的实际图与报告本体。

负例 24 个（`docs/interfaces/samples/invalid/`），每个带 `expected_error`
声明**期望的拒绝原因**；校验器不仅要求它被拒，还要求拒绝理由与声明相符，
否则报「被拒原因与 expected_error 不符」。这样负例不会因为契约收紧而
「碰巧仍然被拒」地失去意义。

下划线开头的键（`_note`、`expected_error`）是给人看的注解，校验前会被剥离，
不属于线上载荷。

> 除 canonical DRAFT 成功样例的仓库内 fixture 外，URI、SHA、commit、镜像名、
> 时间戳均为**说明性值**。DRAFT fixture 的 `sha256` 与 `size_bytes` 是文件真实值；
> 镜像 URI 仍是契约示例，不表示已推送或部署。

