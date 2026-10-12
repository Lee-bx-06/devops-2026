# B3 MDFixer 接口工作记录

## 1. 样本来源
- 复制自 A1 的 `e3/fixtures/md-rd/`
- 来源 commit：`47c273c`

## 2. 修复前行为
- `config.h` 为 `VALUE 1` 时，`make && ./app` 输出 `1`
- 修改 `config.h` 为 `VALUE 2`，不 clean，`make && ./app` 仍输出 `1`

## 3. 四种补丁验证结果
| 风格     | patch 文件     | 验证结果 |
|----------|----------------|----------|
| Target   | target.patch   | 通过     |
| Macro    | macro.patch    | 通过     |
| Hybrid   | hybrid.patch   | 通过     |
| Implicit | implicit.patch | 通过     |

## 4. 无效候选与恢复
- 候选：`broken.patch`，故意引入 `invalid_command`
- 验证：`make` 非零退出，日志见 `broken-failure.log`
- 恢复：`cp Makefile.before Makefile && make clean && make && ./app` 成功

## 5. 与 A3/B2 待对齐事项
- C1→C2 的 `CFLAGS` 变化如何映射到 `configuration_id`
- 本 MDFixer 样本后续被 EChecker 消费时应使用哪个基线 commit 和 artifact

## 6. 证据文件清单
- `SOURCE.md`
- `Makefile.before`
- `Makefile.target` / `macro` / `hybrid` / `implicit`
- `target.patch` / `macro.patch` / `hybrid.patch` / `implicit.patch`
- `broken.patch` / `broken-failure.log`
- `oracle.json`
- `verify_patch.sh`