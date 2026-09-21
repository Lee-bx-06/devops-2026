# ADR-002 契约采用严格 Schema 并配套变更流程

| 项 | 值 |
|---|---|
| 状态 | Proposed |
| 日期 | 2026-09-20 |
| 提议人 | B1 |
| 评审人 | 待 A1 联合确认 |
| 关联文件 | `interfaces/task.schema.json`、`../versioning.md`、`../CHANGELOG.md` |

## Context

第 26 页把"严格 Schema 拒绝新增字段"列在可能破坏兼容的一栏。也就是说，是否使用 `additionalProperties: false` 本身就是一个需要明确决定并记录的取舍。

我们的处境是：六个同学分头写四类任务的样例，字段名不一致是主要风险。契约要在课堂时间内冻结，之后还有 E3 要基于它继续做。

## Decision

契约采用严格模式。所有对象层级设置 `additionalProperties: false`。

与之配套的三条硬规则：

1. 任何新增字段必须同时更新 `task.schema.json`、对应样例和 `../CHANGELOG.md`
2. 新增可选字段递增 MINOR 版本，删改字段递增 MAJOR 版本
3. 字段变更必须由 A1 与 B1 双方各评审一次才能合并

## Alternatives

| 替代方案 | 未采用的理由 |
|---|---|
| 全面放开，允许任意扩展字段 | 拼写错误会静默通过，六个人各写各的字段名时几乎无法发现，联调阶段才会集中爆发 |
| 只在响应侧严格，请求侧放开 | 请求侧的字段错误正是最需要早发现的一类，放开后反例检查失去意义 |
| 完全不做 schema，只靠文档约定 | 第 25 页要求运行校验脚本，且无效输入必须被拒绝，纯文档无法满足 |

## Consequences

好处：

1. 字段拼写错误在提交阶段就被拦住
2. 契约是显式的，新增字段必须走一次双方确认，不会出现"悄悄多了一个字段"
3. 反例检查有确定结论，`job_type` 改成 `ABC`、删除 `baseline` 都会被拒

代价：

1. 扩展成本变高，每加一个字段都要改三处
2. 如果两位接口负责人各自加字段而不走流程，校验会直接失败

需要新增的工作：

1. `versioning.md` 中的变更流程与消费者清单，否则"严格"会变成阻塞而不是保护
2. `CHANGELOG.md` 必须真实维护，否则无法判断对方用的是哪一版

## 验证方式

1. 运行校验脚本，四类请求与响应样例全部通过
2. `samples/invalid/invalid-job-type.example.json` 被拒绝
3. `samples/invalid/invalid-incremental-missing-baseline.example.json` 被拒绝
4. 临时在任一对象里加入一个未声明字段，确认被拒绝，验证严格模式真的生效
