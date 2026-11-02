# A3 证据补采说明（2026-11-02）

A3 朱鸣涛（241250048）的 E5 原始提交是 `2d7ffe1`（2026-11-01），已包含一次完整的 `course.py build`、`course.py e5` 采集、7 份 trace、Make 数据库、程序输出、人工 MD/RD 分析和第三人审计。

2026-11-02 由 A09 组长补采以下三项过程材料，使 A3 证据目录与 A1/A2 对齐：

| 文件 | 来源 | 说明 |
| --- | --- | --- |
| `e5/image.json` | 同一提交的 `build/image/stdout.log` | 同一镜像 `course1027-buildchecker:241250048` 的 `docker image inspect` 输出，按 A1/A2 的命名复制，未改内容 |
| `e5/toolchain.lock` | 同一镜像内的 `dpkg-query`、`python3 --version`、`pip list` | 原提交未保存工具版本 |
| `e5/secret-scan.txt` | `secret_scan.py . --history`、`secret_scan.py . --image course1027-buildchecker:241250048` | 2026-11-02 重跑，两项均为“未发现问题” |

未改动：`trace/`、`make-db.txt`、`program-output.txt`、`manual-analysis.json`、`environment/`、`build/` 的原始内容。补采不改变 MD=`config.h`、RD=`unused.h` 的结论。

执行人：A09 组长 241250014。A3 的原始运行、报告和审计作者仍为 241250048；本说明不把补采材料记作 A3 的独立运行证据。
