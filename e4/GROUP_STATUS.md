# E4 A09 组长运行与成员对照记录

负责人：殷晓瑞（241250014，E4 A1 / 组长）。首版 2026-10-16，2026-10-19 更新：三名成员均已完成个人运行，补齐 A2↔A3 对照。

## 统一入口与运行顺序

- 服务器入口：`ssh DevOps`；教师分配的 2 核 / 2 GiB 配置，实测可见内存约 1.7 GiB。
- 本组仓库：https://github.com/Lee-bx-06/devops-2026.git；E4 分支 `e4-a09-environment`。
- 统一源码基线：`1e0b9232fdc70f249ef29598986b0df436b016ec`（完整 40 位 SHA），三人相同。
- 进入仓库 `e4/` 后执行 `make all`，完整命令见 [README](README.md)。
- 首轮顺序：组长 → 谢浩天（241250033）→ 朱鸣涛（241250048）。避免同时首次构建；成员各自执行，组长没有代跑其他人的实验。
- 对照安排：A1↔A2、A2↔A3。先核对完整 SHA，再比较 `toolchain.lock`、`test.log`、`smoke.json`；差异按 README 规则记录。

## 组长公共准备

已检查本组服务器与远程仓库。原仓库只有 E2/E3，新增独立 `e4/`，保留已有成果。已安装并启动 Ubuntu 仓库 Docker 组件，安装方法随 `setup/bootstrap_ubuntu.sh` 保存。安全组没有新增端口；E4 容器无网络且无需 API Key。

| 项目 | 实测 / 决策 |
| --- | --- |
| 系统、架构 | Ubuntu 24.04.4 LTS，x86_64 / linux/amd64 |
| Docker 引擎 | 29.1.3 |
| Compose / buildx | 2.40.3 / 0.30.1 |
| Git / Make / Python（宿主） | 2.43.0 / 4.3 / 3.12.3 |
| 本组资源 | 2 CPU、可见内存 1.7 GiB、可用盘约 70–71 GiB；建议值不足保留 warnings |
| 内存门槛适配 | 通用模板最低可见内存 3.5 GiB；按教师提供的 2 GiB 配置调整为 1.5 GiB，REC 保持 8 GiB、容器仍限 1 GiB；不宣称达到原 3.5 GiB 门槛 |
| Python 基础镜像 | 固定 `sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74`，索引含 linux/amd64 |
| Debian 下载源 | 首轮访问 deb.debian.org 缓慢，保留首轮中止日志；改用 repo.huaweicloud.com 的 HTTPS Debian / debian-security 镜像，保留发行版签名校验 |
| Python 依赖 | `requirements-dev.lock` 固定版本与哈希安装，实际工具链记录在每次运行的 `toolchain.lock` |
| Git 身份 | 每人只在自己的克隆设置 `user.name=<学号>`、`user.email=<学号>@localhost`；共享全局身份未改 |

## 成员记录（2026-10-19）

| 姓名 / 学号 | E4 专项职责 | 个人克隆绝对路径 | 完整 SHA | 成功完整运行证据 | 假 Key 检出 / 清理 | 组内对照 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 殷晓瑞 / 241250014 | 环境、版本、汇总 | /root/241250014/buildchecker | 1e0b9232fdc70f249ef29598986b0df436b016ec | /root/241250014/buildchecker/e4/work/20261016-130638 | 检出返回 2，清理后返回 0 | 已与 A2 逐项对照 | 个人实验完成；汇总完成 |
| 谢浩天 / 241250033 | 镜像与依赖 | /root/241250033/buildchecker | 1e0b9232fdc70f249ef29598986b0df436b016ec | /root/241250033/buildchecker/e4/work/20261016-181736 | 检出返回 2，清理后返回 0 | 已与 A1 原始证据对照 | 个人实验与 A2 专项完成 |
| 朱鸣涛 / 241250048 | 测试、扫描与互查 | /root/241250048/buildchecker | 1e0b9232fdc70f249ef29598986b0df436b016ec | /root/241250048/buildchecker/e4/work/20261016-192209 | 检出 2 处命中，清理后通过 | 由组长按原始证据补齐 A2↔A3 对照 | 个人实验完成；运行记录经本人确认；相邻组互查未开始 |

成员记录：[A2 谢浩天完成记录](records/E4_A2_241250033_完成记录.md)、[A3 朱鸣涛运行记录](records/E4_A3_241250048_运行记录.md)（组长依据服务器原始证据整理，朱鸣涛 2026-10-19 确认）、[A1 组长完成记录（2026-10-19）](records/E4_A组长完成记录_20261019.md)。

## 组内对照结论

方法：对三人成功运行目录的七份原始证据逐一计算 SHA-256，并比较镜像 RootFS 层摘要、`toolchain.lock`、单测与冒烟结论。机器可读结果见 [reports/comparison-20261019.json](reports/comparison-20261019.json)。

| 对照项 | 结果 |
| --- | --- |
| 统一源码 SHA | 三人相同：`1e0b9232fdc70f249ef29598986b0df436b016ec` |
| `toolchain.lock` | 三人逐字节相同：`bc70f4e9e436d2567c88588171d7fd4575a614c442874baa089407106bbf9358` |
| 单元测试 | 三人 `test.log` 逐字节相同：`3 passed in 0.01s` |
| 冒烟 | 三人 `smoke.json` 逐字节相同：`make_exit_code=0`、`app_output="1"`、`config_h_opened` 非空、`passed=true` |
| 容器工具链 | Python 3.13.14、Make 4.4.1、GCC 14.2.0、strace 6.13，三人一致 |
| 镜像文件系统 | 11 层 RootFS 摘要三人一致 |
| 成品镜像 ID | 三人不同（镜像名带学号、构建时间不同），属预期差异 |
| `.env` 与工作区 | 三人 `.env` 未跟踪且权限 0600，`git status --porcelain` 为空 |
| 密钥扫描 | 三人在当前文件、Git 历史与镜像中均“未发现问题” |

差异解释：`env.json`、`build.log`、`image.json`、`secret-scan.txt` 的哈希不同，来源是运行时间、可见磁盘量、镜像名/ID 与扫描输出中的镜像名；测试与冒烟结论、工具链版本、镜像文件系统层一致。

证据边界：服务器为组内共用 root 账号，证据只证明运行身份（`env.json` 中 Git 身份为各自学号）与结果，不证明键盘前的操作者；A3 的运行归属已由本人于 2026-10-19 确认，A1、A2 为本人运行。三人共用同一台服务器与 Docker 缓存，属手册允许的组内对照，不宣称为独立新机器验证。

## 仓库内证据副本

七份原始证据按课件“用 `git add -f` 挑选需要的证据目录”的做法复制进仓库，便于按 SHA 核验：

- `evidence/241250014/`、`evidence/241250033/`、`evidence/241250048/`：每人七份证据与假 Key 两次扫描输出；
- 逐文件 SHA-256 清单见 [evidence/README.md](evidence/README.md)；
- 机器可读验收：`reports/leader-241250014.json`、`reports/a2-241250033.json`、`reports/a3-241250048.json`。

## 组长个人验收与原始证据

验收时间：2026-10-16 13:11（Asia/Shanghai）。完整 `make all` 成功退出，七份证据在同一目录；机器可见资源按原值记录，没有修改 `env.json` 伪造硬件。验收清单与各文件 SHA-256 见 [reports/leader-241250014.json](reports/leader-241250014.json)。

| 验收项 | 实际结果 / 证据 |
| --- | --- |
| 完整运行目录 | /root/241250014/buildchecker/e4/work/20261016-130638 |
| 环境检查 | `problems=[]`，身份 241250014；warnings 保留较低建议资源和未配置镜像加速提示 |
| 构建 | build.log 成功；image.json 架构 amd64，镜像 `e4-buildchecker:241250014` |
| 工具链 | toolchain.lock 已导出；容器 Python 3.13.14、Make 4.4.1、GCC 14.2.0、strace 6.13 |
| 单元测试 | test.log：3 passed in 0.01s |
| 冒烟 | make_exit_code=0、app_output="1"、config_h_opened 非空、passed=true；trace_lines=1206 |
| 完整运行的扫描 | secret-scan.txt：未发现问题，覆盖 e4 跟踪文件、全仓可见历史、镜像历史和环境变量 |
| 假 Key 检出 | work/20261016-131139-leak-detected/secret-scan.txt；扫描器退出 1，`make scan` 返回 2（预期失败） |
| 清理后再扫描 | work/20261016-131139-after-cleanup/secret-scan.txt；返回 0，通过 |
| Git 与凭据 | 假文件已从索引与工作区移除，`git status --porcelain` 为空，`git ls-files .env` 无输出，`.env` 权限 0600 |
| 证据归档 | E4_A09_241250014_20261016_evidence.tar.gz；SHA-256 `e8b998b8958f1da811da58ec2bf6f8654083f95c9fe0a2fb03db147452a6efb6` |

## 相邻组 README 互查

| 检查方 / 执行人 | 被检查组 / 仓库 | 所测 SHA | 仅按 README 重跑结果 | 证据路径 | 问题与处理 |
| --- | --- | --- | --- | --- | --- |
| 本组 / 朱鸣涛（待执行） | 待老师指定 | 待填 | 未开始 | 待填 | 截至 2026-10-19 未收到指定对象与截止时间 |
| 相邻组 / 待确认 | 本组 E4 分支及源码基线 | 待对方实测 | 未开始 | 待对方提供 | 入口已准备，等待实际互查 |

## 未完成事项

- 相邻组 README 互查：需要老师指定互查对象后由 A3 执行并记录（本组 README 入口已就绪）。
- E5 起在同一环境重跑并采集 `strace -ff`、`make -p` 等完整原始证据；E4 的 `smoke.json` 不能替代。
