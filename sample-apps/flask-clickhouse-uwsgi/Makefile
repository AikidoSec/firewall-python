include ../common.mk

# App-specific configuration
PORT = 8106
RUN_COMMAND = uwsgi --ini uwsgi.ini

runZenDisabled: install
	@echo "Running sample app flask-clickhouse-uwsgi without Zen on port 8107"
	$(AIKIDO_DISABLED_VARS) poetry run uwsgi --ini uwsgi2.ini
