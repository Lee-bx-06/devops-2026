# 241250053 E6 精简证据索引

本目录由赵润昊（B2 / DRAFT）于 2026-11-06 在小组 Ubuntu 云服务器上实际运行产生，实验代码提交为 `2e7d575763a80925ea720313b94d4a5d251f2917`。

- `result.json`：两轮构建和程序验证结构化结果。
- `verification.json`：证据校验脚本输出，`passed=true`。
- `iter-01-*`：首轮 `MISSING_MAKE` 的 Dockerfile 和原始日志。
- `iter-02-*`：候选 Dockerfile、构建日志和镜像 inspect 结果。
- `verify.log`：按第二轮镜像 ID 禁网运行的标准输出。
- `service-tests.log`：重建服务镜像后的 `26 passed`。
- `candidate.Dockerfile`、`model-response.txt`、`e5-candidate-provenance.json`：实际使用的 E5 候选及来源证据副本。
- `executed-commands.txt`：实际执行命令。

服务器完整 `work/` 归档单独保存为 `B2_E6_241250053_work_2e7d575.tar.gz`，SHA-256 为 `15abcf0611a0165023f19a5c944810e0d4f484235466dcade42d6cf06573b035`。
