.PHONY: clean
clean:
	@poetry env remove $(shell poetry env list | grep 'Activated' | awk '{print $$1}')

.PHONY: install
install:
	poetry install --quiet

.PHONY: run
run: install
	@echo "Running sample app django-postgres-gunicorn with Zen on port 8100"
	poetry run python manage.py migrate || true

	AIKIDO_DEBUG=true AIKIDO_BLOCKING=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \

	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8100 sample-django-postgres-gunicorn-app.wsgi

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-postgres-gunicorn without Zen on port 8101"
	poetry run python manage.py migrate || true
	AIKIDO_DISABLE=1 \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8101 sample-django-postgres-gunicorn-app.wsgi
