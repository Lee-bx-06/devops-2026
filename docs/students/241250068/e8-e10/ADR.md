# 决策记录

背景与约束：B 组需从固定 MD 报告出发，只改 Makefile 声明、不动编译配方；报告必须与项目提交绑定；补丁在真实构建前不能落地。
选择与替代方案：
- B（身份绑定）：以 `report['commit'] == 项目 HEAD` 作为补丁前置条件，选择“显式报错 STALE_REPORT”，替代“按文件内容猜测”的不确定做法；代价是报告与提交必须同版本。
- B（补丁落点）：按目标行形态分流 direct/macro/mixed，替代“统一追加到目标行”；代价是共享变量会被其他目标共同引用，作用范围扩大。
- B（失败保证）：先复制 sandbox 验证，五项检查全过才写回原目录，替代“就地修改再回滚”；代价是多一次 build + 一次头文件变化重编译。
代价与覆盖范围：仅支持显式依赖规则与三种 CFLAGS，不支持隐式规则/模式规则/`|` 与 `$` 展开；不做声明图距离与 LLM 提示生成。
验证命令与实际证据：`lab.py:76 patch()`、`lab.py:97 validate()`；证据 work/e8-B-manual.8aBTED/{candidate.patch,expected-failure.json}、work/e9-B-manual.m20x8B/{direct,macro,mixed}.patch、work/e10-B-manual.iKzx5y/{reject-test,accept,reject-patch}/validation.json。
