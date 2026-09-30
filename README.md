# devops-2026 · E2 接口契约与 E3 测试基线（A09 ↔ B09）

小组 **A09** ｜ 配对组 第 9 组（pair09） ｜ 契约版本 **1.0.0**
A1 负责人：**谢浩天（241250033）** ｜ B1 负责人：**李秉轩**

仓库保留 E2 的**接口契约与设计文件**，并增加 E3 的 A1 参考基线与实测证据。
按第 7 页，E2 只定义契约、不要求部署 API；因此 E2 部分只有 schema、样例、校验器与设计记录，
不包含可运行服务。E3 部分是 A1 准备的参考样例，不等同于四个服务的实现或验收。

E3 的 A1 共享测试基线见 [e3/README.md](e3/README.md)：包含 MD/RD 小项目、
C0/C1/C2 真实实验提交、构建行为对照和可复跑证据。这是样例阶段的输入与实测，
不代表 BuildChecker、EChecker、DRAFT 或 MDFixer 服务已实现；服务实现与联调属于后续阶段。
E2 的公共契约版本仍为 1.0.0，E2 本身不部署 API。

## 一、E2 契约范围与 E3 基线范围

E2 的交付范围是 A09 ↔ B09 公共接口契约和设计文档。E3 当前记录 A1 参考基线、
样例运行观察与可复核证据；服务实现和联调属于后续阶段。

### E2 课堂任务（第 2 页）

1. 找到同号配对组 → A09 ↔ B09
2. 约定微服务之间怎样传数据 → `docs/interfaces/`
3. 留下设计文件和个人贡献 → `docs/adr/`、`docs/CHANGELOG.md`、`docs/versioning.md`、`docs/BACKLOG.md`、`docs/AI_USAGE.md`、`docs/CONTRIBUTIONS.md`

## 一之二、文档地图

| 想知道什么 | 看哪里 |
| --- | --- |
| 字段叫什么、必填哪些 | `docs/interfaces/task.schema.json` |
| 端点怎么调、产物怎么读 | `docs/interfaces/endpoints.md` |
| 为什么 MD 不算失败、错误码有哪些 | `docs/interfaces/errors.md` |
| 为什么这样定，考虑过哪些替代方案 | `docs/adr/`，索引见 `docs/adr/README.md` |
| 什么改动安全、什么改动会破坏兼容 | `docs/versioning.md` |
| 改过什么、谁受影响 | `docs/CHANGELOG.md` |
| 还没做完的 | `docs/BACKLOG.md` |
| 谁做了什么 | `docs/CONTRIBUTIONS.md` |
| E3 基线怎么运行、输出如何复现 | [e3/README.md](e3/README.md) |
| E3 已验证范围与责任边界 | [e3/STATUS.md](e3/STATUS.md) |
| E3 主项目提交与发布验证 | [e3/PUBLICATION.md](e3/PUBLICATION.md) |
| E3 仍需协作确认的配置事项 | [e3/COORDINATION.md](e3/COORDINATION.md) |

## 二、四个服务与归属（第 3、4 页）

| 组 | 服务 | 职责 | 交付给谁 | 接口负责人 | 参考论文 |
| --- | --- | --- | --- | --- | --- |
| A | BuildChecker | 全量依赖检测 | EChecker / MDFixer | A2 | TSE |
| A | EChecker | 跨提交增量检测 | MDFixer | A3 | ISSTA 2024 |
| B | DRAFT | 生成可构建环境 | 三个下游服务 | B2 | ICSE 2026 |
| B | MDFixer | 修复缺失依赖 | 重新构建与检测 | B3 | ASE 2025 |
| A/B | **公共契约** | 统一任务模型、错误通道、产物约定 | 全部四个服务 | **A1 ↔ B1** | 跨四篇 |

协作链（第 4 页）：DRAFT → BuildChecker → EChecker → MDFixer → 重新验证。

## 三、快速开始

```bash
make check          # 校验全部样例 + 跑单元测试，零第三方依赖
make validate       # 只校验样例
make test           # 只跑测试
```

单文件校验（联调时校验对方给的文件）：

```bash
python3 tools/validate.py path/to/their-file.json
```

环境：Python 3 标准库即可，实测于 Python 3.14.6。**不需要 `pip install`**
（这是刻意的取舍，见 `docs/adr/ADR-006`）。

E3 基线运行需要 Python 3、Git、GNU Make 和 C 编译器：

```bash
python3 e3/scripts/run_baseline.py
```

默认新建 `e3/work/run-*` 目录。实测平台与版本、输出证据和恢复命令见
[E3 运行说明](e3/README.md) 与 [E3 状态](e3/STATUS.md)。

## 四、第 25 页四条最小检查

| # | 检查 | 怎么验 |
| --- | --- | --- |
| 01 | 四类请求与响应 | `python3 tools/validate.py`（内建覆盖度检查，缺一类即失败） |
| 02 | `job_type` 改成 `ABC` 应被拒 | `docs/interfaces/samples/invalid/invalid-job-type.json` |
| 03 | 删掉增量任务的 `baseline` 应被拒 | `docs/interfaces/samples/invalid/missing-baseline.json` |
| 04 | 解释 MD 为什么不等于工具执行失败 | `docs/interfaces/errors.md` 第一节（文字）+ `tests/…Check04…`（代码） |

## 五、仓库结构与负责人

```
docs/interfaces/
  task.schema.json          A1 ★ 公共契约，唯一权威定义（含 B2 的 DRAFT 输出与 A2 的 artifact 本体）
  buildchecker-contract.md  A2 ★ FULL_CHECK 请求/输出与依赖图契约
  echecker-contract.md      A3   INCREMENTAL_CHECK 基线、差集与下游交接契约
  errors.md                 A1 ★ 两条错误通道 + 错误码注册表（注册表由 B1 维护）
  endpoints.md              B1   五端点 + 状态迁移表（A1 起草，B1 已定稿）
  samples/README.md         A1   命名规范与 DRAFT 重复样例的处理方案
  samples/                  A1 / A2 / A3 / B2 / B3  25 个正例（四类请求响应 + 六种状态 + 产物记录 + 六份 artifact 本体 + REPAIR 候选被拒样例 + QUEUED→FAILED 正例）
  samples/invalid/          A1 / A2 / B2  24 个负例，每个声明期望的拒绝原因
docs/adr/
  README.md                 B1   ADR 索引与编号规则
  ADR-000-template.md       B1   模板
  ADR-001  异步 Job 模型与公共信封            A1
  ADR-002  错误与发现双通道分离                A1
  ADR-003  artifact 命名空间与解析约定         A1（B1 已确认解析端点）
  ADR-004  兼容性策略：信封严格、载荷可扩展     A1（B1 已确认）
  ADR-005  创建期拒绝 vs 运行期失败            A1（判据表述由 ADR-010 修正）
  ADR-006  零依赖校验器                       A1
  ADR-007  DRAFT 与 BuildChecker 环境交接      B2   Accepted
  ADR-008  EChecker 基线与 finding 差集         A3   Accepted，PR #8 已合并
  ADR-009  MDFixer 候选补丁接受与拒绝判据       B3   Accepted，PR #20 已合并
  ADR-010  状态迁移形式化 + 基线一致性归属      A1   Accepted，B1 于 2026-09-22 评审通过
  ADR-011  BuildChecker 输出与 artifact 本体  A2   Proposed，待 A3/B3/B2 本人在 Issue #1 确认，再由 B1 更新状态
e3/
  README.md                 A1   基线运行、环境要求、证据恢复方法
  STATUS.md                 A1   已验证范围、真实提交 SHA、未验证范围
  PUBLICATION.md            A1   E3 内容提交、发布前验证与个人贡献
  COORDINATION.md           A1   A3/B2/A2 对 configuration_id 的待对齐事项
  scripts/run_baseline.py   A1   可重复运行的 MD/RD 与提交版本基线
  fixtures/md-rd/           A1   MD/RD 行为样例
  evidence/                 A1   实测命令、日志、manifest、oracle 与 Git bundles
docs/BACKLOG.md             A1   第 12 页四项 + 待对方确认清单 + 未完成项
docs/AI_USAGE.md            A1/B1/B2/A2/A3/B3  第 14 页格式，真实判断记录
docs/CONTRIBUTIONS.md       A1/B1/B2/A2/A3/B3  作者、提交 SHA、Issue/PR
docs/VALIDATION.md          A1   校验了什么、**没**校验什么
docs/versioning.md          B1   版本规则、变更流程、消费者清单
docs/CHANGELOG.md           B1   契约变更记录与待处理表
tools/validate.py           A1 ★ 零依赖校验器
tests/test_validate.py      A1/B2   公共契约与 A2–B2 环境交接测试
tests/test_buildchecker_contract.py A2 FULL_CHECK 与 artifact 本体测试
tests/test_echecker_contract.py A3 INCREMENTAL_CHECK 基线、差集与 artifact 测试

tests/test_cross_document_consistency.py A1 跨文档一致性守卫（交接链两端逐字一致）
（`make check` 运行 `tests/` 下全部测试。此处**不写测试总数**：每人加测试都会让它过时，
且多份 PR 会在同一行冲突。数量以实际运行为准；样例数量的唯一来源是
`docs/VALIDATION.md` 第五节，由 `TestDocsDoNotRot` 断言其与文件数一致。）
```

★ = A1 核心交付物。

## 六、契约速览

**六种文档**（由必填的 `kind` 判别，互斥；前三类是 Job 封套，后三类是 artifact 本体）：

| `kind` | 用途 | `job_id` / `status` |
| --- | --- | --- |
| `create_request` | POST 请求体，含 `idempotency_key` | 无（服务端产生） |
| `job` | 受理响应与查询响应 | 有 |
| `actual_graph` | 实际依赖图文件本体 | 无 |
| `declared_graph` | 声明依赖图文件本体 | 无 |
| `error_report` | MD/RD 报告文件本体 | 无 |
| `artifact_record` | 第 24 页产物记录 | 无 |

**九个公共字段**（第 19 页）：`schema_version`、`job_id`、`trace_id`、`job_type`、
`status`、`execution`、`input`、`output`、`error`。

**六个状态**（第 8 页）：`QUEUED` / `RUNNING` / `SUCCEEDED` / `FAILED` /
`TIMED_OUT` / `CANCELLED`。

**最重要的一条规则**（第 8、9 页）：
**检出缺失依赖（MD）是分析成功，不是执行失败。**
MD 写进 `output.findings`，状态是 `SUCCEEDED`，`error` 为 `null`；
只有环境/执行/分析器故障才写 `job.error`，此时 `output` 必须为空。
详见 `docs/interfaces/errors.md` 第一节。

## 七、边界声明

- E2 契约样例中的 URI、sha256、commit、镜像名、时间戳通常是**说明性值**，
  不代表服务产物。例外是 canonical DRAFT 与两份 A3 仓库内 artifact fixture 的真实字节哈希，
  以及 E3 文档明确标出的真实实验提交 SHA、命令、日志和时间戳。E3 的人工 oracle
  仍是课程材料派生的预期答案，不是检测器输出；细节见 `e3/STATUS.md` 和 `docs/VALIDATION.md`。
- 本仓库**不宣称**任何服务已实现或已部署，也**不宣称**完成服务验收。B1 已完成其公共契约复核；
  ADR-011 消费侧内容虽由相关 PR 落实，仍待 A3/B3/B2 本人在 Issue #1 明确确认，随后由 B1 更新状态。
  其余待办集中在 `docs/BACKLOG.md`。
- `input` / `output` 内部字段依第 20–23 页拟定，属服务负责人
  （A2/A3/B2/B3）的确认范围；顶层信封由 A1 冻结。
  这条分界线的理由见 `docs/adr/ADR-004`。

## 八、给 B09 同学

想确认我们理解是否一致，最快的方式是读这三份文件：

1. `docs/interfaces/errors.md` 第一节 —— MD 为什么不等于执行失败
2. `docs/interfaces/samples/full-check.job-succeeded.json` —— 一次「成功检出 MD」长什么样
3. `docs/interfaces/samples/job.baseline-mismatch-failed.json` —— 一次「合法失败」长什么样

然后拿你们自己的文件跑 `python3 tools/validate.py 你们的文件.json`。
需要加字段时先看 `docs/adr/ADR-004`：**加在 `input`/`output` 里你们自己决定，
加在顶层信封里需要 ADR + 升版本。**
