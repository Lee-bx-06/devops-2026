# E3 协作待确认

此基线是 A1 准备的共享参考样例，不表示 A2/A3 服务实现或相关交付已完成。

## 待 A3 / B2 对齐（必要时请 A2 作为基线产出方参与）

- 请区分外部冻结环境（工具链、依赖和环境参数）与仓库内供 EChecker 分析的构建定义。C1→C2 只在仓库 Makefile 中改变 `CFLAGS`；样例保留原始 Makefile 和 `make -n -B main.o` 命令快照，没有自行推断 `configuration_id`。
- 请确认仓库内 `CFLAGS` 变化应如何分类，以及如何将原始配置快照映射到 `configuration_id`。
- 请确认本样例后续若被 A3 消费，应使用哪个确切的基线 commit、configuration ID 和 artifact。当前样例没有构造基线 artifact 或服务输出。
- 请确认本地平台生成的参考样例可供接口字段和预期 finding 讨论使用；它不是 Linux BuildChecker 实测图或 A3 实现验收证据。

## 证据边界

预期 oracle 为人工整理的课程派生答案。Make 命令及程序输出由运行器实测记录。运行器不生成实际依赖图、不声称 `ptrace` 覆盖，也不生成服务产物、假 SHA 或假 configuration ID。
