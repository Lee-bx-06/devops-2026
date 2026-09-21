# BACKLOG —— A09 / B09 接口契约

小组 A09 ｜ 配对组 第 9 组（pair09） ｜ 契约版本 1.0.0 ｜ 本文件由 A1（谢浩天）维护

按第 12 页「把需求写成可验收任务」的格式：每项有任务、责任方、产物、验收条件。
第 15 页要求收尾时逐条标注已完成/未完成 + 原因 + 下一步，故本表带状态列。

图例：✅ 已完成并验证 ｜ 🟡 A1 侧完成，待对方确认 ｜ ⬜ 未开始

## 一、第 12 页给定的四项

| # | 状态 | 任务 | 责任方 | 产物 | 验收条件 | 验证方式 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ✅ | 统一任务模型 | A/B 共同（A1 主笔） | `docs/interfaces/task.schema.json` | 四类对象可表达 | `tests/…Check01FourJobTypes` 断言四类请求/响应均通过；`make check` |
| 2 | ✅ | 历史图输入 | A（A1 定形状，A3 定语义） | `samples/incremental-check.{request,job-succeeded}.json` | 缺 baseline 被拒绝 | `samples/invalid/missing-baseline.json` + `tests/…Check03MissingBaseline` 四种变异全被拒 |
| 3 | ✅ | 修复报告输入 | B（A1 定形状，B3 定语义） | `samples/repair.{request,job-succeeded}.json` | 只消费 MD | `md_report.type` 必须为 `ERROR_REPORT`；`samples/invalid/repair-wrong-report-type.json` 被拒 |
| 4 | 🟡 | 产物访问约定 | A/B 共同 | `ADR-003` + `endpoints.md` 第四节 + `samples/artifact.error-report.json` | 说明下游读取方式 | URI 文法与 `GET /v1/artifacts/{id}` 已定义；**待 B1 确认端点** |

第 2、3 项标 ✅ 是指**契约层面**可表达且可校验。`baseline` 的匹配规则语义由 A3
最终确认，`MD` 的消费语义由 B3 最终确认——见下方「待对方确认」。

## 二、A1 自己的交付项

| # | 状态 | 任务 | 产物 | 验收条件 |
| --- | --- | --- | --- | --- |
| 5 | ✅ | 状态枚举与状态矩阵 | `task.schema.json` `$defs.status_matrix` | 六种状态各有样例；非法组合被拒（6 个负例覆盖） |
| 6 | ✅ | 错误码双通道与注册表 | `docs/interfaces/errors.md` | 第 9 页三个给定码全部登记；`MISSING` 写进 `error` 被拒 |
| 7 | ✅ | 第 25 页检查 04 的书面解释 | `errors.md` 第一节 | 「MD 为什么不等于工具执行失败」有成文答案 + 可执行断言 |
| 8 | ✅ | 零依赖校验器 | `tools/validate.py` | `python3 tools/validate.py` 在无第三方包的环境直接跑通 |
| 9 | ✅ | 负例套件 | `samples/invalid/*.json`（18 个） | 每个负例按声明的 `expected_error` 被拒 |
| 10 | ✅ | 单元测试 | `tests/test_validate.py`（27 项） | `python3 -m unittest discover -s tests` 全绿 |
| 11 | ✅ | 六份 ADR | `docs/adr/ADR-001..006` | 按第 13 页 Context/Decision/Alternatives/Consequences 四段式 |
| 12 | ✅ | 校验规则说明 | `docs/VALIDATION.md` | 列出已覆盖与**未覆盖**的约束，不夸大 |
| 13 | ✅ | 端点草案 | `docs/interfaces/endpoints.md` | 第 27 页五端点齐备 + 交互示例；标注负责人为 B1 |

## 三、待对方确认（A1 无法单方面关闭）

| # | 状态 | 事项 | 对方 | 阻塞了什么 |
| --- | --- | --- | --- | --- |
| 14 | ✅ | `GET /v1/artifacts/{artifact_id}` 作为产物读取接口 | B1 已确认 | E12「证明另一组能读取文件」 |
| 15 | ✅ | `VALIDATION_2xxx` 命名空间是否接受 | B1 已确认并限定边界 | `errors.md` 注册表定稿 |
| 16 | ✅ | 信封严格 / 载荷可扩展的分界线（ADR-004） | B1 已确认 | 四组能否自行扩展 `input`/`output` |
| 17 | ✅ | `execution` 字段定义（第 19 页未解释，A1 自定） | B1 已确认，四组待确认 | 若推翻属破坏性变更，需升版本 |
| 18 | 🟡 | URI 用完整 `job_id` 而非第 24 页简写 `full01` | **教师**（B1 已认同） | 有意偏离课件样例，需认可 |
| 19 | ⬜ | `FULL_CHECK` 的 `input`/`output` 字段名 | A2 | A2 的依赖图与报告字段 |
| 20 | ⬜ | `INCREMENTAL_CHECK` 的 baseline 匹配规则与新增/消除 finding 语义 | A3 | A3 的 C0/C1 可追溯验收 |
| 21 | 🟡 | `DRAFT` 的成功判据与每轮日志字段 | B2 已提案，待 A2 确认 | `draft-*.json` 与 ADR-007 对齐环境、成功判据和 `configuration_id`；`make check` 为硬门槛 |
| 22 | ⬜ | `REPAIR` 的 patch 与拒绝原因字段 | B3 | B3 的「能解释 MD≠执行失败」验收 |

第 14 至 17 项由 B1 于 2026-09-21 完成复核，结论与理由见
`docs/CHANGELOG.md` 的 1.0.0 条目与 `docs/AI_USAGE.md` 条目 9。
第 18 项超出 B1 的权限范围，需教师在课上确认。
第 19 至 22 项属四个服务负责人的字段级确认，与 B1 的公共契约复核无关。

## 四、未完成项、原因与下一步（第 15 页要求）

| 事项 | 状态 | 未完成原因 | 下一步 |
| --- | --- | --- | --- |
| 部署任何 API | ⬜ 不做 | 第 7 页明确「E2 先定义，不要求部署 API」 | E3/E12 再评估 |
| 让 B 组真的下载一次 artifact | ⬜ 未做 | 需要产物存储与 `GET /v1/artifacts/{id}` 实现，E2 不部署 | 第 24 页把它列为 E12 要求；本轮先冻结契约（ADR-003） |
| 用 `jsonschema` 库替代手写校验器 | ⬜ 未做 | 本机实测未安装；第 2 页课堂仅 150 分钟且与 E3 共享，无法现场装包 | 若课前确认环境具备，按 ADR-006 的备选方案替换 |
| 校验 `sha256` 与产物本体是否真的相符 | ⬜ 未做 | 样例中的哈希是说明性值，无对应真实文件 | 联调时对真实产物计算并比对 |
| 校验 `base_commit == baseline.commit` 与 `baseline.configuration_id == environment.configuration_id` | ⬜ **故意不做** | 第 5 页把这两项列为「接收方检查」，属运行期职责；ADR-005 的判据表述有误，已由 ADR-010 第四节修正 | 由 EChecker 在运行期落为 `FAILED` + `ENV_3003`；`tests/…TestBaselineConsistencyIsRuntimeNotContract` 钉住此边界 |
| 与 B09 的三轮课堂交换 | ⬜ 未做 | 需课堂现场进行（第 16 页） | 每轮结束把结论写进 ADR、未决项写进本文件 |
| Issue + PR 关联 | ✅ 已完成 | 走 fork 流程（A1 对上游无推送权限） | Issue #1 列出 11 项待确认；PR #2 承载全部 A1 交付物 |
| B1 独立契约与 A1 版本重复 | ✅ 已收敛 | 两人同时在写「只能有一份」的公共契约 | 已移除 `e2-pair09/`，B1 转为复核方；原文可 `git show bbf818a` 取回 |
| 加 `.gitattributes` 统一行尾 | ⬜ 未做 | 只影响 Windows 下的 LF/CRLF 警告，仓库内存储仍是 LF | 不影响验收，随时可加 |
| 建 `artifacts/.gitkeep` 固定产物根目录 | ⬜ 未做 | E2 不部署服务，`artifact://` 目前只用于样例 | E3 落地产物存储前处理 |
| B2 分支 `origin/e2b2` 合并 | ✅ **已合并，前置条件已失效** | B2 已按 schema 重写三个样例并合入 main | 见下方更正说明 |
| DRAFT 样例两套并存、命名不统一 | 🟡 待 B2 处理 | B2 用连字符命名，与 A1 的点号规范冲突 | 见 `interfaces/samples/README.md` 第五节，由 B2 执行改名 |
| `configuration_id` 取值两组不一致 | ⬜ 未定 | A1 用第 22 页原文的 `cc-MODE0`，B2 用 `draft-gcc13-release-9f8e7d6c` | 需 B2 定格式、A2 定消费方式，见 `interfaces/samples/README.md` 第四节 |
| `job.error.code` 排除 `VALIDATION_2xxx` | ✅ 已完成 | B1 在 `errors.md` 定了规则，但 schema 的正则写宽了，文档禁止的事契约放行 | 已拆为 `job_error_code` / `request_error_code`，见 ADR-010 |
| B1 迁移表内 `QUEUED→FAILED` 与硬规则 2 冲突 | 🟡 待 B1 确认 | 表允许从 QUEUED 直达 FAILED，硬规则 2 却说 RUNNING 不可跳过 | A1 建议收窄硬规则 2，见 ADR-010 第二节 |
| `schema_version` 是否因收紧 `error.code` 而递增 | 🟡 待 B1 裁定 | A1 判断不递增（是修 schema 与已定稿规范的偏差，非改规范） | 版本号归 B1 维护，见 ADR-010 第五节 |

### 更正：B2 分支的合并前置条件已失效（A1，2026-09-21）

上方「B2 分支 `origin/e2b2` 合并」一行原为 ⬜ **不可直接合并**，并附有一节
「B2 分支的合并前置条件」，列出三个样例的八类问题、称提交 `38f6694` 基于 `a48d53e`。
该判断由 B1 于 2026-09-21 作出，**现已失效**。A1 实测证据如下：

| 核查项 | 命令 | 结果 |
| --- | --- | --- |
| `e2b2` 是否还有未合并提交 | `git log origin/main..origin/e2b2` | **空** —— `e2b2` 的所有提交都已在 main |
| `e2b2` 是否为 main 的祖先 | `git merge-base --is-ancestor origin/e2b2 origin/main` | **是** |
| `e2b2` 当前指向 | `git log -1 origin/e2b2` | `e04364f`（= main 的 HEAD） |
| 提交 `38f6694` 是否存在 | `git cat-file -t 38f6694` | **`fatal: Not a valid object name`** —— 仓库内无此对象 |
| 三个样例是否通过校验 | `python3 tools/validate.py docs/interfaces/samples/draft-{request,response,failed-response}.json` | **三个全部通过** |
| 全量校验 | `make check` | 通过，39 项测试全绿 |

结论：B2 已经按 `task.schema.json` 重写了三个样例（`d05ee38`「对齐 DRAFT 样例与
环境交接契约」、`e04364f`），ADR 也已改号为 `ADR-007` 并登记进 `adr/README.md` 索引。
B1 列出的八类问题在当前 main 上**一个都不存在**。

保留这段更正而不是直接删掉原文，是因为：助教或教师若读到「B2 分支不可合并、
三个样例通不过校验」，会误判 B2 尚未交付；而 B1 的原始核查在**当时**是成立的
（针对的是已被 force-push 或改写掉的旧提交）。原文可在 `git show 8eb7b4c` 取回。

**遗留的真实问题不在合法性，在一致性**：B2 的三个文件用连字符命名
（`draft-request.json`），与 A1 的点号规范（`draft.request.json`）并存，
导致 DRAFT 有两套请求/响应样例。处理方案见 `interfaces/samples/README.md`。

B1 原文末尾那条关于根 `README.md` 的澄清（B2 并未修改它）仍然有效，未受影响。

## 五、变更规则

任何 MAJOR/MINOR 变更的 PR 必须同时更新：`task.schema.json`、
`tools/validate.py`（若涉及新约束）、受影响的 `samples/`、`tests/`、
相应 ADR、以及本文件。`make check` 不过不予合并（ADR-004）。
