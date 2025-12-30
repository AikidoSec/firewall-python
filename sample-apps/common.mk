PORT ?= 8080
APP_NAME ?= $(notdir $(shell pwd))

# Common environment variables for Aikido Zen
AIKIDO_ENV_VARS = \
	AIKIDO_DEBUG=true \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" \
	AIKIDO_DISABLE=0

AIKIDO_ENV_VARS_BENCHMARK = \
	AIKIDO_DEBUG=false \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" \
	AIKIDO_DISABLE=0 \
	DONT_ADD_MIDDLEWARE=1

AIKIDO_DISABLED_VARS = \
	AIKIDO_DISABLE=1

.PHONY: install
install:
	poetry install --quiet

.PHONY: clean
clean:
	rm -rf .venv __pycache__ */__pycache__ */*/__pycache__

run: install
	@echo "Running sample app $(APP_NAME) with Zen on port $(PORT)"
	$(AIKIDO_ENV_VARS) poetry run $(RUN_COMMAND)

runBenchmark: install
	@echo "Running sample app $(APP_NAME) with Zen (benchmark mode) on port $(PORT)"
	$(AIKIDO_ENV_VARS_BENCHMARK) poetry run $(RUN_COMMAND)

# Calculate the disabled port (PORT + 1)
DISABLED_PORT = $(shell expr $(PORT) + 1)

runZenDisabled: install
	@echo "Running sample app $(APP_NAME) without Zen on port $(DISABLED_PORT)"
	$(AIKIDO_DISABLED_VARS) poetry run $(RUN_COMMAND)


