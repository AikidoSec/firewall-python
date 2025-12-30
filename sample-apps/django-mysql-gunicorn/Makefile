include ../common.mk

# App-specific configuration
PORT = 8082
RUN_COMMAND = python manage.py migrate || true; ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) sample-django-mysql-gunicorn-app.wsgi

run: install
	@echo "Running sample app django-mysql-gunicorn with Zen on port $(PORT)"
	$(AIKIDO_ENV_VARS) poetry run $(RUN_COMMAND)

runZenDisabled: install
	@echo "Running sample app django-mysql-gunicorn without Zen on port 8083"
	$(AIKIDO_DISABLED_VARS) poetry run python manage.py migrate || true; ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8083 sample-django-mysql-gunicorn-app.wsgi
