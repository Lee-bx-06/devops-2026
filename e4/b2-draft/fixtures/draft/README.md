# DRAFT 冒烟样例

本目录只保留 E3 Tiny Greeting 的源码、Makefile 和故意失败的 Dockerfile。
`Dockerfile.broken` 的基础镜像没有 `make`，所以构建必须非零退出，日志必须包含
`make: not found`。E4 用这个固定判据确认容器中的 DRAFT 能调用宿主机 Docker 并取得完整失败日志。
