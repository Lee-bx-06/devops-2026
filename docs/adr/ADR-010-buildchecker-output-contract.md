# ADR-010：BuildChecker 输出与 artifact 本体契约

- 状态：**Proposed**（A2 起草，待 A3、B3 和 B1 复核）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 9、10、21、22、23、24 页；`task.schema.json`、`buildchecker-contract.md`

## Context

公共契约已经定义了 Job 输出中的 `counts`、`findings` 和 `artifacts[]`，也定义了
artifact 元数据。但实际依赖图、声明依赖图和 ERROR_REPORT 的文件本体没有定义。

这会导致两个下游问题：

- A3 的 EChecker 无法按固定格式读取 baseline 实际图。
- B3 的 MDFixer 无法按固定格式读取 MISSING 报告。

只在 Job 响应里内联 findings 不足以解决这个问题，因为大图和大报告通过
`artifact://` 交接。

## Decision

### 1. 在公共 schema 中定义三种 artifact 本体

新增：

- `actual_graph`
- `declared_graph`
- `error_report`

三者都带 `schema_version`、`commit` 和 `configuration_id`，保证产物可追溯到
固定提交与固定构建配置。

### 2. 实际图和声明图使用同一套节点、边标识

- target 使用 Makefile target 名。
- dependency/prerequisite 使用相对 `project_root` 的 POSIX 路径。
- 实际图记录 observation 和可选证据 URI。
- 声明图记录 Makefile 路径和行号。

### 3. FULL_CHECK 成功响应强制三份核心 artifact

`SUCCEEDED` 的 `output.artifacts[]` 必须包含：

```text
ACTUAL_GRAPH
DECLARED_GRAPH
ERROR_REPORT
```

零发现时仍返回三份 artifact，ERROR_REPORT 的 findings 为空数组。

### 4. counts 与 findings 必须一致

`counts.missing` 等于 MISSING findings 数，`counts.redundant` 等于 REDUNDANT
findings 数。Job 内联 findings 和 ERROR_REPORT 本体应表达同一批结果。

### 5. MD 是正常分析结果

检出 MD/RD 时 Job 仍是 `SUCCEEDED`，`error=null`。只有环境、执行或分析器失败
才进入 `FAILED` / `TIMED_OUT`。

## Alternatives

### 只定义 artifact 元数据，不定义文件本体

无法满足第 10、22、23 页的跨组消费要求。EChecker 和 MDFixer 会各自猜测字段。
否决。

### 让每个下游服务自行定义图格式

会造成 A2 产出的图无法被 A3/B3 稳定读取，也无法比较实际图和声明图。否决。

### 把完整图内联到 Job 响应

图可能有几十 KB 到数 MB，违反第 6 页“大日志不必塞进每个响应”的要求。否决。

### 允许 counts 与 findings 不一致

下游无法判断报告是否完整或是否被截断。否决。

## Consequences

**得到的：**

- EChecker 可以按固定格式使用历史实际图。
- MDFixer 可以按固定格式消费 MISSING 报告。
- 图的提交、配置、路径和证据均可追溯。
- counts、findings 和 artifact 之间的关系可自动检查。

**付出的：**

- 生产方必须执行稳定的路径规范化。
- 两份图必须使用相同 target/path 标识，否则 MD/RD 计算不可靠。
- artifact 本体变更需要按版本与兼容性规则处理。

**验证：**

- `samples/artifact.actual-graph.json`
- `samples/artifact.declared-graph.json`
- `samples/artifact.error-report-body.json`
- `samples/invalid/full-check-counts-mismatch.json`
- `samples/invalid/full-check-missing-graph-artifact.json`
- `samples/invalid/artifact.actual-graph-bad-observation.json`
- `samples/invalid/artifact.error-report-counts-mismatch.json`
- `samples/invalid/artifact.actual-graph-relative-root.json`
- `tests/test_buildchecker_contract.py`

## 待复核

- A3：历史实际图还需要哪些字段才能作为 baseline。
- B3：MDFixer 消费 ERROR_REPORT 时是否需要额外字段。
- B1：新增三种 artifact 本体是否按 MINOR 还是保持 1.0.0 冻结前补齐。
- B2：DRAFT 输出的 `environment` / `build` 必须与 FULL_CHECK 输入使用同一语义。
