include ../common.mk

PORT = 8086
PORT_DISABLED = 8087

.PHONY: run
run: install
	@echo "Running sample app flask-mysql with Zen on port $(PORT)"
	$(AIKIDO_ENV_COMMON) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

.PHONY: runBenchmark
runBenchmark: install
	@echo "Running sample app flask-mysql with Zen (benchmark mode) on port $(PORT)"
	$(AIKIDO_ENV_BENCHMARK) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT) --no-reload

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app flask-mysql without Zen on port $(PORT_DISABLED)"
	$(AIKIDO_ENV_DISABLED) \
	poetry run flask --app app.py run --host=0.0.0.0 --port=$(PORT_DISABLED) --no-reload
