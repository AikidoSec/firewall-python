include ../common.mk

# App-specific configuration
PORT = 8100
RUN_COMMAND = python manage.py migrate || true; ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) sample-django-postgres-gunicorn-app.wsgi

run: install
	@echo "Running sample app django-postgres-gunicorn with Zen on port $(PORT)"
	$(AIKIDO_ENV_VARS) poetry run $(RUN_COMMAND)

runZenDisabled: install
	@echo "Running sample app django-postgres-gunicorn without Zen on port 8101"
	$(AIKIDO_DISABLED_VARS) poetry run python manage.py migrate || true; gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8101 sample-django-postgres-gunicorn-app.wsgi
