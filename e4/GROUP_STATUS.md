# E4 A09 组长运行与成员对照记录

负责人：殷晓瑞（241250014，E4 A1 / 组长）。记录日期：2026-10-16。

## 统一入口与运行顺序

- 服务器入口：`ssh DevOps`；按教师分配的 2 核 / 2 GiB 配置运行，实测可见内存约 1.7 GiB。
- 本组仓库：https://github.com/Lee-bx-06/devops-2026.git
- E4 分支：`e4-a09-environment`。源码基线：`1e0b9232fdc70f249ef29598986b0df436b016ec`（完整 40 位 SHA）。
- 进入仓库 `e4/` 后执行 `make all`，完整命令见 [README](README.md)。本文件后续更新属于记录变更，成员对照仍检出上述已实测源码基线。
- 首轮顺序：组长 → 谢浩天（241250033）→ 朱鸣涛（241250048）。避免同时首次构建；成员各自执行，组长没有代跑其他人的实验。
- 对照安排：组长 ↔ 谢浩天、谢浩天 ↔ 朱鸣涛。先核对完整 SHA，再比较 toolchain.lock、test.log、smoke.json；差异按 README 规则记录。
- 截止时间和老师指定的相邻互查组尚未提供，待实际确认后填写；不沿用别班阿里云地址或模拟学生证据。

## 组长公共准备

已检查本组服务器与远程仓库。原仓库只有 E2/E3，新增独立 `e4/`，保留已有成果。已安装并启动 Ubuntu 仓库 Docker 组件；安装方法随 `setup/bootstrap_ubuntu.sh` 保存。安全组没有新增端口，E4 容器无网络且无需 API Key。

| 项目 | 实测 / 决策 |
| --- | --- |
| 系统、架构 | Ubuntu 24.04.4 LTS，x86_64 / linux/amd64 |
| Docker 引擎 | 29.1.3 |
| Compose / buildx | 2.40.3 / 0.30.1 |
| Git / Make / Python（宿主） | 2.43.0 / 4.3 / 3.12.3 |
| 本组资源 | 2 CPU、可见内存 1.7 GiB、初次自检可用盘约 71 GiB；建议值不足保留 warnings |
| 内存门槛适配 | 原通用模板最低可见内存 3.5 GiB；组长明确教师提供 2G，本组最低可见内存调整为 1.5 GiB，REC 保持 8 GiB、容器仍限 1 GiB；不宣称达到原 3.5 GiB 门槛 |
| Python 基础镜像 | 固定 sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74，索引含 linux/amd64 |
| Debian 下载源 | 首轮访问 deb.debian.org 缓慢，保留首轮中止日志；改为 repo.huaweicloud.com 的 HTTPS Debian / debian-security 镜像后重新完整运行，保留 Debian 发行版和签名校验 |
| Python 依赖 | requirements-dev.lock 固定版本和哈希安装，实际工具链记录在每次运行 toolchain.lock |
| Git 身份 | 只设置个人克隆的 local user.name=241250014、user.email=241250014@localhost；共享全局身份未改 |

## 成员记录

| 姓名 / 学号 | E4 专项职责 | 个人克隆绝对路径 | 完整 SHA | 成功完整运行证据 | 假 Key 检出 / 清理 | 组内对照 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 殷晓瑞 / 241250014 | 环境、版本、汇总 | /root/241250014/buildchecker | 1e0b9232fdc70f249ef29598986b0df436b016ec | /root/241250014/buildchecker/e4/work/20261016-130638 | 已检出并清理后通过，详见下表 | 待谢浩天个人完成后对照 | 个人实验完成；组内对照待进行 |
| 谢浩天 / 241250033 | 镜像与依赖 | 待本人运行 | 待本人记录 | 待本人记录 | 待本人验证 | 与组长及朱鸣涛对照，尚未进行 | 待本人完成 |
| 朱鸣涛 / 241250048 | 测试、扫描与互查 | 待本人运行 | 待本人记录 | 待本人记录 | 待本人验证 | 与谢浩天对照，尚未进行 | 待本人完成 |

## 组长个人验收与原始证据

验收时间：2026-10-16 13:11（Asia/Shanghai）。完整 `make all` 成功退出，全部七份证据在同一目录。机器可见资源按原值记录；没有通过修改 env.json 伪造硬件。验收清单和各文件 SHA-256 见 [reports/leader-241250014.json](reports/leader-241250014.json)。

| 验收项 | 实际结果 / 证据 |
| --- | --- |
| 完整运行目录 | /root/241250014/buildchecker/e4/work/20261016-130638 |
| 环境检查 | env.json problems=[]，身份 241250014；warnings 保留较低建议资源和未设置 daemon 级镜像加速提示；基础镜像实际用固定 digest 的显式镜像站地址拉取 |
| 构建 | build.log 成功；image.json 的架构 amd64，镜像名 e4-buildchecker:241250014；镜像 ID 见验收 JSON |
| 工具链 | toolchain.lock 已导出；容器 Python 3.13.14、Make 4.4.1、GCC 14.2.0、strace 6.13，Python 包按原锁文件安装 |
| 单元测试 | test.log：3 passed in 0.01s |
| 冒烟 | make_exit_code=0、app_output="1"、config_h_opened 非空、passed=true；trace_lines=1206，仅作为本次观察 |
| 完整运行的扫描 | secret-scan.txt：未发现问题，覆盖 e4 跟踪文件、全仓可见历史、镜像历史和环境变量 |
| 假 Key 检出 | /root/241250014/buildchecker/e4/work/20261016-131139-leak-detected/secret-scan.txt；扫描器退出 1，make scan 返回 2（预期失败） |
| 清理后再扫描 | /root/241250014/buildchecker/e4/work/20261016-131139-after-cleanup/secret-scan.txt；返回 0，通过 |
| Git 与凭据 | 假文件已从索引与工作区移除，git status --porcelain 为空，git ls-files .env 无输出，.env 权限 0600 |
| 原始日志 | 成功总日志 /root/241250014/e4-make-all-verified.log；首次慢源中止日志 /root/241250014/e4-make-all.log 单独保留 |
| 证据归档 | /root/241250014/E4_A09_241250014_20261016_evidence.tar.gz；未打包 .env、凭据或假 Key 输入文件 |
| 归档 SHA-256 | e8b998b8958f1da811da58ec2bf6f8654083f95c9fe0a2fb03db147452a6efb6 |

服务器常规运行用个人目录直接 `make all`。本次通过临时 systemd 服务保留断线期间的执行，最终成功服务为 `e4-a09-leader-verified`，显式设置 HOME=/root；服务已经结束，无业务常驻进程。首次尝试未设置 HOME 导致一个 Git 全局身份诊断警告，该次记录保留，最终成功自检已消除该环境警告。

后续成员需各自按同一源码 SHA 运行；环境骨架成功只说明构建、测试和跟踪可用，不代表 BuildChecker 论文算法已实现。

## 相邻组 README 互查

| 检查方 / 执行人 | 被检查组 / 仓库 | 所测 SHA | 仅按 README 重跑结果 | 证据路径 | 问题与处理 |
| --- | --- | --- | --- | --- | --- |
| 本组 / 朱鸣涛（待执行） | 待老师指定 | 待填 | 未开始 | 待填 | 尚未指定对象 |
| 相邻组 / 待确认 | 本组 E4 分支及源码基线 | 待对方实测 | 未开始 | 待对方提供 | 入口已准备，等待实际互查 |

以上未完成事项需要其他成员或互查组实际参与。E4 组长个人成功不等于全员独立运行、组内对照或跨组互查全部完成；A/B 真实服务产物联调属于后续 E12。
