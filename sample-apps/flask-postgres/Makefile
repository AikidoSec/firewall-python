include ../common.mk

# Override default ports for flask-postgres
PORT = 8090
PORT_DISABLED = 8091

.PHONY: run
run: install
	@echo "Running sample app flask-postgres with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-postgres without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT_DISABLED) --no-reload
