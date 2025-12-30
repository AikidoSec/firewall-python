include ../common.mk

# App-specific configuration
PORT = 8080
RUN_COMMAND = python manage.py migrate || true; python manage.py runserver 0.0.0.0:$(PORT)

run: install
	@echo "Running sample app django-mysql with Zen on port $(PORT)"
	$(AIKIDO_ENV_VARS) poetry run $(RUN_COMMAND)

runZenDisabled: install
	@echo "Running sample app django-mysql without Zen on port $(PORT)"
	$(AIKIDO_DISABLED_VARS) poetry run $(RUN_COMMAND)
