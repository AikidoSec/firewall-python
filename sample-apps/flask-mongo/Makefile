.PHONY: clean
clean:
	@poetry env remove $(shell poetry env list | grep 'Activated' | awk '{print $$1}')

.PHONY: install
install: clean
	poetry install

.PHONY: run
run: install
	@echo "Running sample app flask-mongo with Zen on port 8094"
	AIKIDO_DEBUG=true AIKIDO_BLOCKING=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run ddtrace-run flask --app app.py run --host=0.0.0.0 --port=8094 --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-mongo without Zen on port 8095"
	AIKIDO_DISABLE=1 \
	poetry run flask --app app.py run --host=0.0.0.0 --port=8095 --no-reload
