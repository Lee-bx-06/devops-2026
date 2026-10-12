# E3 交付索引（A09 ↔ B09 / pair09）

本页把课件《E3 并行测试基线》**第 9 页的提交要求**逐条对到仓库里的实际文件，便于助教和另一位
同学按图索骥。路径都相对于仓库根目录；「怎么验」一列给的是最短的可复跑命令或可核对证据。

角色与负责人：A1 = 谢浩天（241250033）、A2 = 殷晓瑞（241250014）、A3 = 朱鸣涛（241250048）；
B1 = 李秉轩（241250052）、B2 = zrh、B3 = 赵心泉（241250068）。

## 一、A 组：MD/RD 与 C0/C1/C2

| 课件要求 | 仓库落点 | 负责人 | 怎么验 |
| --- | --- | --- | --- |
| MD/RD 项目 | `e3/fixtures/md-rd/`：`main.c` 读 `config.h`，`Makefile` 声明 `unused.h` 而不声明 `config.h` | A1 | 复制到临时目录后 `make && ./app` 输出 `1` |
| 判断依据（人工预期） | `e3/evidence/run-20260930T023602Z-c2ff9588/oracle.json`，标 `COURSE_DERIVED_ORACLE` | A1 | 文件内含 MISSING `main.o→config.h`、REDUNDANT `main.o→unused.h` 两条及理由 |
| C0/C1/C2 三份真实提交 | `e3/fixtures/commits/C0/`、`C1/`、`C2/`，并在证据目录内导出 Git bundle | A1 | `manifest.json` 同时记原始 SHA 与 bundle 重放后的 SHA |
| 版本及预期变化 | 证据目录 `manifest.json` 的观测表、`e3/README.md` 的「样例阶段」一节 | A1 | C0 clean = 10；C1 clean = 12；C2 增量 = 12、clean = 19 |
| 实际观察与失败记录 | 同一证据目录的 `commands.json`、`logs/`、`validation/`、`validation.json` | A1 | 错误输出与缺少工具两条注入路径均失败并保留诊断 |
| Linux 原始系统调用证据 | `e3/review/evidence/linux-strace.txt`、`linux-verification.json` | B1 | 与 `e3/review/B1-review.md` 第三节对照：`openat("config.h")` 与 `make -pn` 的声明不符 |

## 二、B 组：DRAFT 与 MDFixer

| 课件要求 | 仓库落点 | 负责人 | 怎么验 |
| --- | --- | --- | --- |
| DRAFT 项目与构建/功能验证条件 | `e3/fixtures/draft/`；`baseline.json` 定义 `make clean` / `make all` / `make test` 与成功输出 `hello E3` | B2 | `python3 e3/scripts/run_draft_baseline.py --verify-only`（只查映射，不连 Docker） |
| DRAFT 失败样例 | `Dockerfile.broken` + `e3/evidence/draft-run-20261012T075533Z-e00a6be2/logs/002-broken-build.stderr.log` | B2 | 日志末段可见 `make: not found` 与退出码 127 |
| DRAFT 参考成功环境与实测 | `Dockerfile.reference` + 同证据目录 `manifest.json`、`commands.json` | B2 | manifest 记 `status=succeeded`、镜像 ID、`configuration_id` 与逐步退出码 |
| 固定 MD 报告及对应 Makefile | `e3/fixtures/mdfixer/`：`Makefile.before`、`oracle.json`、`SOURCE.md` | B3 | `oracle.json` 给出 MISSING/REDUNDANT 与四种风格的期望改法 |
| 四种声明风格参考修复 | `Makefile.target` / `.macro` / `.hybrid` / `.implicit` 与 `target.patch`、`macro.patch`、`hybrid.patch`、`implicit.patch` | B3 | 四份 `*-fix.log` 均为「修改头文件后输出: 3 / 补丁验证通过」 |
| 无效候选与恢复 | `broken.patch`、`broken-failure.log` | B3 | 非零退出后按 `e3/fixtures/mdfixer/README.md` 第 4 步恢复并再次成功 |

## 三、共同信息

| 课件要求 | 仓库落点 | 负责人 |
| --- | --- | --- |
| README | 根 `README.md`（入口与文档地图）、`e3/README.md`（运行说明）、本页 | A1 / 全组 |
| 环境 | 各证据目录 `manifest.json` 的 `platform` 与工具版本；`e3/review/B1-review.md` 第二节（Linux/WSL2 复核环境） | A1 / B1 |
| 命令与日志 | `e3/evidence/**/commands.json`、`logs/`；`e3/review/evidence/linux-strace.txt` | A1 / B1 / B2 |
| 仓库与 SHA | 本页第五节、`docs/CONTRIBUTIONS.md`、`e3/PUBLICATION.md` | 全组 |
| 个人贡献 | `docs/CONTRIBUTIONS.md`、`docs/AI_USAGE.md`、`e3/PUBLICATION.md` | 各成员 |

## 四、未完成与责任边界（课件第 9 页「未完成也要记录」）

| 事项 | 现状 | 归属 |
| --- | --- | --- |
| ADR-011 消费侧语义确认 | A3 已于 2026-10-12 确认；**待 B2、B3 本人确认**，之后由 B1 把 ADR-011 与索引改为 `Accepted` | B2 / B3 / B1 |
| `configuration_id` 取值格式（E2 样例 8 位十六进制后缀 vs E3 规则 12 位） | 已登记，**待 B1 与 A2/B2 裁定**，见 `docs/versioning.md` 第八节补记 | B1 / A2 / B2 |
| `full-check.clean-project.json` 的 `image_uri` 与 `configuration_id` 自洽性 | 仍登记在 `tests/test_cross_document_consistency.py` 的 `KNOWN_ENV_DEVIATIONS` | A2 |
| B2/B3 的 E3 交付缺 Issue/PR 追溯 | B2 的 `43f6b65`、`cf272b6` 为直接推送 `main`；B3 的 PR #27、#28 未关联 Issue。跟踪 Issue #30 | B2 / B3 |
| 四个服务的实现与跨组 artifact 下载 | 不在 E3 范围，按 E5 / E8 / E12 推进 | 各服务负责人 |

## 五、内容提交与协作记录

E3 的内容提交：

| 交付 | 提交 | Issue / PR |
| --- | --- | --- |
| A1 参考基线与实测证据 | `de31c63`（发布说明 `03d7d75`、文档对齐 `47c273c`） | 直接推送 `main`，见 `e3/PUBLICATION.md` |
| B1 Linux 独立复核与版本影响裁定 | `e293671` | Issue #25 / PR #26 |
| B2 DRAFT 基线 | `43f6b65`、`cf272b6` | 待补（直接推送 `main`），跟踪 Issue #30 |
| B3 MDFixer 固定输入与验证 | `e2ed3f5`、`898fd85` | PR #27 / PR #28 |
| B1 E3 收尾（交付登记、测试门禁、导航） | `ab27738` | PR #29（已合并）；催办 Issue #30 |

## 六、复跑

需要 Python 3、Git、GNU Make 与 C 编译器；DRAFT 基线另需 Docker。

```bash
make check                                  # 样例校验 + tests/ 与 e3/tests/ 的单元测试
python3 e3/scripts/run_baseline.py          # A 侧：MD/RD 与 C0/C1/C2
python3 e3/scripts/run_draft_baseline.py    # B 侧：DRAFT（需要 Docker）
```

边界：人工预期（oracle）与工具实测分开保存，未把人工答案当作检测器输出；
E3 不包含任何服务实现、部署或验收，也不代表跨组 artifact 已被实际下载。
