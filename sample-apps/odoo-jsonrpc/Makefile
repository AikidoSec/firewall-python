include ../common.mk

PORT = 8120
PORT_DISABLED = 8121

.PHONY: run
run: install
	@echo "Running sample app odoo-jsonrpc with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run python app.py $(PORT)

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app odoo-jsonrpc without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run python app.py $(PORT_DISABLED)
