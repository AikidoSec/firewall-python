.PHONY: build
build:
	poetry build

.PHONY: clean
clean:
	poetry env remove python