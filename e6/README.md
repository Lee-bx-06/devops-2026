# E6 A：BuildChecker 自动检测与修复复检

谢浩天（241250033），A09 组。2026-11-02 在本组 Ubuntu 云服务器完成。

- [个人实验报告](REPORT-241250033.md)
- [验收记录](E6验收记录-241250033.csv)
- [修复前后校验](evidence/241250033-20261102/verification.json)
- [原始证据复核](evidence/241250033-20261102/raw-evidence-audit.json)

服务沿用 `e5/reference-a/`，核心实现与 2026-10-29 整理的 E6 学生包一致。本次新增一个“依赖完全一致”测试，服务测试从 15 项增至 16 项。

## 复跑

在本组 Linux 服务器的个人克隆中执行。下面的输出目录用于新一轮复跑，已有目录时换一个名字。

```bash
cd e5/reference-a
python3 scripts/course.py doctor
python3 scripts/course.py build --out work/e6-build-repeat --build-timeout 1200
python3 scripts/course.py e6 --out work/e6-before-repeat
echo "BEFORE_EXIT_CODE=$?"
python3 scripts/course.py e6 --fixed --out work/e6-after-repeat
echo "AFTER_EXIT_CODE=$?"
python3 scripts/verify_e6_evidence.py --before work/e6-before-repeat/evidence/findings.json --after work/e6-after-repeat/evidence/findings.json
```

预期：16 项测试通过；原始检测返回 1，报告为 SUCCEEDED 且精确检出两条 MD/RD；修复后返回 0、findings 为空；校验 passed=true，仅 Makefile 输入哈希变化。`course.py` 调用包内 `lab_cloud.py`，按 Git 本地学号选择个人镜像标签。

本组 2 GiB 服务器沿用既有的 1.5 GiB 最低可见内存配置，本次实测 1.7 GiB。完整 work 目录单独交付为 `E6_A_241250033_20261102_raw.tar.gz`，仓库内保存报告和关键 JSON、测试记录。
