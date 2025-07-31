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
.PHONY: cov
cov: build
	poetry run pytest aikido_zen/ --cov=aikido_zen --cov-report=xml
.PHONY: benchmark
benchmark:
	k6 run -q ./benchmarks/flask-mysql-benchmarks.js


# Binaries cache :
BASE_URL = https://github.com/AikidoSec/zen-internals/releases/download/v0.1.43
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


# Replace version number automatically on publish :
VERSION_FILES = ./build.gradle ./agent_api/src/main/java/dev/aikido/agent_api/Config.java
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

