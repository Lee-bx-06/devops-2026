# E4 B2 DRAFT 可重复工程环境

本目录是 B2 的 E4 独立交付。它把 E3 的 DRAFT 失败样例放进一个可重复运行的服务骨架，
不修改仓库根目录的公共契约、A 组文件或 B3 的 MDFixer 内容。

## 交付范围

- `services/draft/`：DRAFT CLI、冒烟测试实现、单元测试和服务镜像；
- `fixtures/draft/`：从 E3 提取的源码、Makefile 与故意失败的 Dockerfile；
- `compose.yaml`：CPU、内存、进程数限制，以及宿主机 Docker socket 接入；
- `requirements-dev.lock`：带 SHA-256 哈希的 Python 测试依赖；
- `scripts/`：环境自检、证据编排和三层密钥扫描；
- `work/<UTC 时间>/`：每次运行的新证据目录，默认不进入 Git。

本目录只实现 E4 的工程骨架。它确认容器中的 DRAFT 能调用宿主机 Docker、取得失败日志，
但不实现 E5 的错误定位或环境修复算法。

## 安全边界

`compose.yaml` 把 `/var/run/docker.sock` 挂入 DRAFT 容器。能访问这个 socket 的进程基本等同于
拥有宿主机 root 权限。因此只能在课程分配的独占服务器上运行，只能构建课程指定样例，
不能开放 Docker 的 2375/2376 端口。冒烟构建设有超时。

`.env` 已被 `.gitignore` 和 `.dockerignore` 排除。真实 Key 只能通过运行时环境注入，不能写进
源码、Dockerfile、构建参数、日志或截图。`make scan` 检查工作区、Git 历史和镜像历史，
命中时只显示前四个字符。

## 首次准备

在 Ubuntu 22.04/24.04 服务器上安装 Docker、Compose、Git、Make 和 Python 3。进入本目录后：

```sh
cp .env.example .env
chmod 600 .env

# 仅修改当前仓库，不使用 --global
git config user.name "<学号>"
git config user.email "<学号邮箱>"
```

基础镜像与 Docker CLI 镜像均按正式 E4 实验包指定的镜像站和多架构 OCI index digest 固定；
镜像站只是拉取地址，内容仍由 digest 校验：

- `m.daocloud.io/docker.io/library/python@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74`
- `m.daocloud.io/docker.io/library/docker@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad`

升级时只修改 `services/draft/Dockerfile` 顶部的 digest，并在提交说明中记录原因。

## 一键运行

```sh
make all
```

`make all` 在同一个 `work/<UTC 时间>/` 下依次执行：

1. `doctor`：记录系统、架构、Git 身份、Docker 客户端/服务端和 Compose 版本到 `env.json`；
2. `build`：构建 `e4-draft:<Git user.name>`，保存 `build.log`、`image.json` 和 `toolchain.lock`；
3. `test`：在服务镜像内运行单元测试，保存 `test.log`；
4. `smoke`：容器内通过宿主机 Docker 构建 `Dockerfile.broken`，保存 `smoke.json` 和日志；
5. `scan`：检查工作区、全仓 Git 历史，以及镜像历史和环境变量，保存 `secret-scan.txt`。

单独运行某一步也可以：

```sh
make doctor
make build
make test
make smoke
make scan
make shell
```

需要把多条命令写入同一证据目录时，显式复用运行号：

```sh
make doctor RUN_ID=manual-01
make build  RUN_ID=manual-01
make test   RUN_ID=manual-01
make smoke  RUN_ID=manual-01
make scan   RUN_ID=manual-01
```

`make shell` 会将本目录的 `work/` 挂到容器内 `/app/work`。进入后运行 `docker version`，
输出中同时出现 `Client` 和 `Server` 即表示 socket 接入成功。
在非 Linux 的 Docker Desktop 环境中，编排器把 socket 组号回退为 `0`；正式验收仍以 Ubuntu
服务器记录为准。

## 验收判据

- `image.json` 记录仓库完整 commit、镜像 ID、镜像名和两个基础镜像 digest；
- `toolchain.lock` 记录实际 Python、pip 和 Docker CLI 版本；
- 单元测试退出码为 0；
- `smoke.json` 包含 `docker_server`、非零 `build_exit_code`、含 `make: not found` 的
  `make_error_line`、`log_tail` 与 `passed: true`；完整原始日志也保留在 `build_log` 中；
- `secret-scan.txt` 显示三个范围均未发现密钥；
- 另一名组员只读本 README，在新克隆中运行 `make all`，对比 commit、工具版本和冒烟结论。

镜像 ID 可能因构建元数据不同而变化。验收时应比较输入 commit、固定 digest、
`toolchain.lock`、测试结果和冒烟判据；若镜像 ID 不同，需要在对照记录中解释。
