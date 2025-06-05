.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app flask-postgres-xml with Zen on port 8092"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run flask --app app.py run --host=0.0.0.0 --port=8092 --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-postgres-xml without Zen on port 8093"
	AIKIDO_DISABLE=1 \
	poetry run flask --app app.py run --host=0.0.0.0 --port=8093 --no-reload
