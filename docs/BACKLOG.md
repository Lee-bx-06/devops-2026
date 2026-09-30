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
| 4 | ✅ | 产物访问约定 | A/B 共同 | `ADR-003` + `endpoints.md` 第四节 + `samples/artifact.error-report.json` | 说明下游读取方式 | URI 文法与 `GET /v1/artifacts/{id}` 已由 B1 确认；服务实现和真实下载留待后续阶段 |

第 2、3 项标 ✅ 是指**契约层面**可表达且可校验。`baseline` 的匹配规则语义由 A3
最终确认，`MD` 的消费语义由 B3 最终确认——见下方「待对方确认」。

## 二、A1 自己的交付项

| # | 状态 | 任务 | 产物 | 验收条件 |
| --- | --- | --- | --- | --- |
| 5 | ✅ | 状态枚举与状态矩阵 | `task.schema.json` `$defs.status_matrix` | 六种状态各有样例；非法组合被负例逐条覆盖（清单见 `VALIDATION.md` 第五节） |
| 6 | ✅ | 错误码双通道与注册表 | `docs/interfaces/errors.md` | 第 9 页三个给定码全部登记；`MISSING` 写进 `error` 被拒 |
| 7 | ✅ | 第 25 页检查 04 的书面解释 | `errors.md` 第一节 | 「MD 为什么不等于工具执行失败」有成文答案 + 可执行断言 |
| 8 | ✅ | 零依赖校验器 | `tools/validate.py` | `python3 tools/validate.py` 在无第三方包的环境直接跑通 |
| 9 | ✅ | 负例套件 | `samples/invalid/*.json`（24 个，含 A2 的 5 个 FULL_CHECK/本体负例与 B2 的 DRAFT 负例） | 每个负例按声明的 `expected_error` 被拒 |
| 10 | ✅ | 单元测试 | `tests/test_validate.py` + `tests/test_buildchecker_contract.py` + `tests/test_echecker_contract.py` | `python3 -m unittest discover -s tests` 全绿；数量以实际运行为准 |
| 11 | 🟡 | ADR 汇总 | `docs/adr/ADR-001`–`ADR-011` | ADR-001–010 已接受；ADR-011 的消费侧内容已由相关 PR 落实，待 A3/B3/B2 本人在 Issue #1 明确确认，再由 B1 更新为 Accepted |
| 12 | ✅ | 校验规则说明 | `docs/VALIDATION.md` | 列出已覆盖与**未覆盖**的约束，不夸大 |
| 13 | ✅ | 端点草案 | `docs/interfaces/endpoints.md` | 第 27 页五端点齐备 + 交互示例；标注负责人为 B1 |

## 三、待对方确认（A1 无法单方面关闭）

| # | 状态 | 事项 | 对方 | 阻塞了什么 |
| --- | --- | --- | --- | --- |
| 14 | ✅ | `GET /v1/artifacts/{artifact_id}` 作为产物读取接口 | B1 已确认 | E12「证明另一组能读取文件」 |
| 15 | ✅ | `VALIDATION_2xxx` 命名空间是否接受 | B1 已确认并限定边界 | `errors.md` 注册表定稿 |
| 16 | ✅ | 信封严格 / 载荷可扩展的分界线（ADR-004） | B1 已确认 | 四组能否自行扩展 `input`/`output` |
| 17 | ✅ | `execution` 字段定义（第 19 页未解释，A1 自定） | B1 已确认，四组待确认 | 若推翻属破坏性变更，需升版本 |
| 18 | ✅ | URI 用完整 `job_id` 而非第 24 页简写 `full01` | A09/B09 组内协议 | A1 与 B1 于 2026-09-22 同意使用完整 `job_id`；见 [Issue #1 评论](https://github.com/Lee-bx-06/devops-2026/issues/1#issuecomment-5777416000)。课程认可仍是知情事项，不阻塞组内约定 |
| 19 | 🟡 | `FULL_CHECK` 的 `input`/`output` 字段名 | A2 起草；A3/B3/B2 待本人在 Issue #1 明确确认消费侧语义；确认后由 B1 更新 ADR 状态 | `docs/interfaces/buildchecker-contract.md`、`ADR-011`、三份 artifact 本体样例与测试；消费侧内容已由相关 PR 落实，但内容落地不等于本人确认；A3 样例实际读取 A2 的 ACTUAL_GRAPH 与 ERROR_REPORT |
| 20 | ✅ | `INCREMENTAL_CHECK` 的 baseline 匹配规则与新增/消除 finding 语义 | B3/B1 已评审并接受，PR #8 已合并 | `echecker-contract.md`、`ADR-008`、两份 artifact 本体和 12 项专项测试均已落盘；Issue #7 |
| 21 | ✅ | `DRAFT` 的成功判据与每轮日志字段 | B2 已按 A2/B2 v0.1 清单落实，A2 已复核并接受 `ADR-007` | `output.environment/build` 已进入 schema，canonical 链路与 artifact 一致性由专项测试覆盖 |
| 22 | ✅ | `REPAIR` 的 patch 与拒绝原因字段 | B3 已完成并合并 | `repair.job-succeeded-rejected.json` + `ADR-009`（Accepted）；`reason_code` 与 `status` 的封闭 enum 已进入 `task.schema.json` 与 `tools/validate.py`；PR #20 |

第 14 至 17 项由 B1 于 2026-09-21 完成复核，结论与理由见
`docs/CHANGELOG.md` 的 1.0.0 条目与 `docs/AI_USAGE.md` 条目 9。
第 18 项的完整 `job_id` URI 已由 A1/B1 于 2026-09-22 定为组内协议；教师意见仅作后续知情事项。
第 19 项的 A3/B3/B2 消费侧内容已由各自 PR 落实，但截至 2026-09-22 B1 评论仍待三人本人在 Issue #1 明确确认；三方确认后由 B1 更新 ADR-011 与索引为 Accepted。A2 是提议人，不替代消费方确认或 B1 状态维护。
第 20 至 22 项分别按 ADR-008、ADR-009、ADR-007 的 Accepted 状态执行。

## 四、未完成项、原因与下一步（第 15 页要求）

| 事项 | 状态 | 未完成原因 | 下一步 |
| --- | --- | --- | --- |
| 部署任何 API | ⬜ 本轮不做 | E2 只交付契约；当前 E3 是 A1 样例与基线阶段，不是服务部署 | 服务实现按 E5/E8 推进，跨组集成与实际下载在 E12 验证 |
| 让 B 组真的下载一次 artifact | ⬜ 未做 | 需要产物存储与 `GET /v1/artifacts/{id}` 实现；E2 与当前 E3 基线均未部署服务 | 按后续服务阶段推进，并在 E12 验证跨组读取；本轮冻结契约（ADR-003） |
| 用 `jsonschema` 库替代手写校验器 | ⬜ 未做 | 本机实测未安装；第 2 页课堂仅 150 分钟且与 E3 共享，无法现场装包 | 若课前确认环境具备，按 ADR-006 的备选方案替换 |
| 校验 `sha256` 与产物本体是否真的相符 | 🟡 DRAFT/A3 已做 | canonical DRAFT 与 A3 两份 artifact 已提供仓库内 fixture 并重算哈希；其他服务仍是说明性值 | E12 联调时对真实下载产物再次计算 |
| 校验 `base_commit == baseline.commit` 与 `baseline.configuration_id == environment.configuration_id` | ⬜ **故意不做** | 第 5 页把这两项列为「接收方检查」，属运行期职责；ADR-005 的判据表述有误，已由 ADR-010 第四节修正 | 由 EChecker 在运行期落为 `FAILED` + `ENV_3003`；`tests/…TestBaselineConsistencyIsRuntimeNotContract` 钉住此边界 |
| 三轮课堂交换（第 16 页） | 历史课程流程参考 | 本项目通过线上 Issue/PR 协作，未记录三轮课堂交换 | 按实际 Issue #1、已合并 PR 和 ADR 追溯线上结论；不虚构课堂完成记录，也不作为本轮线上文档收尾的阻塞项 |
| Issue + PR 关联 | ✅ 已完成 | 早期 E2 交付曾走 fork 流程；A1 后续已具备普通推送权限 | Issue #1 保留协作记录；E3 内容提交与文档提交分别见 [E3 发布记录](../e3/PUBLICATION.md) |
| B1 独立契约与 A1 版本重复 | ✅ 已收敛 | 两人同时在写「只能有一份」的公共契约 | 已移除 `e2-pair09/`，B1 转为复核方；原文可 `git show bbf818a` 取回 |
| 加 `.gitattributes` 统一行尾 | ✅ A3 artifact 已处理 | Windows 的 CRLF 检出会改变文本 artifact 的工作区字节数，曾导致 Issue #19 的大小与 SHA-256 测试失败 | 两份 A3 artifact 固定为 LF，测试按 UTF-8/LF 规范字节校验；其他 artifact 按各服务需要继续补充 |
| 建 `artifacts/.gitkeep` 固定产物根目录 | ⬜ 未做 | E2 不部署服务，`artifact://` 目前只用于样例 | 后续服务落地产物存储时处理 |
| B2 分支 `origin/e2b2` 合并 | ✅ **已合并，前置条件已失效** | B2 已按 schema 重写三个样例并合入 main | 见下方更正说明 |
| DRAFT 样例两套并存、命名不统一 | ✅ 已由 B2 处理 | B2 按 `interfaces/samples/README.md` 删除重复样例，并把 `draft-failed-response.json` 改名为 `draft.job-failed.json` | 无 |
| `configuration_id` 取值两组不一致 | ✅ 已定，🟡 迁移未完 | A2/B2 定为 `cc-gcc13-release-6f12a4c8`（不绑定 commit，符合 `$defs.configuration_id` 定义），A1 初版的 `cc-MODE0` 退役 | A1 已迁移自己负责的 6 个样例；剩余见下三行 |
| `job.running.json`、`job.baseline-mismatch-failed.json` 仍用 `cc-MODE0` + tag 形式镜像 | ✅ 已由 A3 处理 | 两个 INCREMENTAL_CHECK 样例的环境和 baseline 配置已迁移到规范值 | PR #8 已补齐，并从 `tests/test_cross_document_consistency.py` 的 `KNOWN_ENV_DEVIATIONS` 移除 |
| `full-check.clean-project.json` 的 `image_uri` 与 `configuration_id` 不自洽 | 🟡 待 A2 裁定 | 用了 `draft:9f8e7d6c-iter4`（tag 形式）却配 `cc-gcc13-release-6f12a4c8`。按 A2 自己写的 `$defs.configuration_id` 定义「只随基础镜像、工具链、依赖集或构建参数变化」，镜像不同则该 ID 应不同；反之若 ID 相同则镜像应与规范值一致 | 二者必居其一，由 A2 决定；A1 不擅自改 A2 的样例 |
| 跨文档一致性无守卫 | ✅ 已补 | 单文档校验看不出「同一 artifact 在两个文件里描述不同」，`artifact-full09-error-report` 的 `configuration_id` 曾有两种取值而 `make check` 全绿 | 新增 `tests/test_cross_document_consistency.py`；已知偏差登记在 `KNOWN_ENV_DEVIATIONS`，登记表收缩即在此勾掉 |
| README 写死测试总数导致多份 PR 冲突 | ✅ 已消除 | A1 写 41、A2 改 56、A3 改 68，三者都对只是时点不同，且必然在同一行冲突 | README 不再写总数，改由 `TestDocsDoNotRot` 断言「任何文档不得写死测试总数」；样例数仍以 `VALIDATION.md` 第五节为唯一来源 |
| `job.error.code` 排除 `VALIDATION_2xxx` | ✅ 已完成 | B1 在 `errors.md` 定了规则，但 schema 的正则写宽了，文档禁止的事契约放行 | 已拆为 `job_error_code` / `request_error_code`，见 ADR-010 |
| B1 迁移表内 `QUEUED→FAILED` 与硬规则 2 冲突 | ✅ 已关闭 | B1 于 2026-09-22 收窄硬规则 2，ADR-010 Accepted | 见 `endpoints.md` 修订记录及 ADR-010 第二节 |
| `schema_version` 是否因收紧 `error.code` 而递增 | ✅ 已关闭 | B1 于 2026-09-22 裁定维持 1.0.0，ADR-010 Accepted | 见 `CHANGELOG.md`「B1 版本裁定与复核」及 ADR-010 第五节 |
| A2–B2 v0.1 交接清单 | ✅ 已关闭 | A2 已复核并接受 ADR-007；DRAFT environment/build 交接已落地 | 见 ADR-007、A2/B2 专项校验与历史发布记录 |
| `reason_code` 等新增字段是否进 `task.schema.json` | ✅ 已完成 | A1 在 Issue #14 确认；PR #20 完成，两个 enum 与校验器已同步 |
| REPAIR 样例规范化为 canonical 值 | ✅ 已完成 | A1 在 PR #16、A3 在 PR #8 完成迁移；B3 在 PR #20 采纳 |

### E3 A1 基线状态（2026-09-30）

| 状态 | 事项 | 责任方 | 依据 / 下一步 |
|---|---|---|---|
| ✅ | 可重复的 MD/RD 与 C0/C1/C2 参考基线、运行器及可还原实测证据 | A1 | [E3 运行说明](../e3/README.md)、[E3 当前状态](../e3/STATUS.md)、[保存的实测证据](../e3/evidence/run-20260930T023602Z-c2ff9588/README.md)；内容提交 `de31c63b96d969d5c71da1d172b0786d9b8a351a` |
| 🟡 | `full-check.clean-project.json` 的 `image_uri` 与 `configuration_id` 选择 | A2 | 唯一剩余 `KNOWN_ENV_DEVIATIONS`；由 A2 选择一致镜像/配置组合，A1 不代替其裁定 |
| 🟡 | CFLAGS 变化与 `configuration_id` 的归类和映射 | A3、B2；必要时 A2 | 见 [E3 协作事项](../e3/COORDINATION.md)；样例保存 Makefile 与 `make -n -B main.o` 快照，不自行推断 ID |
| ⬜ | Linux 系统调用跟踪、BuildChecker/EChecker 服务输出及服务实现 | A2/A3 与各服务负责人 | 当前证据仅为 macOS Make 行为与人工 oracle；各服务实现按 E5/E8 推进，集成和真实跨组读取按 E12 验证 |

E3 交付是参考样例和基线，不是四服务验收或部署。[E3 当前状态](../e3/STATUS.md) 中所列真实 fixture SHA、运行日志和时间戳仅描述被保存的实验；它们不构成任何同学的服务验收或接受声明。

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
| 全量校验 | `make check` | 通过，41 项测试全绿 |

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

**B2 后续进展（2026-09-21）：**上表保留为对旧提交 `38f6694` 的历史审计。
当前 `e2b2` 已与 main 对齐，重复 DRAFT 请求/成功响应已删除，
`output.environment/build` 已进入正式 schema，校验器与 A2/B2 专项测试已补齐。
ADR-007 随后已由 A2 复核并接受；当前索引状态为 `Accepted`。上文保持为 2026-09-21 的历史进展记录。

## 五、变更规则

任何 MAJOR/MINOR 变更的 PR 必须同时更新：`task.schema.json`、
`tools/validate.py`（若涉及新约束）、受影响的 `samples/`、`tests/`、
相应 ADR、以及本文件。`make check` 不过不予合并（ADR-004）。
