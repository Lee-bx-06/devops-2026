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
