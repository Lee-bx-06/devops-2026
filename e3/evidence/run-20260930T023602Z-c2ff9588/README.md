# A1 E3 实测证据（2026-09-30）

本目录原样保存 macOS 基线运行的 manifest、oracle、commands、stdout/stderr 和两份 Git bundle。工作目录路径为当时的真实路径；复制证据不会改写历史 cwd。重跑方法见 ../../README.md，恢复确切 SHA 请用 bundles/ 中的 Git bundle。

人工 oracle 标记为 COURSE_DERIVED_ORACLE，与命令观察分开。它不是 BuildChecker 或 EChecker 输出。validation.json 记录独立复跑、bundle/提交检查及 E2 检查。

validation/ 下的 wrong-output 与 missing-tool 是运行器验收用故障注入，分别使用 VALUE 99 和缺少 Make 的 PATH；两者预期返回失败，不能混为原始基线故障或服务检测结果。fault-injected-config.h 保存故障输入。

本目录保留日志，未复制编译产物和嵌套 .git；确切的源版本由 bundles/ 还原。
