.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app flask-postgres-gevent with Zen on port 8110"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8110 app:app

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-postgres-gevent without Zen on port 8111"
	AIKIDO_DISABLE=1 \
	poetry run gunicorn -c gunicorn_config.py --log-level debug --access-logfile '-' --error-logfile '-' --bind 0.0.0.0:8111 app:app
