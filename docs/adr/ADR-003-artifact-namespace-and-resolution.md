# ADR-003：artifact 命名空间与解析约定

- 状态：**已接受**（A1 谢浩天，A09；B1 已接受解析端点与完整 `job_id` URI）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 5、15、21、24 页；`docs/interfaces/endpoints.md` 第四节

## Context

四个服务交接的都是大文件：实际依赖图、声明依赖图、MD/RD 报告、每轮构建日志、
Git patch、重检报告。第 6 页明确「不必把大日志塞进每个响应」，
第 24 页给了产物记录的标准形状：

```json
{
  "artifact_id": "graph-001",
  "type": "ACTUAL_GRAPH",
  "uri": "artifact://pair01/full01/actual.json",
  "media_type": "application/json",
  "producer_job_id": "job-full01"
}
```

并在「讲解与观察」里提出三条要求：**约定解析器或实际下载接口**、
记录提交与配置与生产任务、`sha256` 在需要核验完整性时使用；
最后一条是「E12 必须证明另一组能读取文件」。

这里最容易翻车的地方（本次作业的翻车点 #3）是：**只写 `artifact://` URI
而不写读取方式**。`artifact://` 不是浏览器能打开的协议，如果 A 组写
`artifact://.../actual.json` 而 B 组不知道怎么解析，联调时两边都读不出来，
且这个矛盾会一直藏到 E12 才爆发。

另外第 15 页要求接口文件写明「小组与配对组编号」，第 5 页要求增量检测的
接收方能核对「基线版本和配置匹配」——命名空间与可追溯字段正好承载这两件事。

## Decision

### 1. URI 文法固定为三段

```
artifact://pair09/{job_id}/{name}
```

- `pair09` = A09 与 B09 的共享命名空间，直接写进 URI，满足第 15 页的编号要求
- `{job_id}` 用**完整** `job_id`（如 `job-full09`），而非第 24 页样例里的简写
  `full01`。理由见 Alternatives。
- `{name}` 用 `[A-Za-z0-9._-]+`，不允许再嵌套 `/`，避免解析歧义

schema 用正则强制：`^artifact://pair09/job-[a-z0-9][a-z0-9-]*/[A-Za-z0-9._-]+$`。
写成别的配对组命名空间（如 `pair01`）会被校验器拒绝。

### 2. 产物记录必须自带追溯与完整性字段

在第 24 页五个字段之外，A1 把 `commit`、`configuration_id`、`sha256`
一并列为**必填**：

| 字段 | 为什么必填 |
| --- | --- |
| `artifact_id` | 全局唯一寻址键，解析时用它而不是 URI 字符串 |
| `type` | `ACTUAL_GRAPH` / `DECLARED_GRAPH` / `ERROR_REPORT` / `DOCKERFILE` / `BUILD_LOG` / `GIT_PATCH` / `RECHECK_REPORT` … |
| `uri` | 人类可读的定位提示 |
| `media_type` | 下载方据此设置 `Content-Type`，也据此选解析器 |
| `producer_job_id` | 第 24 页「记录生产任务」；出问题能追到是哪个 job 产的 |
| `commit` | 第 5、21 页：基线属于**固定提交**。40 位完整 SHA |
| `configuration_id` | 第 21、22 页：基线属于**固定构建配置**。增量检测靠它判断基线是否可用 |
| `sha256` | 第 24 页「需要核验完整性时使用」——跨组传输必须能验，所以定为必填而非可选 |

`commit` + `configuration_id` 两个字段合起来，正是 EChecker 判断
「历史图能不能用作本次基线」的依据（第 22 页：「历史图必须能追溯到 base commit」、
「检查基线提交和配置是否匹配」）。

### 3. 解析方式：`GET /v1/artifacts/{artifact_id}`

E2 阶段**不部署**（第 7 页），但契约现在冻结，E12 时任何一方实现都能对接：

```http
GET /v1/artifacts/artifact-full09-error-report
→ 200 OK
  Content-Type: application/json      # 取自记录的 media_type
  ETag: "4e5f6071...a1b2c3d"          # 取自记录的 sha256
  <文件本体>
```

约定四条：

1. **寻址用 `artifact_id`，不用 URI 字符串。** URI 只是给人看的定位提示，
   拿它当键会把命名空间规则焊死进接口。
2. **下载方必须用 `sha256` 校验本体。** 不符即视为传输损坏，重新下载，
   不得静默使用。
3. `404` 时响应体仍是标准 error 形状（`VALIDATION_2001`），不返回裸文本。
4. 保留期至少覆盖本轮 E2 + E3。

### 4. `output.artifacts[]` 内联完整记录，而非只放瘦引用

Job 响应里直接放完整的产物记录（八个字段全带），不再定义一个只有
`artifact_id` + `uri` 的「引用」类型。理由：消费方拿到 Job 响应就该能立刻
决定要不要下载、用什么解析器、下载后怎么验，不需要第二次往返查询。
响应体因此变大一些，但增大的只是几百字节的元数据，不是文件本体——
第 6 页反对的是「把大日志塞进响应」，不是反对塞元数据。

## Alternatives

### 直接用 HTTP URL 作为 `uri`

最省事，浏览器能直接打开。但把产物存储的物理位置（主机名、路径、CDN）
焊进了契约：换存储就要改所有样例和下游代码，属第 26 页的破坏性变更。
逻辑 URI + 约定解析器把「在哪」和「怎么取」解耦。**否决。**

### 把大文件 base64 内联进 `output`

零额外接口。但依赖图动辄几十 KB 到几 MB，base64 再膨胀 33%，
每次查询状态都要重传一遍，直接违反第 6 页「不必把大日志塞进每个响应」。**否决。**

### URI 沿用第 24 页样例的简写 `artifact://pair01/full01/actual.json`

照抄课件最保险。但 `full01` 不是合法 `job_id`（schema 里 `job_id` 形如
`job-full01`），于是 URI 里的段和 `producer_job_id` 对不上，
无法用一条正则同时校验两者，也没法从 URI 直接反查生产任务。
A1 选择用完整 `job_id`，让 URI 自解释且可被机器校验。**否决。** A09/B09 已将
完整 `job_id` 接受为内部契约；课件 URI 仅作说明样例。

### `sha256` 设为可选（照第 24 页「需要核验完整性时使用」的字面意思）

更宽松，各组可省。但 E2 的产物是**跨组**交接的：A 组产、B 组读，
中间可能经过复制粘贴、聊天工具转发、二次上传。不校验就无从知道
对方读到的是不是同一份文件，而 E12 恰恰要求「证明另一组能读取文件」。
定为必填，成本只是生产方多算一次哈希。**否决。**

### 不约定解析器，留到 E12 再说

正是翻车点 #3。等到 E12 才发现读不出来，届时四个服务都要改。**否决。**

## Consequences

**得到的：**

- `artifact://` 有了确定的文法和确定的取法，B 组拿到 URI 就知道该调什么。
- `commit` + `configuration_id` 让 EChecker 的基线匹配检查（第 22 页）
  成为纯数据判断，不需要额外协商。
- `sha256` 必填为 E12「证明另一组能读取文件」提供了客观判据：
  下载后哈希相符即证明成功。
- 命名空间 `pair09` 写进 URI，第 15 页的编号要求自动满足。

**付出的：**

- 生产方必须真的算并保存 sha256，不能填占位值蒙混（校验器只能查格式，
  查不出假哈希——这是人工复核项，已列入 `BACKLOG.md`）。
- URI 里嵌入 `pair09` 意味着换配对组要改样例。但配对关系在本次作业内固定，
  可接受。
- 需要有人实现 `GET /v1/artifacts/{artifact_id}`。E2 不实现，
  E12 前必须落地，已记入 `BACKLOG.md`。
- A09/B09 已接受完整 `job_id` URI；如未来修改这项冻结约定，属破坏性变更，
  需升 `schema_version`。

**验证：**

- `samples/artifact.error-report.json` —— 独立产物记录正例
- `samples/invalid/foreign-artifact-uri.json` —— 命名空间写成 `pair01` → 被拒
- `tests/test_validate.py::TestArtifactContract` —— 断言记录合法、
  跨命名空间被拒、缺 `sha256` 被拒
- `samples/incremental-check.request.json` —— `baseline.actual_graph_uri`
  用同一文法引用上游产物，形成 A2 → A3 的真实交接链

**B1 复核结论：** 接受 `GET /v1/artifacts/{artifact_id}` 作为正式产物读取接口，
并接受 URI 使用完整 `job_id`。
