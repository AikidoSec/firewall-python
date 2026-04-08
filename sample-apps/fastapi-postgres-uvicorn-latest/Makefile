include ../common.mk

PORT = 8116
PORT_DISABLED = 8117

.PHONY: run
run: install
	@echo "Running sample app fastapi-postgres-uvicorn-latest with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app fastapi-postgres-uvicorn-latest without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT_DISABLED) --workers 4
