# A1 E3 发布与个人贡献记录

日期：2026-09-30（Asia/Shanghai）。作者：谢浩天（241250033，A1）。
执行方式：使用 Codex 辅助准备样本、保存日志、复核与发布。

## 发布目标与提交追溯

- 仓库：[Lee-bx-06/devops-2026](https://github.com/Lee-bx-06/devops-2026)
- 分支：`main`
- E3 内容提交：[`de31c63b96d969d5c71da1d172b0786d9b8a351a`](https://github.com/Lee-bx-06/devops-2026/commit/de31c63b96d969d5c71da1d172b0786d9b8a351a)
- 提交说明：`feat(A1): add reproducible E3 dependency baselines and evidence`
- 父提交：`071d637b8a54aeb82a3282d2321fcd4a30aa3228`，即发布准备时的最新共享主分支。
- 本文件与链接补充构成随后的一次文档提交；个人内容贡献引用上面的内容提交。
- 原本地 `a1-e2-coordination-closeout` 分支及 `7ae820c` E2 收尾提交保留。
- 推送采用普通 fast-forward；远端发布结果由本页所在 `main` 和 GitHub 提交历史核验。

## A1 交付清单

| 内容 | 位置 | 用途 |
| --- | --- | --- |
| 一键基线运行器 | `scripts/run_baseline.py` | 每次创建新目录，执行构建/行为断言，保存命令与失败诊断 |
| MD/RD 故障项目 | `fixtures/md-rd/` | config.h 漏声明、unused.h 冗余声明 |
| 三份连续版本源码 | `fixtures/commits/C0/`、`C1/`、`C2/` | 正确起点、新增 include、仅改变编译参数 |
| 人工预期 | `evidence/run-20260930T023602Z-c2ff9588/oracle.json` | COURSE_DERIVED_ORACLE，限定 main.o 的项目依赖 |
| 实测命令及日志 | 同一证据目录的 `commands.json`、`logs/` | 保存实际 argv、cwd、退出码、stdout/stderr |
| 系统、工具、哈希与时间戳 | 同一证据目录的 `manifest.json` | 确认固定环境、输入与 make 前的修改时间关系 |
| 可还原真实提交的 bundle | 同一证据目录的 `bundles/` | 还原 MD/RD 初始版和 C0/C1/C2 的确切 SHA |
| 运行器故障验收 | 同一证据目录的 `validation/`、`validation.json` | 错误输出与缺少工具均失败且保留诊断 |
| 复现与协作说明 | `README.md`、`STATUS.md`、`COORDINATION.md` | 指引复跑和版本恢复，记录未验证范围及负责人问题 |

人工标签与真实运行分开保存，不把 oracle 当成 BuildChecker/EChecker 实际检测结果。
独立实验仓库采用明确的自动化 fixture 作者身份；主项目个人贡献由本页内容提交追溯。

## 发布前验证

1. 从最新主分支的隔离副本添加 E3 内容并运行 `make check`：25 个正例、24 个负例校验通过，77 项单元测试通过。
2. 在该发布副本完整执行 `python3 e3/scripts/run_baseline.py --output-root /tmp/e3-publish.cEHjDq/baseline-runs`，退出码 0；运行目录 `run-20260930T024735Z-bff6a2e2`。
3. 前序独立完整运行、选定证据的 bundle 还原、源版本与时间戳核对，以及两个故障注入检查均已通过，详见证据目录的 `validation.json`。
4. 发布清单只涉及根 README 的入口和 `e3/`；生成的工作副本、嵌套 .git、编译产物和 Python 缓存不入库。
5. 两份 Git bundle 的 SHA-256 与原始 manifest 一致；C2 相对 C1 仅改变 Makefile 中的 `CFLAGS`。

## 已验证行为

| 场景 | 实际观察 |
| --- | --- |
| MD/RD 初始构建 | 输出 1 |
| 只修改 config.h 为 VALUE 2 | 增量仍为 1，clean build 为 2 |
| 只修改 unused.h 注释 | 再次编译 main.o，功能输出仍为 2 |
| C0 | 输出 10 |
| C1 | 输出 12；人工预期为 feature.h 的 MD |
| C2 增加 -DMODE=7 | 保留 C1 产物时增量输出 12，clean build 为 19 |

C2 说明普通 Make 时间戳检查可能漏掉命令变化；这份样例本身尚未运行 EChecker。

## A1 现在完成了什么，下一步交给谁

A1 已准备可分享的固定输入、预期答案、复现入口、真实源版本和构建证据。
这些材料支持 E3 的并行准备，并可作为 A2/A3/B3 复核和后续实现的输入。

- A2：复核 MD/RD 人工依据、在 Linux 采集原始系统调用跟踪，并后续产出实际检测图和报告。
- A3 与 B2（必要时 A2）：确认仓库内 CFLAGS 变化如何归类，以及原始配置快照怎样映射到 configuration_id。
- B3：按确切源版本消费固定 MD 人工预期，准备修复和拒绝样本；本页不代替 B3 确认。
- 四服务真实检测、修复或跨组下载的验收应在相应后续阶段单独保存证据。

本次实测平台为 macOS arm64、GNU Make 3.81、Apple clang 21、Python 3.14.6。
Linux 跟踪、服务实现与跨组实际消费尚未验证。
