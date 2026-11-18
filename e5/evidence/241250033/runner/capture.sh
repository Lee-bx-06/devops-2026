set -eu
cp -R /input/. /evidence/
cd /evidence
cat /opt/toolchain.lock > toolchain.lock
sha256sum Makefile main.c config.h unused.h > input-sha256.txt
make clean > clean.log 2>&1
mkdir trace
strace -ff -s 4096 -o trace/t -e trace=%file,%process make -p app > make-db.txt 2> build-stderr.log
./app > program-output.txt
cat program-output.txt
