include ../common.mk

PORT = 8106
PORT_DISABLED = 8107

.PHONY: run
run: install
	@echo "Running sample app flask-clickhouse-uwsgi with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run uwsgi --ini uwsgi.ini

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-clickhouse-uwsgi without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run uwsgi --ini uwsgi2.ini
