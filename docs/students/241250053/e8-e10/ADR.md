# 决策记录：B2 候选生成与失败隔离

## 背景与约束

B2 需要根据固定 MD 报告生成 Makefile 候选，并在 E9 支持 direct、macro、mixed 三种声明风格。报告只能用于它记录的内部提交；候选未通过构建、测试、增量重编译和 MD 重检前，不得污染原项目。课程要求保留共享变量语义、recipe 字节和可审计的拒绝证据。

## 决策

1. 报告中的 `commit` 必须等于受测项目 `HEAD`，否则返回 `STALE_REPORT`，不通过直接修改报告 SHA 绕过。
2. direct 声明在 target 依赖行追加缺失项；纯 macro 声明修改变量定义；mixed 声明在 target 行追加缺失项，并保留已有变量引用。
3. 候选先应用到独立 sandbox，依次执行 Patch 检查、构建、运行测试、头文件变化后的增量构建和 MD 重检；只有全部通过才把 Makefile 字节写回源目录。
4. 任一步失败均不写回源目录，并记录 `accepted=false`、错误/check、`source_unchanged=true`、`rollback=true`。

## 替代方案及拒绝理由

- 对所有风格都展开宏并重写 target：实现简单，但会破坏共享变量与维护者表达，故拒绝。
- 直接在源目录应用 Patch 后失败再反向恢复：异常中断时可能留下半成品，且字节级恢复更难证明，故采用 sandbox 验证。
- 仅以构建成功作为接受条件：无法证明增量语义和 MD 已消除，故增加测试、头文件变化和动态重检。

## 代价与覆盖范围

每个候选需要复制输入并执行完整验证，耗时和磁盘开销高于就地修改；收益是失败隔离、证据完整和判定可复现。当前决策覆盖课程 profile 的显式规则和三种声明风格，不宣称支持任意 GNU Make 语法。

## 验证命令与证据

```text
python3 run_lab.py e8 --track B --out work/241250053/e8-B-01
python3 run_lab.py e9 --track B --out work/241250053/e9-B-01
python3 run_lab.py e10 --track B --out work/241250053/e10-B-01
docker run --rm --network none ... python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v
```

三阶段退出码均为 0；10 项测试通过；E10 `gate.json` 为 `passed=true`，两个拒绝案例均证明源字节保持，接受案例的 BuildChecker 重检无 `MISSING`。
