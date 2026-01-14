include ../common.mk

PORT = 8102
PORT_DISABLED = 8103

.PHONY: run
run: install
	@echo "Running sample app starlette-postgres-uvicorn with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app starlette-postgres-uvicorn with Zen (benchmark mode) on port $(PORT)"
	$(AIKIDO_ENV_BENCHMARK) poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app starlette-postgres-uvicorn without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT_DISABLED) --workers 4
