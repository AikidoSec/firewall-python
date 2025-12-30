include ../common.mk

.PHONY: run
run: install
	@echo "Running sample app django-mysql with Zen on port $(PORT)"
	poetry run python manage.py migrate || true

	$(AIKIDO_ENV_COMMON) \
	poetry run python manage.py runserver 0.0.0.0:$(PORT)

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-mysql without Zen on port $(PORT_DISABLED)"
	poetry run python manage.py migrate || true
	$(AIKIDO_ENV_DISABLED) \
	poetry run python manage.py runserver 0.0.0.0:$(PORT_DISABLED)
