# Odoo runs in Docker, so this app does not use ../common.mk.
.PHONY: build up run runZenDisabled down

build:
	$(MAKE) -C ../.. build
	docker compose build

up: build
	docker compose up --detach --wait odoo odoo-disabled

run: build
	docker compose up odoo

runZenDisabled: build
	docker compose up odoo-disabled

down:
	docker compose down --volumes --remove-orphans
