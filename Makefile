build: binaries _build
_build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python

.PHONY: lint
lint:
	poetry run black aikido_zen/
	poetry run pylint aikido_zen/

install: binaries _install
_install:
	pip install poetry
	poetry install

dev_install: install _dev_install
_dev_install:
	poetry install --with=dev


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

BASE_URL = https://github.com/AikidoSec/zen-internals/releases/download/v0.1.31
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

binaries: binaries_make_dir $(addprefix aikido_zen/lib/, $(FILES))
binaries_make_dir:
	rm -rf aikido_zen/lib
	mkdir -p aikido_zen/lib/
aikido_zen/lib/%:
	@echo "Downloading $*..."
	curl -L -o $@ $(BASE_URL)/$*
