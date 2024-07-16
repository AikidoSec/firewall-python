.PHONY: build
build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python

.PHONY: lint
lint:
	poetry run pylint aikido_firewall/
