include ../common.mk

# App-specific configuration
PORT = 8088
RUN_COMMAND = uwsgi --ini uwsgi.ini

runBenchmark: install
	@echo "Running sample app flask-mysql-uwsgi with Zen (benchmark mode) on port $(PORT)"
	$(AIKIDO_ENV_VARS_BENCHMARK) poetry run uwsgi --single-interpreter --ini uwsgi.ini

runZenDisabled: install
	@echo "Running sample app flask-mysql-uwsgi without Zen on port 8089"
	$(AIKIDO_DISABLED_VARS) poetry run uwsgi --single-interpreter --ini uwsgi2.ini
