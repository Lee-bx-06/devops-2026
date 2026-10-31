# E6 A 轨交付（241250014）

本目录是 lab6/E6 的 A 轨（BuildChecker）交付，来自 `DevOps_E6_Student_Cloud/labs/A-buildchecker`。

- 学号：241250014
- 轨道：A
- 实验包 SHA-256：`C25E34BD4EB8A836EE7EC9052636B1491BCFEA4E316BCFF47AF63BBCE37A40A0`
- 环境：Ubuntu 24.04.4 LTS，2 CPU / 1.7 GiB 可见内存；服务镜像 `course1020-buildchecker:local`（amd64）
- 原始证据归档：`E6-A-241250014-20261031-work.tar.gz`，SHA-256 `825C2E6A636E21C7526264FB75F3E37912ABA301777AAA66A1E75138E2B31B22`
- 代码/测试提交：`606fdcb6bb86f680df76dbdae03c3d9af8a14d87`

## 复现

在 Linux + Docker 的课程服务器上，把本目录作为仓库根目录执行：

```bash
python3 scripts/lab_cloud.py doctor
python3 scripts/lab_cloud.py build --out work/build-01 --build-timeout 1200
python3 scripts/lab_cloud.py e6 --out work/e6-before
python3 scripts/lab_cloud.py e6 --fixed --out work/e6-after
python3 scripts/verify_e6_evidence.py \
  --before work/e6-before/evidence/findings.json \
  --after  work/e6-after/evidence/findings.json
python3 scripts/lab_cloud.py build --out work/build-02 --build-timeout 1200
python3 scripts/lab_cloud.py e6 --out work/e6-rerun
```

预期：

| 阶段 | 预期 |
| --- | --- |
| `doctor` | 工具齐全；本组 1.7 GiB 内存会报 `mem_gib` problem，按报告书面说明 |
| `build-01` | 15 passed，退出 0 |
| `e6-before` | 退出 1；`MISSING(main.o,config.h)`、`REDUNDANT(main.o,unused.h)` |
| `e6-after` | 退出 0；`findings=[]` |
| `verify` | `passed=true`，`changed_inputs=["Makefile"]` |
| `build-02` | 16 passed，退出 0 |
| `e6-rerun` | 退出 1，仍为同样两条 findings |

## 文件

- `docs/e6-a.md`：实际图、声明图、findings、进程归属、代码阅读与逐条证据行号。
- `docs/E6实验报告.md`：按 lab6 模板填写的实验报告。
- `docs/E6验收记录.csv`：A 轨与共同项验收记录。
- `services/buildchecker/Dockerfile`：环境适配（DaoCloud 同 digest 基础镜像 + 清华 apt/PyPI 源）。
- `services/buildchecker/tests/test_fullcheck.py`：新增 `test_consistent_declaration_produces_no_findings`，测试数 15→16。

`work/` 不在 Git 中；原始 trace、两轮构建日志、`findings.json`、两张图和 `processes.json` 见上面的归档文件。报告中的路径均相对于归档解压后的 `work/`。
