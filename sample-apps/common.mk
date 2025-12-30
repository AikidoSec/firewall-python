# Common Makefile for all sample apps
# This file defines standard ports, AIKIDO environment variables, and common targets

# Standard ports for benchmarking
# PORT: Main application port (with firewall)
# PORT_DISABLED: Application port without firewall
# These can be overridden in individual Makefiles if needed

PORT ?= 8080
PORT_DISABLED ?= 8081

# AIKIDO environment variables
AIKIDO_ENV_COMMON = \
	AIKIDO_DEBUG=true \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" \
	AIKIDO_DISABLE=0

AIKIDO_ENV_BENCHMARK = \
	AIKIDO_DEBUG=false \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/" \
	DONT_ADD_MIDDLEWARE=1

AIKIDO_ENV_DISABLED = \
	AIKIDO_DISABLE=1

# Common target definitions
.PHONY: install
install:
	poetry install --quiet

export PORT
export PORT_DISABLED
