# AI_USAGE.md —— 设计过程证据

小组 A09 ｜ 配对组 第 9 组（pair09） ｜ 记录人：谢浩天（A1）、李秉轩（B1）、zrh（B2）

按第 14 页要求记录四件事：**工具/模型与任务**、**提示摘要与 AI 建议**、
**人工采纳/修改/拒绝的理由**、**关联文件与版本与验证**。

第 14 页特别提醒要写具体，并给了范例格式：
「AI 提议 PENDING → 我们按课程规范改为 QUEUED → 更新四组契约样例 → 运行校验并记录结果」。
下面每条都按这个链条写。

> 说明：本文件记录的是**真实发生过的判断**，不是事后补写的模板。
> 每条都指向具体的文件与具体的验证命令，可逐条复核。
>
> **条目内的样例数与测试数是「写下该条时」的数值，不是当前值。**
> 例如条目 1 说「16 个正例」，指 A1 第一轮交付时的数量，B2 补样例后已是 19 个。
> 这些数字是历史证据的一部分，改成当前值等于篡改记录，故一律不动。
> **当前数量的唯一来源是 `VALIDATION.md` 第五节**，并由
> `tests/test_validate.py::TestDocsDoNotRot` 断言其与实际文件数一致（见条目 17）。

---

## 条目 1：拒绝上一轮 AI 的「不需要四套业务样例」结论

- **工具/模型**：OpenAI Codex（前一会话，产物在本地旧稿 `devops-e2-contract/`）
  → Qoder CLI agent（本会话，谢浩天操作）
- **任务**：判断旧稿能否直接作为 A1 交付物
- **AI 建议**：旧稿 `docs/VALIDATION.md` 写道「每种 job_type 由单元测试变异同一
  通用示例验证可表达；**不需要四套业务样例**」，其样例的 `input` 与 `output`
  全部是空对象 `{}`。
- **人工判断：拒绝。** 理由有三条：
  1. 第 25 页检查 01 的原文是「检查**四类请求与响应**」，不是「检查一种通用请求」。
  2. `input: {}` 让「四类 job 能被同一份 schema 表达」变成空洞的真命题——
     空对象能被任何 schema 表达，等于什么都没验证。
  3. 致命的连带后果：`input` 无结构 ⇒ `baseline` 无从必填 ⇒
     第 25 页检查 03「删除增量任务的 baseline 应被拒绝」**根本无法执行**，
     A3 的验收条件也一并落空。
- **采纳的替代做法**：按第 20–23 页逐服务写出 `input`/`output` 结构，
  四对请求/响应样例齐备，并在 `check_coverage()` 里把「四类各有一对」
  变成**被校验的对象**（删掉一个样例就会红）。
- **关联文件**：`docs/interfaces/task.schema.json`（`$defs.input_*` / `$defs.output_*`）、
  `docs/interfaces/samples/`（16 个正例）、`tools/validate.py`（`check_coverage`）
- **验证**：`python3 -m unittest discover -s tests -v` →
  `TestSlide25Check01FourJobTypes` 通过；`python3 tools/validate.py` 通过

---

## 条目 2：拒绝上一轮 AI 的「A1 不规定错误码命名空间」

- **工具/模型**：同上
- **任务**：撰写 `docs/interfaces/errors.md`
- **AI 建议**：旧稿 `errors.md` 只有 5 行，其中明确写「**A1 不规定错误码命名空间
  或重试策略**」，schema 里 `error.code` 仅约束为「非空字符串」。
- **人工判断：拒绝。** 第 9 页整页就是在给错误码——`ENV_3002` 镜像构建失败、
  `EXEC_4002` 任务超时、`ANALYSIS_5001` 分析器失败，并明确它们「写入 `job.error`」，
  与写入 `ERROR_REPORT.findings` 的 `MISSING`/`REDUNDANT` 分开。
  把这页课件的要求说成「A1 不规定」，等于放弃了 A1 的核心交付物之一。
  而且 `code` 只约束为非空字符串，会让第 25 页检查 04（MD≠执行失败）
  失去类型层面的保障——`{"code": "MISSING"}` 能顺利通过校验。
- **采纳的替代做法**：从三个给定码反推命名空间规律
  （`ENV_3xxx` / `EXEC_4xxx` / `ANALYSIS_5xxx`），补 `VALIDATION_2xxx`
  承载创建期拒绝（ADR-005），写成正则约束 + `errors.md` 注册表。
  用正则而非封闭枚举是为了让各组能在自己命名空间内增码而不触发
  第 26 页的破坏性变更（ADR-004）。
- **关联文件**：`docs/interfaces/errors.md`、`task.schema.json`（`$defs.error_code`）、
  `docs/adr/ADR-002`、`ADR-004`、`ADR-005`
- **验证**：`samples/invalid/md-reported-as-error.json`（`code: "MISSING"`）被拒；
  `samples/invalid/bad-error-code-namespace.json`（`code: "BOOM"`）被拒；
  `tests/…Check04…::test_system_error_codes_are_accepted` 断言五个合法码通过

---

## 条目 3：AI 提议 `status: PENDING`，按第 8 页改为 `QUEUED`

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：定义 `status` 枚举
- **AI 建议**：初稿讨论中出现过 `PENDING` 作为「已受理未开始」的取值——
  这是通用任务队列 API 的常见命名，第 14 页也专门拿它当反面范例。
- **人工判断：修改。** 第 8 页给的是 `QUEUED`（「任务已接受」）。
  课件用 `QUEUED` 而非 `PENDING` 是有意的：`QUEUED` 明确表示「已入队」，
  而 `PENDING` 在不同系统里既可能指「已受理」也可能指「等待前置条件」，
  语义含糊。跨组契约要的是无歧义。
- **落实**：枚举定为 `QUEUED / RUNNING / SUCCEEDED / FAILED / TIMED_OUT / CANCELLED`，
  封闭不可扩展（第 26 页：状态枚举改变属破坏性变更）。
  并且**专门写了一个负例**把 `PENDING` 钉死，防止后续有人凭直觉改回去。
- **关联文件**：`task.schema.json`（`$defs.job_status`）、
  `samples/invalid/pending-status.json`、`docs/adr/ADR-001`
- **验证**：`tests/…TestSchemaAndValidatorAgree::test_schema_declares_the_deck_enums`
  断言枚举与第 8 页一致；`pending-status.json` 被拒且拒绝理由含「status 非法」

---

## 条目 4：AI 自己写出的 JSON Schema 语义错误，人工复核时发现并修正

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：定义 `artifact_record`
- **AI 产出**：初版写成
  ```json
  "artifact_record": {
    "allOf": [
      {"$ref": "#/$defs/artifact"},
      {"additionalProperties": false, "properties": {"kind": ..., "schema_version": ...}}
    ]
  }
  ```
- **人工判断：拒绝该写法。** `additionalProperties` 在 JSON Schema 里**只看同一个
  模式对象内的 `properties`**，跨 `allOf` 分支不可见。上面这个写法的实际效果是：
  第二个分支会拒绝所有不在它自己 `properties` 里的字段——也就是把
  `artifact_id`、`uri`、`sha256` 等全部判为非法。整个 `artifact_record`
  会变成只有两个字段能通过，且报错信息完全指向错误的方向。
- **落实**：把 `artifact` 的九个字段**平铺**进 `artifact_record`，
  并在 schema 的 `description` 里写明这个坑，避免后来者改回去。
- **同类问题一并修正**：初版把 `http_status` 对所有 `QUEUED` 文档设为必填，
  但 `GET /v1/jobs/{id}` 查一个仍在排队的任务返回的是 200，
  不该被迫带上 `http_status: 202`。改为可选，并保留「若出现则必须是 202
  且状态必须是 QUEUED」的约束。
- **关联文件**：`task.schema.json`（`$defs.artifact_record`、`$defs.status_matrix`）
- **验证**：`samples/artifact.error-report.json` 十字段完整通过；
  `tests/…TestArtifactContract` 四项全绿；
  `samples/invalid/queued-http-200.json` 仍被拒（说明约束没被放松）

---

## 条目 5：AI 建议改用 `jsonschema` 库，人工拒绝

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：实现第 25 页要求的 `validate.py`
- **AI 建议**：用 `jsonschema` 库直接对 `task.schema.json` 求解。这是标准做法，
  schema 成为唯一真源，天然不会与校验逻辑漂移，还能完整求解
  `oneOf` / `if-then` / `allOf`。技术上明显优于手写。
- **人工判断：拒绝（但记录为条件性备选）。** 实测本机
  `jsonschema`、`referencing`、`jsonschema_specifications` **全部未安装**；
  第 2 页给出苏州 09-20 是 E2+E3 **共 150 分钟**且与另一实验共享，
  现场装包不现实，评分环境也未必有网。第 25 页要求「运行 validate.py」
  必须当场可跑，跑不起来的正确性没有意义。
- **缓解漂移的替代设计**：校验器不硬编码常量，而是启动时**从 schema 读取**
  枚举、正则、必填清单（`validate.py` 的 `Schema` 类）。改 schema 里的枚举，
  校验器立即跟着变。并加一组测试断言抽取结果与课件给定值一致。
- **关联文件**：`tools/validate.py`、`docs/adr/ADR-006`、`docs/VALIDATION.md` 第四节
- **验证**：`python3 tools/validate.py` 在无任何第三方包的环境下通过；
  `tests/…TestSchemaAndValidatorAgree` 四项全绿

---

## 条目 6：AI 建议偏离课件样例的 URI 写法，人工采纳但标记待确认

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：定义 `artifact://` URI 文法
- **AI 建议**：第 24 页样例是 `artifact://pair01/full01/actual.json`，
  但 `full01` 不是合法 `job_id`（schema 里形如 `job-full01`）。
  建议改用完整 `job_id`：`artifact://pair09/job-full09/actual.json`。
- **人工判断：采纳，但明确标记为对课件的有意偏离，需教师/B1 确认。**
  理由：用完整 `job_id` 后，URI 里的段与 `producer_job_id` 能用同一条正则校验，
  也能从 URI 直接反查生产任务；用简写则两者对不上，校验器只能放宽。
  但课件是评分依据，擅自偏离有风险，所以不隐瞒、写进 ADR 待确认清单。
- **关联文件**：`task.schema.json`（`$defs.artifact_uri`）、
  `docs/adr/ADR-003`（Alternatives 与 Consequences 各记一处）、
  `docs/BACKLOG.md` 第 18 项
- **验证**：`samples/invalid/foreign-artifact-uri.json`（写成 `pair01`）被拒；
  `samples/incremental-check.request.json` 的 `baseline.actual_graph_uri`
  用同一文法引用上游产物，形成 A2 → A3 的真实交接链

---

## 条目 7：AI 生成的分工方案，人工按课件逐页核对后采纳

- **工具/模型**：另一 AI 会话（用户提供的长文方案）→ Qoder CLI agent 核对
- **任务**：确认 A1 的职责边界
- **AI 建议**：3+3 结对分工，A1 = 公共契约与集成，产物为
  `task.schema.json` / `errors.md` / `tools/validate.py`，对接 B1；
  并给出仓库骨架与四步执行顺序。
- **人工判断：采纳，但先做了逐页核对。** 把方案里引用的每一个页码
  （第 2、3、4、5、7、8、9、10、15、16、19、24、25、26、27 页）
  与 PPTX 原文比对，全部吻合，才据此确定 A1 边界。
- **核对中发现的一处不一致（已在方案内修正）**：方案正文说
  「4 篇 PDF 一人认领一篇」，但分工表里 A2=TSE、A3=ISSTA、B2=ICSE、B3=ASE，
  A1 与 B1 并无论文。结论是 A1 需要的是**跨四服务的字段级通读**
  （第 20–23 页已给出四个服务的输入输出摘要），而非深读某一篇。
- **关联文件**：本仓库整体结构、`README.md` 的分工与归属表
- **验证**：`README.md` 中标注了每份文件的负责人；
  B1 归属的 `endpoints.md` 由 A1 起草但明确标注「负责人：B1，待复核」，
  不冒认他人工作

---

## B1（李秉轩）的记录

环境 Windows / Python 3.10.11，工具 OpenAI Codex。条目编号接在 A1 之后。

### 条目 8：AI 起草的独立契约与 A1 版本重复，人工决定收敛为一套

- **工具/模型**：OpenAI Codex
- **任务**：按分工表完成 B1 负责的公共契约与版本部分
- **AI 产出**：一套完整契约，含 `task.schema.json`（378 行、23 个 `$defs`）、
  5 个样例、2 篇 ADR、版本规则与变更记录，提交为 `bbf818a`，位置 `e2-pair09/`
- **人工判断：先采纳并提交。** 提交时并不知道 A1 已在 PR #2 中交过根目录 `docs/`，
  这是本次重复的直接原因
- **发现**：读远端仓库时看到两套契约并存。AI 指出第 12 页「统一任务模型」的
  责任方是 A/B 共同，公共部分只能有一份，否则 E3 联调时产物路径会对不上
- **人工决定：收敛为一套。** 逐项对比后确认 A1 版本更完整（34 个 `$defs`、
  20 个负例、6 篇 ADR、518 行校验器），B1 转为复核与版本维护方，
  移除 `e2-pair09/`，独有内容并入 `docs/`
- **保留取回方式**：`git show bbf818a`，`git restore` 可整体撤销
- **关联文件**：`docs/CHANGELOG.md`、`docs/versioning.md`、`docs/adr/README.md`、
  提交 `bcf217e`、`docs/CONTRIBUTIONS.md` 的 B1 提交追溯
- **验证**：移除后仓库只剩 `docs/interfaces/task.schema.json` 一处定义；
  `python tools/validate.py` 通过；27 项单元测试全绿
- **这条的教训**：公共契约开工前应先确认对方进度。六个同学里两个人同时写
  「只能有一份」的文件，返工是必然的

### 条目 9：AI 建议直接接受 `VALIDATION_2xxx`，人工限定适用边界后接受

- **工具/模型**：OpenAI Codex
- **任务**：复核 Issue #1 第二节的七项待确认
- **AI 建议**：`VALIDATION_2xxx` 是 A1 自行扩展的命名空间，已经进了注册表，
  直接接受即可，理由与 ADR-005 一致
- **人工判断：修改。** 第 9 页的原话是系统执行错误「写入 `job.error`」，
  而创建期拒绝根本不产生 Job。两者放进同一个通道会自相矛盾：
  一个没有 `job_id` 的错误不可能出现在 Job 文档里
- **落实**：在 `errors.md` 新增「B1 复核补充」一节，把适用范围限死为
  只在创建期同步拒绝出现、只落在 HTTP 4xx 响应体、不写 `job.error`、
  不产生 `job_id`，并加一列约束「出现位置」。同时明确注册表自 2026-09-21 起由 B1 维护
- **关联文件**：`docs/interfaces/errors.md`、`docs/CHANGELOG.md`
- **验证**：`task.schema.json` 的 `error_code` 正则仍为四段，
  `job.error.code` 只取 `ENV_3xxx` / `EXEC_4xxx` / `ANALYSIS_5xxx`；
  `tools/validate.py` 通过，18 个负例仍按各自声明的 `expected_error` 被拒

### 条目 10：AI 复核时发现「配对组 B09」把两个编号写混，人工确认后全局修正

- **工具/模型**：OpenAI Codex
- **任务**：复核 A1 交付的公共契约
- **AI 发现**：A1 在 8 个文件里写作「配对组 **B09**」。第 15 页要求提交材料写明
  「小组与配对组编号」，这两者是不同的东西：小组编号是 A09 与 B09，
  配对组编号是第 9 组
- **人工判断：采纳并修正。** 理由是编号混用会在验收时对不上号，
  而且 `artifact://pair09/` 的命名空间本来就在表达「第 9 组」这一层
- **落实**：8 个文件的同一处表述统一改为「配对组 第 9 组（pair09）」，
  涉及 `README.md`、`CONTRIBUTIONS.md`、`BACKLOG.md`、`AI_USAGE.md`、
  `VALIDATION.md`、`interfaces/endpoints.md`、`interfaces/errors.md` 与
  `interfaces/task.schema.json` 的描述字段。编号本身（A09 / B09 / pair09）
  与各处 `artifact://pair09/` 的写法未动，只改表述
- **关联文件**：上述 8 个文件，提交 `bcf217e`
- **验证**：改完后 `python -c "import json; json.load(...)"` 确认 schema 仍是合法 JSON；
  `python tools/validate.py` 通过

### 条目 11：AI 指出三处第 26 页要求但仓库缺失的内容，人工确认后补齐

- **工具/模型**：OpenAI Codex
- **任务**：审查仓库是否满足第 15 页的四类提交材料
- **AI 发现**：三处缺口。
  1. 第 26 页整页讲「版本与变更记录」，仓库里既没有 `CHANGELOG.md`，
     也没有独立的版本与兼容性规则
  2. `docs/adr/` 下 6 篇 ADR 没有索引，没有编号规则，也没有模板
  3. 第 13 页的四段式模板没有落成文件
- **人工判断：采纳。** 第 15 页把"设计文件"列为提交材料，
  「版本怎样变更」是第 11 页明确要求自己决定的事项之一
- **落实**：新增 `docs/CHANGELOG.md`、`docs/versioning.md`、
  `docs/adr/README.md`、`docs/adr/ADR-000-template.md`。
  `versioning.md` 把第 26 页的两栏分类转成本仓库的具体动作，
  并补了消费者清单——改字段前先查它影响谁
- **顺带发现**：B2 的分支 `origin/e2b2` 里 `ADR-001-draft-buildchecker-contract.md`
  与已合并的 `ADR-001-async-job-model.md` 编号撞车，已记入 `adr/README.md` 第五节
- **关联文件**：`docs/CHANGELOG.md`、`docs/versioning.md`、
  `docs/adr/README.md`、`docs/adr/ADR-000-template.md`
- **验证**：`docs/CHANGELOG.md` 的 1.0.0 条目逐条对应 Issue #1 的七项结论；
  ADR 索引里 6 篇全部登记且有状态列

### B1 未处理的两条 AI 建议

| 建议 | 状态 | 原因 |
| --- | --- | --- |
| 加 `.gitattributes` 写 `* text=auto eol=lf` | 暂未采纳 | 只影响 Windows 下的行尾警告，仓库内存储仍是 LF，不影响验收 |
| 建 `artifacts/.gitkeep` 固定产物根目录 | 暂未采纳 | E2 不部署服务，`artifact://` 目前只用于样例；E3 落地前处理即可 |

两条都保留在 `docs/BACKLOG.md` 的未决项里，避免「想起来了就做」。

---

## 汇总

| 类别 | 条目 |
| --- | --- |
| 拒绝 AI 建议 | 1（不要四套样例）、2（不规定错误码）、5（改用 jsonschema 库） |
| 修改 AI 建议 | 3（PENDING → QUEUED）、4（AI 自身的 Schema 语义错误 + `http_status` 必填范围）、9（限定 `VALIDATION_2xxx` 的适用边界） |
| 采纳 AI 建议 | 6（URI 用完整 job_id，但标记待确认）、7（分工方案，逐页核对后采纳）、8（收敛为一套契约）、10（修正配对组编号）、11（补齐版本与变更记录） |
| 发现 AI 产出中的问题 | 8（B1 自己那版与 A1 重复）、10（A1 交付里的编号混用）、11（三处文档缺口） |

**统一验证命令**（本文件所有条目均以此复核）：

```bash
make check
# = python3 tools/validate.py && python3 -m unittest discover -s tests -v
```

**版本**：契约 1.0.0 ｜ 记录时间 2026-09-21

- A1 侧环境：macOS / Python 3.14.6
- B1 侧环境：Windows / Python 3.10.11

**诚实声明**：所有样例中的 URI、sha256、commit、镜像名、时间戳均为**说明性值**，
不对应真实仓库或真实检测结果。它们的作用是让 A09 与 B09 用同一份具体例子
确认彼此理解一致（第 11 页）。本仓库不宣称任何服务已实现、已部署。

B1 的复核已于 2026-09-21 完成，逐条结论见 `docs/CHANGELOG.md` 的 1.0.0 条目。
A2、A3、B3 尚未确认各自负责的 `input` / `output` 字段。B2 已在
`e2b2` 分支提交 DRAFT 字段与成功判据提案，待 A2 交叉确认。其余待确认项
集中在 `docs/BACKLOG.md` 第三节与 Issue #1 第三节。
少数条目仍需教师确认，已在 `docs/CHANGELOG.md` 的待处理表中单独标注，
其中最重要的是 `artifact://` URI 使用完整 `job_id` 这一处对课件样例的有意偏离。

---

## B2（zrh）的记录

### 条目 12：AI 建议直接修补旧样例，人工改为先对齐公共契约再重写

- **工具/模型**：OpenAI Codex（本次会话）
- **任务**：按课件、任务分工和两张复核截图修正 B2 的 DRAFT 契约交付
- **AI 建议**：在原有三份 JSON 上逐项增加缺失字段，并保留原 ADR 编号
- **人工判断：修改。** 截图明确要求先 `rebase origin/main`，且已合并的
  `task.schema.json` 冻结了公共信封。如果只修补旧结构，会继续混用
  `schema_version=1.0`、占位 `trace_id`、顶层缺 `kind` 等旧语义。
- **落实**：先将 `e2b2` 变基到最新 `origin/main`，再按公共 schema 重写三份
  B2 样例。成功响应补齐 `build_result`、每轮理由、可追溯 artifact 和一致的
  `configuration_id`；失败响应依公共状态矩阵使用 `output={}`，没有伪造
  可交付的部分环境。原 ADR-001 改号为 ADR-007，避免覆盖 A1 的异步 Job 决策。
- **关联文件**：`docs/interfaces/samples/draft-*.json`、
  `docs/adr/ADR-007-draft-buildchecker-contract.md`、`docs/adr/README.md`
- **验证**：`make check`（公共校验器与 27 项单元测试）

---

## A1（谢浩天）第二轮记录（2026-09-21，PR #2 合并后复核）

> 上方「汇总」表覆盖条目 1–11，条目 12 属 B2，以下 13–16 属 A1 第二轮。
> 本轮起因：PR #2 合并后拉取 main，复核 B1 与 B2 的改动是否与 A1 的契约一致。

### 条目 13：AI 复核发现 B1 的文档规则与 A1 的 schema 相互矛盾，人工确认后收紧 schema

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：核对 B1 合并后的 `errors.md` 与 A1 的 `task.schema.json` 是否一致
- **AI 发现**：B1 在 `errors.md` 第二节新增硬规则——`VALIDATION_2xxx` 只出现在
  创建期 HTTP 4xx 响应体、**不写入 `job.error`**，`job.error.code` 只取
  `ENV_3xxx` / `EXEC_4xxx` / `ANALYSIS_5xxx` 三段。但 A1 的 schema 里
  `error_code` 正则四段全允许，而 `$defs.error` 直接引用它。
  **文档禁止的事，契约放行。** 更糟的是 A1 自己的
  `tests/test_validate.py:160` 还专门断言 `VALIDATION_2001` 能进 `job.error`——
  测试在守护一个错误行为。
- **人工判断：采纳，并认定这是 A1 的责任而非 B1 的。** B1 只能写文档，
  改 schema 是 A1 的职责；一份规则如果只写在文档里、契约不强制，
  等于没写。这也是 A1 上一轮的疏漏：自己定义了四段命名空间，
  却没有区分「哪段能出现在哪里」。
- **落实**：`error_code` 拆为 `job_error_code`（三段）与 `request_error_code`
  （`VALIDATION_2xxx`）；`$defs.error.code` 只引前者；改正那条测试；
  新增负例 `invalid/validation-code-in-job-error.json`；
  新增 `test_schema_splits_the_two_code_namespaces` 断言两个正则互斥。
  校验器的拒绝信息会明确指出「该码属创建期 HTTP 4xx 段，不得写入 job.error」。
- **未做的事**：没有递增 `schema_version`。A1 判断 1.0.0 的 `errors.md`
  从未允许过这种写法，是 schema 正则写宽了，属修正实现偏差而非改规范；
  且仓库内无任何合法样例受影响。但版本号归 B1 维护，
  已提交 B1 裁定（`CHANGELOG.md` 待处理表第 6 项、ADR-010 第五节）。
- **关联文件**：`task.schema.json`、`tools/validate.py`、`tests/test_validate.py`、
  `samples/invalid/validation-code-in-job-error.json`、`errors.md`（A1 补记）、
  `adr/ADR-010`
- **验证**：`make check` 全绿，测试由 27 项增至 41 项

### 条目 14：AI 指出 B1 的迁移表自相矛盾，人工选择收窄规则而非删除表行

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：把 B1 在 `endpoints.md` 新增的「状态迁移」一节转成可校验约束
- **AI 发现**：迁移表第三行是 `QUEUED → FAILED`（受理后环境准备失败），
  但硬规则 2 写「`RUNNING` 不可跳过……从 `QUEUED` 直达终态意味着
  `execution.started_at` 会缺失」。同一行里 `QUEUED → CANCELLED` 也是同样问题。
  两处直接冲突，且冲突点落在 `started_at` 能否为 `null` 这个会影响四个服务
  执行器实现的硬约束上。
- **人工判断：采纳，但修正方式与 AI 的第一反应不同。** AI 最初倾向把
  `started_at` 一律要求非空（严格贯彻硬规则 2）。人工否决：那样
  「镜像拉不下来」这种真实故障就必须伪造一次 `started_at`，
  或者硬塞进 `RUNNING` 之后再失败，两种做法都污染「任务实际运行时长」这个指标，
  而 `EXEC_4002` 的超时归属恰恰依赖它。**迁移表是对的，该收窄的是硬规则 2。**
- **落实**：把六条计时约束写进 `status_matrix` 与 `check_transition_timing()`——
  `QUEUED` 两者皆 null；`RUNNING` 有 `started_at` 无 `finished_at`；
  `SUCCEEDED` / `TIMED_OUT` 两者皆有；`FAILED` / `CANCELLED` 必须有 `finished_at`，
  `started_at` 允许为 null。B1 规则的本意（超时归属可判定）完整保留，
  因为超时只能是 `TIMED_OUT`，而 `TIMED_OUT` 必须有 `started_at`。
  建议 B1 据此改述硬规则 2，已记入 `CHANGELOG.md` 待处理表第 7 项。
- **同时修正 A1 自己上一轮的错误理由**：ADR-005 说
  `baseline.commit ≠ base_commit` 属运行期，理由是「必须去读产物、比对提交」。
  **这个理由是错的**——比对请求体里两个字面量不需要任何 I/O。结论对，理由错，
  而错误理由会误导后来者按「需不需要 I/O」分类，把所有文档内交叉比对都划到创建期。
  正确判据是**职责归属**：第 5 页把它列为「接收方检查」，所以属运行期。
  按 B1 在 `adr/README.md` 定的规则（不修改原文，新建并标注替代关系），
  在 ADR-010 第四节修正，ADR-005 原文未动。
- **关联文件**：`task.schema.json`（`status_matrix`）、`tools/validate.py`
  （`check_transition_timing`）、`tests/…TestTransitionTiming`（七条）、
  `tests/…TestBaselineConsistencyIsRuntimeNotContract`（三条）、
  `adr/ADR-010`、`VALIDATION.md` 第三节
- **验证**：`make check` 全绿；`test_failed_without_started_at_is_allowed`
  专门断言「`FAILED` 且 `started_at` 为 null」合法

### 条目 15：AI 对比两套 DRAFT 样例，发现 B2 有一处比 A1 做得更好，人工采纳并合并

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：处理 `samples/` 里 DRAFT 样例两套并存（A1 点号命名 vs B2 连字符命名）
- **AI 发现**：B2 的 `draft-response.json` 在 `output` 里写了 `environment`
  （含 `image_uri`、`configuration_id`、`project_root`、`clean_command`），
  而 A1 的 `draft.job-succeeded.json` **完全没有产出这个字段**。
- **人工判断：采纳，并认定这是 A1 的疏漏，不是风格差异。**
  第 21 页规定 `FULL_CHECK` 输入需要「可运行镜像与 `configuration_id`」，
  第 22 页规定 `INCREMENTAL_CHECK` 的 `baseline` 需要 `configuration_id`，
  而这些值的**唯一来源**就是 DRAFT 的输出。A1 的样例没有产出它，
  等于把 DRAFT → BuildChecker 这条交接链断在了契约里——
  A2 无从得知自己要消费的 `configuration_id` 是谁给的、长什么样。
  这一条比命名冲突严重得多，而命名冲突是显眼的、这个是隐形的。
- **落实**：schema 新增 `$defs.produced_environment` 并挂到 `output_draft.environment`；
  依 ADR-004（`output` 内部属服务负责人）定为**可选而非必填**，
  是否升为必填请 B2 决定；`draft.job-succeeded.json` 补入该字段；
  `validate.py` 增加形状检查。
- **未做的事**：没有删除或改名 B2 的三个文件。它们被 B2 自己的
  `ADR-007`（第 23、35、69 行）与 `CONTRIBUTIONS.md`（第 102–104 行）引用，
  擅自改名会连带弄坏 B2 的文档，属 B2 的所有权范围。
  改为写 `samples/README.md` 定命名规范、列出请 B2 做的三件事，
  并说明 A1 已把 B2 版本中更好的内容合并进规范版本，所以 B2 删除自己那两个
  重复文件不会丢失任何信息。
- **一并发现的分歧**：`configuration_id` 取值两组不一致
  （A1 用第 22 页原文的 `cc-MODE0`，B2 用 `draft-gcc13-release-9f8e7d6c`）。
  该值必须全组统一，否则环境交接对不上。A1 建议采用 B2 的描述性格式，
  但需 B2 定格式、A2 定消费方式，已记入待处理表第 8 项。
- **关联文件**：`task.schema.json`、`samples/draft.job-succeeded.json`、
  `tools/validate.py`、`samples/README.md`、`BACKLOG.md`、`CHANGELOG.md`
- **验证**：`make check` 全绿

### 条目 16：AI 报告 B1 的一条 BACKLOG 判断已过时，人工逐条取证后更正而非静默删除

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：核对 `BACKLOG.md` 里「B2 分支 `origin/e2b2` 不可直接合并、
  三个样例全部通不过 `tools/validate.py`、提交 `38f6694` 基于 `a48d53e`」是否仍成立
- **AI 发现**：全部不成立。
- **人工判断：采纳，但要求先取证再更正，且不删原文。** 逐项跑了命令：
  `git log origin/main..origin/e2b2` 为空；
  `git merge-base --is-ancestor origin/e2b2 origin/main` 返回真；
  `origin/e2b2` 指向 `e04364f`（= main HEAD）；
  `git cat-file -t 38f6694` 报 `Not a valid object name`，**该对象在仓库内不存在**；
  三个样例单独跑 `validate.py` 全部通过。
  B2 早已按 schema 重写（`d05ee38`、`e04364f`）并把 ADR 改号为 007。
- **为什么不静默删除**：助教或教师若读到那条，会误判 B2 尚未交付；
  而 B1 的原始核实在**当时**是成立的（针对的是已被改写掉的旧提交）。
  因此保留更正段落 + 六行证据表 + `git show 8eb7b4c` 取回原文的路径，
  而不是把原文抹掉。这也符合第 15 页「未完成项、失败原因、下一步」要留痕的要求。
- **顺带区分了两类问题**：B2 样例的**合法性**没有问题（全部通过校验），
  真正遗留的是**一致性**问题（两套命名并存、`configuration_id` 取值不统一）。
  B1 的原文把焦点放在合法性上，而那部分已经解决了。
- **关联文件**：`BACKLOG.md` 第四节、`CHANGELOG.md`
- **验证**：证据表中六条命令均可复现

---

### 条目 17：AI 写的自动自检脚本查出文档计数腐烂，人工改为加断言而非逐处修数字

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：取得上游协作权限后，在合并 PR #3 前做自检
- **AI 做法**：临时写了一个审计脚本，检查 JSON 可解析性、文件编码、
  文档交叉引用是否落地、**文档声明的数量与实际文件数是否一致**、
  `validate.py` 引用的 `$defs` 是否都存在、schema 内部 `$ref` 是否悬空。
- **发现**：30 项报告，人工分辨后 **6 项是真问题**，其余是正则误报
  （把「见 ADR-004」这类按编号的引用当成了文件路径）或他人的历史记录。
  真问题全部是同一类：ADR-001/002/006、BACKLOG、README 里写死的样例数与测试数，
  在 B2 补样例、A1 加测试之后全部过时。
- **人工判断：修改 AI 的处理方式。** AI 的第一反应是逐处把数字改对。
  人工否决——**改完下次还会腐烂**，因为根因是同一个数字被抄在六个地方。
  正确做法是消除重复：指定 `VALIDATION.md` 第五节为数量的唯一来源，
  其余文档改为指向它；再加一条断言让唯一来源本身不可能悄悄失真。
- **落实**：
  1. 三个 ADR 与 BACKLOG 的写死计数改为指向 `VALIDATION.md` 第五节
  2. 新增 `tests/…TestDocsDoNotRot` 两条断言：`VALIDATION.md` 声明的正例/负例数
     必须等于实际文件数；README 与 `VALIDATION.md` 若写了测试项数必须与实际一致
  3. 守卫立刻发挥作用——它当场查出 README 还写着 39 项而实际已是 41 项，
     包括**本次为加守卫而产生的偏差**
- **未做的事**：没有改 B1 的 `CHANGELOG.md` [1.0.0] 段、B1 的 AI_USAGE 条目 8–11、
  B2 的条目 12 里的历史计数。那些是「当时确实是那个数」的历史记录，
  改成当前值等于篡改记录。守卫因此只覆盖 README 与 `VALIDATION.md` 两份当前态文档。
- **关联文件**：`tests/test_validate.py`、`docs/adr/ADR-001`、`ADR-002`、`ADR-006`、
  `docs/BACKLOG.md`、`docs/VALIDATION.md`、`README.md`、`docs/CHANGELOG.md`
- **验证**：`make check` 全绿，41 项测试

这条与条目 13–16 是同一个教训的两面：**`make check` 全绿不等于仓库自洽。**
上一轮是「文档规则没有对应的机器约束」，这一轮是「同一事实被抄在多处、
其中几处已过时」。两次的解法方向一致——把规则变成断言，把重复变成单一来源。

---

### A1 第二轮汇总

| 类别 | 条目 |
| --- | --- |
| 发现 A1 自己的错误 | 13（schema 与已定稿文档矛盾，且测试在守护错误行为）、14（ADR-005 的理由错误）、15（DRAFT 输出缺 `environment`，断了交接链）、17（六个文档里的样例/测试计数全部过时） |
| 发现他人的矛盾并给出修正 | 14（B1 迁移表 vs 硬规则 2）、16（B1 的 BACKLOG 判断过时） |
| 采纳他人更好的做法 | 15（B2 的 `output.environment`） |
| 明确不做、并说明为什么 | 13（不递增 `schema_version`，交 B1 裁定）、14（不把基线一致性收紧为创建期拒绝）、15（不擅自改名 B2 的文件）、17（不改他人历史记录里的计数） |
| 改进方法而非只改结果 | 17（把重复的数字收敛为单一来源 + 断言守卫，而不是逐处改对） |

本轮的一个教训：条目 13、14、15 三处都是 **A1 上一轮自己的疏漏**，
而且都属于「文档写了但契约没强制」或「契约有但链路断了」这类
**不会让 `make check` 变红**的问题。校验全绿并不等于契约自洽。
下一轮复核应优先检查「文档里的每条规则是否都有对应的机器约束」，
而不是只看测试是否通过。

### 条目 18：AI 建议把 A2–B2 交接写成说明，人工要求落成可执行契约

- **工具/模型**：OpenAI Codex（本次会话）
- **任务**：依据 `A2_B2_约定清单.md` 固化 DRAFT 到 FULL_CHECK 的环境交接
- **AI 建议**：先在 ADR 和样例中描述 `image_uri`、`configuration_id` 与构建命令，
  由 A2 联调时再决定是否升级 schema 和校验器
- **人工判断：修改。** 仅有文字约定无法阻止字段遗漏、`:latest` 镜像、相对工作目录、
  轮次日志缺失或 DRAFT/FULL_CHECK 两侧取值漂移，也不能满足清单要求的自动验收
- **落实**：把 `output.environment`、`output.build` 写进正式 schema；要求镜像使用 OCI 引用
  且禁用 `:latest`，构建/清理/验证命令分离，`project_root` 使用绝对 POSIX 路径；
  校验器增加 DRAFT→FULL_CHECK 逐字段一致性、稳定配置 ID、轮次与制品关联检查。
  同时删除重复命名的旧 DRAFT 样例，仅保留一条规范成功链，并补齐失败、超时和
  达到最大迭代次数三条路径
- **真实制品处理**：为 DRAFT 样例提交 Dockerfile 与三份日志，样例中的
  `sha256` 和 `size_bytes` 由这些文件实际计算，不再使用说明性占位值
- **关联文件**：`docs/interfaces/task.schema.json`、`docs/interfaces/samples/draft.*.json`、
  `docs/interfaces/samples/full-check.*.json`、`docs/interfaces/artifacts/job-draft09/`、
  `tools/validate.py`、`tests/test_validate.py`、`docs/adr/ADR-007-draft-buildchecker-contract.md`
- **验证**：`make check`，其中新增 `TestA2B2DraftHandoff` 覆盖规范样例唯一性、
  直接映射、缺字段拒绝、路径与镜像语义、真实哈希、跨字段漂移和失败路径
---

## A2（殷晓瑞）的记录

### 条目 19：补齐 FULL_CHECK 的 artifact 本体和跨字段约束

- **工具/模型**：OpenAI Codex（本次会话）
- **任务**：在 B2 完成 DRAFT 对齐后，直接推进 A2 自己负责的 BuildChecker /
  FULL_CHECK 交付
- **AI 建议**：只补 DRAFT 对接字段还不够；如果 ACTUAL_GRAPH、DECLARED_GRAPH
  和 ERROR_REPORT 的文件本体没有定义，A3 的 EChecker 与 B3 的 MDFixer
  无法稳定消费 artifact。
- **人工判断：采纳执行。** 用户明确要求“能做就直接做”，因此本轮直接落盘；
  A2 本人仍需在提交和对外确认前复核 MD/RD 语义、detector 取值以及 TSE
  论文中的依赖图表示。
- **落实**：
  - 新增 `docs/interfaces/buildchecker-contract.md`，定义请求、输出、三份
    artifact 本体、MD/RD、失败路径和下游交接。
  - 在 `task.schema.json` 增加 `actual_graph` / `declared_graph` /
    `error_report`。
  - 新增三份 artifact 本体正例、零发现正例和五个负例。
  - 在 `tools/validate.py` 增加 counts/findings 一致性、核心 artifact 类型
    和本体字段校验。
  - 新增 `tests/test_buildchecker_contract.py`。
  - 新增 `ADR-011`（起草时编号 010），记录本体的设计与取舍。
- **关联文件**：
  `docs/interfaces/buildchecker-contract.md`、
  `docs/interfaces/task.schema.json`、
  `docs/interfaces/samples/artifact.*.json`、
  `docs/interfaces/samples/full-check.clean-project.json`、
  `docs/interfaces/samples/invalid/…`、
  `docs/adr/ADR-011-buildchecker-output-contract.md`、
  `tests/test_buildchecker_contract.py`
- **验证**：`python tools/validate.py` 通过；
  `python -m unittest discover -s tests -v` 在 A2 分支上 35 项全绿
  （条目 20 合并 B2 的改动后为 56 项）

### 条目 20：AI 复核 B2 的更新，人工决定"接受并顺手修好"而不是打回

- **工具/模型**：OpenAI Codex（本次会话）
- **任务**：复核 B2 已合并进 `main` 的 DRAFT 交接更新（`Issue #4` / `PR #5`），
  判断 `ADR-007` 能否由 A2 接受
- **AI 发现**：
  1. 原计划里列的六个卡点，五个已解决：`output_draft` 已进 schema、重复样例已删、
     `configuration_id` 不再含 commit 前缀、`clean_command` 与 `project_root` 语义统一、
     Issue + PR 追溯齐备。
  2. **但 `make check` 在干净检出上是红的**：`TestA2B2DraftHandoff` 报
     `308 != 318`。根因是 `draft.job-succeeded.json` 里 Dockerfile 制品的
     `size_bytes` / `sha256` 取自 CRLF 工作副本，与仓库内 LF blob 不符。
     B2 的 PR 勾了"48 项单元测试通过"，与实际不符。
  3. `PR #5` 正文写着"验收通过后再合并"，但它在本轮复核之前就已经合进 `main`，
     A2 的验收关卡被绕过。
  4. 双方各自新增的 ADR 都编号 010，索引里会出现两篇同号 ADR。
- **人工判断：接受 ADR-007，但先把红测修好再合。** 打回重做的时间成本高于直接修正：
  缺陷只有一行数据，而验收条件（字段级契约）本身已经满足。同时明确记下"验收关卡
  被绕过"这个流程问题，避免下次再发生。
- **落实**：
  - 按 blob 实际字节改正 Dockerfile 制品的 `size_bytes` / `sha256`；
  - 把 `ADR-007` 由 `Proposed` 改为 `Accepted`，登记进 `adr/README.md`；
  - A2 的 `ADR-010` 让号改名为 `ADR-011`（008/009 已预留给 A3/B3）；
  - 合并 `main` 并解决 7 个文件的冲突，`tools/validate.py` 保留双方各自的
    FULL_CHECK 与 DRAFT 校验块。
- **关联文件**：`docs/interfaces/samples/draft.job-succeeded.json`、
  `docs/adr/ADR-007-draft-buildchecker-contract.md`、`docs/adr/README.md`、
  `docs/adr/ADR-011-buildchecker-output-contract.md`、`README.md`、
  `docs/BACKLOG.md`、`docs/VALIDATION.md`、`docs/CHANGELOG.md`、`tools/validate.py`
- **验证**：合并后 `python tools/validate.py` 通过、
  `python -m unittest discover -s tests` 56 项全绿；
  `docs/VALIDATION.md` 第五节的正例/负例数与实际文件数一致（21 / 24）。

---

## A1（谢浩天）第三轮记录（2026-09-21，A2/B2 合并后复核）

### 条目 18：AI 建议把守卫写成「登记表必须与实际违规完全相等」，人工否决

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：修复 `configuration_id` 交接链断裂，并加一个防止复发的守卫
- **AI 建议**：写成棘轮断言——`KNOWN_ENV_DEVIATIONS` 必须与实际违规集**完全相等**，
  这样每修好一个文件就必须同步缩小登记表，债务不会被遗忘。
- **人工判断：否决。** 登记表里那四个文件属 A3 的 PR #8，而该 PR 只迁移了其中两个。
  若断言完全相等，**A3 的 PR 一合并 `make check` 就红**，等于用 A1 的守卫去卡
  A3 的进度。同理，AI 还想再加一条「登记表不得有已修好的条目」，
  写的时候自称是「软提醒」，实现出来却是硬断言，同样会卡人——已删。
- **落实**：改为**子集**断言 `violations - KNOWN_ENV_DEVIATIONS == ∅`，
  只拦登记表之外的新违规；登记表的收缩改由 `BACKLOG.md` 追踪。
  登记表每项带负责人与原因，让债务可见但不阻塞他人。
- **关联文件**：`tests/test_cross_document_consistency.py`、`docs/BACKLOG.md`
- **验证**：注入旧值做变异测试，4 条断言变红，确认守卫真的有效（不是永绿的装饰）

> 这条的教训与条目 13–17 不同：前几条是「该加的约束没加」，
> 这条是**「加约束时别把自己的测试变成别人的合并障碍」**。
> 守卫的价值在于拦新增问题，不在于逼所有人同步修历史问题。

### 条目 19：AI 想同步更新 README 里的测试总数，人工改为取消这个数字

- **工具/模型**：Qoder CLI agent（本会话）
- **任务**：新增测试文件后，README 写的「56 项单元测试」过时，`TestDocsDoNotRot` 变红
- **AI 建议**：把 56 改成 63。
- **人工判断：拒绝，改为消除这个数字。** A3 的 PR #8 把同一行改成 68，
  A2 之前改成 56，A1 写的是 41——**三个数都对，只是时点不同**。
  任何人加测试都会让它过时，且并行 PR 必然在这一行冲突。
  上一轮对样例数用的是「收敛到单一来源」，这一轮更彻底：测试总数根本没有
  单一来源可言，运行一次就知道，不该写进文档。
- **落实**：README 改为不写总数并说明理由；`TestDocsDoNotRot` 里那条
  「测试数必须与实际一致」的断言反转为「**任何文档不得写死测试总数**」。
  样例数仍保留单一来源（`VALIDATION.md` 第五节）与断言，因为样例清单本身有信息量。
- **连带影响**：A3 的 PR #8 会在 README 这一行冲突。已在 PR 描述里注明
  请取 A1 版本（无数字），避免反复同步。
- **关联文件**：`README.md`、`tests/test_validate.py`
- **验证**：`make check` 全绿，63 项测试

### A1 第三轮汇总

| 类别 | 条目 |
| --- | --- |
| 发现他人未发现的缺陷 | `artifact-full09-error-report` 的 `configuration_id` 有两种取值（5 个样例），`make check` 全绿；`full-check.clean-project.json` 的 `image_uri` 与 `configuration_id` 不自洽 |
| 否决 AI 建议 | 18（棘轮断言会卡住 A3 的 PR）、19（同步更新测试总数） |
| 改进方法而非只改结果 | 18（守卫改为只拦新增违规）、19（取消重复数字而非同步数字） |
| 未擅自改动他人文件 | A3 的 4 个样例、A2 的 `full-check.clean-project.json` 一律登记不改，附负责人与原因 |

本轮的核心教训写在 `VALIDATION.md` 第四节末尾：**部分覆盖不等于覆盖。**
A2 补上 DRAFT → FULL_CHECK 的断言后，把「跨文档一致性未覆盖」整条删掉了，
但交接链还有 FULL_CHECK → EChecker → MDFixer 两段。
删掉整条等于向后来者宣称问题已解决。
