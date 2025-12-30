include ../common.mk

# App-specific configuration
.ONESHELL:
PORT = 8098
RUN_COMMAND = QUART_APP=app:app quart run --host 0.0.0.0 --port=$(PORT)

runZenDisabled: install
	@echo "Running sample app quart-mongo without Zen on port $(DISABLED_PORT)"
	$(AIKIDO_DISABLED_VARS) QUART_APP=app:app poetry run quart run --host 0.0.0.0 --port=$(DISABLED_PORT)
