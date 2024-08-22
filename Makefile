.PHONY: build
build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python

.PHONY: lint
lint:
	poetry run black aikido_firewall/
	poetry run pylint aikido_firewall/

.PHONY: install
install:
	pip install poetry
	poetry install

.PHONY: test
test:
	poetry run pytest aikido_firewall/

.PHONY: end2end
end2end:
	poetry run pytest end2end/ 	

.PHONY: cov
cov:
	poetry run pytest aikido_firewall/ --cov=aikido_firewall --cov-report=xml
