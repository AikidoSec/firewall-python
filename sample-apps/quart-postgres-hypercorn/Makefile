include ../common.mk

PORT = 8096
PORT_DISABLED = 8097

.PHONY: run
run: install
	@echo "Running sample app quart-postgres-uvicorn with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run hypercorn app:app -b 0.0.0.0:$(PORT) --workers 2

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app quart-postgres-uvicorn without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run hypercorn app:app -b 0.0.0.0:$(PORT_DISABLED) --workers 2
