include ../common.mk

PORT = 8088
PORT_DISABLED = 8089

.PHONY: run
run: install
	@echo "Running sample app flask-mysql-uwsgi with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) AIKIDO_DISABLE=0 \
	poetry run uwsgi --ini uwsgi.ini

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app flask-mysql-uwsgi with Zen on port $(PORT)"
	$(AIKIDO_ENV_BENCHMARK) AIKIDO_DISABLE=0 \
	poetry run uwsgi --single-interpreter --ini uwsgi.ini

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-mysql-uwsgi without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run uwsgi --single-interpreter --ini uwsgi2.ini
