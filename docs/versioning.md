# 版本与兼容性

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 负责人 B1（李秉轩）｜ 契约版本 1.0.0

依据第 11、26 页编写。第 11 页把「哪些字段必填、名称是什么」与「失败怎样处理、版本怎样变更」
列为需要自己决定的事项，本文件负责后半部分；前半部分见 `interfaces/task.schema.json`。

**改任何一个字段之前，先查第三节的消费者清单和第 26 页的两栏分类。**

## 一、版本号规则

契约版本写在每个请求与响应的 `schema_version` 字段，形式为三段式 `MAJOR.MINOR.PATCH`。

| 变化类型 | 版本动作 |
|---|---|
| 笔误、注释、样例补充，契约形状不变 | PATCH 加一 |
| 新增可选字段、新增错误码、新增产物类型 | MINOR 加一 |
| 删除字段、改名、改语义、改动状态枚举、改动错误码含义 | MAJOR 加一，后两段归零 |

必须写三段，写两段会被校验器拒绝，见 `interfaces/samples/invalid/bad-schema-version.json`。
理由是消费方靠 `schema_version` 决定能否解析，两段式会让版本协商失去确定性。

## 二、第 26 页的两栏分类

### 可兼容变化

| 第 26 页原文 | 在本契约里的具体表现 | 需要谁同意 |
|---|---|---|
| 新增可选字段需要消费者允许 | 在 `input` / `output` 内部追加字段 | 消费该字段的服务负责人 |
| 共享 Schema 同步更新 | 改动同时落到 schema、样例、`CHANGELOG.md` | A1 与 B1 双方 |
| 保留已有字段的含义 | 字段含义不得在 MINOR 内改变 | 无需额外同意 |

### 可能破坏兼容

| 第 26 页原文 | 在本契约里的具体表现 | 处理方式 |
|---|---|---|
| 字段删除、改名或改语义 | 顶层信封字段、`status`、`error.code` | 先加替代字段，双方切换后再删。MAJOR 加一 |
| 状态枚举改变 | `QUEUED / RUNNING / SUCCEEDED / FAILED / TIMED_OUT / CANCELLED` | 必须先写 ADR 并与全部下游确认 |
| 严格 Schema 拒绝新增字段 | 顶层三类对象为 `additionalProperties: false` | 见第三节的分界，扩展走 `input` / `output` |

## 三、严格与可扩展的分界线

第 26 页把「严格 Schema 拒绝新增字段」列为破坏兼容的风险，因此本组把边界画在**所有权**上，
而不是一刀切。完整论证见 `adr/ADR-004`。

| 层 | 归属 | 严格程度 | 谁来改 |
|---|---|---|---|
| 顶层 `create_request` / `job` / `artifact_record` | 公共契约，A1 与 B1 共管 | `additionalProperties: false` | 必须走本节第五节的流程 |
| `input` / `output` 内部 | 四个服务负责人各自所有 | 允许追加字段 | 服务负责人自行扩展，同步样例即可 |

效果是四个服务各自加字段不必全组同步升级，而公共信封的每一次改动都有人把关。

## 四、变更流程

1. 提出方在 `BACKLOG.md` 记一条，写明动机和受影响的消费者
2. 若属破坏性变更，先写 ADR，状态为 Proposed
3. 与全部受影响消费者确认，确认人与日期记在 ADR 里
4. 改动落到 schema 与文档，同步补正例与负例
5. 更新本文件与 `CHANGELOG.md`，递增 `schema_version`
6. A1 与 B1 双方评审后合并

破坏性变更在消费者确认前不得合并。

## 五、消费者清单

改字段前先查这张表。找不到确认人说明消费者还没确定，此时应先进 `BACKLOG.md` 而不是直接改 schema。

| 契约内容 | 主要消费者 | 确认人 |
|---|---|---|
| 顶层信封九个公共字段 | 四个服务全部 | A1、B1 |
| `input.repository`、`input.environment`、`input.build` | DRAFT、BuildChecker、EChecker、MDFixer | B2、A2、A3、B3 |
| `baseline` 相关字段与匹配规则 | EChecker | A3 |
| `md_report` 与 `PATCH` 相关字段 | MDFixer | B3 |
| `finding` 结构与 `detector` 取值 | MDFixer，以及所有读 MD 报告的一方 | B3、A2、A3 |
| `artifact_record` 与产物读取接口 | 四个服务全部 | A1、B1 |
| `status`、`execution`、`error.code` | 四个服务全部 | A1、B1 |
| `error` 注册表 | 全部调用方 | B1 维护 |

## 六、与其他文档的关系

| 文档 | 回答的问题 |
|---|---|
| `interfaces/*.md`、`task.schema.json` | 现在约定的内容是什么 |
| `adr/*.md` | 为什么这样约定，考虑过哪些替代方案 |
| `CHANGELOG.md` | 什么时候变的，谁受影响 |
| `BACKLOG.md` | 还没定的和还没做的 |

## 七、冻结期内的补齐与破坏性变更（2026-09-22 B1 裁定）

第一节按「契约形状是否变化」归类，但契约在**尚未被任何一方消费**的窗口内，
形状变化不会破坏任何消费者。为免把「刚写好还没人用」也当成破坏性变更处理，
本节补一条判据，并记录 2026-09-22 的三条裁定。

**判据：变更要不要递增，取决于它是否落在「已有消费者按旧版本解析」的场景里。**

| 情形 | 版本动作 |
| --- | --- |
| 契约尚未被任何服务部署或消费（E2 阶段即此情形，第 7 页明确不部署 API），改动属冻结前补齐 | 不递增，但必须在 `CHANGELOG.md` 逐条写明影响面 |
| 已有服务按当前版本消费之后，再改字段语义、增删 `kind` / `status` / `error.code` 的取值 | 按第一节归类递增 |

**2026-09-22 的三条裁定（均判为冻结前补齐，维持 `1.0.0`）：**

| # | 变更 | 第一节的字面归类 | 裁定与理由 |
| --- | --- | --- | --- |
| 1 | `error.code` 收紧为 `job_error_code` / `request_error_code`（ADR-010） | 改动 `error.code` → 破坏兼容 | 不递增。1.0.0 的 `errors.md` 从未允许 `VALIDATION_2xxx` 进 `job.error`，是 schema 正则写宽了，本次是让 schema 符合已定稿的规范，规范没变 |
| 2 | `output_repair` 两个字段引入封闭 enum（ADR-009 / PR #20） | 取值集收紧 | 不递增。字段属 B3 的 `output` 载荷（ADR-004 第三节），消费者是 MDFixer 一方；封闭取值同时写进 schema 与校验器，无跨组破坏 |
| 3 | 新增三种 artifact 本体 `kind`（ADR-011 / PR #6） | 新增产物类型 → MINOR | 不递增。只新增 `kind` 取值，不改既有取值的含义，属第 26 页「可兼容变化」一侧；且尚无任何一方按 1.0.0 消费过 |

**若日后改判为递增，需要同步修改的位置（一次说清，避免漏改）：**

1. `interfaces/task.schema.json` 中 `schema_version` 的 `const`
2. `interfaces/samples/**` 下全部正例的 `schema_version` 字段（负例 `bad-schema-version.json` 除外）
3. `tools/validate.py` 与 `tests/` 中从 schema 读取版本号的断言
4. `README.md`、`interfaces/*.md`、`VALIDATION.md` 里标注的契约版本
5. `CHANGELOG.md` 新增对应版本条目，并把本节的三条裁定移入该条目

**一条边界**：本判据只适用于「还没有消费者」的窗口。E2 之后（E3 起服务开始落地、
E12 跨组实际交接产物）任何改动都不再适用，必须回到第一节的归类。
