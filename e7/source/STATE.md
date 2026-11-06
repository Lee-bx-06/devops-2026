# E7 A 当前状态

谢浩天，241250033，A09 组。

## 主机内存适配

教师为本组分配 2 GiB 主机，系统实际报告约 1.7 GiB。`scripts/doctor.py` 的模板最低内存 4 GiB 会拦住这台分配主机，因此本组将最低内存改为 1.5 GiB。

内存仍从 `/proc/meminfo` 读取并写入资源报告；CPU 最低 2 核、磁盘最低 40 GiB 保持原值。建议配置仍为 4 核、8 GiB 内存、100 GiB 磁盘，低于建议值仍提示。主机升级达到 4 GiB 后，可将 `MIN["mem_gib"]` 恢复为模板的 4。

## 代码与验证

buildchecker 核心算法和 E7 gate 实现未改。沿用 E6 个人新增的依赖一致性测试，并给 E7 oracle 新增两条拒绝错误报告的行为测试；E7 oracle 共 8 条，服务器实测全部通过。

实验与测试只在服务器 `60.204.240.40` 的 `/root/241250033/e7-a` 执行。2026-11-06 服务器最终运行和 CI 均通过，oracle 8 项、服务 17 项、gate 8 项；同一 PR #1 已完成失败拦截、恢复及合并。CI 工作目录位于同一主机 `/opt/actions-runner-e7-241250033/_work/`。

构建使用服务器已缓存的 DaoCloud Python 基础镜像，内容 digest 与模板相同。Dockerfile 使用内置 frontend，避免无须使用的外部 syntax 镜像下载。
