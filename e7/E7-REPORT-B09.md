# DevOps E7 论文 1 验证报告：DRAFT

## 1. 基本信息

| 项目 | 内容 |
| --- | --- |
| 小组 | B09 |
| 轨道 | B，DRAFT |
| 报告负责人 | 李秉轩，241250052 |
| 实验日期 | 2026-11-04 至 2026-11-13 |
| 仓库 | https://github.com/Lee-bx-06/devops-2026 |
| E7 集成基线 | `4ca1f967899262b450021d03817449b9f29c8d1c` |
| 环境 | Ubuntu 22.04.5 LTS、x86_64、2 CPU、约 3.6 GiB 内存 |
| Docker | 29.1.3 |

本报告只覆盖 E7。E5、E6 作为候选构建和运行验证的输入，不重复展开。

## 2. E7 验证目标

- 验证正常候选能够完成两轮构建、同一镜像运行并输出 `hello E3`。
- 验证输出不符、无效候选、候选构建失败和运行超时。
- 验证运行超时后容器被清理。
- 验证单元测试能够发现错误预期。
- 验证 CI 失败会阻止合并，修复后可以恢复。

## 3. B1 李秉轩

### 3.1 本地门禁

| 场景 | 结果 | 工具退出码 | workflow status |
| --- | --- | --- | --- |
| 服务单元测试 | PASS | 0 | — |
| 正常候选 | PASS | 0 | `SUCCEEDED` |
| 输出不符 | PASS | 1 | `FAILED` |
| 无效候选 | PASS | 1 | `FAILED` |
| 构建失败 | PASS | 1 | `FAILED` |
| 运行超时 | PASS | 1 | `TIMED_OUT` |

整体 gate 退出码为 `0`。超时清理检查返回 `No such container`。

### 3.2 GitHub CI 与合并门禁

| 阶段 | 结果 | 证据 |
| --- | --- | --- |
| 正常 PR #48 | CI 成功并合并 | https://github.com/Lee-bx-06/devops-2026/pull/48 |
| 故意失败 PR #49 | `1 failed / 24 passed`，BLOCKED | https://github.com/Lee-bx-06/devops-2026/pull/49 |
| 真实合并拒绝 | HTTP 405 | `e7-01` 与最终 E7 证据包 |
| 修复恢复 | `25 passed` 后合并 | https://github.com/Lee-bx-06/devops-2026/pull/49 |
| 最终证据 PR #50 | 已合并 | https://github.com/Lee-bx-06/devops-2026/pull/50 |

分支保护：`e7-b-quality-gate/app15368`、`strict=true`、`enforce_admins=true`。

B1 证据位于：

```text
e7/submissions/241250052/
```

## 4. B2 赵润昊

- PR #55：https://github.com/Lee-bx-06/devops-2026/pull/55
- 合并提交：`0f96dad9ea395a9d1e9efd67941acb87e4cc19b9`
- 当前 E7 证据提交：`13b3b996295949f9250e9665dc309926a8b65560`
- 服务测试：28 passed
- 完整 work 归档 SHA-256：`a5e8e631012b36446ca3b25573e2639677162e1acd8c552235616a43bd48f3a9`

### 4.1 五场景结果

| 场景 | 结果 | 工具退出码 | workflow status |
| --- | --- | --- | --- |
| 服务单元测试 | PASS | 0 | — |
| 正常候选 | PASS | 0 | `SUCCEEDED` |
| 输出不符 | PASS | 1 | `FAILED` |
| 无效候选 | PASS | 1 | `FAILED` |
| 构建失败 | PASS | 1 | `FAILED` |
| 运行超时 | PASS | 1 | `TIMED_OUT` |

- 正常场景 trace：`e6-b-af9ad7fadbf54abd90e41b7a53e6abf2`
- 运行超时 trace：`e6-b-c8e7915d4b6d4ef0a0a5a4913b6933b7`
- 超时后检查：`No such container`

### 4.2 B2 个人 CI

- 正常：run 42450903831，成功
- 故意失败：run 42451759777，失败
- 修复恢复：run 42452024528，成功
- PR #55 的最终运行 42452667828 成功

B2 账号无仓库管理权限，因此组级分支保护与真实拒绝合并由 B1 的 PR #48–#50 证据承担。

B2 材料位于：

```text
e7/submissions/241250053/
```

## 5. B3 赵心泉

- PR #58：https://github.com/Lee-bx-06/devops-2026/pull/58
- 合并提交：`4ca1f967899262b450021d03817449b9f29c8d1c`
- 个人仓库：https://git.nju.edu.cn/Varecia/devops-26-personal.git
- 合并提交：`71901fd812fa2542c8be46569ba4fa155fa3b129`
- GitLab 失败 Pipeline：`352929`
- GitLab 恢复 Pipeline：`352933`

### 5.1 本地门禁

| 场景 | 结果 | 工具退出码 | workflow status |
| --- | --- | --- | --- |
| 服务单元测试 | PASS | 0 | — |
| 正常候选 | PASS | 0 | `SUCCEEDED` |
| 输出不符 | PASS | 1 | `FAILED` |
| 无效候选 | PASS | 1 | `FAILED` |
| 构建失败 | PASS | 1 | `FAILED` |
| 运行超时 | PASS | 1 | `TIMED_OUT` |

整体 gate 退出码为 `0`，服务测试 27 passed。超时容器已清理。

### 5.2 GitLab CI 与门禁

| 阶段 | 结果 | 证据 |
| --- | --- | --- |
| 故意失败 | `1 failed / 25 passed` | Pipeline 352929、Job 711050 |
| 修复恢复 | `26 passed` | Pipeline 352933、Job 711057 |
| MR | 已合并 | GitLab MR !1 |
| 分支保护 | `main` 已保护 | `protected-branches.json` |

B3 材料位于：

```text
e7/submissions/241250068/
```

## 6. 组内结果对照

| 项目 | B1 | B2 | B3 |
| --- | --- | --- | --- |
| 本地六项门禁 | PASS | PASS | PASS |
| 五个真实场景 | PASS | PASS | PASS |
| 超时容器清理 | PASS | PASS | PASS |
| 正常 CI | PASS | PASS | PASS |
| 故意失败 CI | PASS | PASS | PASS |
| 修复恢复 | PASS | PASS | PASS |
| 正式 Review | B1/B3 已复核 | B1/B3 已复核 | B1/B2 已复核 |

## 7. 验证范围与限制

- 本次使用单个教学 fixture，不等同于论文的完整项目集。
- 负向场景的工具退出码为 `1` 是预期行为，整体 gate 退出码必须为 `0`。
- B1、B2 在组 GitHub 仓库完成 CI；B3 在个人 GitLab 仓库完成独立 CI。两者均验证了失败阻断和修复恢复。
- 镜像 ID 和 trace ID 因成员、候选及运行环境不同而不同。

## 8. 证据索引

| 成员 | 统一目录 | 关键证据 |
| --- | --- | --- |
| B1 | `e7/submissions/241250052/` | 本地六项门禁、GitHub 正常/失败/恢复 |
| B2 | `e7/submissions/241250053/` | 本地门禁、完整 work、GitHub 个人 CI |
| B3 | `e7/submissions/241250068/` | 本地门禁、GitLab Pipeline、原始日志和保护配置 |

## 9. 提交状态

三个人均已完成 E7；B2 与 B3 的 E7 PR 已合并，组级 GitHub 分支保护仍启用。补丁已经具备 E7 验收与提交条件。
