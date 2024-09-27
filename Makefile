build: internals_lib_install _build
_build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python

.PHONY: lint
lint:
	poetry run black aikido_zen/
	poetry run pylint aikido_zen/

install: internals_lib_install _install
_install:
	pip install poetry
	poetry install

dev_install: install _dev_install
_dev_install:
	poetry install --with=dev


.PHONY: test
test:
	poetry run pytest aikido_zen/

.PHONY: end2end
end2end:
	poetry run pytest end2end/ 	

.PHONY: cov
cov:
	poetry run pytest aikido_zen/ --cov=aikido_zen --cov-report=xml

.PHONY: benchmark
benchmark:
	k6 run -q ./benchmarks/flask-mysql-benchmarks.js

.PHONY: internals_lib_install
internals_lib_install:
	mkdir -p ./libzen_internals/
	curl -L -o ./libzen_internals/lib.so https://github.com/AikidoSec/zen-internals/releases/download/v0.1.1/libzen_internals.so
