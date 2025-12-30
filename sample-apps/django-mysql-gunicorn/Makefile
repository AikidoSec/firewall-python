include ../common.mk

# Override default ports for django-mysql-gunicorn
PORT = 8082
PORT_DISABLED = 8083

.PHONY: run
run: install
	@echo "Running sample app django-mysql-gunicorn with Zen on port $(PORT)"
	poetry run python manage.py migrate || true

	$(AIKIDO_ENV_COMMON) \
	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) sample-django-mysql-gunicorn-app.wsgi

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-mysql-gunicorn without Zen on port $(PORT_DISABLED)"
	poetry run python manage.py migrate || true
	$(AIKIDO_ENV_DISABLED) \
	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT_DISABLED) sample-django-mysql-gunicorn-app.wsgi
