# E5 B 轨道复现说明

## 输入与版本

- 基线仓库提交：`ed74447`
- 运行目录：`work/e5-03/`
- 实际初始输入：`evidence/241250053/e5/Dockerfile.initial`
- 候选来源：实验包保存的 DeepSeek E5 教学候选回放
- 候选适配后 SHA-256：`34cea12b2065cf6a2cb13f29ee0816ff207854954b4408d7ff8408975dfdc004`

## 初始失败

初始构建在 `RUN make` 失败，日志包含 `/bin/sh: 1: make: not found`。镜像内部命令退出 127，Docker build 退出 1；证据采集脚本成功生成错误定位和两类提示，因此 E5 入口退出 0。

## 候选与选择

本次采用包内记录候选，不声称进行了新的模型调用。候选保持固定 FROM digest、`WORKDIR`、`COPY`、`RUN make` 和 `CMD ["./hello"]`，只新增安装 `build-essential` 的 RUN 指令。服务器访问上游超时时，仅替换注册表和 Debian 下载地址，未改变固定 digest 或修复语义。

## 手工复建与功能验证

- 候选构建退出码：0
- 镜像 ID：`sha256:33d128c3903dcd5072826369415a9586face50e0d460f4fb191d29628590f44a`
- 验证网络：`--network none`
- 验证退出码：0
- 标准输出：`hello E3`

对应证据位于 `evidence/241250053/e5/`。
