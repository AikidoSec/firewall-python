include ../common.mk

PORT = 8108
PORT_DISABLED = 8109

.PHONY: run
run: install
	@echo "Running sample app flask-openai with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-openai without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT_DISABLED) --no-reload

