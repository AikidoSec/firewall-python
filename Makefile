.PHONY: build
build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python

.PHONY: lint
lint:
	poetry run black aikido_zen/
	poetry run pylint aikido_zen/

.PHONY: install
install:
	pip install poetry
	poetry install

.PHONY: dev_install
dev_install:
	pip install poetry
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
