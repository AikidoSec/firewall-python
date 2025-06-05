.PHONY: install
install:
	poetry install

.PHONY: run
run: install
	@echo "Running sample app quart-mongo with Zen on port 8098"
	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	QUART_APP=app:app poetry run quart run --host 0.0.0.0 --port 8098

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app quart-mongo without Zen on port 8099"
	AIKIDO_DISABLE=1 \
	QUART_APP=app:app poetry run quart run --host 0.0.0.0 --port 8099
