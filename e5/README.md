# E5 A：BuildChecker 原始证据复现

本目录对应 2026-10-28 手册的 E5 A：采集完整构建记录，人工比较实际依赖和 Make 声明。复用本组 E4 镜像中的 gcc、make、strace 和固定依赖；原始样例取自当前提交的 `e4/fixtures/md-rd/`。

## 运行

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

该入口按新版手册的手工采集步骤运行，容器限 1 CPU、512 MiB、128 个进程。E5E7 参考服务的 15 项单测与 `course.py` 升级尚未执行；后续导入由小组统一安排。现有 E4 单测基线为 3 项，报告分别记录这两个版本。

## 人工分析与交付

1. 找出 `main.c` 和 `config.h` 的成功读打开记录，记录 trace 文件、PID 和行号。
2. 从 make → cc → cc1/as 的进程关系解释读取与 `main.o` 的对应关系。
3. 在同次运行的 Make 数据库中定位 `main.o: main.c unused.h`。
4. 写出 `MD(main.o, config.h)`、`RD(main.o, unused.h)`；说明项目外系统头文件的处理和当前编译配置。
5. 保存个人报告、完整原始证据和复跑入口。个人原始日志位于被忽略的 `e5/work/`，归档另外保存。

论文为 *Detecting Build Dependency Errors by Dynamic Analysis of Build Execution against Declaration*（BuildChecker，所发 PDF 标注 IEEE TSE 2025），方法见第 4 节、图 2、算法 1/2。
