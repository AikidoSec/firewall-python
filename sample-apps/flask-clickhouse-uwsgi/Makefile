.PHONY: install
install:
	poetry install --quiet

.PHONY: run
run: install
	@echo "Running sample app flask-clickhouse-uwsgi with Zen on port 8106"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run uwsgi --ini uwsgi.ini

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-clickhouse-uwsgi without Zen on port 8107"
	AIKIDO_DISABLE=1 \
	poetry run uwsgi --ini uwsgi2.ini
