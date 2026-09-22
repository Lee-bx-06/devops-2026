# 个人贡献与可追溯记录

小组 **A09** ｜ 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0

按第 15 页要求记录：仓库地址、提交 SHA、作者、提交说明、Issue 或 PR。

## 仓库

- 地址：https://github.com/Lee-bx-06/devops-2026
- 分支：`main`
- 起始状态：仓库原有一次提交 `a48d53e`（"first commit"），内容仅 `README.md`。
  本次交付在此之上建立全部目录结构。

## A09 成员与分工

| 成员 | 学号 | 角色 | 主责 | 对接人 |
| --- | --- | --- | --- | --- |
| **谢浩天** | **241250033** | **A1** | 公共契约与集成：`task.schema.json`、`errors.md`、`tools/validate.py`、样例套件、ADR | B1 |
| **殷晓瑞** | `241250014` | A2 | BuildChecker 接口（读 TSE）：`FULL_CHECK` 请求/响应、依赖图与 MD/RD 报告字段 | B2 |
| **朱鸣涛** | `241250048` | A3 | EChecker 接口（读 ISSTA 2024）：`INCREMENTAL_CHECK` 样例、baseline 匹配规则 | B3 |

## B09 成员与分工

| 成员 | 学号 | 角色 | 主责 | 对接人 |
| --- | --- | --- | --- | --- |
| **李秉轩** | `<待填写>` | **B1** | 公共契约与版本：`CHANGELOG.md`、`versioning.md`、`adr/README.md`、`endpoints.md` 定稿、错误码注册表维护、Issue #1 复核 | A1 |
| **zrh** | `<待填写>` | **B2** | DRAFT 接口（读 ICSE 2026）：`DRAFT` 请求/响应、成功判据与每轮日志字段 | A2 |
| **赵心泉** | **241250068** | B3 | MDFixer 接口（读 ASE 2025）：`REPAIR` 样例、patch 与拒绝原因字段 | A3 |

## A1 提交追溯

A1 交付内容集中于一次提交：

- **Commit SHA**：`2a9bd2c3d388245236d33cb76a230b0f4ef48b18`（短 `2a9bd2c`）
- **作者**：谢浩天 `<241250033@smail.nju.edu.cn>`
- **提交说明**：`A1: 建立 A09/B09 公共接口契约与零依赖校验器`
- **父提交**：`a48d53e`（仓库原有的 "first commit"）

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| 公共任务契约 schema | `docs/interfaces/task.schema.json` | `2a9bd2c` | Issue #1 / PR #2 | `make check` 通过；四类 `job_type` 均可表达 |
| 错误与发现双通道 | `docs/interfaces/errors.md` | `2a9bd2c` | Issue #1 / PR #2 | 第 25 页检查 04 有成文答案 + 可执行断言 |
| 零依赖校验器 | `tools/validate.py` | `2a9bd2c` | Issue #1 / PR #2 | 16 正例通过、18 负例按声明原因被拒 |
| 样例套件 | `docs/interfaces/samples/**` | `2a9bd2c` | Issue #1 / PR #2 | 四类请求响应 + 六状态 + 产物记录齐备 |
| 单元测试 | `tests/test_validate.py` | `2a9bd2c` | Issue #1 / PR #2 | 27 项全绿 |
| 设计记录 | `docs/adr/ADR-001..006` | `2a9bd2c` | Issue #1 / PR #2 | 六份，第 13 页四段式 |
| 流程文档 | `docs/BACKLOG.md`、`docs/AI_USAGE.md`、`docs/VALIDATION.md` | `2a9bd2c` | Issue #1 / PR #2 | 第 12、14 页格式 |
| 端点草案（B1 负责） | `docs/interfaces/endpoints.md` | `2a9bd2c` | Issue #1 / PR #2 | A1 起草，明确标注待 B1 定稿 |

> 回填 SHA 与 Issue/PR 号本身构成追加提交，故上表 SHA 指向**交付内容所在的那次提交**
> （`2a9bd2c`），不是回填提交。

## A1 第二轮：PR #2 合并后的复核

- **Commit SHA**：`73cc5b693e6b6d4529c630f3c1b7b44139aac431`（短 `73cc5b6`）
- **作者**：谢浩天 `<241250033@smail.nju.edu.cn>`
- **提交说明**：`A1: 复核合并后的契约，修三处不一致并形式化 B1 的迁移规则`
- **分支**：`a1-review-round2`
- **起因**：PR #2 合并后拉取 main，复核 B1（`bcf217e` 等）与 B2（`d05ee38`、`e04364f`）
  的改动是否与 A1 的契约一致

| 工作项 | 文件 | 类型 |
| --- | --- | --- |
| `job.error.code` 排除 `VALIDATION_2xxx` | `task.schema.json`、`tools/validate.py`、`tests/`、`samples/invalid/validation-code-in-job-error.json`、`errors.md` 补记 | 修正 A1 自己的疏漏 |
| 状态迁移规则形式化为 `execution` 计时约束 | `task.schema.json`（`status_matrix`）、`tools/validate.py`（`check_transition_timing`）、`tests/…TestTransitionTiming` | 落实 B1 的规则并解开其表内冲突 |
| 补 `output_draft.environment` | `task.schema.json`、`samples/draft.job-succeeded.json`、`tools/validate.py` | 采纳 B2 的字段，修 A1 断掉的交接链 |
| ADR-010（含对 ADR-005 判据的修正） | `docs/adr/ADR-010-…md`、`docs/adr/README.md` 索引 | 新建，不修改 ADR-005 原文 |
| 更正 `e2b2` 合并前置条件已失效 | `docs/BACKLOG.md` 第四节 | 附六行证据表，保留原文取回路径 |
| 样例命名规范与 DRAFT 重复样例处理方案 | `docs/interfaces/samples/README.md` | 未擅自改名 B2 文件，列出请 B2 做的三件事 |
| 变更记录与文档同步 | `docs/CHANGELOG.md`、`docs/VALIDATION.md`、`README.md`、`docs/AI_USAGE.md` 条目 13–16 | —— |

验证：`make check` 全绿，测试由 27 项增至 41 项（正例 19、负例 19）。

本轮三处问题**都不会让 `make check` 变红**——校验全绿不等于契约自洽。
教训已记入 `AI_USAGE.md` A1 第二轮汇总。

## B1 提交追溯

B1 的工作分两段。第一段是独立起草公共契约，第二段是审查 A1 版本并接管版本与兼容性。

### 第一段：B1 首版独立契约

- **Commit SHA**：`bbf818a5378ff4403602c2aec81cfccefa828035`（短 `bbf818a`）
- **作者**：李秉轩
- **提交说明**：`B1 work`
- **内容**：19 个文件，位于 `e2-pair09/`，含统一任务模型、端点契约、状态机与错误码、两篇 ADR、版本规则、变更记录

该版本与 A1 在 PR #2 中提交的 `docs/` 重复。按第 12 页「统一任务模型」责任方为 A/B 共同，
公共部分只能有一份，因此 B1 转为复核方，`e2-pair09/` 已移除，避免仓库里存在两套契约定义。
原文可通过 `git show bbf818a` 取回，其独有内容已并入 `docs/`。

### 第二段：B1 复核与版本维护

- **Commit SHA**：`bcf217e5f808325113546f9340d60a23f325cb5a`
- **作者**：李秉轩
- **提交说明**：`docs(B1): 复核 Issue #1 七项、定稿端点、补齐版本与变更记录`
- **关联**：Issue #1

对应 Issue #1 第二节的七项待确认，逐条结论见 `CHANGELOG.md` 的 1.0.0 条目。

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| 逐条复核 Issue #1 的七项待确认 | `CHANGELOG.md` | `bcf217e5f808325113546f9340d60a23f325cb5a` | Issue #1 | 七项均有结论与理由，落点文件明确 |
| 端点定稿 | `interfaces/endpoints.md` 第五节 | `bcf217e5f808325113546f9340d60a23f325cb5a` | Issue #1 | 四个待确认项有结论；补入第 5 页交接验收清单 |
| 错误码注册表边界与维护权 | `interfaces/errors.md` | `bcf217e5f808325113546f9340d60a23f325cb5a` | Issue #1 | 限定 `VALIDATION_2xxx` 只出现在 HTTP 4xx，不进 `job.error` |
| 版本与兼容性规则 | `versioning.md` | `bcf217e5f808325113546f9340d60a23f325cb5a` | —— | 三段式版本号，与校验器的 schema_version 模式一致 |
| 契约变更记录 | `CHANGELOG.md` | `bcf217e5f808325113546f9340d60a23f325cb5a` | —— | 补上第 26 页要求但原先缺失的变更记录 |
| ADR 索引与模板 | `adr/README.md`、`adr/ADR-000-template.md` | `bcf217e5f808325113546f9340d60a23f325cb5a` | —— | 六篇 ADR 入索引；发现 B2 分支 ADR 编号冲突 |
| 配对组编号修正 | `README.md`、`docs/` 共 8 个文件 | `bcf217e5f808325113546f9340d60a23f325cb5a` | —— | 「配对组 B09」改为「配对组 第 9 组（pair09）」 |
| 消除重复契约 | 移除 `e2-pair09/` | `bcf217e5f808325113546f9340d60a23f325cb5a` | —— | 公共契约只剩 `docs/` 一处定义 |

### 关于回填

本节的 SHA 在提交 `bcf217e` 之后回填，回填动作本身构成一次追加提交。
沿用 A1 的做法：表内 SHA 指向**交付内容所在的那次提交**，不是回填提交本身。

## B2 提交追溯

- **Commit SHA**：`a587263bd82b88526769732004540c7766bd75b1`
- **作者**：zrh `<3407953470@qq.com>`
- **提交说明**：`b2修改`
- **分支**：`e2b2`

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| canonical DRAFT 链路 | `interfaces/samples/draft.request.json`、`draft.job-succeeded.json`、`full-check.request.json` | `a587263` | Issue #4 / PR #5 | `environment/build` 可从 DRAFT 直接映射到 FULL_CHECK |
| DRAFT 失败路径 | `interfaces/samples/draft.job-failed.json`、`job.timed-out.json` | `a587263` | Issue #4 / PR #5 | 迭代耗尽、环境失败与超时均有明确状态/错误码 |
| DRAFT 正式 schema 与校验 | `interfaces/task.schema.json`、`tools/validate.py`、`tests/test_validate.py` | `a587263` | Issue #4 / PR #5 | 缺环境/配置/命令/路径均被拒绝，`make check` 通过 |
| DRAFT artifact fixture | `interfaces/artifacts/job-draft09/*` | `a587263` | Issue #4 / PR #5 | 四个产物的大小与 SHA-256 由测试重算 |
| DRAFT/BuildChecker 决策 | `adr/ADR-007-draft-buildchecker-contract.md` | `a587263` | Issue #4 / PR #5 | 已纳入 A2/B2 v0.1 约定，待 A2 在 PR 中接受 |

## A2 提交追溯

- **作者**：殷晓瑞（Git 作者 `Inxerph`）
- **学号**：`241250014`
- **分支**：`a2-full-check-contract`
- **Commit SHA**：`74c69d2`（合并 B2 的 `324a32e` 后的提交，对应 PR #6）；
  内容提交为 `26bda5c`（TSE 语义复核）与 `1c38393`（首个内容提交）

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| FULL_CHECK 接口契约 | `interfaces/buildchecker-contract.md` | `1c38393` | PR #6 | 请求/输出、MD/RD、失败路径和下游交接已定义 |
| artifact 本体 schema | `interfaces/task.schema.json` | `1c38393` | PR #6 | `actual_graph` / `declared_graph` / `error_report` 均有必填约束 |
| BuildChecker ADR | `adr/ADR-011-buildchecker-output-contract.md` | `1c38393` | PR #6 | 第 13 页四段式，记录本体与一致性决策；与 A1 的 ADR-010 撞号后改号为 011 |
| artifact 正例 | `interfaces/samples/artifact.*.json` | `1c38393` | PR #6 | 三份本体通过校验 |
| FULL_CHECK 边界样例 | `interfaces/samples/full-check.clean-project.json`、`samples/invalid/…` | `1c38393` | PR #6 | 零发现正例与五项负例通过校验 |
| A2 测试 | `tests/test_buildchecker_contract.py` | `1c38393` | PR #6 | A2 分支上 35 项全绿；合并 B2 的改动后整体 56 项全绿 |
| TSE 语义复核 | `interfaces/buildchecker-contract.md`、`task.schema.json`、相关样例 | `26bda5c` | PR #6 | 隐式目标、GNU Make 动态数据库、外部依赖过滤和 MD 不导致 clean build 失败均已写入契约 |
| 复核 B2 的 DRAFT 交接 | `interfaces/samples/draft.job-succeeded.json`、`adr/ADR-007-…md`、`adr/README.md` | `74c69d2` | PR #6 | 五项待确认全部满足，`ADR-007` 改为 `Accepted`；按 blob 实际字节改正 Dockerfile 制品的 `size_bytes` / `sha256` |

## A3 提交追溯

- **Git 作者**：`zhumingtao <2830849787@qq.com>`
- **正式姓名 / 学号**：朱鸣涛 / `241250048`
- **分支**：`a3-echecker-contract`
- **内容提交**：`f8a7fe9`（可执行契约）
- **设计记录提交**：`e86ad0e`（BACKLOG / CHANGELOG / ADR-010 同步）
- **环境一致性收尾提交**：`a45c3b7`
- **跨平台 artifact 完整性修复提交**：`703aca5`
- **关联 Issue**：[#7](https://github.com/Lee-bx-06/devops-2026/issues/7)
- **缺陷 Issue**：[#19](https://github.com/Lee-bx-06/devops-2026/issues/19)
- **PR**：[#8](https://github.com/Lee-bx-06/devops-2026/pull/8)（已合并）
- **合并提交**：`f1d3dbb`

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| EChecker 接口契约 | `interfaces/echecker-contract.md` | `f8a7fe9` | Issue #7 / PR #8 | C0/C1、基线匹配、差集和 B3 交接均已定义 |
| baseline 与增量输出 schema | `interfaces/task.schema.json`、`tools/validate.py` | `f8a7fe9` | Issue #7 / PR #8 | 缺历史报告、错误集合关系和不可消费更新图均被拒绝 |
| 请求、成功与失败样例 | `interfaces/samples/incremental-check.*.json`、`job.baseline-mismatch-failed.json` | `f8a7fe9`、`a45c3b7` | Issue #7 / PR #8 | 创建期与运行期失败边界可表达，环境配置已与 canonical DRAFT 对齐 |
| C1 artifact 本体 | `artifact.incremental-actual-graph.json`、`artifact.incremental-error-report-body.json` | `f8a7fe9` | Issue #7 / PR #8 | 元数据、大小和 SHA-256 由测试重算 |
| EChecker ADR | `adr/ADR-008-incremental-baseline-and-finding-diff.md` | `f8a7fe9` | Issue #7 / PR #8 | 记录历史报告、finding 身份、祖先关系和无基线策略；B3/B1 已接受 |
| 项目状态同步 | `BACKLOG.md`、`CHANGELOG.md`、`adr/ADR-010-…md` | `e86ad0e` | Issue #7 / PR #8 | A3 状态、上游消费结论和新增基线字段均已登记 |
| A3 专项测试 | `tests/test_echecker_contract.py` | `f8a7fe9` | Issue #7 / PR #8 | 12 项专项测试通过；全仓测试结果以实际运行为准 |
| 跨平台 artifact 完整性校验 | `.gitattributes`、`tests/test_echecker_contract.py`、`interfaces/echecker-contract.md` | `703aca5` | Issue #19 | 固定两份 artifact 为 LF，并按 UTF-8/LF 规范字节校验大小与 SHA-256，避免 Windows CRLF 造成误报 |

## B3 提交追溯

- **作者**：赵心泉（Git 作者 `Varecia`）
- **学号**：241250068
- **分支**：`b3-repair-contract`（已合并）
- **内容提交**：`feadb30`
- **PR 合并提交**：`877e7c4`
- **关联 Issue**：[#14](https://github.com/Lee-bx-06/devops-2026/issues/14)（B3 追踪）
- **PR**：[#20](https://github.com/Lee-bx-06/devops-2026/pull/20)（已合并）
- **协作 Issue**：[#19](https://github.com/Lee-bx-06/devops-2026/issues/19)（Windows CRLF 报告）

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| REPAIR 候选被拒样例 | `interfaces/samples/repair.job-succeeded-rejected.json` | `feadb30` | Issue #14 / PR #20 | `errors_of == []`，正例通过 |
| MDFixer 决策记录 | `adr/ADR-009-patch-acceptance-criteria.md` | `feadb30` | Issue #14 / PR #20 | 7 条接受判据、8 个拒绝原因码、3+1 字段追加；回答 A1 的 `configuration_id` 语义问题 |
| schema 与校验器联动 | `interfaces/task.schema.json`、`tools/validate.py` | `feadb30` | Issue #14 / PR #20 | 两个封闭 enum 从 schema 读取；REPAIR 分支新增两条取值校验 |
| 样例命名规范登记 | `interfaces/samples/README.md` | `feadb30` | Issue #14 / PR #20 | 用途枚举登记 `job-succeeded-rejected` |
| 文档同步 | `VALIDATION.md`、`adr/README.md` | `feadb30` | Issue #14 / PR #20 | `test_counts_in_validation_md_match_the_files` 通过 |
| CRLF 遗留报告与验证 | Issue #19；A3 的 `a3-fix-artifact-line-endings` | `182de4d`（合并） | Issue #19 / PR #21 | Windows `make check` 由红转绿 |

## 其它分支

| 远端分支 | 提交 | 作者 | 内容 | 状态 |
| --- | --- | --- | --- | --- |
| `origin/e2b2` | `e04364fe606376c9b9d7e790a9ed2301188795f7` | zrh `<3407953470@qq.com>` | B2 的 DRAFT 请求与响应样例、ADR-007 | 已与 `main` 同步；ADR-007 仍为 Proposed，待 A2 最终验收 |

## 协作方式：fork + PR

A1 对上游仓库没有直接推送权限，因此按第 15 页「Issue 或 PR」的要求走 fork 流程：

| 远端 | 地址 | 用途 |
| --- | --- | --- |
| `origin` | https://github.com/Lee-bx-06/devops-2026 | 小组共享仓库（上游），PR 的目标 |
| `fork` | https://github.com/mcjiansheng/devops-2026 | A1 的 fork，推送工作分支 |

- 工作分支：`a1-public-contract`
- Issue：https://github.com/Lee-bx-06/devops-2026/issues/1
  （列出待 B1 与 A2/A3/B2/B3 确认的 11 项）
- PR：https://github.com/Lee-bx-06/devops-2026/pull/2

推送与开 PR 的命令：

```bash
git push -u fork a1-public-contract
gh pr create --repo Lee-bx-06/devops-2026 --base main --head mcjiansheng:a1-public-contract
```

其他成员请照此模式：各自的分支推到各自的 fork，向上游开 PR，
**不要**直接推 `main`——公共契约的变更必须经 PR 复核（ADR-004）。

## 验证记录

```
$ python3 tools/validate.py
A09/B09 公共契约校验通过：四类请求与响应、六种状态、artifact 记录与全部负例均符合 task.schema.json。

$ python3 -m unittest discover -s tests -v
Ran 27 tests in 0.008s
OK
```

环境：Python 3.14.6 / macOS (arm64) / 无第三方依赖。

### A2 本轮本地验证

```text
$ python tools/validate.py
A09/B09 公共契约校验通过：四类请求与响应、六种状态、artifact 元数据/本体
与全部负例均符合 task.schema.json。

$ python -m unittest discover -s tests
Ran 56 tests
OK
```

## B3 提交追溯

- **作者**：赵心泉（Git 作者 `Varecia`）
- **学号**：241250068
- **分支**：`b3-repair-contract`

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| REPAIR 候选被拒样例 | `interfaces/samples/repair.job-succeeded-rejected.json` | `<SHA>` | `<PR 号>` | `errors_of == []`，`make check` 全绿 |
| MDFixer 决策记录 | `adr/ADR-009-patch-acceptance-criteria.md` | `<SHA>` | `<PR 号>` | 接受判据与拒绝原因码覆盖第 23 页要求 |
| 文档同步 | `BACKLOG.md`、`VALIDATION.md`、`adr/README.md`、`CHANGELOG.md`、`AI_USAGE.md` | `<SHA>` | `<PR 号>` | `test_counts_in_validation_md_match_the_files` 通过 |

## 贡献约定

- 公共字段、状态、版本或错误码命名空间的变更，必须在**同一个 PR** 内同步更新：
  `task.schema.json`、`tools/validate.py`（若涉及新约束）、受影响的 `samples/`、
  `tests/`、相应 `ADR`、`docs/BACKLOG.md`。`make check` 不过不予合并。
- 服务专属 `input` / `output` 扩展由服务负责人自行决定，但建议加组前缀
  （`a09_*` / `b09_*`）以避免两组各加同名字段而语义不同（ADR-004）。
- 不得提交凭据、真实访问令牌、未脱敏产物或课程原始材料。
- 每个成员至少一个 Issue + 一个关联 PR + 一条可追溯提交。

## 待补

- [x] A3 的正式姓名与学号（朱鸣涛 / `241250048`）
- [ ] B09 三位成员的姓名与学号（由 B1 填写）
- [x] 各工作项的 Commit SHA —— `2a9bd2c`
- [x] Issue 编号与 PR 链接 —— Issue #1 / PR #2
- [ ] 三轮课堂交换的结论（第 16 页）落到 ADR 与 BACKLOG
- [ ] PR #2 合并后，把 B1 复核结论回写到各 ADR 的「待 B1 复核」清单
