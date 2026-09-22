# ADR-009: 候选补丁的接受与拒绝判据

**状态**: Proposed
**提议人**: B3
**日期**: 2026-09-22

## Context

MDFixer（B3）收到 A3 的 MD 报告后，需要生成候选补丁并决定是否接受。
E2 阶段需要定义：什么样的补丁可以接受、什么样的补丁必须拒绝，
以及拒绝时如何记录原因，使 A3 和后续“重新验证”环节能够追溯。

第 23 页规定 MDFixer 输出包括“Git Patch 与声明风格说明，
构建、测试、重检结果，失败时拒绝候选并记录原因”。

### A3 已确认的 MD 消费规则

A3 在 PR 交互与 Issue 交互中已确认：

1. `findings` 和 `introduced` 的 `commit` 是 **C1**，与 REPAIR 的
   `repository.commit` 一致。`resolved` 的 `commit` 是 **C0**，
   不进入 MDFixer 输入；MDFixer 只消费 C1 ERROR_REPORT 中仍存在的 `MISSING`。
2. ERROR_REPORT 的 `configuration_id` 同时存在于
   `output.artifacts[]` 的元数据和下载后的报告文件中。
3. `artifact_uri` 指向完整错误报告 JSON，包含 `commit`、`configuration_id`、
   `counts`、`findings`，不是完整 Job、不是裸数组。
4. ERROR_REPORT 不含 `baseline.commit`；C0 SHA 在生产 Job 的
   `input.base_commit` 和 `input.baseline.commit` 中。

### B2 已确认的环境与命令规则

B2 在 Issue 交互中依 ADR-007 已确认：

1. `input.environment` 在 REPAIR 请求中**必填**，含 `image_uri` 与
   `configuration_id`。DRAFT 未产出 environment 时，
   请求在创建期被拒（`VALIDATION_2001`），MDFixer 不使用默认镜像兜底。
2. `configuration_id` 形式为 `cc-<build-profile>-<normalized-config-hash>`，
   下游视为 opaque ID；canonical 值示例 `cc-gcc13-release-6f12a4c8`。
   `cc-MODE0` 为旧值，不作为新契约的格式依据。
3. `image_uri` 使用不可变 OCI/Docker reference，成功交接优先使用 digest。
   MDFixer **原样消费**上游传入的 `image_uri` 与 `configuration_id`，
   不重建、不改写。
4. 三条命令语义互不重叠：
   - `clean_command = make clean`
   - `command = make all`
   - `verify_command = make test`

### 现有样例

`docs/interfaces/samples/repair.request.json` 与
`repair.job-succeeded.json` 由 A1 起草、A2 润色。A1 在 PR #16
中已将这两个文件及 `job.cancelled.json` 的 `environment` / `build` /
`md_report.configuration_id` 统一为 B2 的 canonical 规则；A3 在 PR #8
中完成了 `incremental-check.*` 的迁移。B3 的 REPAIR 样例在 rebase 时
采纳了上述 canonical 值，保证 REPAIR 切片内部一致，不再存在旧值。

## Decision

### 接受判据（全部满足方可接受）

1. **只消费 C1 的 MISSING**：候选补丁对应的 finding 必须是
   `type: "MISSING"`，且其 `commit` 为 C1。
   `REDUNDANT` 和 `resolved`（C0 的历史变化说明）不进入修复流程。

2. **commit 一致**：`md_report.commit` 必须与 `repository.commit`
   完全一致（均为 C1）。不一致则拒绝整份报告，
   reason_code = MD_COMMIT_MISMATCH。

3. **configuration_id 一致**：`md_report.configuration_id` 必须与
   `environment.configuration_id` 完全一致，且均为
   `cc-<build-profile>-<hash>` 形式（ADR-007）。
   不一致或格式错误则拒绝，reason_code = MD_CONFIG_MISMATCH。

4. **补丁可应用**：在 `build.clean_command`（只清理，如 `make clean`）
   执行后的干净工作区上，`git apply --check` 通过。

5. **构建通过**：应用补丁后 `build.command`（如 `make all`）返回 0。

6. **测试通过**：应用补丁后 `build.verify_command`（如 `make test`）返回 0。

7. **重检无新发现**：使用相同 `configuration_id` 重新运行增量检测，
   目标 finding 消失，且不引入新的 `MISSING`。

### environment 缺失的处理

`input.environment` 是 schema 层必填。请求若缺 `environment`，
在**创建期**被拒（`VALIDATION_2001`），不产生 Job，**不进入 MDFixer**。
因此 MDFixer 自身不需要在 output 中处理“无 environment”场景；
`repair.request.json` 的 schema 已强制这一点。

### 关于「configuration_id 必须相等」是否有意禁止换环境修复

判据 3 要求 `md_report.configuration_id == environment.configuration_id`。
这是**有意的**，理由如下：

MDFixer 的修复结果必须在产生 MD 报告的同一构建配置下可复现。
如果允许换环境修复，修复后的验证结果将无法归因于补丁本身——
可能是环境变化导致 MD 消失，而非补丁真正补全了依赖声明。
E2 阶段不允许换环境修复；若 E3 需要支持，应作为独立场景走新的
reason_code（如 `ENV_CHANGED_FOR_REPAIR`）并更新本 ADR，
而非放松本判据。

一个推论：`repair.request.json` 的 `environment` 和 `md_report`
都来自同一个 FULL_CHECK / INCREMENTAL_CHECK 任务，两者的
`configuration_id` 天然一致。判据 3 是把这个隐含事实显式化，
而不是新增限制。

### 拒绝原因码

| reason_code | 含义 | 是否可重试 |
|---|---|---|
| MD_COMMIT_MISMATCH | md_report.commit 与 repository.commit 不一致 | false |
| MD_CONFIG_MISMATCH | md_report.configuration_id 与 environment.configuration_id 不一致或格式错误 | false |
| WRONG_FINDING_TYPE | finding 不是 MISSING，或 commit 不是 C1 | false |
| PATCH_CONFLICT | 补丁无法应用到目标文件 | false |
| BUILD_FAILED_AFTER_PATCH | 应用补丁后构建失败 | false |
| TEST_FAILED_AFTER_PATCH | 应用补丁后测试失败 | false |
| RECHECK_STILL_MISSING | 重检后目标依赖仍然缺失 | false |
| RECHECK_NEW_FINDING | 重检引入了新的 MISSING | false |

### 字段追加（相对现有样例）

`output.rejected_candidates[]` 追加：

- `reason_code`：上表中的一个值
- `finding_id`：回指 `output.findings[]` 中的 finding
- `evidence_uri`：拒绝证据 artifact URI

`output.findings[]` 追加：

- `status`：`FIXED` / `REJECTED` / `NOT_ATTEMPTED`

`PENDING` 曾是候选值，因与 job status 的 `QUEUED` 语义混淆而被排除
（A1 在 Issue #14 提出，B3 采纳）。`NOT_ATTEMPTED` 作为未来备用值，
当前样例未使用。

**不删、不改**现有 `candidate`、`reason`、`id`、`type`、`target`、
`dependency`、`commit`、`detector`、`location`、`evidence`、`message` 字段。

依据第 26 页，新增可选字段属于可兼容变更。按 A1 在 Issue #14 的
确认，`reason_code` 与 `status` 的封闭取值集已同时写入
`task.schema.json` 的 `output_repair` 与 `tools/validate.py` 的
REPAIR 分支（常量从 schema 读取，遵循 ADR-006 的防漂移原则）。
`reason_code` 与 `status` 均为可选字段，既有的
`repair.job-succeeded.json` 无需修改。

### 无候选被接受时的 output 形态

候选全部被拒绝、没有生成有效补丁时：

- `output.patch` **不出现**（不写 null，见 `validate.py` 的 `check_artifact`）
- `output.declaration_style` 写非空字符串说明本次无变更，
  例如 `"本次未生成可接受的补丁，无声明风格变更。"`
- `output.verification.build/test/recheck` 全为 `false`
- `output.rejected_candidates[]` 记录拒绝原因
- `output.findings[]` 记录消费的 finding，`status = "REJECTED"`
- `status = "SUCCEEDED"`，`error = null`

### 状态语义

修复任务正常完成但全部候选被拒绝时，`status` 为 `SUCCEEDED`，
`error` 为 `null`，拒绝原因写入 `output.rejected_candidates[]`。
只有环境不可用、超时、分析器崩溃等系统故障才使用
`FAILED` / `TIMED_OUT` + `job.error`。

这与 `errors.md` 的核心规则一致：MD 是正常分析发现，
不等于工具执行失败；候选被拒也不等于修复服务故障。

## Alternatives

1. **保持散文式 reason，不引入 reason_code**：改动最小，但下游
   “重新验证”环节无法程序化判断“为什么被拒”，只能人工读文本。

2. **把候选被拒当成 FAILED**：实现简单，但与 errors.md 冲突——
   “候选不可接受”不是系统故障，用 FAILED 会误导调用方。

3. **不新增 status，只记录已修复的 finding**：现有 A1 样例走的就是这条路
   （`repair.job-succeeded.json` 的 `findings[0]` 没有 status 字段）。
   代价是被拒绝候选对应的 finding 没有地方记录，
   下游无法回答“哪条 MD 被拒”。B3 选择保留该样例不动（因为它是
   「全部候选被接受」的场景，本来就不需要 REJECTED），只在新样例中
   用 `status` 区分消费状态。

4. **新样例沿用 `cc-MODE0` / `draft:...iter3` 旧值**（已排除）：
   这是 B2 确认 canonical 规则之前的选项。B2 在 Issue 交互中明确
   `cc-MODE0` 不能作为新契约的格式依据；A1 在 PR #16、A3 在 PR #8
   已分别迁移各自负责的样例，`cc-MODE0` 属退役值。
   `tests/test_cross_document_consistency.py` 的
   `TestNoStaleValuesRemain` 会拦下任何新用旧值的样例，
   因此该选项**在当前契约下已不可执行**，记录于此仅供追溯。

## Consequences

- `output.rejected_candidates[]` 追加 `reason_code`、`finding_id`、
  `evidence_uri`；`output.findings[]` 追加 `status`。按 A1 在 Issue #14
  的确认，两个封闭取值集已写入 `task.schema.json` 与 `tools/validate.py`，
  校验器从 schema 读取（ADR-006）。
- REPAIR 切片的 `environment` / `build` / `md_report.configuration_id`
  已在 A1 的 PR #16 中统一为 canonical 规则；A3 在 PR #8 完成
  `incremental-check.*` 的迁移。本 PR 不再涉及旧值清理。
- `repair.job-succeeded-rejected.json` 已在
  `docs/interfaces/samples/README.md` 第一节的用途枚举中登记
  （A1 在 Issue #14 中确认）。
- `VALIDATION.md` 第五节的正例数由本 PR 更新，数量以其与实际文件数
  一致为准（`test_counts_in_validation_md_match_the_files` 断言）。
- 下游“重新验证”环节如何接收 patch 和验证结果，留待 E3/E12。