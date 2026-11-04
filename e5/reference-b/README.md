# B 轨道 E5–E7：DRAFT

本目录来自 `DevOps_1020_Student_Cloud/labs/B-draft`，并保留课程提供的 CI、模板和实验包自测。实现覆盖：

- E5：复现缺少 `make` 的构建失败，生成两类提示并保存模型候选。
- E6：自动执行失败基线、候选构建和程序输出验证。
- E7：验证正常、输出不符、无效候选、构建失败和运行超时五个场景。

所有命令均从**本目录**执行，不要从仓库根目录直接运行：

```bash
cd e5/reference-b

python3 scripts/lab_cloud.py doctor
python3 scripts/lab_cloud.py build \
  --out work/b01/build-01 \
  --build-timeout 1200
python3 scripts/lab_cloud.py e5 \
  --out work/b01/e5-01 \
  --build-timeout 600
```

服务测试预期为 `24 passed`。E5 的真实基线必须出现 `/bin/sh: 1: make: not found`，初始 Docker 构建退出码为 `1`，采集脚本退出码为 `0`。

模型修复候选和来源记录放在：

```text
work/b01/candidate/Dockerfile
work/b01/candidate/model-response.txt
course-support/templates/候选来源记录.json
```

E6 和 E7 使用已保存候选：

```bash
python3 scripts/lab_cloud.py e6 \
  --candidate work/b01/candidate/Dockerfile \
  --out work/b01/e6-01 \
  --build-timeout 600

python3 scripts/verify_e6_b_evidence.py \
  --run-dir work/b01/e6-01/evidence

python3 scripts/lab_cloud.py gate \
  --candidate work/b01/candidate/Dockerfile \
  --out work/b01/e7-01 \
  --build-timeout 600
```

课程回放仅作为备用：

```bash
python3 scripts/lab_cloud.py e6 \
  --replay \
  --out work/b01/e6-replay \
  --build-timeout 600

python3 scripts/lab_cloud.py gate \
  --replay \
  --out work/b01/e7-replay \
  --build-timeout 600
```

使用 `--replay` 时必须在来源记录和报告中注明“课程记录回放”，不能声明为本人新生成的候选。

`.github/workflows/e7-quality-gate.yml` 保留为本目录的原始模板。实际 GitHub Actions 入口位于仓库根目录 `.github/workflows/e7-b-quality-gate.yml`，工作目录已经设为 `e5/reference-b`。
