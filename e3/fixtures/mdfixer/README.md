# MDFixer 固定输入与验证

本目录为 E3 阶段 B3 的 MDFixer 测试基线。所有验证在 Windows + Git Bash 下执行。

## 快速开始

1. 将当前目录复制到临时工作区：
    ```bash
    cp -r . /tmp/mdfixer-test
    cd /tmp/mdfixer-test
    ```

2. 验证修复前结果：
    ```bash
    make && ./app
    ```

3. 四种风格正确补丁依次验证：
    ```bash
    ./verify_patch.sh target.patch
    ./verify_patch.sh macro.patch
    ./verify_patch.sh hybrid.patch
    ./verify_patch.sh implicit.patch
    ```

4. 验证无效补丁候选：
    ```bash
    cp Makefile.before Makefile
    patch -p0 -o Makefile < broken.patch
    make # 应非零退出
    cp Makefile.before Makefile
    make clean && make && ./app   # 应再次成功
    ```