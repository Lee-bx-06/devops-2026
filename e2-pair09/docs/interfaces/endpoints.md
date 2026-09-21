# 端点契约

| 项 | 值 |
|---|---|
| 负责人 | B1 |
| 版本 | v0.1（草案，待 A1 联合评审） |
| 依据 | 《E2 需求与接口契约》第 7、24、27 页 |
| 单一事实来源 | 字段定义只写在 `task.schema.json`，本文只描述端点、方法与返回语义 |

## 1. 通用约定

| 项 | 约定 |
|---|---|
| 基础路径 | `/v1` |
| 请求媒体类型 | `application/json` |
| 创建语义 | 受理后立即返回 HTTP 202，响应体只含 `job_id` 与 `status: "QUEUED"`，不回传执行结果 |
| `job_id` | 服务端产生，客户端不可指定 |
| 幂等键 | 创建请求必须携带 `idempotency_key`。同一个键重复提交不得产生第二个任务 |
| 查询语义 | 返回 `status`、`execution` 与产物引用，不内嵌大日志 |
| 产物 | 一律通过 `artifact.uri` 引用，读取方式见第 4 节 |
| 时间字段 | ISO 8601，UTC，带 `Z` |
| 契约版本 | 请求与响应都携带 `schema_version`，规则见 `../versioning.md` |

## 2. 端点清单

| 操作 | 方法 | 端点 | 服务 | 主要消费者 |
|---|---|---|---|---|
| 生成构建环境 | POST | `/v1/dockerfile-jobs` | DRAFT | BuildChecker、EChecker、MDFixer |
| 全量检测 | POST | `/v1/full-check-jobs` | BuildChecker | EChecker、MDFixer |
| 增量检测 | POST | `/v1/incremental-check-jobs` | EChecker | MDFixer |
| 修复缺失依赖 | POST | `/v1/repair-jobs` | MDFixer | 重新构建与检测 |
| 查询任务 | GET | `/v1/jobs/{job_id}` | 四个服务共用 | 全部 |

第 27 页注明端点命名是参考值、配对组可协商修改。**本组决定完全采用参考命名，未做修改。**若后续协商修改，必须在此表逐条记录并同步 `../CHANGELOG.md`。

## 3. 各端点明细

### 3.1 生成构建环境

```
POST /v1/dockerfile-jobs
Content-Type: application/json

{
  "schema_version": "0.1",
  "job_type": "DRAFT",
  "idempotency_key": "pair09-draft-c1-0001",
  "input": {
    "repository": { "url": "https://git.example.edu/pair09/demo-project.git",
                    "commit": "3f2a91c0d4e5b6a7f8091a2b3c4d5e6f708192a3" },
    "build": { "command": "make -j4", "verify_command": "make test" },
    "max_iterations": 5,
    "timeout_seconds": 1800
  }
}
```

```
HTTP/1.1 202 Accepted
{ "job_id": "job-draft01", "status": "QUEUED" }
```

终态查询必须能取到：Dockerfile 与镜像引用（`DOCKERFILE`、`IMAGE_REF`）、每轮日志与修改理由（`BUILD_LOG`）、最终构建与验证结果（`VERIFY_REPORT`）。

### 3.2 全量检测

```
POST /v1/full-check-jobs
Content-Type: application/json

{
  "schema_version": "0.1",
  "job_type": "FULL_CHECK",
  "idempotency_key": "pair09-full-c1-0001",
  "input": {
    "repository": { "url": "https://git.example.edu/pair09/demo-project.git",
                    "commit": "3f2a91c0d4e5b6a7f8091a2b3c4d5e6f708192a3" },
    "environment": { "image_ref": "registry.example.edu/pair09/demo-project:cc-MODE0",
                     "configuration_id": "cc-MODE0" },
    "build": { "clean_command": "make clean && make -j4",
               "project_root": "/workspace/demo-project" }
  }
}
```

```
HTTP/1.1 202 Accepted
{ "job_id": "job-full01", "status": "QUEUED" }
```

完整响应见 `samples/job-full-check-succeeded.example.json`。该端点必须同时产出 `ACTUAL_GRAPH`、`DECLARED_GRAPH`、`MD_REPORT`、`RD_REPORT` 四类可引用产物。

### 3.3 增量检测

```
POST /v1/incremental-check-jobs
Content-Type: application/json

{
  "schema_version": "0.1",
  "job_type": "INCREMENTAL_CHECK",
  "idempotency_key": "pair09-incr-c2-0001",
  "input": {
    "repository": { "url": "https://git.example.edu/pair09/demo-project.git",
                    "commit": "7c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f60718293" },
    "base_commit": "3f2a91c0d4e5b6a7f8091a2b3c4d5e6f708192a3",
    "environment": { "image_ref": "registry.example.edu/pair09/demo-project:cc-MODE0",
                     "configuration_id": "cc-MODE0" },
    "build": { "clean_command": "make clean && make -j4",
               "project_root": "/workspace/demo-project" },
    "baseline": { "actual_graph_uri": "artifact://pair09/full01/actual.json",
                  "commit": "3f2a91c0d4e5b6a7f8091a2b3c4d5e6f708192a3",
                  "configuration_id": "cc-MODE0" }
  }
}
```

`baseline` 是必填输入。缺少它的请求必须在入口被拒绝，见 `samples/invalid/invalid-incremental-missing-baseline.example.json`。

两条必须成立的语义约束：

1. `baseline.commit` 必须等于 `base_commit`
2. `baseline.configuration_id` 必须等于本次 `environment.configuration_id`，否则历史图与当前图不可比

终态输出除当前发现外，还要给出新增与消除的发现，并返回更新后的图供下一次提交使用。

### 3.4 修复缺失依赖

```
POST /v1/repair-jobs
Content-Type: application/json

{
  "schema_version": "0.1",
  "job_type": "REPAIR",
  "idempotency_key": "pair09-repair-c1-0001",
  "input": {
    "repository": { "url": "https://git.example.edu/pair09/demo-project.git",
                    "commit": "3f2a91c0d4e5b6a7f8091a2b3c4d5e6f708192a3" },
    "md_report_uri": "artifact://pair09/full01/md-report.json",
    "makefile_path": "Makefile",
    "environment": { "image_ref": "registry.example.edu/pair09/demo-project:cc-MODE0",
                     "configuration_id": "cc-MODE0" },
    "build": { "command": "make -j4", "verify_command": "make test" }
  }
}
```

本任务只消费 `MISSING`。`REDUNDANT` 不在修复范围内。终态输出必须给出 Git Patch（`PATCH`）、声明风格说明与构建和重检结果（`REPAIR_REPORT`）。候选补丁未通过验证时必须拒绝并记录原因，此时任务仍可以是 `SUCCEEDED`，因为修复流程本身正常跑完了。

### 3.5 查询任务

```
GET /v1/jobs/job-full01

HTTP/1.1 200 OK
{
  "schema_version": "0.1",
  "job_id": "job-full01",
  "trace_id": "trace-pair09-0001",
  "job_type": "FULL_CHECK",
  "status": "RUNNING",
  "execution": { "attempt": 1, "started_at": "2026-09-20T02:10:05Z" }
}
```

## 4. 产物读取方式

本组约定两条读取路径，二者必须同时可用：

| 方式 | 形式 | 用途 |
|---|---|---|
| 引用解析 | 把 `artifact://pair09/full01/actual.json` 解析为配对组共享目录下的 `pair09/full01/actual.json` | 课堂联调与本地互读 |
| 下载接口 | `GET /v1/artifacts/{artifact_id}` | 后续服务化时替换引用解析 |

第 24 页要求"必须证明另一组能读取文件"，因此验收动作是：由对方按上表任选一种方式真实打开该文件并把内容贴回，而不是只确认地址写法正确。

## 5. HTTP 层错误与任务层错误的分工

这两类不能混用，否则第 25 页的检查 02 与 03 会判不出来。

| 场景 | HTTP 状态 | 响应体 |
|---|---|---|
| 请求体不符合契约（如 `job_type` 非法、缺 `baseline`） | 400 | 校验错误说明，**不创建任务** |
| 查询的 `job_id` 不存在 | 404 | 错误说明 |
| 任务正常执行但检出 MD/RD | 200 | `status` 为 `SUCCEEDED`，发现写在 output 或 `ERROR_REPORT` 产物里 |
| 任务执行失败（镜像构建失败、超时、分析器崩溃） | 200 | `status` 为 `FAILED` 或 `TIMED_OUT`，原因写在 `job.error` |

任务已受理后，执行结果一律用 HTTP 200 加 `status` 表达，不用 5xx。5xx 只保留给服务自身不可用的情况。

## 6. 变更规则

端点增删、语义调整、`job.error.code` 枚举变化都会影响下游。变更流程、兼容性判定与版本递增规则见 `../versioning.md`，每次变更必须同时更新本文与 `../CHANGELOG.md`。
