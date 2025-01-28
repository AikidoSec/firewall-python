.PHONY: clean
clean:
	@poetry env remove $(shell poetry env list | grep 'Activated' | awk '{print $$1}')

.PHONY: install
install:
	poetry install --quiet

.PHONY: run
run: install
	@echo "Running sample app django-mysql with Zen on port 8080"
	poetry run python manage.py migrate || true

	AIKIDO_DEBUG=true AIKIDO_BLOCK=true AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" AIKIDO_DISABLE=0 \
	poetry run python manage.py runserver 0.0.0.0:8080

.PHONY: runZenDisabled
runZenDisabled: install
	@echo "Running sample app django-mysql without Zen on port 8081"
	poetry run python manage.py migrate || true
	AIKIDO_DISABLE=1 \
	poetry run python manage.py runserver 0.0.0.0:8081
