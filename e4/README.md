# A09 BuildChecker 可重复环境（E4）

本目录是 A 组 E4 服务骨架。环境准备、单测、E3 样例冒烟和密钥扫描由一次 `make all` 完成；E5 起再实现论文方法。

## 运行

在本组服务器通过 `ssh DevOps` 登录。每名成员（含组长）在自己的学号目录独立运行，首次构建请依次进行：

```sh
mkdir -p ~/<学号>
cd ~/<学号>
git clone --branch e4-a09-environment https://github.com/Lee-bx-06/devops-2026.git buildchecker
cd buildchecker
git checkout --detach <组长公布的完整40位SHA>
git config --local user.name '<学号>'
git config --local user.email '<学号>@localhost'
cd e4
make all
```

运行命令的目录必须是 `e4/`；仓库根目录的 Makefile 是既有 E2/E3 校验入口。Git 身份只写本地仓库，不能加 `--global`。`git remote -v` 应指向上面的本组仓库。`make all` 不产生个人提交，原始日志默认不进入 Git。

## 本组资源与依赖

教师分配服务器为 **2 核 / 2 GiB**，实测可见内存约 **1.7 GiB**。原通用模板的最低可见内存为 3.5 GiB；按组长确认的教师配置，本组将 `scripts/doctor.py` 的最低可见内存改为 **1.5 GiB**，保留真实资源记录与原建议值（4 核 / 8 GiB / 100 GiB 可用盘）。这项适配不代表服务器达到原通用模板的资源门槛。Compose 中容器仍限制为 2 CPU / 1 GiB / 256 进程。全组顺序构建，共享 Docker 缓存；若资源不足导致失败，保留原始日志后排查。

宿主机需要 Ubuntu、Docker 引擎、Compose v2、Git、Make、Python 3；buildx 用于镜像索引核验，doctor 将其列为建议项，本组已安装。组长统一安装一次，组员不用重复安装。新服务器缺少依赖时，由有管理员权限的组长执行一次 `sudo bash setup/bootstrap_ubuntu.sh`（安装 Ubuntu 仓库 Docker 组件，不执行整机升级）。A 组不需要 API Key。`make build` 自动生成权限 600 的 `.env`，不要填入真实密钥。

基础镜像固定为 `m.daocloud.io/docker.io/library/python@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74`，已核验含 `linux/amd64`。容器内 Debian 软件源使用 `https://repo.huaweicloud.com/debian` 与 `debian-security`，保留 Debian 签名校验。Python 依赖使用 `requirements-dev.lock` 及哈希安装；系统包实际版本记录在 `toolchain.lock`。

## 命令与验收

| 命令 | 证据（work/<时间>/） | 预期 |
| --- | --- | --- |
| make doctor | env.json | problems=[]，Git 身份为本人学号 |
| make build | build.log、image.json、toolchain.lock | 构建成功、记录镜像架构和实际依赖版本 |
| make test | test.log | 3 passed |
| make smoke | smoke.json | make_exit_code=0、app_output="1"、config_h_opened 非空、passed=true |
| make scan | secret-scan.txt | 未发现问题，.env 未跟踪 |
| make all | 同一目录中的以上全部文件 | 五步全部成功 |
| make shell | work/ 挂载到容器 /app/work | 为 E5 后续采集保留入口 |
| make lock | requirements-dev.lock | 更新依赖后重新生成哈希锁文件 |

成功后记录 `git rev-parse HEAD` 和打印的完整证据目录。`warnings` 中低于建议资源的提示按本组 2G 配置记录，不伪造为建议资源达标。密钥扫描从 e4 只检查当前目录的 Git 跟踪文件，`--history` 则检查整个仓库所有可见引用的历史；镜像检查覆盖构建历史和环境变量。

每人再验证假 Key（不要提交）：

```sh
printf 'api_key = "%s%s"\n' 'sk-' 'demo1234567890abcdefghijk' > leak-demo.txt
git add leak-demo.txt
make scan                    # 应失败并掩码显示假 Key
git rm --cached -q leak-demo.txt
rm leak-demo.txt
make scan                    # 应通过
git ls-files .env            # 无输出
git status --short           # 无假 Key 遗留
```

假 Key 验证的两次扫描各自生成目录，不能替代成功的完整 make all 证据。组内用相同源码 SHA 对照 toolchain.lock、单测和冒烟结论；镜像 ID、耗时、进程号、trace_lines 可以不同。组长个人记录和成员待办见 [GROUP_STATUS.md](GROUP_STATUS.md)。相邻组 README 互查由指定成员实际完成后再记录。

E4 的 smoke.json 只有 strace 摘要，不能代替 E5 的完整 strace -ff / make -p 原始证据。

## 镜像与依赖离线复核

`make verify` 只使用宿主 Python 标准库和本地 Make，检查本目录的 digest、平台、依赖锁格式、直接依赖一致性和资源配置，并运行回归测试；不调用真实 Docker、SSH 或网络。它检查配置约束，下载内容的哈希仍由 pip 实际验证。

本分支将服务及 `make lock` 统一到 `linux/amd64`；digest 保持原值。构建时记录全部 dpkg 包（包括传递依赖），Python 清单包含 pip 自身，并执行 `pip check`。仅接受锁定哈希的 wheel，避免退回 sdist 后引入额外构建依赖。`toolchain.lock` 是**实际版本清单**：当前 apt 源随时间更新，尚未通过 snapshot / 精确包版本锁定系统包；同一源码、digest 和平台仍可能得到不同系统工具链。共享缓存命中也无法证明冷构建一致。

运行容器的 2 CPU / 1 GiB / 256 PID 限制不约束 BuildKit 构建。`make all` 即使带 `-j` 也在本次 Make 调用内串行执行；不同成员的独立调用仍需遵守组内首构建顺序。不要为此改共享 Docker daemon 或同时启动多份无缓存构建。复跑时保留资源 warnings、失败日志和实际 OOM 情况；修复版仍需在教师服务器验证构建峰值和运行限制是否实际生效。

修复版 `make build` 额外写出 `source.json`，记录完整源码 SHA、工作区是否有修改、基础镜像引用、平台及 Python 锁文件哈希。应从干净检出运行；该文件补充原七份证据，不取代个人完整 `make all` 和假 Key 检出/清理记录。

取得组长**七份原始文件**后，可以在任意机器离线对照（路径自行替换）：

```sh
python3 scripts/verify_environment.py compare \
  /path/to/leader-run /path/to/my-run \
  --leader-summary reports/leader-241250014.json
```

工具先校验组长原始文件的七个 SHA-256，再检查双方平台、源码、单测和冒烟条件，并逐项比较工具链。退出码 0 表示所查项目一致，1 表示发现差异，2 表示证据缺失/损坏或验收条件不满足。build/scan 原始日志、学号、假 Key 两次扫描和来源真实性仍需本人检查；本工具的结果不自动登记个人验收。

原组长基线 `1e0b9232fdc70f249ef29598986b0df436b016ec` 没有 `source.json`，工具只在提供并验证组长清单时采用清单里的源码 SHA。新旧基线的源码、清单范围、缺失的 provenance 字段会明确报差异，不将其判为一致。按照 GROUP_STATUS 的原 SHA 做课程个人复跑时，仍检出原 SHA；可从本修复分支的绝对路径调用比较脚本，再由本人补录真实 provenance。若组内采用修复版，先统一新的完整 SHA，再由相关成员重新生成同版本证据，不能沿用组长旧证据宣称新版已验收。

公开的 `leader-241250014.json` 只有工具链文件哈希和部分版本摘要，无法据此还原完整工具链；仅凭该 JSON 无法完成版本逐项对照。镜像 ID、时间、耗时、PID、trace_lines 允许不同；源码、平台、基础镜像、Python 锁和实际工具链差异需要解释。完整复核结论见 [reports/image-dependency-review.md](reports/image-dependency-review.md)。
