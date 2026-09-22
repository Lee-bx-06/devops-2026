# EChecker / INCREMENTAL_CHECK 接口契约

小组 A09 ｜ 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0
负责人：A3 ｜ 上游：A2 的 BuildChecker ｜ 下游：B3 的 MDFixer

本文定义 `INCREMENTAL_CHECK` 的请求、成功输出、基线匹配规则，以及
EChecker 交给后续提交和 MDFixer 的 artifact。E2 只定义契约，不实现或部署 API。

## 一、职责边界

EChecker 比较两个提交：

- `C0`：已有完整检测结果的历史提交，即 `input.base_commit`。
- `C1`：本次要检测的当前提交，即 `input.repository.commit`。

它使用 C0 的实际依赖图作为历史基线，在同一构建配置中分析 C1，产生：

- C1 的当前 MD/RD findings；
- 相对 C0 新增的 findings；
- 相对 C0 已消除的 findings；
- 可供下一次检测继续使用的 C1 实际依赖图；
- 交给 B3 的 C1 ERROR_REPORT。

EChecker 不生成构建镜像、不修改 Makefile，也不负责部署 artifact 下载端点。

## 二、论文机制与本契约的映射

ISSTA 2024 论文中的 EChecker 以项目、当前 commit 和历史 clean build 的实际依赖图
为输入。它监控增量构建，并结合源码预处理指令变化、文件变化和 Makefile 构建命令
变化，更新历史实际依赖图；最后比较实际依赖图与声明依赖图，得到 MD/RD。

本契约只冻结跨服务必须交换的信息：

| 论文概念 | 契约字段或产物 |
| --- | --- |
| 项目和当前提交 C1 | `input.repository` |
| 历史提交 C0 | `input.base_commit` |
| 历史实际依赖图 | `input.baseline.actual_graph_uri` |
| 历史检测结果 | `input.baseline.error_report_uri` |
| 固定构建配置 | `input.environment.configuration_id` |
| 增量构建命令和根目录 | `input.build` |
| 更新后的实际依赖图 | `output.updated_graph` |
| C1 当前检测结果 | `output.findings` + C1 `ERROR_REPORT` |

源码 diff、预处理指令解析、构建跟踪和图更新算法属于 EChecker 内部实现，E2 不把
它们暴露成公共字段。

## 三、INCREMENTAL_CHECK 请求

请求使用公共 `create_request` 信封，`job_type=INCREMENTAL_CHECK`。

`input` 必填：

```text
base_commit
repository.url
repository.commit
environment.image_uri
environment.configuration_id
build.command
build.project_root
baseline.actual_graph_uri
baseline.error_report_uri
baseline.commit
baseline.configuration_id
```

字段语义：

- `base_commit`：C0 的完整 40 位 SHA。
- `repository.commit`：C1 的完整 40 位 SHA。
- `environment`：沿用 DRAFT 冻结的镜像和配置。
- `build.command`：对 C0 工作区应用 C1 变化后执行的增量构建命令。
- `build.project_root`：容器内项目根目录的绝对 POSIX 路径。
- `baseline.actual_graph_uri`：A2 在 C0 生成的 `ACTUAL_GRAPH`。
- `baseline.error_report_uri`：A2 在 C0 生成的 `ERROR_REPORT`，用于计算新增与消除。
- `baseline.commit` / `configuration_id`：声明两个历史 artifact 的归属。

正常增量路径不要求 `clean_command`。强制 clean build 会失去 EChecker 相对全量检测
的意义；若没有历史基线，本课程契约直接拒绝请求，不在 EChecker 内部回退到 clean
build。论文中的首次 clean build 由上游 BuildChecker 提供。

完整样例：`samples/incremental-check.request.json`。

## 四、创建期校验与运行期匹配

创建期只检查形状和格式：

- `baseline` 以及四个子字段必须存在；
- commit 必须是完整 SHA；
- artifact URI 必须属于 `pair09`；
- 环境、构建命令和项目根目录必须能表达。

以下是 EChecker 的运行期接收方检查：

1. `baseline.commit == base_commit`；
2. `baseline.configuration_id == environment.configuration_id`；
3. 下载后的两个基线 artifact 的 `commit` 和 `configuration_id` 与声明一致；
4. 历史实际图的 `project_root == build.project_root`；
5. C0 是 C1 的祖先提交，因而“从 C0 到 C1”的变化有确定含义。

任一项不满足时，Job 为 `FAILED`、`output={}`、`error.code=ENV_3003`。这类输入结构
合法，所以先被受理，再由接收方失败；它不同于删除 `baseline` 后的 HTTP 400。
失败样例：`samples/job.baseline-mismatch-failed.json`。

## 五、finding 集合语义

在同一配置下，记 C0 ERROR_REPORT 的 finding 集合为 `F0`，C1 当前 finding 集合为
`F1`。集合身份由以下三个字段的字面值组成：

```text
(type, target, dependency)
```

因此：

```text
output.findings   = F1
output.introduced = F1 - F0
output.resolved   = F0 - F1
```

规则：

- `introduced` 中每项必须同时出现在 `findings` 中。
- `resolved` 中每项不得仍出现在 `findings` 中。
- `findings` 与 `introduced` 的 `commit` 必须是 C1。
- `resolved` 保留历史记录，`commit` 必须是 C0。
- `id`、位置、证据和说明用于追溯，不参与集合身份；同一依赖在不同检测器中
  重新生成 ID，不应被误判为新增。
- `target` 与 `dependency` 按上游 ERROR_REPORT 原值进行比较；A3 不根据文件名
  猜测或重写上游身份。

## 六、成功输出

`SUCCEEDED` 的 `output` 至少包含：

```text
findings[]
introduced[]
resolved[]
updated_graph
artifacts[]
```

`updated_graph` 必须：

- `type=ACTUAL_GRAPH`；
- `producer_job_id` 等于当前 Job ID；
- `commit` 等于 C1；
- `configuration_id` 等于本次环境配置；
- 作为同一条 artifact 记录出现在 `output.artifacts[]`；
- 文件本体的 `project_root` 等于本次 `build.project_root`。

这份图是 C0 历史图经 C1 变化更新后的完整实际依赖图，不只是本次增量构建中碰巧
执行到的 target 子集。它可以作为下一次 `INCREMENTAL_CHECK` 的基线。

成功 Job 样例：`samples/incremental-check.job-succeeded.json`。
更新图本体：`samples/artifact.incremental-actual-graph.json`。

## 七、交给 MDFixer 的报告

EChecker 同时生成 C1 的 `ERROR_REPORT` artifact：

- `commit` 和 `configuration_id` 属于 C1；
- `findings` 与 Job 的 `output.findings` 完全一致；
- `counts` 与报告中的 MISSING/RD 数量一致；
- B3 只消费其中当前仍存在的 `type=MISSING`；
- `resolved` 是历史变化说明，不是 B3 的修复输入。

报告本体样例：`samples/artifact.incremental-error-report-body.json`。

## 八、状态与失败路径

- 检出 MD/RD：`SUCCEEDED + error=null`，findings 是正常分析结果。
- 基线不可读或不匹配：`FAILED + ENV_3003`。
- 增量构建命令失败：`FAILED + EXEC_4001`。
- 执行超时：`TIMED_OUT + EXEC_4002`。
- 图推导或依赖比较失败：`FAILED + ANALYSIS_5001`。
- artifact 写出失败：`FAILED + ANALYSIS_5002`。
- 取消：`CANCELLED + error=null + output={}`。

失败或超时时不交接半成品 findings、图或报告。

## 九、artifact 读取顺序

`artifact://pair09/{job_id}/{name}` 是稳定标识，不是可直接打开的 HTTP 地址。
消费方先从 URI 得到生产 Job，查询 Job 的 `output.artifacts[]` 找到同 URI 的记录，
再用其中的 `artifact_id` 调用 `GET /v1/artifacts/{artifact_id}`。具体约定见
`endpoints.md` 与 ADR-003。

## 十、验证

```bash
python tools/validate.py
python -m unittest tests.test_echecker_contract -v
```

专项测试覆盖：

- 历史实际图和历史 ERROR_REPORT 都必须提供；
- 请求确实引用 A2 冻结的 C0 artifact；
- `introduced` / `resolved` 是精确集合差；
- C0/C1 finding 的 commit 可追溯；
- 更新图属于 C1、由当前 Job 产生且可作为下一次基线；
- C1 ERROR_REPORT 与当前 findings 一致，并可直接交给 B3；
- artifact 的字节数和 SHA-256 与仓库内本体一致。
