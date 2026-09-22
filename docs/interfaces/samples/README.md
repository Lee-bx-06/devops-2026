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
| 用途 | `request` / `job-succeeded` / `job-succeeded-rejected` / `accepted-queued` / `running` / `failed` / `timed-out` / `cancelled` / … | 该文档演示什么 |

**分隔符统一用点号 `.`，不用连字符 `-`。** 连字符已经用在段内
（`full-check`、`job-succeeded`），再用它做段分隔会让文件名无法机械解析。
`tools/validate.py` 的覆盖度检查和 `tests/test_validate.py` 都按
`{service}.request.json` / `{service}.job-succeeded.json` 这个规则定位文件，
改名会直接让测试失败。

负例放在 `invalid/`，用**描述性连字符名**（如 `missing-baseline.json`），
文件名即它守护的那条规则；每个负例必须带 `expected_error` 声明期望的拒绝原因。

下划线开头的键（`_note`、`expected_error`）是给人看的注解，校验前会被剥离，
不属于线上载荷。

## 二、当前状态：DRAFT 已收敛为一套 canonical 样例

| 文件 | 来源 | 命名 | 状态 |
| --- | --- | --- | --- |
| `draft.request.json` | A1/B2 | 符合规范 | **唯一规范请求** |
| `draft.job-succeeded.json` | A1/B2 | 符合规范 | **唯一规范成功响应** |
| `draft.job-failed.json` | B2 | 符合规范 | 环境失败/迭代耗尽响应 |

旧的 `draft-request.json`、`draft-response.json` 已删除，
`draft-failed-response.json` 已按点号规范改名。专项测试会在重复请求或成功响应
再次出现时失败。

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

最终处理：

1. `task.schema.json` 的 `output_draft` 正式要求 `environment` 与独立的 `build`，
   两者均为成功响应必填字段。
2. `draft.job-succeeded.json` 的这两个对象与 `full-check.request.json` 对应对象全等，
   形成 DRAFT → FULL_CHECK 的直接交接链。
3. `tools/validate.py` 与专项测试会拒绝缺字段、浮动 `latest`、相对工作目录、
   命令语义重叠和跨字段不一致。

## 四、`configuration_id` 取值已按 A2–B2 v0.1 收敛

| 出处 | 值 |
| --- | --- |
| canonical DRAFT 输出 | `cc-gcc13-release-6f12a4c8` |
| canonical FULL_CHECK 输入 | `cc-gcc13-release-6f12a4c8` |

该值采用 `cc-<build-profile>-<normalized-config-hash>` 形式，只描述标准化构建配置，
不包含 commit、Job ID 或随机 UUID。相同配置可跨 Job、轮次和 commit 稳定复用；
基础镜像、工具链、依赖集或构建参数变化时才生成新值。

## 五、B2 已完成的三件事

A1 没有擅自删除或改名 B2 文件；以下操作已由 B2 在自己的分支完成：

1. **`draft-failed-response.json` → `draft.job-failed.json`**
   保留独有的失败样例并按规范改名。
2. **`draft-request.json` 与 `draft-response.json`：与 A1 版本二选一后删除另一份。**
   保留点号命名的规范文件，并把 B2 的环境、构建、轮次与制品信息合并进去。
3. **同步更新 `ADR-007` 与 `CONTRIBUTIONS.md` 里的文件名引用。**

上述修改通过 B2 的 Issue + PR 请求 A2 复核，不直接推送 `main`。

## 六、新增样例时的检查清单

- [ ] 文件名符合第一节规范
- [ ] 正例放本目录，负例放 `invalid/` 且带 `expected_error`
- [ ] `python3 tools/validate.py 你的文件.json` 单文件先过一遍
- [ ] `make check` 全绿
- [ ] 若新增了某类 `job_type` 的请求或成功响应，确认没有与既有样例重复
- [ ] `input` / `output` 内部字段可自行扩展（ADR-004），但顶层信封不得加字段
- [ ] 涉及的 `configuration_id`、`image_uri`、`commit` 与上下游样例逐字一致
