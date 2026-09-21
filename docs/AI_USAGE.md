# AI_USAGE.md —— 设计过程证据

小组 A09 ｜ 配对组 第 9 组（pair09） ｜ 记录人：谢浩天（A1）、李秉轩（B1）

按第 14 页要求记录四件事：**工具/模型与任务**、**提示摘要与 AI 建议**、
**人工采纳/修改/拒绝的理由**、**关联文件与版本与验证**。

第 14 页特别提醒要写具体，并给了范例格式：
「AI 提议 PENDING → 我们按课程规范改为 QUEUED → 更新四组契约样例 → 运行校验并记录结果」。
下面每条都按这个链条写。

> 说明：本文件记录的是**真实发生过的判断**，不是事后补写的模板。
> 每条都指向具体的文件与具体的验证命令，可逐条复核。

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

## A2（待填写姓名）的记录

### 条目 13：补齐 FULL_CHECK 的 artifact 本体和跨字段约束

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
  - 新增 `ADR-010`，记录本体的设计与取舍。
- **关联文件**：
  `docs/interfaces/buildchecker-contract.md`、
  `docs/interfaces/task.schema.json`、
  `docs/interfaces/samples/artifact.*.json`、
  `docs/interfaces/samples/full-check.clean-project.json`、
  `docs/interfaces/samples/invalid/…`、
  `docs/adr/ADR-010-buildchecker-output-contract.md`、
  `tests/test_buildchecker_contract.py`
- **验证**：`python tools/validate.py` 通过；
  `python -m unittest discover -s tests -v` 共 35 项全绿。
