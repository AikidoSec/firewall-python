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
BASE_URL = https://github.com/AikidoSec/zen-internals/releases/download/v0.1.60
BINARY_FILES = \
    libzen_internals_aarch64-apple-darwin.dylib \
    libzen_internals_aarch64-unknown-linux-gnu.so \
    libzen_internals_x86_64-apple-darwin.dylib \
    libzen_internals_x86_64-pc-windows-gnu.dll \
    libzen_internals_x86_64-unknown-linux-gnu.so

DIGEST_FILE = binary_digests.txt

binaries: binaries_make_dir $(addprefix .cache/binaries/, $(BINARY_FILES)) verify_binaries
binaries_make_dir:
	rm -rf .cache/binaries
	mkdir -p .cache/binaries/
.cache/binaries/%:
	@echo "Downloading $*..."
	curl -L -o $@ $(BASE_URL)/$*

.PHONY: verify_binaries
verify_binaries:
	@echo "Verifying binary integrity against trusted digests..."
	@if [ ! -f "$(DIGEST_FILE)" ]; then \
		echo "ERROR: Trusted digest file $(DIGEST_FILE) not found."; \
		echo "Cannot verify binary integrity. Build aborted."; \
		exit 1; \
	fi
	@if grep -q "PLACEHOLDER_DIGEST_MUST_BE_REPLACED_BEFORE_BUILD" "$(DIGEST_FILE)"; then \
		echo "ERROR: $(DIGEST_FILE) contains placeholder digests."; \
		echo ""; \
		echo "To initialize trusted digests, choose one of:"; \
		echo ""; \
		echo "Option 1 (Recommended): Download and compute digests independently"; \
		echo "  python3 scripts/compute_binary_digests.py"; \
		echo ""; \
		echo "Option 2: Initialize from upstream .sha256sum files (faster, less secure)"; \
		echo "  python3 scripts/init_digests_from_upstream.py"; \
		echo ""; \
		echo "After initialization:"; \
		echo "  1. Review the computed digests in $(DIGEST_FILE)"; \
		echo "  2. Verify binaries are from a trusted source"; \
		echo "  3. Commit the changes with a clear audit trail"; \
		echo ""; \
		echo "Build aborted for security reasons."; \
		exit 1; \
	fi
	@cd .cache/binaries && \
	for binary in $(BINARY_FILES); do \
		if [ ! -f "$$binary" ]; then \
			echo "ERROR: Binary $$binary not found in cache."; \
			exit 1; \
		fi; \
		expected_digest=$$(grep "$$binary$$" ../../$(DIGEST_FILE) | awk '{print $$1}'); \
		if [ -z "$$expected_digest" ]; then \
			echo "ERROR: No trusted digest found for $$binary in $(DIGEST_FILE)."; \
			echo "Cannot verify binary integrity. Build aborted."; \
			exit 1; \
		fi; \
		if command -v sha256sum >/dev/null 2>&1; then \
			actual_digest=$$(sha256sum "$$binary" | awk '{print $$1}'); \
		elif command -v shasum >/dev/null 2>&1; then \
			actual_digest=$$(shasum -a 256 "$$binary" | awk '{print $$1}'); \
		else \
			echo "ERROR: Neither sha256sum nor shasum found. Cannot verify binaries."; \
			exit 1; \
		fi; \
		if [ "$$actual_digest" != "$$expected_digest" ]; then \
			echo "ERROR: Digest mismatch for $$binary"; \
			echo "  Expected: $$expected_digest"; \
			echo "  Actual:   $$actual_digest"; \
			echo ""; \
			echo "Binary integrity verification FAILED. Build aborted."; \
			echo "This may indicate:"; \
			echo "  - A compromised download or man-in-the-middle attack"; \
			echo "  - Corrupted cache files"; \
			echo "  - Outdated digest file"; \
			echo ""; \
			echo "To resolve:"; \
			echo "  1. Clear the cache: make clean"; \
			echo "  2. Verify $(DIGEST_FILE) is up to date"; \
			echo "  3. Re-run the build"; \
			exit 1; \
		fi; \
		echo "✓ $$binary verified successfully"; \
	done
	@echo "All binaries verified successfully against trusted digests."

.PHONY: check_binaries
check_binaries:
	@if [ -d "$(CACHE_DIR)" ] && [ -n "$$(ls -A $(CACHE_DIR) 2>/dev/null)" ]; then \
		echo "Cache directory $(CACHE_DIR) exists. Verifying cached binaries..."; \
		$(MAKE) verify_binaries || { \
			echo "Cached binaries failed verification. Re-downloading..."; \
			$(MAKE) binaries; \
		}; \
	else \
		echo "Cache directory $(CACHE_DIR) is empty or missing. Running 'make binaries'..."; \
		$(MAKE) binaries; \
	fi

.PHONY: download_and_compute_digests
download_and_compute_digests:
	@echo "Downloading binaries and computing digests..."
	@echo "WARNING: This will download binaries from $(BASE_URL)"
	@echo "Ensure you trust this source before proceeding."
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	@$(MAKE) binaries_make_dir
	@for binary in $(BINARY_FILES); do \
		echo "Downloading $$binary..."; \
		curl -L -o .cache/binaries/$$binary $(BASE_URL)/$$binary || { \
			echo "ERROR: Failed to download $$binary"; \
			exit 1; \
		}; \
	done
	@echo ""
	@echo "Computing SHA256 digests..."
	@echo "# Trusted SHA256 digests for zen-internals v0.1.60 binaries" > $(DIGEST_FILE).new
	@echo "# Format: <sha256> <filename>" >> $(DIGEST_FILE).new
	@echo "# These digests are independently verified and committed to the repository" >> $(DIGEST_FILE).new
	@echo "# Any mismatch will cause the build to fail" >> $(DIGEST_FILE).new
	@echo "" >> $(DIGEST_FILE).new
	@echo "# Generated on $$(date -u +"%Y-%m-%d %H:%M:%S UTC")" >> $(DIGEST_FILE).new
	@echo "# Source: $(BASE_URL)" >> $(DIGEST_FILE).new
	@echo "" >> $(DIGEST_FILE).new
	@cd .cache/binaries && \
	for binary in $(BINARY_FILES); do \
		if command -v sha256sum >/dev/null 2>&1; then \
			digest=$$(sha256sum "$$binary" | awk '{print $$1}'); \
		elif command -v shasum >/dev/null 2>&1; then \
			digest=$$(shasum -a 256 "$$binary" | awk '{print $$1}'); \
		else \
			echo "ERROR: Neither sha256sum nor shasum found. Cannot compute digests."; \
			exit 1; \
		fi; \
		echo "$$digest  $$binary" >> ../../$(DIGEST_FILE).new; \
		echo "  $$binary: $$digest"; \
	done
	@echo ""
	@echo "Digests computed and saved to $(DIGEST_FILE).new"
	@echo "IMPORTANT: Review the digests, verify they match trusted sources,"
	@echo "then replace $(DIGEST_FILE) with $(DIGEST_FILE).new"
	@echo ""
	@echo "To apply: mv $(DIGEST_FILE).new $(DIGEST_FILE)"


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

