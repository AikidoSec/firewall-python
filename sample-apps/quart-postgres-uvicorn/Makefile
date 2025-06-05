.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app quart-postgres-uvicorn with Zen on port 8096"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run uvicorn app:app --host 0.0.0.0 --port 8096 --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app quart-postgres-uvicorn without Zen on port 8097"
	AIKIDO_DISABLE=1 \
	poetry run uvicorn app:app --host 0.0.0.0 --port 8097 --workers 4
