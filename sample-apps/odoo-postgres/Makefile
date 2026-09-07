ROOT_DIR := ../..
COMPOSE := docker compose

.PHONY: build build-wheel up run runZenDisabled smoke logs down clean

build-wheel:
	$(MAKE) -C $(ROOT_DIR) build

build: build-wheel
	$(COMPOSE) build

up: build
	$(COMPOSE) up --detach --wait odoo odoo-disabled

run: build
	$(COMPOSE) up odoo

runZenDisabled: build
	$(COMPOSE) up odoo-disabled

smoke: build
	./scripts/smoke-test.sh

logs:
	$(COMPOSE) logs --follow odoo odoo-disabled

down:
	$(COMPOSE) down --volumes --remove-orphans

clean: down
