# 样例目录说明与命名规范

小组 A09 ｜ 配对组 第 9 组（`pair09`）｜ 本目录负责人：**A1（谢浩天）**
本文件由 A1 于 2026-09-21 补写，用于解决 DRAFT 样例两套并存的问题。

## 一、命名规范（以 A1 现有点号命名为准）

```
{服务或状态}.{用途}.json
```

| 段 | 取值 | 说明 |
| --- | --- | --- |
| 服务 | `draft` / `full-check` / `incremental-check` / `repair` | `job_type` 的 kebab-case，与第 27 页端点名同构 |
| 状态 | `job` | 不属于某一类服务、只演示状态或错误码的 Job 文档 |
| 状态 | `artifact` | 独立的 `artifact_record` |
| 用途 | `request` / `job-succeeded` / `accepted-queued` / `running` / `failed` / `timed-out` / `cancelled` / … | 该文档演示什么 |

**分隔符统一用点号 `.`，不用连字符 `-`。** 连字符已经用在段内
（`full-check`、`job-succeeded`），再用它做段分隔会让文件名无法机械解析。
`tools/validate.py` 的覆盖度检查和 `tests/test_validate.py` 都按
`{service}.request.json` / `{service}.job-succeeded.json` 这个规则定位文件，
改名会直接让测试失败。

负例放在 `invalid/`，用**描述性连字符名**（如 `missing-baseline.json`），
文件名即它守护的那条规则；每个负例必须带 `expected_error` 声明期望的拒绝原因。

下划线开头的键（`_note`、`expected_error`）是给人看的注解，校验前会被剥离，
不属于线上载荷。

## 二、当前状态：DRAFT 有两套样例并存

| 文件 | 来源 | 命名 | 状态 |
| --- | --- | --- | --- |
| `draft.request.json` | A1 | 符合规范 | **规范版本** |
| `draft.job-succeeded.json` | A1 | 符合规范 | **规范版本** |
| `draft-request.json` | B2（`d05ee38`） | 连字符 | 内容重复，待处理 |
| `draft-response.json` | B2（`d05ee38`） | 连字符 | 内容重复，待处理 |
| `draft-failed-response.json` | B2（`d05ee38`） | 连字符 | **内容不重复，应保留** |

两套都能通过 `tools/validate.py`，所以 `make check` 是绿的——
问题不在合法性，在于下游拿到两份 DRAFT 请求样例时不知道以哪份为准。

## 三、A1 的判断：命名以 A1 为准，但 B2 有一处内容比 A1 的好

**必须如实说明：B2 的 `draft-response.json` 里有一个字段是 A1 的样例缺失的，
而且这个缺失是 A1 的疏漏。**

B2 在 `output` 里写了 `environment`：

```json
"environment": {
  "image_uri": "registry.pair09.local/demo-make-project:9f8e7d6c",
  "configuration_id": "draft-gcc13-release-9f8e7d6c",
  "project_root": "/workspace/project",
  "clean_command": "make clean && make all"
}
```

第 21 页规定 `FULL_CHECK` 的输入需要「可运行镜像与 `configuration_id`」，
第 22 页规定 `INCREMENTAL_CHECK` 的 `baseline` 需要 `configuration_id`。
这些值的**唯一来源**就是 DRAFT 的输出。A1 原来的 `draft.job-succeeded.json`
根本没有产出 `environment`，等于把 DRAFT → BuildChecker 这条交接链断在了契约里——
A2 无从得知自己要消费的 `configuration_id` 是谁给的、长什么样。

已做的处理：

1. `task.schema.json` 新增 `$defs.produced_environment`，并挂到 `output_draft.environment`，
   使该字段可被校验（此前它是自由字段）。依 ADR-004，`output` 内部属服务负责人，
   因此**定为可选而非必填**；是否升为必填请 B2 决定。
2. `draft.job-succeeded.json` 已补入 `output.environment`，A1 侧的
   DRAFT → FULL_CHECK → INCREMENTAL_CHECK 交接链现在完整。
3. `tools/validate.py` 增加对 `output.environment` 的形状检查。

## 四、一处需要 B2 与 A2 一起定的分歧：`configuration_id` 取值

| 出处 | 值 |
| --- | --- |
| A1 全部样例 | `cc-MODE0` |
| B2 的 `draft-*.json` | `draft-gcc13-release-9f8e7d6c` |

A1 用 `cc-MODE0` 是因为第 22 页的原文样例就是这个值：

```json
"baseline": { "configuration_id": "cc-MODE0" }
```

B2 的取值更具描述性（编码了编译器、构建类型与 commit），从工程角度更好。
但**这个值必须全组统一**：`FULL_CHECK` 的 `input.environment.configuration_id`
要逐字等于 DRAFT 输出的那个值，`INCREMENTAL_CHECK` 的基线匹配也靠它
（第 21、22 页，以及 B1 在 `endpoints.md` 末尾补的一致性规则）。
两边各用一个值，交接就对不上。

A1 的建议：**采用 B2 的描述性格式，但由 DRAFT 单一产出、下游逐字引用**，
即 A1 样例里的 `cc-MODE0` 改为 B2 风格的值。这需要 B2 确认格式、A2 确认消费方式，
已记入 `../../BACKLOG.md`。在三人达成一致前，A1 样例暂留 `cc-MODE0`
以保持与第 22 页原文可对照。

## 五、请 B2 做的三件事

A1 **没有**删除或改名 B2 的任何文件——`draft-request.json` 等三个文件被
B2 自己的 `ADR-007-draft-buildchecker-contract.md`（第 23、35、69 行）和
`CONTRIBUTIONS.md`（第 102–104 行）引用，擅自改名会连带弄坏 B2 的文档。
这属于 B2 的所有权范围，应由 B2 执行：

1. **`draft-failed-response.json` → `draft.job-failed.json`**
   这个文件内容不重复（A1 没有 DRAFT 的失败样例，只有 `job.failed.json`
   用的是 `FULL_CHECK`），**应当保留**，只需改名以符合规范。
2. **`draft-request.json` 与 `draft-response.json`：与 A1 版本二选一后删除另一份。**
   A1 建议保留 A1 的 `draft.request.json` / `draft.job-succeeded.json`
   作为规范版本（它们被 `tests/` 与 `endpoints.md` 引用），
   并把 B2 版本中更好的内容——即 `output.environment`——合并进来。
   **这一步 A1 已经做完了**（见第三节），所以 B2 只需删除自己那两个文件，
   不会丢失任何信息。若 B2 认为还有别的内容值得保留，请提 PR 合并进规范版本。
3. **同步更新 `ADR-007` 与 `CONTRIBUTIONS.md` 里的文件名引用。**

若 B2 更希望由 A1 代为改名，请在 Issue 里说明，A1 会连同 `ADR-007`
的三处引用一起改，并在 `CONTRIBUTIONS.md` 注明改动归属，不冒认 B2 的工作。

## 六、新增样例时的检查清单

- [ ] 文件名符合第一节规范
- [ ] 正例放本目录，负例放 `invalid/` 且带 `expected_error`
- [ ] `python3 tools/validate.py 你的文件.json` 单文件先过一遍
- [ ] `make check` 全绿
- [ ] 若新增了某类 `job_type` 的请求或成功响应，确认没有与既有样例重复
- [ ] `input` / `output` 内部字段可自行扩展（ADR-004），但顶层信封不得加字段
- [ ] 涉及的 `configuration_id`、`image_uri`、`commit` 与上下游样例逐字一致
