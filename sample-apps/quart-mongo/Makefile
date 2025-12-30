include ../common.mk

PORT = 8098
PORT_DISABLED = 8099

.PHONY: run
run: install
	@echo "Running sample app quart-mongo with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	QUART_APP=app:app poetry run quart run --host 0.0.0.0 --port $(PORT)

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app quart-mongo without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	QUART_APP=app:app poetry run quart run --host 0.0.0.0 --port $(PORT_DISABLED)
