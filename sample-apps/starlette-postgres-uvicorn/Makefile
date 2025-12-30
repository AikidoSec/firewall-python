include ../common.mk

# Override default ports for starlette-postgres-uvicorn
PORT = 8102
PORT_DISABLED = 8103

.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app starlette-postgres-uvicorn with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) AIKIDO_DISABLE=0 \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app starlette-postgres-uvicorn with Zen (benchmark mode) on port $(PORT)"
	$(AIKIDO_ENV_BENCHMARK) AIKIDO_DISABLE=0 \
	DONT_ADD_MIDDLEWARE=1 \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app starlette-postgres-uvicorn without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT_DISABLED) --workers 4
