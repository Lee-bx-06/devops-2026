# A 组 E5E7 教学参考服务

来源：`DevOps_E4_E7_GitHub_20261028.zip` 中的 `07_实验包/E5E7/A-buildchecker/`。包含参考实现及其 15 项服务测试；个人贡献及实际运行结果见上层 E5 报告。

在 Linux 服务器自己的仓库内执行：

```bash
cd e5/reference-a
python3 scripts/course.py doctor
python3 scripts/course.py build --out work/build-01 --build-timeout 1200
python3 scripts/course.py e5 --out work/e5-01
```

入口按当前仓库的 Git 学号使用 `course1027-buildchecker:学号` 镜像标签。每次重跑使用新的输出目录。修改服务或测试后，先重新构建镜像。全部命令的原始输出保存在 `work/`。

导入时还复制了随包的 `tools/course.py`、`ci/` 和 `templates/`，布局与课程升级工具一致。因为本组仓库同时保存 E2/E3/E4，参考服务放在独立子目录；Docker 构建上下文和脚本工作目录均为本目录。

本组服务器为 2 CPU、2 GiB，实际可见内存约 1.7 GiB。`scripts/doctor.py` 沿用 E4 的 1.5 GiB 最低可见内存；通用模板原值为 4 GiB。其余资源检查和实际输出保留。

`.github/workflows/e7-quality-gate.yml` 在本子目录中作为原始模板保存。E7 阶段将它接入仓库根目录并配置本目录的工作路径，再完成远程验证。
