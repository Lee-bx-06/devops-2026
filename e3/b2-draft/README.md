# B2 E3 DRAFT 基线交付

负责人：B2（zrh）。本目录只记录 B2 在 E3 的新增交付，不修改或替代 A1/B1 已有基线。

## 交付范围

- `../fixtures/draft/`：Tiny Greeting 源码、Makefile、失败与参考 Dockerfile、固定预期。
- `../scripts/run_draft_baseline.py`：生成不可覆盖的逐次运行证据。
- `../tests/test_draft_baseline.py`：检查 E2 契约映射、不可变基础镜像、命令顺序和配置 ID。
- `../evidence/draft-run-*/`：真实 Docker 运行的命令、日志、镜像 ID 和最终判断。

## 与 E2 契约的对应关系

| E2 DRAFT 字段或判据 | E3 落点 |
| --- | --- |
| `build.clean_command` | `make clean` |
| `build.command` | `make all` |
| `build.verify_command` | `make test` |
| `build.project_root` | `/workspace/project` |
| `environment.image_uri` | 成功构建的本地不可变镜像 ID |
| `environment.configuration_id` | 基础镜像、包、CFLAGS、profile 与 build 块的规范哈希 |
| 失败样例 | `Dockerfile.broken` 非零退出并保留缺少 make 的日志 |
| 成功判据 | clean/build/verify 均为 0，`./hello` 输出 `hello E3` |

## 边界

本交付是 DRAFT 的测试基线，不实现异步 Job API，不生成虚假的 registry digest，也不声称
BuildChecker、EChecker 或 MDFixer 已验收。运行器只记录 Docker 实际返回的镜像 ID和日志。
