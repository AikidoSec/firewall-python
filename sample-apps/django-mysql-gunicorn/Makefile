.PHONY: clean
clean:
	@poetry env remove $(shell poetry env list | grep 'Activated' | awk '{print $$1}')

.PHONY: install
install: clean
	poetry install --quiet

.PHONY: run
run: install
	@echo "Running sample app django-mysql-gunicorn with Zen on port 8082"
	poetry run python manage.py migrate

	AIKIDO_DEBUG=true AIKIDO_BLOCKING=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8082 sample-django-mysql-gunicorn-app.wsgi

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-mysql-gunicorn without Zen on port 8083"
	poetry run python manage.py migrate
	AIKIDO_DISABLE=1 \
	poetry run ddtrace-run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8083 sample-django-mysql-gunicorn-app.wsgi
