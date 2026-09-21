# BuildChecker / FULL_CHECK 接口契约

小组 A09 ｜ 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0  
负责人：A2 ｜ 上游：B2 的 DRAFT ｜ 下游：A3 的 EChecker、B3 的 MDFixer

本文定义 `FULL_CHECK` 请求、成功输出，以及 BuildChecker 产出的三份 artifact
本体。E2 只定义契约，不实现或部署服务。

## 一、职责边界

BuildChecker 在 DRAFT 生成的固定镜像和固定构建配置中执行 clean build，得到：

- 实际依赖图：所有新生成文件在构建过程中实际访问的项目内输入文件。
- 声明依赖图：GNU Make 动态数据库中的 target-prerequisite。
- ERROR_REPORT：比较两张图后得到的 MD/RD findings。

BuildChecker 不负责生成镜像，也不负责修改 Makefile。

## 二、FULL_CHECK 请求

请求使用公共 `create_request` 信封，`job_type=FULL_CHECK`。

`input` 必填：

```text
repository.url
repository.commit
environment.image_uri
environment.configuration_id
build.command
build.clean_command
build.project_root
```

`build.verify_command` 可选。

字段语义：

- `repository.commit`：40 位完整 SHA。
- `environment.image_uri`：DRAFT 产出的可运行镜像，A2 不从 Dockerfile 重建。
- `environment.configuration_id`：DRAFT 生成，A2 原样使用。
- `build.clean_command`：只负责清理，例如 `make clean`。
- `build.command`：构建命令，例如 `make all`。
- `build.verify_command`：验证命令，例如 `make test`。
- `build.project_root`：容器内仓库根目录的绝对 POSIX 路径。

执行顺序固定为：

```text
clean_command -> command -> verify_command
```

样例：`samples/full-check.request.json`。

## 三、FULL_CHECK 成功输出

只有分析器正常结束时才是 `SUCCEEDED`。检出 MD/RD 仍然是成功。

`output` 至少包含：

```text
summary
counts.missing
counts.redundant
findings[]
artifacts[]
```

三条硬约束：

1. `counts.missing` 必须等于 `findings[]` 中 `type=MISSING` 的数量。
2. `counts.redundant` 必须等于 `findings[]` 中 `type=REDUNDANT` 的数量。
3. `SUCCEEDED` 的 `artifacts[]` 必须同时包含：

```text
ACTUAL_GRAPH
DECLARED_GRAPH
ERROR_REPORT
```

零发现也是合法成功：

```json
{
  "counts": {"missing": 0, "redundant": 0},
  "findings": []
}
```

样例：`samples/full-check.job-succeeded.json`。

## 四、实际依赖图

artifact 元数据：

```json
{
  "artifact_id": "artifact-full09-actual-graph",
  "type": "ACTUAL_GRAPH",
  "uri": "artifact://pair09/job-full09/actual.json",
  "media_type": "application/json",
  "producer_job_id": "job-full09",
  "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
  "configuration_id": "cc-gcc13-release-6f12a4c8",
  "sha256": "..."
}
```

文件本体使用 schema 中的 `actual_graph`，样例：
`samples/artifact.actual-graph.json`。

要求：

- `commit`、`configuration_id` 与 Job 输入一致。
- `project_root` 与 Job 输入一致。
- `targets[].target` 表示实际构建中新生成的文件，使用相对 `project_root` 的
  POSIX 路径；它可以是显式 target，也可以是隐式 target 或中间文件。
- `dependencies[].path` 使用相对 `project_root` 的 POSIX 路径。
- `observation` 只允许 `FILE_ACCESS` / `PROCESS_TRACE`。
- 有进程或文件访问证据时，用 `evidence_uri` 指向 BUILD_LOG 等 artifact。
- 构建过程中访问到的外部系统头文件（例如 `/usr/include/...`）在比较前过滤，
  不写入本项目实际依赖图。

## 五、声明依赖图

artifact 元数据：

```json
{
  "artifact_id": "artifact-full09-declared-graph",
  "type": "DECLARED_GRAPH",
  "uri": "artifact://pair09/job-full09/declared-graph.json",
  "media_type": "application/json",
  "producer_job_id": "job-full09",
  "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
  "configuration_id": "cc-gcc13-release-6f12a4c8",
  "sha256": "..."
}
```

文件本体使用 schema 中的 `declared_graph`，样例：
`samples/artifact.declared-graph.json`。

要求：

- `commit`、`configuration_id` 与 Job 输入一致。
- 声明信息来自 GNU Make 动态打印的数据库，不是静态解析 Makefile。
- `targets[].target` 与实际图使用相同命名和路径规范化规则。
- `prerequisites[].path` 与实际图使用相同路径规范化规则。
- `makefile_path` 和 `line` 必须能定位声明。
- 某些实际生成的文件可能没有声明；对应 target 仍可保留，只是 prerequisite
  为空数组。

## 六、ERROR_REPORT

artifact 元数据：

```json
{
  "artifact_id": "artifact-full09-error-report",
  "type": "ERROR_REPORT",
  "uri": "artifact://pair09/job-full09/error-report.json",
  "media_type": "application/json",
  "producer_job_id": "job-full09",
  "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
  "configuration_id": "cc-gcc13-release-6f12a4c8",
  "sha256": "..."
}
```

文件本体使用 schema 中的 `error_report`，样例：
`samples/artifact.error-report-body.json`。

要求：

- `counts` 与 `findings` 必须一致。
- `findings[]` 使用公共 finding 结构。
- 每条 finding 必须有位置和证据。
- `output.findings[]` 与 artifact 本体的 `findings[]` 表达同一批结果。
- 不一致时以 ERROR_REPORT artifact 为准，且视为需要人工复核的问题。
- MDFixer 只消费 `type=MISSING`。

## 七、MD/RD 语义

`MISSING`：

- 实际构建访问了依赖。
- Makefile 没有声明该依赖。
- MD 通常不会使 clean build 失败，因为 clean build 会重新执行预处理和编译；
  它主要破坏增量构建的正确性。

`REDUNDANT`：

- Makefile 声明了依赖。
- 当前 `configuration_id` 下的实际构建没有访问该依赖。

`detector`：

- `INSTRUCTOR_ORACLE`：教师提供的人工样本。
- `BUILDCHECKER_DYNAMIC`：BuildChecker 动态检测结果。

实际图来自 ptrace/系统调用跟踪加新文件建模；声明图来自 GNU Make 的内部
数据库输出。外部系统依赖不参与 MD/RD 判定。

## 八、失败路径

- 镜像不可用：`FAILED + ENV_3002`
- 依赖图提取器崩溃：`FAILED + ANALYSIS_5001`
- 产物写出失败：`FAILED + ANALYSIS_5002`
- 超过执行时限：`TIMED_OUT + EXEC_4002`
- 取消：`CANCELLED + error=null + output={}`

`FAILED` / `TIMED_OUT` 时 `output` 必须是 `{}`，禁止交接半成品图或 findings。

## 九、下游交接

### EChecker（A3）

EChecker 可以把本 Job 的 `ACTUAL_GRAPH` 作为后续提交的 baseline。因此实际图
必须自带：

- `commit`
- `configuration_id`
- `project_root`
- 稳定的 target/dependency 标识

### MDFixer（B3）

MDFixer 只消费 `ERROR_REPORT`，并只处理 `type=MISSING` 的记录。因此每条 MD
必须包含可修改的位置和可复核的证据。

## 十、验证

```bash
python tools/validate.py
python -m unittest discover -s tests -v
```

覆盖内容：

- 三份 artifact 本体正例。
- counts 与 findings 不一致负例。
- 缺少 ACTUAL_GRAPH 的负例。
- 非法 observation 负例。
- ERROR_REPORT 本体 counts 不一致负例。
- MD/RD 与两张图的语义对应关系。

## 十一、待 B2 对齐

本文使用以下 A2 期望语义：

```text
clean_command = 只清理
project_root  = 容器内绝对 POSIX 路径
```

FULL_CHECK 请求应直接复用 DRAFT 的 `output.environment` 和 `output.build`。
ADR-007 只有在 DRAFT 样例、schema 和本文件使用同一套语义后才能接受。
