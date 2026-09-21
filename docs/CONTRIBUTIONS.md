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
| `<待填写>` | `<待填写>` | A2 | BuildChecker 接口（读 TSE）：`FULL_CHECK` 请求/响应、依赖图与 MD/RD 报告字段 | B2 |
| `<待填写>` | `<待填写>` | A3 | EChecker 接口（读 ISSTA 2024）：`INCREMENTAL_CHECK` 样例、baseline 匹配规则 | B3 |

## B09 成员与分工

| 成员 | 学号 | 角色 | 主责 | 对接人 |
| --- | --- | --- | --- | --- |
| **李秉轩** | `<待填写>` | **B1** | 公共契约与版本：`CHANGELOG.md`、`versioning.md`、`adr/README.md`、`endpoints.md` 定稿、错误码注册表维护、Issue #1 复核 | A1 |
| **zrh** | `<待填写>` | **B2** | DRAFT 接口（读 ICSE 2026）：`DRAFT` 请求/响应、成功判据与每轮日志字段 | A2 |
| `<待填写>` | `<待填写>` | B3 | MDFixer 接口（读 ASE 2025）：`REPAIR` 样例、patch 与拒绝原因字段 | A3 |

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

- **Commit SHA**：`<本轮交付提交后回填>`
- **作者**：zrh `<3407953470@qq.com>`
- **提交说明**：`b2修改`
- **分支**：`e2b2`

| 工作项 | 文件 | Commit SHA | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- |
| canonical DRAFT 链路 | `interfaces/samples/draft.request.json`、`draft.job-succeeded.json`、`full-check.request.json` | `<回填>` | 待创建 | `environment/build` 可从 DRAFT 直接映射到 FULL_CHECK |
| DRAFT 失败路径 | `interfaces/samples/draft.job-failed.json`、`job.timed-out.json` | `<回填>` | 待创建 | 迭代耗尽、环境失败与超时均有明确状态/错误码 |
| DRAFT 正式 schema 与校验 | `interfaces/task.schema.json`、`tools/validate.py`、`tests/test_validate.py` | `<回填>` | 待创建 | 缺环境/配置/命令/路径均被拒绝，`make check` 通过 |
| DRAFT artifact fixture | `interfaces/artifacts/job-draft09/*` | `<回填>` | 待创建 | 四个产物的大小与 SHA-256 由测试重算 |
| DRAFT/BuildChecker 决策 | `adr/ADR-007-draft-buildchecker-contract.md` | `<回填>` | 待创建 | 已纳入 A2/B2 v0.1 约定，待 A2 在 PR 中接受 |

## 其它分支

| 远端分支 | 提交 | 作者 | 内容 | 状态 |
| --- | --- | --- | --- | --- |
| `origin/e2b2` | `38f66940e26da87a9490532e6f342735dbb20da2` | zrh `<3407953470@qq.com>` | B2 的 DRAFT 请求与响应样例 3 个、ADR-001 | **不要直接合并**，三个样例全部通不过当前校验器。详见 `BACKLOG.md` 第四节 |

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

## 贡献约定

- 公共字段、状态、版本或错误码命名空间的变更，必须在**同一个 PR** 内同步更新：
  `task.schema.json`、`tools/validate.py`（若涉及新约束）、受影响的 `samples/`、
  `tests/`、相应 `ADR`、`docs/BACKLOG.md`。`make check` 不过不予合并。
- 服务专属 `input` / `output` 扩展由服务负责人自行决定，但建议加组前缀
  （`a09_*` / `b09_*`）以避免两组各加同名字段而语义不同（ADR-004）。
- 不得提交凭据、真实访问令牌、未脱敏产物或课程原始材料。
- 每个成员至少一个 Issue + 一个关联 PR + 一条可追溯提交。

## 待补

- [ ] A2、A3 的姓名与学号
- [ ] B09 三位成员的姓名与学号（由 B1 填写）
- [x] 各工作项的 Commit SHA —— `2a9bd2c`
- [x] Issue 编号与 PR 链接 —— Issue #1 / PR #2
- [ ] 三轮课堂交换的结论（第 16 页）落到 ADR 与 BACKLOG
- [ ] PR #2 合并后，把 B1 复核结论回写到各 ADR 的「待 B1 复核」清单
