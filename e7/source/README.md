# E7 A 运行源码快照

谢浩天 241250033，A09。对应独立实验仓库实际通过运行的 `d2cbe210b2a90c34ebd10c360846314321d17d04`。检测器和 gate 沿用课程参考实现，个人新增测试与环境适配见上级目录 CONTRIBUTIONS.md。

在本组 DevOps 云服务器进入本目录后运行：

```bash
python3 scripts/lab_cloud.py doctor
python3 -m unittest discover -s tests/e7 -v
python3 scripts/lab_cloud.py build --image e7-buildchecker:241250033 --out work/build-repeat --build-timeout 1200
python3 scripts/lab_cloud.py gate --image e7-buildchecker:241250033 --out work/gate-repeat
```

独立仓库根目录的 `.github/workflows/e7-quality-gate.yml` 已由同机 self-hosted runner 完成 CI 验证；本快照放在小组仓库子目录供提交与复跑使用。
