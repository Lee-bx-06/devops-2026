# ADR-001: DRAFT 与 BuildChecker 的环境交接契约

## Context
DRAFT 负责生成可构建环境，BuildChecker 需要在该环境中执行全量依赖检测。
E2 阶段只定义接口，不要求部署 API。

## Decision
DRAFT 成功后向 BuildChecker 提供：
- `image_reference`
- `configuration_id`
- `project_root`
- `clean_build_command`
- Dockerfile artifact
- 构建/验证结果
- 每轮日志及修改原因

大文件通过 artifact URI 引用，不直接塞入 Job 响应。

## Pending confirmation with A2
以下内容需要 A2 明确确认后冻结：
1. `image_reference` 的具体格式；
2. `configuration_id` 的命名规则；
3. `clean_build_command` 是否由 DRAFT 输出；
4. `project_root` 的字段名和含义；
5. artifact URI 的实际读取方式。

## Alternatives
- 仅传 Dockerfile：BuildChecker 仍需自行构建环境。
- 仅传镜像：缺少构建过程与可追溯信息。

## Consequences
- BuildChecker 可以直接复用 DRAFT 生成的环境。
- 破坏性字段改名/删除前必须与消费者协商并更新 ADR。
