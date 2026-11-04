# B01：E5–E7 组长执行与验收流程

## 1. 基线与职责

- E4 基线：B09 已完成，证据见提交时附带的 `B09_E4_工作与贡献汇总.md`。
- 本条线小组：B01。
- 轨道：B，DRAFT。
- 执行目录：`e5/reference-b`。
- B1：个人复现、仓库和 CI 门禁、失败 PR、最终合并与验收。
- B2：DRAFT 自动构建实现、修复候选和 E6 证据。
- B3：独立负向验证、超时清理检查、Review 和复核记录。

## 2. 环境检查

在 Ubuntu 云服务器从仓库根目录执行：

```bash
cd e5/reference-b
docker version
docker compose version
docker buildx version
docker run --rm hello-world
python3 scripts/lab_cloud.py doctor
```

拉取课程固定镜像：

```bash
docker pull python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
docker pull python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74
docker pull docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad
```

## 3. E5

```bash
python3 scripts/lab_cloud.py build \
  --out work/b01/build-01 \
  --build-timeout 1200

python3 scripts/lab_cloud.py e5 \
  --out work/b01/e5-01 \
  --build-timeout 600
```

检查：

```bash
cat work/b01/e5-01/iter-01/result-retry.json
cat work/b01/e5-01/iter-01/prompt-error-driven.txt
cat work/b01/e5-01/iter-01/prompt-context-driven.txt
grep -n "make: not found" \
  work/b01/e5-01/iter-01/build/build-stdout.log \
  work/b01/e5-01/iter-01/build/build-stderr.log
```

合格条件：基线构建退出码为 `1`，真实日志包含 `make: not found`，E5 采集退出码为 `0`。网络错误、空日志和权限错误不算复现成功。

分别发送两类提示给对话模型，保存完整原始回复和最终 Dockerfile，填写：

```text
course-support/templates/候选来源记录.json
```

手工构建并运行候选：

```bash
docker build --progress=plain \
  -f work/b01/candidate/Dockerfile \
  -t course1020-b01-e5:local \
  work/b01/e5-01/project \
  > work/b01/e5-01/candidate-build.log 2>&1

image_id=$(docker image inspect course1020-b01-e5:local --format '{{.Id}}')
docker run --rm --network none "$image_id" \
  > work/b01/e5-01/verify.log 2> work/b01/e5-01/verify-stderr.log
cat work/b01/e5-01/verify.log
```

合格条件：构建和运行退出码均为 `0`，输出为 `hello E3`。

## 4. E6

```bash
python3 scripts/lab_cloud.py e6 \
  --candidate work/b01/candidate/Dockerfile \
  --out work/b01/e6-01 \
  --build-timeout 600

python3 scripts/verify_e6_b_evidence.py \
  --run-dir work/b01/e6-01/evidence
```

检查 `work/b01/e6-01/evidence/result.json`：

- 第一轮 `failure_class=MISSING_MAKE`，退出码为 `1`。
- 第二轮构建退出码为 `0`。
- 程序运行使用第二轮 `image_id`。
- 程序退出码为 `0`，输出 `hello E3\n`，`output_matches=true`。

## 5. E7 本地门禁

```bash
python3 scripts/lab_cloud.py gate \
  --candidate work/b01/candidate/Dockerfile \
  --out work/b01/e7-01 \
  --build-timeout 600

cat work/b01/e7-01/gate/gate-result.json
cat work/b01/e7-01/gate/results.csv
```

整体门禁退出码必须为 `0`，`unit-tests` 和五个场景必须全部 `passed=true`。场景自身的预期故障退出码可以为 `1`。

## 6. GitHub CI 与合并门禁

仓库根目录的 `.github/workflows/e7-b-quality-gate.yml` 已配置工作目录 `e5/reference-b`。首次推送后确认 `e7-b-quality-gate` 正常通过。

1. 核对实际 Check Run 的 `app_id`，通常为 `15368`。
2. 使用 `course-support/ci/B-main-protection.json` 配置 `main`。
3. 开启 `strict=true` 和 `enforce_admins=true`。
4. 创建 `e7-gate-reject-demo` 分支，复制 `test_ci_reject_demo.py` 错误版本。
5. 确认预期为 `1`、实际为 `0` 的断言使 PR 检查失败。
6. 尝试普通合并，保存真实拒绝日志、PR JSON 和失败 artifact。
7. 在同一 PR 中替换为 `fixed/test_ci_reject_demo.py`。
8. 确认最新 SHA 为 `25 passed` 后再合并，保存 `MERGED`、`mergeCommit` 和恢复 artifact。

CI 命令、分支保护和证据路径以课程 04 指南为准。不得把课程示例运行 ID 写成 B01 自己的运行结果。

## 7. 最终交付

- B1、B2、B3 的个人运行证据和实际贡献。
- 候选 Dockerfile、原始模型回复、SHA-256 和来源记录。
- E5 原始失败、E6 两轮构建、E7 六项门禁的完整日志。
- 正常、失败、恢复三次 CI URL 及 artifact。
- `main` 分支保护、合并拒绝和最终合并记录。
- `course-support/templates/实验报告.md` 和 `验收记录.csv` 的填写版本。
- 密钥扫描结果，并确认未提交 `.env`、Token、私钥或密码。

`work/` 被 `.gitignore` 忽略，提交原始证据时按 05 清单选择性使用 `git add -f work/...`。
