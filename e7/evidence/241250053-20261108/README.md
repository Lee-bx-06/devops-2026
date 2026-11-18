# B2 E7 精简证据

本目录对应赵润昊（241250053）的 B 轨道 E7 实验。

- 服务器执行提交：`96a19af49d072600305bfdfbbaa1aaf809894757`
- 故意失败提交：`b5d6170056006e5f0d949e6af387f83fd8db86c0`
- 修复恢复提交：`1150e8ffb4a0395c9ad940251078a732ba617091`
- PR：<https://github.com/Lee-bx-06/devops-2026/pull/55>
- 六项门禁：全部 `passed=true`
- 服务测试：服务器 27 passed；修复后本地与 CI 28 passed

`gate-result.json`、各场景 `result.json`、超时清理日志和三次 CI 摘要为精简可审查证据。完整 `work/`、CI 日志和 artifact 单独保存在仓库外的 `B2_E7_241250053_work/`，避免把大量运行产物提交进 Git。

`main-effective-rules.json` 为 `[]`；当前账号 `admin=false`，无法配置保护。故意失败时未执行可能真实合并错误代码的命令，详见 `merge-attempt-safety-note.txt`。
