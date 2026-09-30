# E3 A1 基线参考样例

本目录提供一个可重复运行的依赖检测参考样例。它用于 A1 与 A2/A3 对齐输入、提交和证据的形状，不是 BuildChecker、EChecker 或 Makefile 修复服务的实现，也不代表 Linux `ptrace` 检测结果。

[A1 完成记录](STATUS.md)列出已验证内容、真实提交 SHA 和待协作事项。
[发布与个人贡献记录](PUBLICATION.md)给出主项目内容提交、发布前验证及责任边界。
[本次实测证据](evidence/run-20260930T023602Z-c2ff9588/README.md)保留命令、日志和可恢复确切版本的 bundle。
样例根据课程《E3 并行测试基线》课件人工整理，没有使用原实验包或声称原实验包已验证。

## 运行

需要 Python 3 和 GNU Make、C 编译器、Git。运行：

```sh
python3 e3/scripts/run_baseline.py
```

默认在 `e3/work/` 下创建全新 `run-*` 目录。也可指定父目录：

```sh
python3 e3/scripts/run_baseline.py --output-root /tmp/e3-runs
```

每次运行都创建新目录，不覆盖或删除已有结果。脚本在成功或失败时写入 `manifest.json`；命令及其 argv、cwd、退出码、stdout/stderr 保存在 `commands.json` 和 `logs/`。失败时退出码非零，并保留现场供诊断。

## 样例阶段

`md-rd` 阶段先 clean build 并运行程序，随后只修改 `config.h`，再只 clean build，最后只修改未使用的 `unused.h` 并观察编译器是否重新编译 `main.o`。声明依赖故意包含 `unused.h`、遗漏实际 include 的 `config.h`。样例观察的是 Make 的增量行为，不声称捕获了实际文件访问图。

`commits` 阶段在运行目录建立独立本地 Git 仓库和真实顺序提交 C0、C1、C2。C0 输出 `10`；C1 加入未声明的 `feature.h` 并输出 `12`；C2 仅改变 `CFLAGS`，普通增量构建仍输出 `12`，clean build 后输出 `19`。配置变化通过原始 Makefile 与 `make -n -B main.o` 命令快照展示。两套仓库都导出并验证 Git bundle，随后在临时恢复仓库中核对标签指向的提交。

`oracle.json` 是独立的、基于课程材料整理的预期答案：项目依赖边仅涉及项目文件，不包含系统头文件。它不是检测器输出。`manifest.json` 的命令记录和观察值才是本次运行证据。样例中的人工预期图没有由工具生成，故不计算准确率或误报率。

运行成功后，终端会打印实际运行目录。以下命令在项目根目录执行，使用已保存的实测证据恢复确切版本；也可把 `E3_EVIDENCE` 改为新运行目录的绝对路径：

```sh
E3_EVIDENCE="$(pwd)/e3/evidence/run-20260930T023602Z-c2ff9588"
E3_RESTORE="$(mktemp -d /tmp/e3-replay.XXXXXX)"
git clone "$E3_EVIDENCE/bundles/md-rd.bundle" "$E3_RESTORE/md-rd"
git -C "$E3_RESTORE/md-rd" bundle verify "$E3_EVIDENCE/bundles/md-rd.bundle"
git -C "$E3_RESTORE/md-rd" rev-parse 'refs/tags/MD-RD-INITIAL^{commit}'

git clone "$E3_EVIDENCE/bundles/commits.bundle" "$E3_RESTORE/commits"
git -C "$E3_RESTORE/commits" bundle verify "$E3_EVIDENCE/bundles/commits.bundle"
git -C "$E3_RESTORE/commits" show-ref --tags
git -C "$E3_RESTORE/commits" checkout C1
```

manifest 同时记录原始提交 SHA 与 bundle 重放后各标签解析出的 SHA，便于逐项核对。
恢复后若要观察 C2 的旧产物，先在 C1 运行 `make clean`、`make` 和 `./app`，
再切换到 C2，直接运行 `make` 和 `./app`；此步骤之间不要 clean。

## 边界与待协作事项

- 本机环境可能是 macOS；这里没有 Linux `ptrace` 证据，也没有服务实现。
- `configuration_id` 暂不生成或推断。ADR-007 将构建参数列入配置标识的变化因素，EChecker 又把仓库内命令变化作为分析输入；本样例保留 flags 和配置快照，由 A3/B2 确认本次变化的归类和映射。
- A1 交付的是共享参考样例。它不代表 A2 已提供 BuildChecker 服务或 A3 已提供 EChecker 服务，也不替代他人复核。
- `COORDINATION.md` 记录需要责任人确认的开放项。
