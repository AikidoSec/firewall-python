include ../common.mk

# App-specific configuration
PORT = 8104
RUN_COMMAND = flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

runZenDisabled: install
	@echo "Running sample app flask-mssql without Zen on port $(DISABLED_PORT)"
	$(AIKIDO_DISABLED_VARS) poetry run flask --app app.py run --host=0.0.0.0 --port=$(DISABLED_PORT) --no-reload
