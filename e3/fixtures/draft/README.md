# B2 E3 DRAFT fixture

本目录是 B2 在 E3 阶段负责的 DRAFT 测试基线。它提供一个故意失败的环境候选、
一个参考成功环境和明确的功能判据，不实现或伪装 DRAFT 服务。

## 固定输入和预期

- 源码：`main.c`
- 构建：`make all`
- 清理：`make clean`
- 验证：`make test`
- 容器内项目根目录：`/workspace/project`
- 成功输出：`hello E3`
- 成功退出码：`0`

`Dockerfile.broken` 使用不含 GNU Make/C 工具链的基础镜像，预期在 `RUN make all`
处非零退出。`Dockerfile.reference` 安装 `gcc`、`make` 和 `libc6-dev`，随后依次执行
clean、build、verify，并以 `./hello` 作为容器入口。

基础镜像按 OCI index digest 固定；本地构建成功后，运行器另外记录实际镜像 ID，
形成不使用 `latest` 的不可变证据。

## 运行

在仓库根目录执行：

```sh
python3 e3/scripts/run_draft_baseline.py
```

需要 Docker CLI 和可用的 Linux Docker engine。每次运行创建全新目录，保留命令、
退出码、stdout/stderr、fixture 哈希、仓库 commit、镜像 ID 和最终判断。失败时同样
保留现场，不覆盖既有证据。

只检查 fixture 与 E2 契约映射而不连接 Docker：

```sh
python3 e3/scripts/run_draft_baseline.py --verify-only
```

## `configuration_id` 规则

`configuration_id` 对下游仍是 opaque 字符串，但 B2 使用确定性算法生成它：对基础镜像、
工具包集合、CFLAGS、构建 profile 以及四个 build 字段组成的规范 JSON 计算 SHA-256，
取前 12 位作为后缀。

因此 A1 样例的 C1 到 C2 若只把 `CFLAGS=-O0` 改为 `CFLAGS=-O0 -DMODE=7`，
配置哈希也会变化，两个提交必须获得不同的 `configuration_id`。commit、Job ID 和随机
UUID 都不参与该 ID。
