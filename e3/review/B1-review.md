# B1 对 E3 A1 基线的独立复核（2026-10-10）

复核人：**B1（李秉轩）**，主责「公共契约与版本」。本文件是 B1 作为 A1 复核方，
对 [E3 A1 参考基线](../README.md) 的独立复核记录，不新增服务实现，也不代表四服务验收。

## 一、复核对象与范围

- 被复核交付物：`e3/`（A1，内容提交 `de31c63`，文档提交 `03d7d75`/`47c273c`）。
- 复核基线点：`main` = `47c273c595706c58ca7090a4296e3391f662e685`。
- 复核契约版本：`1.0.0`。
- 复核内容对第 9、10 页的四问：
  1. 别人能否按 README 复跑？
  2. 人工答案与实际日志是否分清？
  3. 预期结果能否说明依据？
  4. 失败记录能否定位到具体版本？

## 二、复核环境（与 A1 保存的 macOS 证据不同平台）

A1 的实测平台是 macOS arm64 / GNU Make 3.81 / Apple clang 21。本节在 **Linux（WSL2）** 上重做，
用于交叉验证基线在不同平台是否得到相同观测，并补 A1 在 [`STATUS.md`](../STATUS.md) 中标记为
「未验证」的 Linux 行为。

| 项目 | 复核环境取值 |
| --- | --- |
| 系统 | Linux 6.18.33.2-microsoft-standard-WSL2（x86_64） |
| C 编译器 | `cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0` |
| GNU Make | `GNU Make 4.4.1` |
| Python | `Python 3.14.4` |
| Git | `git version 2.53.0` |

复核使用仓库的干净克隆（非工作区），避免 Windows 工作区行尾/时间戳干扰。

## 三、复核步骤与结果

### 1. 公共契约与单元测试

```sh
make check     # 结果：Ran 77 tests ... OK
```

### 2. 重跑基线运行器

```sh
python3 e3/scripts/run_baseline.py --output-root /tmp/e3b1/runs
```

运行器自身在退出前完成 bundle `verify` 与克隆回放，并断言原标签与回放标签 SHA 相同，
本次 `status = succeeded`。观测值与 A1 保存的 macOS 证据一致：

| 场景 | 本次观测 | A1 已保存观测 |
| --- | --- | --- |
| MD/RD 初始构建 | `1` | `1` |
| 只改 `config.h` 的增量构建 | `1`（旧值，未重建） | `1` |
| 同源码 clean build | `2` | `2` |
| 只改 `unused.h` 注释后增量 | `2`，且出现 `cc -c main.c -o main.o` | `2`，且重新编译 `main.o` |
| C0 clean | `10` | `10` |
| C1 clean | `12` | `12` |
| C2 保留 C1 产物增量 | `12`（旧值） | `12` |
| C2 clean | `19` | `19` |

命令快照佐证 C1→C2 只改编译参数：

```text
C1: cc -O0 -c main.c -o main.o
C2: cc -O0 -DMODE=7 -c main.c -o main.o
```

### 3. Linux 原始文件访问（A1 未验证项）

在 `e3/fixtures/md-rd/` 的一次性副本中：

```sh
make clean
strace -ff -o trace.log -e trace=%file,%process make all
./app
make -pn
```

关键观察（完整摘录见 `evidence/linux-strace.txt`）：

- `openat(AT_FDCWD, "config.h", O_RDONLY) = 4`：编译器**读取**了 `config.h`，且它没有出现在
  make 的 stat 序列里 —— Make 不知道这条边。
- `make -pn` 解析出的声明是 `main.o: main.c unused.h`：`config.h` **未声明**（MD），
  `unused.h` **被声明**。
- `unused.h` 只有 `newfstatat`（Make 检查前置依赖），**没有** `openat`：编译器从不读它（RD）。

即：人工 oracle 里的两条发现（`MISSING: main.o→config.h`、`REDUNDANT: main.o→unused.h`）
在 Linux 原始系统调用层面得到独立印证，不只是 Mac 上的行为推断。

## 四、复核结论

1. **基线可在 Linux 上复现**，`make check` 与 `run_baseline.py` 均通过，观测值与 A1 保存证据一致；
   第 10 页「别人能按 README 复跑」这一问成立。
2. **人工 oracle 与运行器观测分开记录**：`oracle.json` 标 `COURSE_DERIVED_ORACLE`，
   命令、stdout/stderr、时间戳另存，未把 oracle 当作检测器输出。第 9 页要求成立。
3. **未发现与冻结契约 `1.0.0` 冲突**。E3 只新增样例、fixture 与文档，不改公共 schema、端点或字段，
   因此**不递增 `schema_version`**（判据见 [`versioning.md`](../../docs/versioning.md) 第八节，
   变更记录见 [`CHANGELOG.md`](../../docs/CHANGELOG.md)）。
4. **失败记录可定位**：运行器在任一断言失败时保留 `manifest.json` 的 `failure` 字段与全套日志，
   并带 `started_at_utc`/`finished_at_utc` 与工具版本；A1 另存了 `wrong-output`/`missing-tool`
   两个注入检查。第 9 页「失败也要记录」成立。

## 五、仍未验证 / 责任边界

- 每次运行的 fixture 标签 SHA 是**新建的自动化身份**，与 A1 保存的 SHA 不同属预期行为
  （见 [E3 运行说明](../README.md)），不能拿本文件的 SHA 与 A1 的 SHA 直接比对。
- BuildChecker / EChecker 的实际依赖图与产物、服务实现、跨组 `artifact` 下载仍属后续阶段
  （E5/E8/E12），本复核未覆盖。
- `CFLAGS` 变化到 `configuration_id` 的**取值映射**仍由 A3/B2 给出；B1 只给**归类口径**，
  不代替服务负责人断言具体 ID。

## 六、随本复核提交的证据

- `evidence/linux-verification.json` — 复核环境、命令、观测与结论的机读摘要。
- `evidence/linux-strace.txt` — Linux 原始跟踪的项目文件相关摘录。

## 七、复核范围的时间边界（2026-10-12 补记，B1）

本复核的对象锁定在 `main = 47c273c` 的 A1 基线。2026-10-12 合入的 B2 DRAFT 基线
（`43f6b65`、`cf272b6`）与 B3 MDFixer 固定输入（PR #27、#28）在本复核之后新增，
**不在本文件的复核范围内**，也没有经过 B1 独立复核；B 侧 E3 目前只有 B3 的自证工作记录
（[`B3-review.md`](B3-review.md)）。引用本文件时请勿把它当作 B 侧交付的复核结论。

同一时间点，A3 已在 Issue #1 确认 EChecker 对基线的字段消费（C0 的 ACTUAL_GRAPH 与
ERROR_REPORT，分别用 `actual_graph_uri`、`error_report_uri` 引用）。ADR-011 仍待 B2、B3
本人确认后由 B1 改为 `Accepted`，见
[`ADR-011`](../../docs/adr/ADR-011-buildchecker-output-contract.md)。
