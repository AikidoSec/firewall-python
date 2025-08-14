.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app flask-mysql-gunicorn with Zen on port 8110"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --bind 0.0.0.0:8110 app:app

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app flask-mysql-gunicorn with Zen (benchmark mode) on port 8110"
	AIKIDO_DEBUG=false AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	DONT_ADD_MIDDLEWARE=1 \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --bind 0.0.0.0:8110 app:app

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-mysql-gunicorn without Zen on port 8111"
	AIKIDO_DISABLE=1 \
	poetry run gunicorn -c gunicorn_config.py --workers 4 --threads 2 --bind 0.0.0.0:8111 app:app
