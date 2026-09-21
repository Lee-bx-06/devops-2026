# 个人贡献与可追溯记录

小组 **A09** ｜ 配对组 **B09** ｜ 契约版本 1.0.0

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

B 侧（B1/B2/B3）由配对组 B09 填写。

## A1 提交追溯

| 工作项 | 文件 | Commit SHA | 提交说明 | Issue / PR | 验证结果 |
| --- | --- | --- | --- | --- | --- |
| 公共任务契约 schema | `docs/interfaces/task.schema.json` | `待填写` | `待填写` | `待填写` | `make check` 通过 |
| 错误与发现双通道 | `docs/interfaces/errors.md` | `待填写` | `待填写` | `待填写` | 第 25 页检查 04 有成文答案 |
| 零依赖校验器 | `tools/validate.py` | `待填写` | `待填写` | `待填写` | 15 正例通过、18 负例按声明原因被拒 |
| 样例套件 | `docs/interfaces/samples/**` | `待填写` | `待填写` | `待填写` | 四类请求响应 + 六种状态 + 产物记录齐备 |
| 单元测试 | `tests/test_validate.py` | `待填写` | `待填写` | `待填写` | 27 项全绿 |
| 设计记录 | `docs/adr/ADR-001..006` | `待填写` | `待填写` | `待填写` | 六份，第 13 页四段式 |
| 流程文档 | `docs/BACKLOG.md`、`docs/AI_USAGE.md`、`docs/VALIDATION.md` | `待填写` | `待填写` | `待填写` | 第 12、14 页格式 |

> SHA 与 Issue/PR 号在提交后回填。回填本身会形成一次追加提交，
> 因此表中 SHA 指向**交付内容所在的那次提交**，不是回填提交。

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
- [ ] 各工作项的 Commit SHA
- [ ] Issue 编号与 PR 链接
- [ ] 三轮课堂交换的结论（第 16 页）落到 ADR 与 BACKLOG
