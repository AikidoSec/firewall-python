CACHE_DIR := .cache/binaries
BUILD_DIR := dist/

# Build/clean/lint/install :
.PHONY: build
build: check_binaries
	@echo "Building using poetry, creates $(BUILD_DIR) folder."
	@echo "Copying binaries from $(CACHE_DIR) folder : "
	cp -r .cache/binaries/* aikido_zen/libs
	poetry build
.PHONY: clean
clean:
	@echo "Cleaning up: Removing build and cache directories, remove poetry env"
	rm -rf $(BUILD_DIR)
	rm -rf $(CACHE_DIR)
	@poetry env remove $(shell poetry env list | grep 'Activated' | awk '{print $$1}')
.PHONY: lint
lint:
	poetry run black aikido_zen/
	poetry run pylint aikido_zen/
install: check_binaries
	pip install poetry
	poetry install
.PHONY: dev_install
dev_install: install
	poetry install --with=dev


# Testing/Benchmarks :
.PHONY: test
test:
	poetry run pytest aikido_zen/
.PHONY: end2end
end2end:
	poetry run pytest end2end/
.PHONY: cov
cov:
	poetry run pytest aikido_zen/ --cov=aikido_zen --cov-report=xml
.PHONY: benchmark
benchmark:
	k6 run -q ./benchmarks/flask-mysql-benchmarks.js

# Mock server :
mock_init: mock_stop
	cd end2end/server && docker build -t mock_core .
	docker run --name mock_core -d -p 5000:5000 mock_core
mock_restart:
	docker restart mock_core
mock_stop:
	if [ "$(docker ps -aq -f name=mock_core)" ]; then
		# Kill and remove the container
		docker kill mock_core
		docker rm mock_core
	else
		echo "Container 'mock_core' does not exist."
	fi


# Binaries cache :
BASE_URL = https://github.com/AikidoSec/zen-internals/releases/download/v0.1.35
FILES = \
    libzen_internals_aarch64-apple-darwin.dylib \
    libzen_internals_aarch64-apple-darwin.dylib.sha256sum \
    libzen_internals_aarch64-unknown-linux-gnu.so \
    libzen_internals_aarch64-unknown-linux-gnu.so.sha256sum \
    libzen_internals_x86_64-apple-darwin.dylib \
    libzen_internals_x86_64-apple-darwin.dylib.sha256sum \
    libzen_internals_x86_64-pc-windows-gnu.dll \
    libzen_internals_x86_64-pc-windows-gnu.dll.sha256sum \
    libzen_internals_x86_64-unknown-linux-gnu.so \
    libzen_internals_x86_64-unknown-linux-gnu.so.sha256sum

binaries: binaries_make_dir $(addprefix .cache/binaries/, $(FILES))
binaries_make_dir:
	rm -rf .cache/binaries
	mkdir -p .cache/binaries/
.cache/binaries/%:
	@echo "Downloading $*..."
	curl -L -o $@ $(BASE_URL)/$*

.PHONY: check_binaries
check_binaries:
	@if [ -d "$(CACHE_DIR)" ]; then \
  		echo "Directory $(CACHE_DIR) exists."; \
	else \
		echo "Directory $(CACHE_DIR) is empty. Running 'make binaries'..."; \
		$(MAKE) binaries; \
	fi
