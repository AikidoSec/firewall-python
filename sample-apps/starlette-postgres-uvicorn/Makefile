.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app django-mysql with Zen on port 8102"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run uvicorn app:app --host 0.0.0.0 --port 8102 --workers 4

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app django-mysql with Zen (benchmark mode) on port 8102"
	AIKIDO_DEBUG=false AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	DONT_ADD_MIDDLEWARE=1 \
	poetry run uvicorn app:app --host 0.0.0.0 --port 8102 --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app starlette-postgres-uvicorn without Zen on port 8103"
	AIKIDO_DISABLE=1 \
	poetry run uvicorn app:app --host 0.0.0.0 --port 8103 --workers 4
