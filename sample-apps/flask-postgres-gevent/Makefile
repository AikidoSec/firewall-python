include ../common.mk

# App-specific configuration
PORT = 8110
RUN_COMMAND = gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) app:app

runZenDisabled: install
	@echo "Running sample app flask-postgres-gevent without Zen on port $(DISABLED_PORT)"
	$(AIKIDO_DISABLED_VARS) poetry run gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(DISABLED_PORT) app:app
