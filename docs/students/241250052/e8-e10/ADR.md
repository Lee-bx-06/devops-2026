# 决策记录

背景与约束：

实验目标是把依赖声明诊断、候选补丁生成和接受判断分开。受测项目是显式 C/Make 样例，使用本地 GCC 依赖输出；实验要求在拒绝时保持源目录不变，并让报告与具体 commit 绑定。

选择与替代方案：

- A：每条 MD 报告绑定被测项目 HEAD。扫描或生成前比较 commit，不一致即返回 `STALE_REPORT`。替代方案是只比较文件名或内容摘要，但无法清晰表达报告针对的版本，因此未采用。
- B：生成补丁时不直接修改源树；在独立 sandbox 中依次执行 patch check、构建、程序测试、头文件变化增量构建和重检。所有检查成功后才写回源 `Makefile`。替代方案是先在源目录应用、失败后再回滚，但任何中断都可能留下部分写入，因此未采用。
- B：遇到纯变量声明（如 `main.o: $(DEPS)`）时修改 `DEPS` 定义；遇到混合声明时修改目标依赖行并保留宏引用。这样分别验证变量修复和目标修复。共享变量可能被多个目标使用，故报告记录 style 与 target，不将其解释为只影响单一路径。

代价与覆盖范围：

- commit 检查会拒绝旧报告，要求重新扫描，增加一次完整检查，但能防止错版本修复。
- sandbox 验证需要复制项目并重复构建，成本高于原地试改，但保证拒绝路径可恢复。
- 当前只处理显式目标和受支持 CFLAGS；不支持隐式规则、模式规则、order-only 依赖、复杂条件语法和跨目录生成规则。

验证命令与实际证据：

- E8：`work/e8-B-manual.lXCX28` 中 `expected-failure.json` 为 `STALE_REPORT`，源 `project` 的 `git status` 为空。
- E9：`work/e9-B-manual.3CJ2vc` 中三份 plan 的 style 分别为 direct/macro/mixed；三份 `git apply --check` 均通过，`apply-demo` 修改副本而原 macro 项目未改。
- E10：`work/e10-B-manual.eqvh2V/results.csv` 为 3/3 `True`；`source-before.Makefile` 与测试拒绝后的源文件 `cmp` 为 0，`source-after-accept.Makefile` 与坏 patch 拒绝后的源文件 `cmp` 为 0。
- 单元测试：8 项全部通过，含编译失败拒绝回归用例。
