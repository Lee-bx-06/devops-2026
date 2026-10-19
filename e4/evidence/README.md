# E4 A09 原始证据副本

本目录是从小组服务器各成员学号目录复制出来的 `work/<时间>/` 原始证据副本，用于随仓库提交、便于核验。
服务器上的原始路径见 `../GROUP_STATUS.md` 与 `../records/`；`work/` 本身不进 Git，这里是按课件第 20 页“用 git add -f 挑选需要的证据目录”的做法挑选后的副本。

| 学号 | 完整运行证据目录（服务器） | 成功运行时间 | 单测 | 冒烟 | 密钥扫描 |
| --- | --- | --- | --- | --- | --- |
| 241250014 | /root/241250014/buildchecker/e4/work/20261016-130638 | 2026-10-16 13:06-13:11 | 3 passed | passed=true | 未发现问题 |
| 241250033 | /root/241250033/buildchecker/e4/work/20261016-181736 | 2026-10-16 18:17 | 3 passed | passed=true | 未发现问题 |
| 241250048 | /root/241250048/buildchecker/e4/work/20261016-192209 | 2026-10-16 19:22 | 3 passed | passed=true | 未发现问题 |

每人的 `env.json`、`build.log`、`image.json`、`toolchain.lock`、`test.log`、`smoke.json`、`secret-scan.txt` 七份文件来自同一次成功运行；`scan-leak-detected/` 与 `scan-after-cleanup/` 是假 Key 验证的两次扫描输出，不能替代完整运行证据。

## 逐文件 SHA-256

### 殷晓瑞 / 241250014

| 文件 | SHA-256 |
| --- | --- |
| env.json | `9628c7261de1a2afe78c38069f4db0a71ac757cbf3ec576928d74f9d8b5e0f56` |
| build.log | `9d5f0afcad99fd9abcf7b9d69c17a48af537da233366562380dabafd29c8921f` |
| image.json | `374b3dfd15cbcb7d4ebc103904a8be15d61b685395b2b050a3958915a04ad47f` |
| toolchain.lock | `bc70f4e9e436d2567c88588171d7fd4575a614c442874baa089407106bbf9358` |
| test.log | `e0a6ea218ea5d725ce7272da8d68d45a029e489423e03af6960c7bff0f7fe414` |
| smoke.json | `3f33c782ff95e31fa488b120729f9f9a1dc68278c1ec9e61d0fa15a58d46609a` |
| secret-scan.txt | `453d6d058739c4fa4056e83ea4353d04cdaa7b8eb5f9644d93a125516a16258d` |

### 谢浩天 / 241250033

| 文件 | SHA-256 |
| --- | --- |
| env.json | `7c5dfa8c0e07b7c3698eaaf8228cae267a46a34158e5f002677f9cb7720721ab` |
| build.log | `ea888707443d1b69bf95e2c24097cb95742a1e2860fbb65d5ddc5427ac4acc62` |
| image.json | `21feef1b99b4f52f54a32e64682bcdbb2f95b6252c1d1859e3507ad0dad681c1` |
| toolchain.lock | `bc70f4e9e436d2567c88588171d7fd4575a614c442874baa089407106bbf9358` |
| test.log | `e0a6ea218ea5d725ce7272da8d68d45a029e489423e03af6960c7bff0f7fe414` |
| smoke.json | `3f33c782ff95e31fa488b120729f9f9a1dc68278c1ec9e61d0fa15a58d46609a` |
| secret-scan.txt | `e5a3b3c45b244b0ecc3b274fb6930ac0b4cf5117e013e1bdf4b87be89ebb5e2e` |

### 朱鸣涛 / 241250048

| 文件 | SHA-256 |
| --- | --- |
| env.json | `f8d9e72b1366f961c8e0a53a1f18afd8af987d7b90ebfbf856a95b2745ff0190` |
| build.log | `a974ffd87c5eddc60da4db9341efd62132475931994841d92bd452206d29c861` |
| image.json | `2b07400124b0733f89b18688689bce4d46aa80cd51d119b80103c80edafbd558` |
| toolchain.lock | `bc70f4e9e436d2567c88588171d7fd4575a614c442874baa089407106bbf9358` |
| test.log | `e0a6ea218ea5d725ce7272da8d68d45a029e489423e03af6960c7bff0f7fe414` |
| smoke.json | `3f33c782ff95e31fa488b120729f9f9a1dc68278c1ec9e61d0fa15a58d46609a` |
| secret-scan.txt | `f5dedb8c3cf67a931754f2834f1f7a920d50cedf7b0de20a76916fe791142517` |

假 Key 两次扫描：

- 谢浩天 / 241250033：检出 `/root/241250033/buildchecker/e4/work/20261016-181518-leak-detected/secret-scan.txt`，清理后 `/root/241250033/buildchecker/e4/work/20261016-181518-after-cleanup/secret-scan.txt`。
- 朱鸣涛 / 241250048：检出 `/root/241250048/buildchecker/e4/work/20261016-192618/secret-scan.txt`，清理后 `/root/241250048/buildchecker/e4/work/20261016-192628/secret-scan.txt`。
