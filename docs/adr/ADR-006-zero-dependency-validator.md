# ADR-006：校验器零依赖，从 schema 读常量而非硬编码

- 状态：**已接受**（A1 谢浩天，A09）
- 日期：2026-09-21
- 契约版本：1.0.0
- 相关：第 2、11、25 页；`docs/VALIDATION.md` 第四节

## Context

第 25 页的第一条最小检查是「运行 `validate.py`，检查四类请求与响应」。
第 25 页的措辞是「运行」，暗示它应当当场可跑。

而第 2 页给出了硬时间约束：苏州 09-20 是 **E2 + E3 共 150 分钟**，
且与另一实验共享课堂。任何需要现场装环境、配网络、等依赖的方案，
在这个预算下都是风险。评分环境同样未必有网、未必有第三方包。

Python 生态里校验 JSON Schema 的标准做法是 `jsonschema` 库。
但本机实测 `jsonschema`、`referencing`、`jsonschema_specifications`
**全部未安装**（Python 3.14.6）。

于是有两个问题要一起解决：

1. 没有 JSON Schema 引擎，怎么执行第 25 页的检查？
2. 手写校验逻辑必然与 `task.schema.json` 重复。两份定义如何不漂移？
   第 26 页「共享 Schema 同步更新」正是在担心这件事。

## Decision

### 1. `tools/validate.py` 只用 Python 标准库

`json` + `re` + `pathlib` + `sys`，零第三方依赖。任何有 Python 3 的环境
（含课堂机器、评分机、B 组同学的机器）都能直接跑：

```bash
python3 tools/validate.py
```

### 2. 校验器**从 schema 读取**常量，不硬编码

`validate.py` 的 `Schema` 类在启动时解析 `task.schema.json`，抽取：

| 抽取项 | schema 来源 |
| --- | --- |
| `job_type` 枚举 | `$defs.job_type.enum` |
| `status` 枚举 | `$defs.job_status.enum` |
| `finding.type` 枚举 | `$defs.finding_type.enum` |
| `schema_version` 值 | `$defs.create_request.properties.schema_version.const` |
| 错误码正则 | `$defs.error_code.pattern` |
| `job_id` / `trace_id` / `artifact_uri` / `commit` / `sha256` / ISO8601 正则 | 对应 `$defs.*.pattern` |
| 三种 `kind` 的字段集与必填集 | `$defs.{create_request,job,artifact_record}` |
| 每类 job 的 `input` 必填集 | `$defs.input_*.required` |
| 每类 job 的 `output` 必填集 | `$defs.output_*.required` |
| `finding` / `error` / `execution` / `artifact` 的必填集 | 对应 `$defs.*.required` |

**这是防漂移的核心机制**：把 `job_type` 枚举从四个改成五个，
校验器立刻按五个校验，不需要同步修改任何 Python 常量。
反之，如果校验器里硬编码了 `JOB_TYPES = {...}`，两处就会各自演化。

`tests/test_validate.py::TestSchemaAndValidatorAgree` 断言抽取结果与
第 8、9、19 页给定值一致，确保抽取本身没出错。

### 3. 明确声明它是「镜像」，不是引擎

`validate.py` 的模块 docstring 和 `VALIDATION.md` 第四节都写明：
**`task.schema.json` 是权威定义，`validate.py` 是它的可执行镜像。**
若两者分歧，以 schema 为准并修 `validate.py`。

镜像覆盖不到的部分（如 `output_draft` 的 `allOf` 组合求解）由等价的
手写逻辑覆盖，而不是机械求解 JSON Schema。

### 4. 覆盖度检查内建

`check_coverage()` 不只校验单个文件，还断言**样例集本身完整**：

- 四类 `job_type` 各有请求样例与成功响应样例（第 25 页检查 01）
- 六种 `status` 各有 Job 样例（第 8 页）
- 至少一个独立 `artifact_record`（第 24 页）

所以「删掉一个样例」也会让 `make check` 失败——覆盖度本身是被校验的对象。

### 5. 负例必须声明拒绝原因

`samples/invalid/*.json` 每个都带 `expected_error` 字段，
校验器不仅要求它被拒，还要求**拒绝理由包含该字符串**，否则报
「被拒原因与 expected_error 不符」。

理由：如果只检查「被拒」，那么契约收紧后一个负例可能因为**另一个**原因
被拒，测试仍然绿，但它守护的那条规则其实已经失效了。
声明原因让每个负例锁定它真正要防的回归。

## Alternatives

### 用 `jsonschema` 库

最正统，schema 是唯一真源，天然不漂移，且能完整求解 `allOf` / `oneOf` /
`if-then`。但需要 `pip install`，在第 2 页的 150 分钟共享课堂里是实打实的风险；
评分环境无网时直接跑不起来，第 25 页检查 01 无法演示。

**这是本 ADR 里最难舍弃的选项。** 若课前能确认所有环境都装好 `jsonschema`，
应当改用它，届时 `validate.py` 可缩到几十行。已作为前置条件记入 `BACKLOG.md`。**当前否决。**

### 硬编码常量（`JOB_TYPES = {...}` 写在 Python 里）

写起来最快，旧稿正是这么做的。但两份定义会各自演化：
改了 schema 忘改 Python，校验器就开始放行 schema 不允许的东西，
而且这种失效是**静默**的——测试照样绿。第 26 页「共享 Schema 同步更新」
的要求在这种情况下无法满足。**否决。**

### 不写校验器，只提供 schema 和样例

省掉最多工作量。但第 25 页四条检查里有三条依赖「运行 `validate.py`」，
而 A1 的验收条件在分工表里就是「四类 job 能被同一份 schema 表达，
`validate.py` 可跑」。没有校验器，A1 的核心交付物就缺了一件，
B 组也无法自行验证他们写的样例是否合规。**否决。**

### 写一个通用 JSON Schema 求解器

技术上可行且能彻底消除镜像问题。但要支持 `oneOf` / `if-then` / `allOf` /
`$ref` / `pattern` / `maxProperties` 的完整语义，代码量会远超本次作业需要，
且引入自身 bug 的风险高于它消除的风险。**否决。**

### 用 Makefile 之外的方式（如 pre-commit hook）强制校验

好实践，但依赖各人本地环境配置，课堂上不可靠。`make check` 是最小公约数。**部分采纳**：
提供 `Makefile`，但不强制 hook。

## Consequences

**得到的：**

- `python3 tools/validate.py` 在任何有 Python 3 的机器上立即工作，
  第 25 页检查 01–03 可当场演示，不依赖网络。
- schema 与校验器由构造保证同步：常量是读来的，不是抄来的。
- `expected_error` 机制让 18 个负例各自锁定一条规则，不会因为契约收紧而假绿。
- 覆盖度检查防止「样例集悄悄缺了一类 job」。
- B 组可以拿 `validate.py` 校验他们自己的文件
  （`python3 tools/validate.py ../B09/x.json`），联调成本降低。

**付出的：**

- 校验逻辑与 schema 存在**结构性重复**：schema 声明约束，
  Python 用等价逻辑执行约束。新增一类约束要改两处。
  缓解：常量已自动化，剩下的只是「检查函数」这一层。
- 不是完整 JSON Schema 实现，schema 里某些声明性组合
  （`allOf` 合并 `output_common`）由手写逻辑覆盖，理论上可能与 schema 语义有细微差异。
  缓解：`VALIDATION.md` 第四节列出已知未覆盖项。
- 约 380 行 Python 需要维护。
- 如果课前环境确认能装 `jsonschema`，这份工作会部分作废。
  接受这个风险，因为「当场跑不起来」的代价更高。

**验证：**

```bash
$ python3 tools/validate.py
A09/B09 公共契约校验通过：四类请求与响应、六种状态、artifact 记录与全部负例均符合 task.schema.json。

$ python3 -m unittest discover -s tests -v
Ran 27 tests in 0.008s
OK
```

`TestSchemaAndValidatorAgree` 专门验证「读取」这条机制：
断言从 schema 抽出的枚举与第 8、9、19 页一致，且四类 `job_type`
都抽到了非空的 `input` 必填集。
