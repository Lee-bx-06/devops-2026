.PHONY: check validate test clean help

help:
	@echo "make check     校验全部样例并运行单元测试（零第三方依赖）"
	@echo "make validate  只运行 tools/validate.py"
	@echo "make test      只运行 tests/"
	@echo "make clean     清理 __pycache__"

check: validate test

validate:
	python3 tools/validate.py

test:
	python3 -m unittest discover -s tests -v

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
