# AI使用记录

工具/模型/日期：DeepSeek Harness 编码助手（deepseek 系列模型），2026-11-18。
输入上下文与问题：提供 E8—E10 材料包、手册与服务器终端记录，请其梳理 B 组执行顺序、核对每步判定、生成报告/ADR/证据清单结构。
模型建议：逐步执行清单（`lab_ready`→`lab_new_run`→`lab_python`）、报告字段（固定 MD 来源、声明风格、拒绝证据、两个 SHA 分开写）、证据包打包命令。
采纳/拒绝及理由：采纳“一实验一 OUT”“只认 STEP_EXIT_CODE=0”“拒绝场景也是 0”等流程建议；未采纳“代写实验结论/代填数值”，所有数值均来自本人终端实际输出。
人工修改：报告的姓名/校区/实验叙述、三个测试类的输入变化与预期、PR 与 CI 链接均由本人填写核对。
实际验证命令/输入/结果：`python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v` → Ran 10 tests, OK, 退出码 0；`lab_ready` → 仓库/学号/镜像三行。
