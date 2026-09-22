# ADR 目录说明

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 本文件由 B1（李秉轩）维护

依据第 13、16 页。ADR 记录「为什么这样定」，`interfaces/` 记录「最终定成什么」，两者互补。

## 一、什么时候要写 ADR

1. 两个服务之间的交接内容变了
2. 出现两种以上做法，组内选了其中一个
3. 撤销或修正了前面已写下的某个决定
4. 对课件样例有意偏离

单纯的错别字与样例补充不需要 ADR，走 `../CHANGELOG.md` 即可。

## 二、编号与命名

| 项 | 规则 |
|---|---|
| 文件名 | `ADR-NNN-短标题.md`，编号三位，从 001 起递增 |
| 编号 | 一经使用不再复用，即使对应 ADR 被废弃 |
| 状态 | `Proposed`、`Accepted`、`Superseded by ADR-NNN`、`Rejected` |
| 日期 | 决定日期，不是文件创建日期 |

同一主题的后续决定新建一篇并标注替代关系，不修改原文。

## 三、结构

四段固定结构取自第 13 页：`Context`、`Decision`、`Alternatives`、`Consequences`。
模板见 `ADR-000-template.md`。第 16 页要求把配对练习的决定写入 ADR。

## 四、索引

| 编号 | 标题 | 状态 | 提议人 |
|---|---|---|---|
| 001 | 采用异步 Job 模型与单一公共信封 | Accepted | A1 |
| 002 | 错误与检测发现走两条独立通道 | Accepted | A1 |
| 003 | artifact 命名空间与解析约定 | Accepted | A1 |
| 004 | 兼容性策略：信封严格，载荷可扩展 | Accepted | A1 |
| 005 | 创建期拒绝与运行期失败的边界 | Accepted | A1 |
| 006 | 校验器零依赖，从 schema 读常量 | Accepted | A1 |
| 007 | [DRAFT 与 BuildChecker 的环境交接契约](ADR-007-draft-buildchecker-contract.md) | Accepted | B2 |
| 008 | [增量检测的基线可比性与 finding 差集语义](ADR-008-incremental-baseline-and-finding-diff.md) | Accepted | A3 |
| 009 | [候选补丁的接受与拒绝判据](ADR-009-patch-acceptance-criteria.md) | Accepted | B3 |
| 010 | [状态迁移规则的形式化，兼修正 ADR-005 的判据表述](ADR-010-transition-timing-and-baseline-ownership.md) | Accepted（B1 于 2026-09-22 评审通过） | A1 |
| 011 | [BuildChecker 输出与 artifact 本体契约](ADR-011-buildchecker-output-contract.md) | Proposed（B1 复核项已完成，待 A2/B3/B2 在 Issue #1 确认） | A2 |

本表由 B1 维护。每新增一篇 ADR 必须同时在此登记，否则视为未完成。

## 五、已解决的编号冲突

B2 原文件 `ADR-001-draft-buildchecker-contract.md` 与公共契约已使用的
`ADR-001-async-job-model.md` 编号重复。2026-09-21 已在 `e2b2` 分支改号为
`ADR-007-draft-buildchecker-contract.md` 并登记到上方索引。

A2 原文件 `ADR-010-buildchecker-output-contract.md` 与 A1 已合并的
`ADR-010-transition-timing-and-baseline-ownership.md` 编号重复。2026-09-21
已在 `a2-full-check-contract` 分支改号为 `ADR-011-buildchecker-output-contract.md`
并登记到上方索引。008 与 009 已预留给 A3 与 B3，因此 A2 让号到 011。
