include ../common.mk

PORT = 8118
PORT_DISABLED = 8119

.PHONY: run
run: install
	@echo "Running sample app fastapi-postgres-uvicorn-old with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT) --workers 4

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app fastapi-postgres-uvicorn-old without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run uvicorn app:app --host 0.0.0.0 --port $(PORT_DISABLED) --workers 4
