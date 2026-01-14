include ../common.mk

PORT = 8114
PORT_DISABLED = 8115

.PHONY: run
run: install
	@echo "Running sample app django-asgi-uvicorn with Zen on port $(PORT)"
	poetry run python manage.py migrate || true

	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
	$(AIKIDO_ENV_COMMON) \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT) sample-django-asgi-uvicorn-app.asgi:application

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-asgi-uvicorn without Zen on port $(PORT_DISABLED)"
	poetry run python manage.py migrate || true
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES \
	$(AIKIDO_ENV_DISABLED) \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:$(PORT_DISABLED) sample-django-asgi-uvicorn-app.asgi:application
