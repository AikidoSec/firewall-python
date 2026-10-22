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
test: build
	poetry run pytest aikido_zen/
.PHONY: end2end
end2end:
	poetry run pytest end2end/
.PHONY: e2e
e2e:
	@if [ -z "$(app)" ]; then echo "Usage: make e2e app=<app-name>  (e.g. make e2e app=flask-postgres)"; exit 1; fi
	./end2end/e2e.sh $(app)
.PHONY: cov
cov: build
	poetry run pytest aikido_zen/ --cov=aikido_zen --cov-report=xml --cov-report=lcov:lcov.info
.PHONY: benchmark
benchmark:
	k6 run -q ./benchmarks/flask-mysql-benchmarks.js


# Binaries cache :
BASE_URL = https://github.com/AikidoSec/zen-internals/releases/download/v0.1.74
FILES = \
    libzen_internals_aarch64-apple-darwin.dylib \
    libzen_internals_aarch64-apple-darwin.dylib.sha256sum \
    libzen_internals_aarch64-pc-windows-msvc.dll \
    libzen_internals_aarch64-pc-windows-msvc.dll.sha256sum \
    libzen_internals_aarch64-unknown-linux-gnu.so \
    libzen_internals_aarch64-unknown-linux-gnu.so.sha256sum \
    libzen_internals_aarch64-unknown-linux-musl.so \
    libzen_internals_aarch64-unknown-linux-musl.so.sha256sum \
    libzen_internals_x86_64-apple-darwin.dylib \
    libzen_internals_x86_64-apple-darwin.dylib.sha256sum \
    libzen_internals_x86_64-pc-windows-gnu.dll \
    libzen_internals_x86_64-pc-windows-gnu.dll.sha256sum \
    libzen_internals_x86_64-unknown-linux-gnu.so \
    libzen_internals_x86_64-unknown-linux-gnu.so.sha256sum \
    libzen_internals_x86_64-unknown-linux-musl.so \
    libzen_internals_x86_64-unknown-linux-musl.so.sha256sum

binaries: binaries_make_dir $(addprefix .cache/binaries/, $(FILES))
	echo "$(BASE_URL)" > $(CACHE_DIR)/.version
binaries_make_dir:
	rm -rf .cache/binaries
	mkdir -p .cache/binaries/
.cache/binaries/%:
	@echo "Downloading $*..."
	curl -L -o $@ $(BASE_URL)/$*

# Binaries from another release may not match the Python bindings, so download them again.
.PHONY: check_binaries
check_binaries:
	@if [ "$$(cat $(CACHE_DIR)/.version 2>/dev/null)" = "$(BASE_URL)" ]; then \
  		echo "Directory $(CACHE_DIR) has the binaries from $(BASE_URL)."; \
	else \
		echo "Directory $(CACHE_DIR) is missing or outdated. Running 'make binaries'..."; \
		$(MAKE) binaries; \
	fi


# Replace version number automatically on publish :
replace_version:
	@if [ -z "$(version)" ]; then \
		echo "Error: No version specified. Use 'make replace_version version=<new_version>'."; \
		exit 1; \
	fi;

	poetry version $(version)
	sed -i.bak "s/1.0-REPLACE-VERSION/$$version/g" aikido_zen/config.py
	rm aikido_zen/config.py.bak



relock_sample_apps:
	@for f in sample-apps/**/; do \
  		echo "Entering $$f"; \
  		cd $$f && poetry lock; \
  		cd ../../; \
  	done

