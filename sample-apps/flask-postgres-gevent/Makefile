include ../common.mk

PORT = 8110
PORT_DISABLED = 8111

.PHONY: run
run: install
	@echo "Running sample app flask-postgres-gevent with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) app:app

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-postgres-gevent without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT_DISABLED) app:app
