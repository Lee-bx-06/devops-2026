# ADR 目录说明

| 项 | 值 |
|---|---|
| 负责人 | B1 |
| 依据 | 《E2 需求与接口契约》第 13、16、26 页 |
| 作用 | 记录"为什么这样定"，与 `interfaces/` 下记录"最终定成什么"互为补充 |

## 1. 什么时候需要写 ADR

第 16 页要求把配对练习的决定写入 ADR。具体是以下三类：

1. 两个服务之间的交接内容变了
2. 出现了两种以上做法，组内选了其中一个
3. 撤销了前面已经写下的某个决定

纯粹的字段拼写修正不需要 ADR，走 `../CHANGELOG.md` 即可。

## 2. 编号与命名

| 项 | 规则 |
|---|---|
| 文件名 | `ADR-NNN-短标题.md`，编号三位，从 001 起递增，不复用已删除编号 |
| 标题 | 一句名词短语，说明被决定的事 |
| 状态 | `Proposed`、`Accepted`、`Superseded by ADR-NNN`、`Rejected` |
| 归属 | 每篇写清提议人和参与评审的人 |

编号顺序代表决定的时间顺序，不代表重要性。同一主题的后续决定新建一篇并标记替代关系，不修改原文。

## 3. 结构

四段固定结构，取自第 13 页：`Context`、`Decision`、`Alternatives`、`Consequences`。模板见 `ADR-000-template.md`。

## 4. 索引

| 编号 | 标题 | 状态 | 提议人 | 关联文件 |
|---|---|---|---|---|
| ADR-001 | 长耗时任务采用异步 Job 与 202 受理 | Accepted | B1 | `interfaces/endpoints.md` |
| ADR-002 | 契约采用严格 Schema 并配套变更流程 | Proposed | B1 | `interfaces/task.schema.json` |
| ADR-003 | 产物通过引用交接而非内嵌响应 | 待认领 | | `interfaces/endpoints.md` |
| ADR-004 | 增量检测的基线可比性判定 | 待认领，建议 A3 | | `interfaces/states-errors.md` |
| ADR-005 | 候选补丁的接受与拒绝判据 | 待认领，建议 B3 | | `interfaces/endpoints.md` |

第 4 节由 B1 维护。每新增一篇 ADR，必须同时在此表登记，否则视为未完成。

## 5. 与其它文档的边界

| 文档 | 回答的问题 |
|---|---|
| `interfaces/*.md`、`task.schema.json` | 现在约定的内容是什么 |
| `adr/*.md` | 为什么这样约定，考虑过哪些替代方案 |
| `../CHANGELOG.md` | 什么时候变的，谁受影响 |
| `../BACKLOG.md` | 还没定的和还没做的 |
