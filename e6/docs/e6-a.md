# E6 A 轨个人分析与证据说明（241250014）

> 轨道：A（BuildChecker）｜学号：241250014｜日期：2026-10-31
> 服务器：Ubuntu 24.04.4 LTS，2 CPU / 1.7 GiB 可见内存 / 69.4 GiB 可用磁盘
> 实验包：`DevOps_E6_Student_Cloud.zip`，SHA-256 `C25E34BD4EB8A836EE7EC9052636B1491BCFEA4E316BCFF47AF63BBCE37A40A0`
> 工作副本：`/root/241250014/e6-a`；代码提交 `b2c4cb8`，初始提交 `45130a1`
> 原始证据归档：`E6-A-241250014-20261031-work.tar.gz`，SHA-256 `825C2E6A636E21C7526264FB75F3E37912ABA301777AAA66A1E75138E2B31B22`

## 1. 运行命令与实际退出码

| 步骤 | 命令（工作副本根目录） | 实际退出码 | 证据 |
| --- | --- | --- | --- |
| 包校验 | `python3 tools/check_package.py`（解压后的包根目录） | 0 | `passed=true`，138 个文件 |
| 环境自检 | `python3 scripts/lab_cloud.py doctor` | 1 | `work/doctor/env.json`：唯一 problem 是 `mem_gib=1.7 低于最低要求 4` |
| 基线构建 | `python3 scripts/lab_cloud.py build --out work/build-01 --build-timeout 1200` | 0 | `work/build-01/unit-tests/stdout.log`：**15 passed**；镜像 `sha256:0602aaa7…` |
| 原始检测 | `python3 scripts/lab_cloud.py e6 --out work/e6-before` | 1 | `work/e6-before/evidence/findings.json`：`SUCCEEDED`，两条 findings |
| 修复复检 | `python3 scripts/lab_cloud.py e6 --fixed --out work/e6-after` | 0 | `work/e6-after/evidence/findings.json`：`findings=[]` |
| 证据校验 | `python3 scripts/verify_e6_evidence.py --before work/e6-before/evidence/findings.json --after work/e6-after/evidence/findings.json` | 0 | `passed=true`，`changed_inputs=["Makefile"]` |
| 修改后构建 | `python3 scripts/lab_cloud.py build --out work/build-02 --build-timeout 1200` | 0 | `work/build-02/unit-tests/stdout.log`：**16 passed**；镜像 `sha256:d905a8b…` |
| 修改后复跑 | `python3 scripts/lab_cloud.py e6 --out work/e6-rerun` | 1 | `work/e6-rerun/evidence/findings.json`：同样两条 findings |

> `e6` 的退出码 1 来自 `--fail-on-findings`，表示“检出依赖错误”，不是检测器执行失败；两次运行的 `findings.json` 都是 `status=SUCCEEDED`、`clean_exit_code=0`、`build_exit_code=0`。

## 2. 实际图（本次运行）

`work/e6-before/evidence/actual-graph.json`：

| target | dependency | 证据 | 说明 |
| --- | --- | --- | --- |
| `app` | `main.o` | `t.18:82`，pid 18，`openat(AT_FDCWD, "main.o", O_RDONLY)` | 链接器 `ld` 读入 `main.o` |
| `main.o` | `config.h` | `t.14:579`，pid 14，`openat(AT_FDCWD, "config.h", O_RDONLY\|O_NOCTTY) = 4` | `cc1` 成功读打开 |
| `main.o` | `main.c` | `t.14:67`，pid 14，`openat(AT_FDCWD, "main.c", O_RDONLY\|O_NOCTTY) = 3` | `cc1` 成功读打开 |

没有把 `/usr/include/...` 算进依赖：`execution_graph` 对每个路径调用 `project_path`，只有落在项目根（容器内 `/evidence`）下的路径才保留；`/usr/include/x86_64-linux-gnu/bits/...` 在根外，返回 `None`，被跳过（`fullcheck.py:60-65`、`169-171`）。

没有把 `unused.h` 算成实际读取：`t.12:46` 只有 `newfstatat(AT_FDCWD, "unused.h", …) = 0`，是 `make` 在检查先决条件是否存在，不是 `openat(... O_RDONLY)`；`execution_graph` 只把成功 `open/openat` 且带 `O_RDONLY` 的事件记为读取（`fullcheck.py:164-186`），`newfstatat` 不在其列。

## 3. 声明图（Make 数据库）

`work/e6-before/evidence/declared-graph.json`，来源 `make-db.txt`：

| target | dependency | `make-db.txt` 行号 | 原始声明 |
| --- | --- | --- | --- |
| `app` | `main.o` | 601 | `app: main.o` |
| `main.o` | `main.c` | 1053 | `main.o: main.c unused.h` |
| `main.o` | `unused.h` | 1053 | 同上 |

`declaration_graph` 只解析 `# Files` 到 `# files hash-table stats` 之间（`fullcheck.py:240-245`），跳过 Tab/空格开头的命令行、`.PHONY`、含 `%`/`$(`/`${` 的模式名（`247-265`），把 `|` 之后的项放进 `order_only`（`268-269`），再展开 `.PHONY` 先决条件（`285-301`）。本 fixture 没有 order-only 项，`all/clean/test` 是 `.PHONY`，不会进入目标集合。

## 4. Findings 与修复前后

`work/e6-before/evidence/findings.json`：

| type | target | dependency | 证据 | 解释 |
| --- | --- | --- | --- | --- |
| `MISSING` | `main.o` | `config.h` | 读：`t.14:579`；目标写入：`t.15:23` | `config.h` 被实际读取，但声明只有 `main.c, unused.h` |
| `REDUNDANT` | `main.o` | `unused.h` | `make-db.txt:1053` | 声明了 `unused.h`，但本次 recipe job 没有成功读打开；`scope` 明确写“Not observed in this recipe job under this build configuration” |

`analyze` 用集合差生成两类 finding（`fullcheck.py:304-329`）：`observed - specified` 为 `MISSING`，`specified - observed` 为 `REDUNDANT`；`MISSING.evidence` 同时带读取证据和输出写入证据，`REDUNDANT.evidence` 只带声明证据。

修复只改 Makefile 第 6 行：

```text
修复前：main.o: main.c unused.h
修复后：main.o: main.c config.h
```

`work/e6-after/evidence/findings.json` 为 `findings=[]`；`verify_e6_evidence.py` 比较前后输入哈希，只有 `Makefile` 变化：

```text
Makefile  fd1dcd76… -> 128069c9…
config.h  ac32a92f…（不变）
main.c    bfa1c2d1…（不变）
unused.h  1e431554…（不变）
```

## 5. 进程归属

`work/e6-before/evidence/processes.json`：

| pid | parent | executable | job_pid | 归属 |
| --- | --- | --- | --- | --- |
| 12 | — | `/usr/bin/make` | — | Make 根进程 |
| 13 | 12 | `/usr/bin/cc` | 13 | `main.o` recipe 的 driver |
| 14 | 13 | `cc1` | 13 | `main.o` 的编译前端，读 `main.c`/`config.h` |
| 15 | 13 | `/usr/bin/as` | 13 | 汇编器，写 `main.o` |
| 16 | 12 | `/usr/bin/cc` | 16 | `app` recipe 的 driver |
| 17 | 16 | `collect2` | 16 | 链接驱动 |
| 18 | 17 | `/usr/bin/ld` | 16 | 链接器，读 `main.o`，写 `app` |

`load_processes` 从 `clone/clone3/fork/vfork` 的返回值建立父子表，并检查每个 child 都有 `t.<pid>` trace、只有一个 Make 进程（`fullcheck.py:92-121`）。`job_for` 从当前 pid 沿 parent 向上走，直到“父进程是 make”的那一层，把该层 pid 作为 `job_pid`（`131-142`）；因此 `cc1`/`as` 归到 `cc 13`，`collect2`/`ld` 归到 `cc 16`。`visit` 在 fork 时继承当前 cwd，而不是用父进程最终 cwd（`144-163`），避免 `chdir` 之后的路径错配。

## 6. 代码阅读要点

### 6.1 `load_processes`（`fullcheck.py:92`）

- 只认 `t.<数字>` 文件；把 `<unfinished ...>` 和 ` resumed>` 合并成一条系统调用，保留起始行号（`68-89`）。
- 用 `CALL` 正则解析 `name(args) = ret`；`ret < 0` 的失败调用不会成为依赖或子进程（`154-155`）。
- 遇到缺 child trace、多个 Make、共享线程 cwd（`CLONE_FS`）等教学 profile 之外的形态，抛 `Unsupported`，不静默猜测。

### 6.2 `execution_graph`（`fullcheck.py:124`）

- 从唯一根 Make 开始 `visit`，按 fork 时的 cwd 解析相对路径。
- `open/openat/openat2/creat`：写打开记 `writes/produced`，读打开记 `reads`；输出目标由“job 内唯一的最终写入”确定（`216-228`）。
- `rename`/`unlink` 会更新写集合；`O_DIRECTORY`/`O_PATH` 跳过；数字目录 FD 的相对路径和 `fchdir` 明确报 `Unsupported`。
- 一个 recipe job 多个最终输出时直接报错，不猜。

### 6.3 `declaration_graph`（`fullcheck.py:237`）

- 只读 `# Files` 段；没有该段或没有目标就报 `Unsupported`，避免“空成功”。
- `.PHONY` 先收集再展开；`|` 右边是 order-only，不算普通依赖。
- 目标/依赖都做项目根过滤，和实际图使用同一套 `project_path`。

### 6.4 `analyze`（`fullcheck.py:304`）

- 实际图与声明图都归一化为 `target -> {dependency: evidence}`。
- 两类 finding 的语义分开：`MISSING` 是“读了没声明”，`REDUNDANT` 是“声明了但本次没读”；后者带 scope 说明，不把它写成执行失败。
- 同时输出 `actual_graph`、`declared_graph`、`processes` 三份边列表，供报告逐条回查。

## 7. 新增测试

文件：`services/buildchecker/tests/test_fullcheck.py:112`

```python
def test_consistent_declaration_produces_no_findings(self):
    """E6 added: declarations match observed reads, so analyze reports nothing."""
    self.traces()
    db = self.write("db.txt", "# Files\nunit.o: unit.c needed.h\n# files hash-table stats:\n")
    result = analyze(self.folder, db, self.root)
    self.assertEqual(result["findings"], [])
```

- 输入：`self.traces()` 生成的微型 trace（`unit.o` 实际读 `unit.c`、`needed.h`）＋声明完全一致的 Make 数据库。
- 预期：`findings == []`。
- 实际：`16 passed`（`work/build-02/unit-tests/stdout.log`），基线为 `15 passed`（`work/build-01/unit-tests/stdout.log`）。
- 目的：盯住“声明与读取一致时不得误报”，防止后续改 `analyze` 时把正常项目判成 MD/RD；与文档给的示例一致。

另有一处**环境适配**（不是任务要求的代码修改）：`services/buildchecker/Dockerfile` 把基础镜像改为本机已缓存的 DaoCloud 同 digest 镜像 `m.daocloud.io/docker.io/library/python@sha256:f82c9645…`，并把 Debian/PyPI 源换成清华镜像。原 digest 不变，指令语义不变；报告和验收表里单独说明，避免和新增测试混为一谈。

## 8. 边界与未覆盖

- 本实现只支持**单 Make 进程、每个 recipe job 单最终输出**；递归 Make、`fchdir`、数字目录 FD、符号链接等会明确报 `Unsupported`，不做猜测（`fullcheck.py:108-121`、`166-168`、`186-191`、`353-354`）。
- “实际读”指**成功的 `openat(... O_RDONLY)` 观测**，不等于证明字节被读取；这是教学 profile 的边界，报告里不夸大成完整论文工具。
- `doctor` 的 1.7 GiB 低于 4 GiB 最低要求，是本次唯一 problem；构建和 E6 在 1.7 GiB 上实际跑通，但按 lab5 的做法保留 `env.json` 和 `free -h`，交老师/助教书面说明，不改脚本、不伪造数据。
- 六人共用 root 账号和 Docker 缓存，`doctor` 的 Git 身份只能证明运行身份，不能宣称“独立新机器验证”。
- `work/` 不进 Git；原始 trace、两轮 Dockerfile、日志和报告按学号单独打包，归档 SHA-256 见文首。

## 9. 证据索引

| 路径 | 内容 |
| --- | --- |
| `work/doctor/env.json` | 环境自检、资源、Git 身份、problems/warnings |
| `work/build-01/` | 基线构建日志、镜像 inspect、15 passed |
| `work/build-02/` | 修改后构建日志、镜像 inspect、16 passed |
| `work/e6-before/evidence/findings.json` | 原始检测报告、两条 findings、输入哈希 |
| `work/e6-before/evidence/actual-graph.json` | 实际读打开边 |
| `work/e6-before/evidence/declared-graph.json` | Make 声明边 |
| `work/e6-before/evidence/processes.json` | 7 个进程的父子/归属 |
| `work/e6-before/evidence/trace/t.*` | 原始 strace，含 `config.h`/`main.c`/`main.o` 行号 |
| `work/e6-before/evidence/make-db.txt` | `make -p` 输出，`app:601`、`main.o:1053` |
| `work/e6-after/evidence/findings.json` | 修复后 `findings=[]`、仅 Makefile 哈希变化 |
| `work/e6-rerun/evidence/findings.json` | 修改后复跑，仍为同样两条 findings |
| `work/git-provenance.txt` | 两次提交的完整 SHA、作者、时间、工作区状态 |
| `E6-A-241250014-20261031-work.tar.gz` | 以上 `work/` 的完整归档（SHA-256 见文首） |
