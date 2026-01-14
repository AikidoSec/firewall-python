include ../common.mk

PORT = 8100
PORT_DISABLED = 8101

.PHONY: run
run: install
	@echo "Running sample app django-postgres-gunicorn with Zen on port $(PORT)"
	poetry run python manage.py migrate || true

	$(AIKIDO_ENV_COMMON) \
	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) sample-django-postgres-gunicorn-app.wsgi

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-postgres-gunicorn without Zen on port $(PORT_DISABLED)"
	poetry run python manage.py migrate || true
	$(AIKIDO_ENV_DISABLED) \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT_DISABLED) sample-django-postgres-gunicorn-app.wsgi
