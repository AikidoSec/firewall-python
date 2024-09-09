.PHONY: install
install:
	pip install -r requirements.txt
	pip install poetry
	rm -rf ../../dist

	cd ../../ && $(MAKE) build
	mv ../../dist/aikido_zen-*.tar.gz ../../dist/aikido_zen.tar.gz
	pip install ../../dist/aikido_zen.tar.gz

.PHONY: run_unsafe
run_unsafe:
	python-lambda-local init.py payloads/nosql-injection-request.json

.PHONY: run_safe
run_safe:
	python-lambda-local init.py payloads/safe-request.json
