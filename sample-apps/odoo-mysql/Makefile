PORT = 8114
PORT_DISABLED = 8115

.PHONY: build
build:
	@echo "Building Odoo Docker image..."
	docker-compose build

.PHONY: run
run: build
	@echo "Running Odoo with Aikido on port $(PORT)"
	docker-compose up odoo

.PHONY: runZenDisabled
runZenDisabled: build
	@echo "Running Odoo without Aikido on port $(PORT_DISABLED)"
	docker-compose --profile disabled up odoo_disabled

.PHONY: up
up: build
	@echo "Starting all services in detached mode..."
	docker-compose up -d

.PHONY: down
down:
	@echo "Stopping all services..."
	docker-compose down

.PHONY: logs
logs:
	@echo "Showing logs..."
	docker-compose logs -f odoo

.PHONY: clean
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v

.PHONY: restart
restart: down up

.PHONY: shell
shell:
	@echo "Opening shell in Odoo container..."
	docker-compose exec odoo /bin/bash

.PHONY: install
install:
	@echo "Installation handled via Docker - run 'make build' to build the image"

.PHONY: health-check
health-check:
	@echo "Checking Odoo health on port $(PORT)..."
	@curl -f http://localhost:$(PORT) > /dev/null 2>&1 && echo "Port $(PORT): OK" || echo "Port $(PORT): FAILED"
	@echo "Checking Odoo health on port $(PORT_DISABLED) (if running)..."
	@curl -f http://localhost:$(PORT_DISABLED) > /dev/null 2>&1 && echo "Port $(PORT_DISABLED): OK" || echo "Port $(PORT_DISABLED): Not running or FAILED"
