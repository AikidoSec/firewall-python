.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app flask-mssql with Zen on port 8104"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run flask --app app.py run --host=0.0.0.0 --port=8104 --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-mssql without Zen on port 8105"
	AIKIDO_DISABLE=1 \
	poetry run flask --app app.py run --host=0.0.0.0 --port=8105 --no-reload
