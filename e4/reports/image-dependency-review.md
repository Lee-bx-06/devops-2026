# E4 镜像与依赖复核

复核日期：2026-10-18。对象：PR #35 head `dd4c9128f474b9747427b88d75c73944681aedcd`；组长验收源码为 `1e0b9232fdc70f249ef29598986b0df436b016ec`。两个提交之间为验收记录变更。GitHub 连接账号确认为 `mcjiansheng`。

这是谢浩天职责范围的代码复核及本地验证记录，个人服务器验收仍待本人完成。当前环境没有 Docker 命令，也没有 `DevOps` SSH 配置或已提供的服务器凭据，未尝试登录服务器。组长原始证据目录和归档未在此环境提供，公开 JSON 的成功字段作为组长已有记录引用，未转写为个人成功证据。

## 发现与处理

| 检查项 | 代码/现有证据结论 | 最小处理与待确认事项 |
| --- | --- | --- |
| 基础镜像 | Dockerfile 用 SHA-256 固定索引；组长记录索引含 amd64，image.json 摘要为 amd64。索引可以包含多个平台，原 Compose 未固定平台 | 保持 digest，Compose 和 make lock 显式使用 linux/amd64；服务器仍需核验实际拉取子 manifest / 镜像架构。此次未重新拉取索引 |
| 系统工具 | apt 安装未锁版本，原清单只写 gcc/make/libc6-dev/strace/git，遗漏 gcc-14、binutils、运行库等传递包 | 导出排序的全部 dpkg 包版本；不宣称 apt 完全可重复，不贸然换源或固定未经验证的 snapshot |
| Python | 五个包均为精确版本加 SHA-256；直接依赖 pytest 与锁一致 | 保留锁，wheel-only 安装、pip check、freeze --all；五个 wheel 已从 PyPI 实际下载并通过 --require-hashes，宿主隔离 venv 离线安装通过 |
| 证据可靠性 | 原 build 的 inspect/cat 管道只返回 tee 状态，其余管道仅检查上游，证据写失败可能漏报 | Make 统一启用 errexit/pipefail；Dockerfile 的管道也启用 pipefail；回归测试注入构建失败、inspect 失败、cat 失败和 /dev/full 写失败 |
| 构建一致性 | 缓存命中不能证明冷构建一致；基础镜像相同也不能证明 apt 包相同 | 增加 source.json 和离线原始证据对照；旧版清单范围与新版不同会如实报差异 |
| 资源 | doctor 最低 1.5 GiB，保留 4 CPU / 8 GiB 建议及 warnings；Compose 限制运行容器 2 CPU / 1 GiB / 256 PID | 保留组长资源适配；Make 调用内禁止并行；BuildKit 不受服务 mem_limit 约束，实际冷构建内存峰值、OOM、限制是否生效仍待服务器验证 |

未发现关闭 Debian 签名校验、未带哈希的 Python 安装或将 .env 传入服务的问题。`make lock` 的生成工具 uv 固定版本，但引导安装不带哈希，仍是需要人工审阅锁变更的维护步骤；本次未重生成依赖、未将它计入已锁定的服务安装链。未将系统版本记录功能表述为系统版本锁定。

## 本地验证

- `cd e4 && make verify`：静态检查通过，10 项离线回归测试通过，不启动真实 Docker 或远程服务。
- 根目录 `make check`：公共契约校验通过，77 项根目录测试及 7 项 E3 测试通过。
- `pip download --only-binary=:all: --require-hashes --python-version 3.13 --platform manylinux_2_28_x86_64 --implementation cp --abi cp313 --index-url https://pypi.org/simple -r e4/requirements-dev.lock`：5 个 wheel 下载且哈希校验成功。
- 宿主 Python 3.12.14 的临时 venv 使用下载的 wheel，`--no-index --only-binary=:all: --require-hashes` 离线安装成功，`pip check` 通过，E4 骨架单测 3 passed。此项是宿主 Python 验证；镜像中的 Python 3.13.14、gcc、make、strace 和 smoke 尚需实际构建验证。

## 必须本人上机完成的对照

1. 遵循组长 → 谢浩天 → 朱鸣涛的顺序，在个人学号目录、local Git 身份、干净检出及统一完整 SHA 下执行 make all。原课程基线继续使用原 SHA；采用本修复需全组明确新版 SHA 并重验。
2. 对照完整 source SHA、索引 digest、实际 amd64 子镜像、全部系统包与 Python 清单；取得组长七份原始文件并先验哈希。公开摘要只能支持 Python 3.13.14、Make 4.4.1、GCC 14.2.0、strace 6.13 等部分版本观察，无法推出整个工具链相同。
3. 确认 test.log 的 3 passed、smoke 的退出码 0 / app_output=1 / config.h 打开 / passed=true。镜像 ID、时间、PID、trace_lines 可以不同。
4. 检查资源 warnings 和实际运行限制，保存构建日志及任何资源失败；如需冷构建对照，预约串行运行并保留缓存/无缓存模式，不清理共享缓存。
5. 本人执行假 Key 检出与清理后扫描，记录 .env 未跟踪且权限 0600；最后登记真实个人证据路径，并分别与组长、朱鸣涛核对。截止时间待老师明确。

离线对照会把不同源码、字段缺失、包增删或版本改变报告为差异；它不自动批准差异，也不替代个人上机验收。

参考：[Docker Compose platform](https://docs.docker.com/reference/compose-file/services/#platform)、[Compose Build platforms](https://docs.docker.com/reference/compose-file/build/#platforms)、[Compose build memory 选项限制](https://docs.docker.com/reference/cli/docker/compose/build/)、[pip 哈希安装](https://pip.pypa.io/en/stable/topics/secure-installs/)。
