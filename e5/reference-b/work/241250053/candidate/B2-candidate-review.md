# B2 模型候选与 Dockerfile 约束复核

## 复核人与基线

- 姓名：赵润昊
- 学号：241250053
- 角色：B2 / DRAFT
- 完整仓库提交 SHA：`82ff73160e646114ae5799da49d9caf9b64135dc`
- 复核日期：2026-11-04

## 候选来源

本次 B2 复核对象是当前 `main` 中 B1 已保存的原始模型回复与最终候选，不声称本次独立复跑新调用了模型。

- 原始来源记录：`work/b01/candidate/provenance.json`
- 完整原始模型回复：`work/241250053/candidate/model-response.txt`
- 最终候选 Dockerfile：`work/241250053/candidate/Dockerfile`
- 候选 SHA-256：`5e28da373adeb6e649ddf00f122b08d0d5c39ab41b041d3e6e72370c910c0452`

## 原始回复与最终候选差异

原始回复建议安装 `build-essential`，并保留固定基础镜像、`RUN make` 与 `CMD ["./hello"]`。最终候选在原始回复基础上只有一项手工适配：

1. 由于实验服务器无法稳定访问 `deb.debian.org`，在 `apt-get update` 前把 Debian 软件源改为可访问的华为云镜像。

该修改只属于网络基础设施适配，没有改变修复语义，也没有改变项目构建和运行指令。

## 强制约束复核

| 约束 | 结果 | 证据 |
|---|---|---|
| 保留固定 `FROM` digest | 通过 | Dockerfile 第 1 行，digest 为 `70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f` |
| 保留 `RUN make` | 通过 | Dockerfile 第 14 行 |
| 保留 `CMD ["./hello"]` | 通过 | Dockerfile 第 15 行 |
| 只补充缺失工具链 | 通过 | 安装 `build-essential`，未改动源码与 Makefile |

原始行号提取结果保存在 `constraint-lines.txt`。

## 独立构建与运行验证

- 候选构建退出码：`0`
- 候选镜像 ID：`sha256:96e15ed70d8952511c44a3da8766bad510fec20125ce8a0bd15aa92fe87ee842`
- 按镜像禁网运行退出码：`0`
- stdout：`hello E3`
- stderr：空

## 复核结论

选择该候选的理由成立：它针对 `make: not found` 补充最小必要的构建工具链，同时保留了固定 `FROM` digest、`RUN make` 和 `CMD ["./hello"]` 三项关键约束。最终候选已在完整 SHA `82ff73160e646114ae5799da49d9caf9b64135dc` 上独立构建并禁网运行成功。
