# A1 E3 完成记录

日期：2026-09-30（Asia/Shanghai）。负责人：A1；执行方式：通过 Codex 准备样本并在本机运行。

## 已完成

- 提供 MD/RD 故障项目及 C0/C1/C2 三份源版本，限定 main.o 的项目文件依赖。
- 人工预期使用 COURSE_DERIVED_ORACLE，实际命令、输出、退出码和时间戳另行记录。
- 运行器每次创建新目录；保存系统、架构、工具版本、源码及运行器哈希。
- 创建独立实验 Git 历史和标签，导出两份 bundle，验证克隆还原后的 SHA 相同。
- 保存一份可随项目分享的实测证据及运行器故障注入记录。
- 两次独立完整运行通过；故障输出与缺少工具的路径均正确返回失败并保留诊断。
- 本地 E2 检查和最新远端主分支副本叠加 e3 后的 E2 检查均通过，日志见证据目录。

## 实际观察

| 场景 | 观察 | 依据 |
| --- | --- | --- |
| MD/RD 初始构建 | 输出 1 | make 与程序日志 |
| 只把 config.h 的 VALUE 改为 2 | 增量仍为 1；clean build 为 2 | 命令日志与 make 前文件时间戳 |
| 只修改 unused.h 注释 | main.o 重新编译，输出仍为 2 | 编译命令与文件时间戳 |
| C0 | clean build 输出 10 | 对应真实源提交与程序日志 |
| C1 新增 feature.h include | clean build 输出 12；人工预期缺失 feature.h 依赖 | 源码、Makefile 和 oracle |
| C2 只增加 -DMODE=7 | 沿用 C1 产物时增量输出 12；clean build 为 19 | C1/C2 diff、强制预演命令、实测日志 |

## 可还原的提交

这些是独立本地实验仓库的源提交，不是主项目发布提交；作者身份明确标为自动化 fixture。

| 标签 | 完整 SHA |
| --- | --- |
| MD-RD-INITIAL | a5b6b42dd7ef5fa52a6d9eeb112b541cd24064cb |
| C0 | b96ccadeed36ec72eca1901895a13ddb56990d4b |
| C1 | 06185dafc5bb05254cb83a040fcb043de07b1eb6 |
| C2 | f5949ebfabf41565f7416a8b843160e5f1e6f7a4 |

[本次证据](evidence/run-20260930T023602Z-c2ff9588/README.md)包含 manifest、oracle、commands、日志、bundle 和 validation.json。
新运行会产生自己的真实 SHA；用已保存的 bundle 可以保持本表版本不变。

## 待协作与未验证范围

- A2 可复核 MD/RD 人工依据并在 Linux 采集系统调用跟踪；当前只验证 macOS 构建行为。
- A3/B2（必要时 A2）需要确认仓库内 CFLAGS 变化与 configuration_id 的关系，见 [协作问题](COORDINATION.md)。
- 本次没有 BuildChecker/EChecker 实际图或检测结果，也没有 DRAFT/MDFixer 服务验收。
- A1 已可用固定样本与人工 MD 预期对接 B3；这里不宣称对方已读取或接受。
- 上游核查基准是 071d637b8a54aeb82a3282d2321fcd4a30aa3228；原本地分支和 E2 收尾提交保留。
- 个人贡献的主项目内容提交为 de31c63b96d969d5c71da1d172b0786d9b8a351a，见 [发布记录](PUBLICATION.md)；不能用上表的实验提交代替。
