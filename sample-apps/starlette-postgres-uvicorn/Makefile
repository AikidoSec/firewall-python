include ../common.mk

# App-specific configuration
PORT = 8102
RUN_COMMAND = uvicorn app:app --host 0.0.0.0 --port=$(PORT) --workers 4

runZenDisabled: install
	@echo "Running sample app starlette-postgres-uvicorn without Zen on port $(DISABLED_PORT)"
	$(AIKIDO_DISABLED_VARS) poetry run uvicorn app:app --host 0.0.0.0 --port=$(DISABLED_PORT) --workers 4
