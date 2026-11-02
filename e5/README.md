# E5 A：BuildChecker 原始证据复现

本目录对应 2026-10-28 手册的 E5 A：采集完整构建记录，人工比较实际依赖和 Make 声明。2026-10-29 已导入 A 组新版参考服务，构建镜像、15 项服务测试和新版入口 E5 运行均通过。最新结果按成员记录：[241250033 的报告](REPORT-241250033-20261029.md)、[241250014 的报告](REPORT-241250014-20261029.md)。

## 新版入口

在本组 Linux 服务器、自己的仓库根目录执行：

```bash
cd e5/reference-a
python3 scripts/course.py doctor
python3 scripts/course.py build --out work/build-01 --build-timeout 1200
python3 scripts/course.py e5 --out work/e5-01
git rev-parse HEAD > work/e5-01/source-commit.txt
```

从仓库根目录进入时使用上面的 `cd`；若已经在 `e5/`，则进入 `reference-a/`。每次重跑使用新目录。构建完成后应有 `15 passed`，E5 输出 `1` 且退出 0。镜像标签是 `course1027-buildchecker:学号`，详见 [参考服务说明](reference-a/README.md)。

## 10 月 28 日手工采集入口

在本组 Linux 服务器、自己的仓库根目录执行：

```bash
python3 e5/collect_a.py --out e5/work/e5-01
```

每次使用新目录。默认镜像为 `e4-buildchecker:学号`，学号读取当前仓库的 Git 本地配置。也可通过 `--image` 指定已有镜像。脚本解析并使用镜像 ID，复制当前仓库样例到证据目录，然后执行手册的原始采集命令：

```bash
make clean
strace -ff -s 4096 -o trace/t -e trace=%file,%process make -p app > make-db.txt 2> build-stderr.log
./app > program-output.txt
```

预期程序输出 `1`，采集退出 0。`source-commit.txt`、`source-working-tree.patch`、`image.json` 和 `runner/command.json` 保存执行版本及命令；`evidence/` 保存实际输入、工具版本、完整 trace、Make 数据库和构建产物。

该入口复用 E4 镜像，容器限 1 CPU、512 MiB、128 个进程。10 月 28 日记录对应 E4 的 3 项服务测试；10 月 29 日新版记录对应 15 项服务测试，两次证据分别保存。

## 人工分析与交付

1. 找出 `main.c` 和 `config.h` 的成功读打开记录，记录 trace 文件、PID 和行号。
2. 从 make → cc → cc1/as 的进程关系解释读取与 `main.o` 的对应关系。
3. 在同次运行的 Make 数据库中定位 `main.o: main.c unused.h`。
4. 写出 `MD(main.o, config.h)`、`RD(main.o, unused.h)`；说明项目外系统头文件的处理和当前编译配置。
5. 保存个人报告、完整原始证据和复跑入口。新版原始日志位于 `e5/reference-a/work/`，旧手工记录位于 `e5/work/`；两个目录均被忽略，归档另外保存。

论文为 *Detecting Build Dependency Errors by Dynamic Analysis of Build Execution against Declaration*（BuildChecker，所发 PDF 标注 IEEE TSE 2025），方法见第 4 节、图 2、算法 1/2。
