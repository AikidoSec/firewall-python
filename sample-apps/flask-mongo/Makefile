include ../common.mk

# App-specific configuration
PORT = 8094
RUN_COMMAND = ddtrace-run flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

runZenDisabled: install
	@echo "Running sample app flask-mongo without Zen on port 8095"
	$(AIKIDO_DISABLED_VARS) poetry run flask --app app.py run --host=0.0.0.0 --port=8095 --no-reload
