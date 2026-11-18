# DevOps E6 论文 1 MVP 报告：DRAFT

## 1. 基本信息

| 项目 | 内容 |
| --- | --- |
| 小组 | B09 |
| 轨道 | B，DRAFT |
| 报告负责人 | 李秉轩，241250052 |
| 实验日期 | 2026-11-04 至 2026-11-06 |
| 运行环境 | Ubuntu 云主机，x86_64 |
| Docker | 29.1.3 |
| 运行目录 | `e5/reference-b` |

本报告只覆盖 E6。E5 用作候选来源，E7 的故障场景和 CI 门禁不在本次提交范围内。

## 2. E6 目标与通过标准

E6 自动执行以下流程：

1. 读取 E5 保存的修复候选。
2. 第一轮使用初始 Dockerfile，必须真实复现 `MISSING_MAKE`。
3. 第二轮使用候选 Dockerfile 构建成功。
4. 保存第二轮生成的完整镜像 ID。
5. 使用同一个镜像 ID，在 `--network none` 下运行程序。
6. 验证退出码为 `0`、stdout 为 `hello E3`、`output_matches=true`。

组内技术验收状态：

| 成员 | 状态 | trace / 镜像 |
| --- | --- | --- |
| B1 李秉轩 | PASS | `e6-b-a3ff8e26b8b74670959b024ae3b9be78` |
| B2 赵润昊 | PASS | `e6-b-5c213473b24f4a6fa39051bf63680fb3` |
| B3 赵心泉 | PASS | `e6-b-bbaa076742bf4f41b05b70d4cea01c9d` |

三人的结构化证据均通过 `verify_e6_b_evidence.py`；该脚本验证保存证据的一致性，不替代原始 Docker 运行。

## 3. B1 李秉轩

### 3.1 输入和追溯

- 仓库：https://github.com/Lee-bx-06/devops-2026
- E6 实际运行提交：`88d97a799e08eb6acd1bcfb4b9c2127e078d7a20`
- 候选：`e5/reference-b/work/b01/candidate/Dockerfile`
- 候选 SHA-256：`5e28da373adeb6e649ddf00f122b08d0d5c39ab41b041d3e6e72370c910c0452`
- 服务测试：`24 passed`

### 3.2 自动构建结果

| 项目 | 实际值 |
| --- | --- |
| `trace_id` | `e6-b-a3ff8e26b8b74670959b024ae3b9be78` |
| 第一轮失败分类 | `MISSING_MAKE` |
| 第一轮构建退出码 | `1` |
| 第二轮构建退出码 | `0` |
| 第二轮镜像 ID | `sha256:cd1759adc087e51df671f7d6e83878c8e935881c400ea05564083eb31d7f8516` |
| 禁网运行退出码 | `0` |
| stdout | `hello E3\n` |
| `output_matches` | `true` |
| 证据一致性校验 | `passed=true` |

B1 证据：

```text
e5/reference-b/work/b01/e6-01/evidence/
```

## 4. B2 赵润昊

### 4.1 输入和追溯

- 实验基线：`30cca975e6d98c165fa46acd5df68200a4990a7a`
- 实验代码提交：`2e7d575763a80925ea720313b94d4a5d251f2917`
- PR：https://github.com/Lee-bx-06/devops-2026/pull/53
- PR 状态：已由 B1 Review 并合并
- 合并提交：`5efb40d0573b5043070806769edcbfc89d2ce5d7`
- 合并时间：`2026-11-06T11:04:22Z`
- 候选 SHA-256：`5e28da373adeb6e649ddf00f122b08d0d5c39ab41b041d3e6e72370c910c0452`
- 完整运行归档 SHA-256：`15abcf0611a0165023f19a5c944810e0d4f484235466dcade42d6cf06573b035`

### 4.2 自动构建结果

| 项目 | 实际值 |
| --- | --- |
| `trace_id` | `e6-b-5c213473b24f4a6fa39051bf63680fb3` |
| 第一轮失败分类 | `MISSING_MAKE` |
| 第一轮构建退出码 | `1` |
| 第二轮构建退出码 | `0` |
| 第二轮镜像 ID | `sha256:11738ba730ce644d0c89b891bfb37c9a6dfb98f41c73e15fed47c060d835d58d` |
| 禁网运行退出码 | `0` |
| stdout | `hello E3\n` |
| `output_matches` | `true` |
| 证据一致性校验 | `passed=true` |

B2 新增测试：

```text
e5/reference-b/services/draft/tests/test_e6_b2_241250053.py
```

新增测试阻止包含第二个 `FROM` 的多阶段候选，确认候选在 Docker 构建前被拒绝。加入测试并重建服务镜像后为 `26 passed`。

材料：

```text
e6/REPORT-241250053.md
e6/submissions/241250053/E6-ACCEPTANCE-241250053.csv
e6/submissions/241250053/E6-CANDIDATE-SOURCE-241250053.json
e6/submissions/241250053/B2_E6_241250053_work_2e7d575.tar.gz
```

## 5. B3 赵心泉

### 5.1 输入和追溯

- 个人仓库：https://git.nju.edu.cn/Varecia/devops-26-personal.git
- 实验提交：`f7d169e02aa81a1eb848eed88de12969313047fc`
- 候选 SHA-256：`9989b8495ffebb2fc45580691b13efed697788234a92dffb40578d702634bd17`
- E6 证据包 SHA-256：`7a762246fe5ca8a67cbea54d41774d3ac70ab4baa7193576fa86693714b739c5`
- 测试源码 patch SHA-256：`7a49d09812b3527d57bcdbddf77f5c90f67bffd49ce112033ad14163037d6677`
- B2 PR #53 复核链接：https://github.com/Lee-bx-06/devops-2026/pull/53#issuecomment-6685641449

### 5.2 自动构建结果

| 项目 | 实际值 |
| --- | --- |
| `trace_id` | `e6-b-bbaa076742bf4f41b05b70d4cea01c9d` |
| 第一轮失败分类 | `MISSING_MAKE` |
| 第一轮构建退出码 | `1` |
| 第二轮构建退出码 | `0` |
| 第二轮镜像 ID | `sha256:c8e330003e55629d1a06f86f591cde0f9c60b447ac56fc8fad336f0a6e0246d4` |
| 禁网运行退出码 | `0` |
| stdout | `hello E3` |
| `output_matches` | `true` |
| 证据一致性校验 | 由 B1 使用课程校验脚本复核，`passed=true` |
| 服务测试 | `25 passed` |

B3 新增 `test_changed_workdir_rejected`，用于检查候选修改 `WORKDIR` 时被拒绝。源码 patch 已收到并归档，测试结果为 `25 passed`。他还在 B2 的 PR #53 下留下了独立复核记录，确认失败分类、镜像一致性、禁网运行和新增测试逻辑。

材料：

```text
e6/submissions/241250068/E5-E6-REPORT-241250068.md
e6/submissions/241250068/B09_241250068_E6_Evidence.zip
e6/submissions/241250068/B3_test_diff.patch
e6/submissions/241250068/B3-REVIEW-PR53.md
```

## 6. 三人结果对比

| 项目 | B1 | B2 | B3 |
| --- | --- | --- | --- |
| 第一轮 | `MISSING_MAKE`，exit=1 | `MISSING_MAKE`，exit=1 | `MISSING_MAKE`，exit=1 |
| 第二轮 | build=0 | build=0 | build=0 |
| 镜像 | 构建后保存并复用 | 构建后保存并复用 | 构建后保存并复用 |
| 禁网运行 | exit=0，`hello E3` | exit=0，`hello E3` | exit=0，`hello E3` |
| 输出校验 | `true` | `true` | `true` |
| 服务测试 | 24 passed | 26 passed（含新增测试） | 25 passed（含新增测试） |

镜像 ID 不同是正常现象，因为各成员使用了不同候选内容和构建上下文；相同的是同一成员构建与运行的镜像 ID。

## 7. 验证范围与限制

- 本轮验证的是 DRAFT 的两轮候选构建与运行闭环，不是论文全部 35 个项目。
- 证据校验脚本检查保存文件的一致性，不重新执行 Docker。
- B2、B3 的 E6 运行各自包含新增测试，因此服务测试数与 B1 不同。
- 环境网络故障和真实目标故障必须区分；有效失败必须是缺少 `make`。

## 8. 证据索引

| 成员 | 证据路径 | 状态 |
| --- | --- | --- |
| B1 | `e5/reference-b/work/b01/e6-01/evidence/` | PASS |
| B2 | `e6/evidence/241250053-20261106/` 与 `e6/submissions/241250053/B2_E6_241250053_work_2e7d575.tar.gz` | PASS |
| B3 | `e6/submissions/241250068/B09_241250068_E6_Evidence.zip`、`B3_test_diff.patch`、`B3-REVIEW-PR53.md` | PASS |

## 9. 当前集成状态

1. B2 PR #53 已完成 B1 Review 并合并。
2. B3 已提供测试源码 patch，并完成对 B2 证据的正式复核。
3. B2 合并后的 `main@5efb40d0573b5043070806769edcbfc89d2ce5d7` 上，`e7-b-quality-gate` 运行成功。
4. E6 报告、验收表和三人证据现已齐全；创建最终报告 PR 后即可提交。
