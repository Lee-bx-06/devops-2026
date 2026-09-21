# E2 接口契约交付件

本目录是 E2 阶段 B1（公共契约与版本）的交付内容，按可直接合并进小组仓库的结构组织。

| 项 | 值 |
|---|---|
| 配对组编号 | 第 9 组，`pair09` |
| A 组 | A09 |
| B 组 | B09 |
| 仓库 | https://github.com/Lee-bx-06/devops-2026 |
| 本文档维护人 | 李秉轩（B1） |

## 1. 目录结构

```
.
├─ README.md                      本文件，交付索引与评审说明
├─ AI_USAGE.md                    AI 使用记录，按条目追加
├─ CONTRIBUTIONS.md               个人贡献记录
└─ docs/
   ├─ BACKLOG.md                  按第 12 页格式的可验收任务
   ├─ CHANGELOG.md                契约变更记录，含本组自行决定的部分
   ├─ versioning.md               版本规则、兼容性判定、变更流程、消费者清单
   ├─ adr/
   │  ├─ README.md                ADR 规则与索引
   │  ├─ ADR-000-template.md      四段式模板
   │  ├─ ADR-001-async-job.md     异步 Job 与 202 受理
   │  └─ ADR-002-strict-schema.md 严格 Schema 与配套变更流程
   └─ interfaces/
      ├─ task.schema.json         统一任务模型，A1 与 B1 共管
      ├─ endpoints.md             四个创建端点与一个查询端点
      ├─ states-errors.md         状态机、错误码、检测发现与系统错误的分离
      └─ samples/
         ├─ create-repair-request.example.json
         ├─ job-full-check-succeeded.example.json
         ├─ job-timed-out.example.json
         └─ invalid/
            ├─ invalid-job-type.example.json
            └─ invalid-incremental-missing-baseline.example.json
```

## 2. 仓库信息与合并步骤

编号已按第 9 组落实：配对组 `pair09`，A 组 A09，B 组 B09。文档里的编号、样例里的 `artifact://pair09/...` 产物命名空间、`idempotency_key` 前缀三处已保持一致。

合并进仓库的动作：

1. 把 `docs/`、`README.md`、`AI_USAGE.md`、`CONTRIBUTIONS.md` 拷到仓库根目录
2. 把 A09 的组员加为仓库协作者。第 24 页要求另一组能读取产物文件，没有访问权限这条做不了
3. `task.schema.json` 交给 A1 做联合评审
4. 建 Issue 与 PR，把完整 40 位 SHA 回填到 `CONTRIBUTIONS.md`

## 3. 所有权边界

写清边界是为了避免两个人改同一份文件。A1 与 B1 都负责公共契约，因此需要分工。

| 文件 | 归属 | 说明 |
|---|---|---|
| `docs/interfaces/task.schema.json` | A1 与 B1 共管 | B1 出初稿，A1 从校验实现角度复核。任何一方改动都要另一方确认 |
| `docs/interfaces/endpoints.md` | B1 | A1 只确认端点与 schema 的引用关系是否一致 |
| `docs/interfaces/states-errors.md` | B1 | 涉及 EChecker 的部分需 A3 确认 |
| `docs/versioning.md`、`docs/CHANGELOG.md` | B1 | |
| `docs/adr/README.md`、`ADR-000`、`ADR-001`、`ADR-002` | B1 | ADR-003 至 005 在索引里已留位，待认领 |
| `docs/BACKLOG.md` | 共同维护 | B1 起草，任何人可加行 |
| `AI_USAGE.md`、`CONTRIBUTIONS.md` | 每人自行追加 | |

本目录中**不包含**以下内容，它们属于其他同学，需要向对方索取：

| 内容 | 负责人 | 为什么需要 |
|---|---|---|
| `tools/validate.py` | A1 | 第 25 页第 01 条检查要靠它 |
| 全量检测与增量检测的请求响应样例 | A2、A3 | `endpoints.md` 里只放了最小示例，权威样例应由接口负责人提供 |
| DRAFT 与 REPAIR 的完整样例 | B2、B3 | 同上 |

## 4. 验收对照

### 第 17 页课堂作业三条

| 作业要求 | 当前状态 | 还差什么 |
|---|---|---|
| 配对组能解释同一份请求和结果 | 部分满足 | `endpoints.md` 与样例已具备，需要与 A 组对读一次 |
| 有接口样例、Backlog 和设计记录 | 满足 | 样例由四位接口负责人补全后更完整 |
| 个人贡献与版本能够追溯 | 未满足 | 待填仓库地址、提交 SHA、Issue 与 PR |

### 第 25 页最小检查四条

| 检查 | 当前状态 | 说明 |
|---|---|---|
| 01 运行脚本检查四类请求与响应 | 部分满足 | 已用 `jsonschema` 验证现有样例，完整脚本待 A1 |
| 02 `job_type` 改成 `ABC` 应被拒绝 | 满足 | `samples/invalid/invalid-job-type.example.json` |
| 03 删除增量任务的 `baseline` 应被拒绝 | 满足 | `samples/invalid/invalid-incremental-missing-baseline.example.json` |
| 04 解释 MD 为什么不等于工具执行失败 | 满足 | `states-errors.md` 第 3 节 |

### 第 24 页附加要求

| 要求 | 当前状态 |
|---|---|
| 证明另一组能读取产物文件 | 未执行。需要对方按 `endpoints.md` 第 4 节真实打开一次并回贴内容 |

## 5. 本地校验方式

```
python -m pip install jsonschema
python tools/validate.py
```

`tools/validate.py` 由 A1 提供。在它完成之前，可以用下面的方式做临时校验：加载 `task.schema.json`，对 `samples/` 下的样例逐个校验，`samples/invalid/` 下的样例必须报错。

建议 A1 在脚本里按 `job_type` 先选分支再校验。当前 schema 顶层用 `oneOf` 区分 Job 与创建请求，直接校验时的报错信息是"不匹配任何分支"，不利于定位。按 `job_type` 选分支后可以给出更准确的提示。

## 6. 已知限制

1. `finding.detector` 目前是自由字符串，取值集合未收敛
2. `ERROR_REPORT` 产物的文件结构未定稿
3. 严格模式在扩展字段时有成本，见 ADR-002，该决定目前状态为 Proposed
4. `docs/BACKLOG.md` 中第 9 至 12 项尚未开始
