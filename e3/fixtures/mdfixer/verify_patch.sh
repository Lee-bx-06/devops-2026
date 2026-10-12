#!/usr/bin/env bash
set -euo pipefail

PATCH=$1
WORKDIR=$(mktemp -d)
cp -r . "$WORKDIR"
cd "$WORKDIR"

# 重置为原始 Makefile
cp Makefile.before Makefile

# 重写补丁头，让 patch 只针对 Makefile
sed 's|^--- .*|--- Makefile|; s|^+++ .*|+++ Makefile|' "$PATCH" > "$WORKDIR/apply.patch"
patch -p0 < "$WORKDIR/apply.patch"

# 确保 config.h 初始为 VALUE 1
cat > config.h <<'EOF'
#define VALUE 1
EOF

make clean
sleep 1
make
OUTPUT=$(./app)
echo "修复前输出: $OUTPUT"
if [ "$OUTPUT" != "1" ]; then
  echo "错误：初始输出应为 1"
  exit 1
fi

# 修改 config.h 为 VALUE 3，确保时间戳严格新于 main.o
sleep 1
cat > config.h <<'EOF'
#define VALUE 3
EOF

make
OUTPUT=$(./app)
echo "修改头文件后输出: $OUTPUT"
if [ "$OUTPUT" != "3" ]; then
  echo "错误：修复后应输出 3，实际为 $OUTPUT"
  exit 1
fi

echo "补丁验证通过"