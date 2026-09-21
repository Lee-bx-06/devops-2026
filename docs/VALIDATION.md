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

### 服务专有 input（第 20–23 页，按 `job_type` 分叉）

| `job_type` | 必填 |
| --- | --- |
| `DRAFT` | `repository`、`build`、`limits.max_iterations`、`limits.timeout_seconds` |
| `FULL_CHECK` | `repository`、`environment`、`build`（含 `clean_command`、`project_root`） |
| `INCREMENTAL_CHECK` | `base_commit`、`repository`、`environment`、`build`、**`baseline`**（含 `actual_graph_uri`、`commit`、`configuration_id`） |
| `REPAIR` | `repository`、`environment`、`build`、**`md_report`（`type` 必须为 `ERROR_REPORT`）**、`makefile_path` |

`REPAIR` 的 `md_report.type` 限制对应第 12、23 页「修复只消费 MD」。

### 服务专有 output（第 20–23 页）

| `job_type` | `SUCCEEDED` 时必填 |
| --- | --- |
| `DRAFT` | `build_result`（`build_succeeded` / `verify_succeeded` / `iterations`） |
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

定义见 `interfaces/buildchecker-contract.md` 与 `ADR-010`。

### finding（第 10 页）

九个字段全必填：`id`、`type`、`target`、`dependency`、`commit`、`detector`、
`location`、`evidence`、`message`。`type` 只能是 `MISSING` / `REDUNDANT`；
`evidence` 必须非空，`kind` 取 `PROCESS_TRACE` / `FILE_ACCESS` / `DECLARATION` /
`INSTRUCTOR_SAMPLE`。缺位置或证据即拒绝——B3 拿它没法改文件（第 5 页）。

### error（第 9 页）

`code` 必须落在命名空间正则内（见 `errors.md`），`message` 必填。
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

尚未由校验器强制、需人工或 B1 复核的约束：

- `base_commit` 与 `baseline.commit` 语义上应一致——但**故意不**在校验期拒绝，
  因为这是运行期才能确认的语义问题，落为 `FAILED` + `ENV_3003`（见 ADR-005、
  `samples/job.baseline-mismatch-failed.json`）。
- Job 内联 `output.findings` 与下载后的 `ERROR_REPORT` 文件本体是否一致：
  需要读取 artifact 才能比对，校验期只能检查两者各自的 counts。
- `trace_id` 在跨服务调用链上的实际串联。
- `sha256` 与产物本体是否真的匹配（需下载后计算）。

## 五、样例清单

正例 23 个（`docs/interfaces/samples/`）：四类 `job_type` 各一对请求/响应、
六种 `status` 各至少一个、独立 `artifact_record`、三种 artifact 本体和零发现路径。

负例 23 个（`docs/interfaces/samples/invalid/`），每个带 `expected_error`
声明**期望的拒绝原因**；校验器不仅要求它被拒，还要求拒绝理由与声明相符，
否则报「被拒原因与 expected_error 不符」。这样负例不会因为契约收紧而
「碰巧仍然被拒」地失去意义。

下划线开头的键（`_note`、`expected_error`）是给人看的注解，校验前会被剥离，
不属于线上载荷。

> 所有 URI、SHA、commit、镜像名、时间戳均为**说明性值**，不对应真实仓库或真实
> 检测结果。它们的作用是让 A09 与 B09 能用同一份具体例子确认彼此理解一致
> （第 11 页：「用自己的例子证明双方理解一致」）。
