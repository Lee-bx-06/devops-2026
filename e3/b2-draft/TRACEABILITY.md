# B2 E3 收尾确认与交付追溯

负责人：B2（zrh / GitHub `ZRH1213`）。日期：2026-10-12。

关联 Issue：[E3 收尾 #30](https://github.com/Lee-bx-06/devops-2026/issues/30)。
关联 PR：[B2 收尾 PR #32](https://github.com/Lee-bx-06/devops-2026/pull/32)。
B2 确认评论：[Issue #30 中的本人回复](https://github.com/Lee-bx-06/devops-2026/issues/30#issuecomment-6125655483)。

## ADR-011 的 B2 消费侧确认

B2 确认：依据已接受的 ADR-007，DRAFT 成功输出的 `environment` 和 `build`
可直接、无损映射到 FULL_CHECK 输入，不需要追加字段：

```text
FULL_CHECK.input.environment = DRAFT.output.environment
FULL_CHECK.input.build       = DRAFT.output.build
```

逐字段对应：`environment.image_uri`、`environment.configuration_id`、
`build.command`、`build.clean_command`、`build.verify_command`、`build.project_root`。
`configuration_id` 由 DRAFT 生成并原样交接；命令依次执行 clean、build、verify，
`clean_command` 只做清理；`project_root` 为容器内绝对 POSIX 路径。

验证依据为 `tests/test_validate.py` 中的 `TestA2B2DraftHandoff`，特别是
`test_draft_output_maps_directly_to_full_check_input` 对两个对象的全等断言。
ADR-011 的整体状态仍由 B1 在所需消费方全部确认后更新。

## 原始 E3 交付

| 内容 | 原始内容提交 | 文件落点 |
| --- | --- | --- |
| Tiny Greeting、失败/参考 Dockerfile、运行器及测试 | [43f6b651a51ee98c0dcbc6f2c36ac525bd865d7e](https://github.com/Lee-bx-06/devops-2026/commit/43f6b651a51ee98c0dcbc6f2c36ac525bd865d7e) | `e3/fixtures/draft/`、`e3/scripts/run_draft_baseline.py`、`e3/tests/test_draft_baseline.py`、`e3/b2-draft/README.md` |
| 真实 Docker 实测证据 | [cf272b656fe16f536d048aee8b409dd6e2efd790](https://github.com/Lee-bx-06/devops-2026/commit/cf272b656fe16f536d048aee8b409dd6e2efd790) | `e3/evidence/draft-run-20261012T075533Z-e00a6be2/` |

这两个提交已直接进入 `main`。本次收尾 PR 补充 Issue/PR 关联与确认记录，
保留原始提交历史，不将追溯补录描述为原始代码通过 PR 合并。

Docker 实测 `manifest.json` 记录 `status=succeeded`：失败候选暴露 `make: not found`
（容器内命令退出码 127）；参考镜像 clean/build/verify/执行均为 0，输出 `hello E3`。
运行时内容提交为 `43f6b651a51ee98c0dcbc6f2c36ac525bd865d7e`，并保存 fixture 与运行器哈希。

该证据覆盖 B2 DRAFT 测试基线；实际服务交接与可拉取镜像的验收另行进行。
