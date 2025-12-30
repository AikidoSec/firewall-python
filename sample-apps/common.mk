# Common Makefile variables for all sample apps
# This file defines standard ports and AIKIDO environment variables

# Standard ports for benchmarking
# PORT: Main application port (with firewall)
# PORT_DISABLED: Application port without firewall
# These can be overridden in individual Makefiles if needed

PORT ?= 8086
PORT_DISABLED ?= 8087

# AIKIDO environment variables
AIKIDO_ENV_COMMON = \
	AIKIDO_DEBUG=true \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/"

AIKIDO_ENV_BENCHMARK = \
	AIKIDO_DEBUG=false \
	AIKIDO_BLOCK=true \
	AIKIDO_TOKEN="AIK_secret_token" \
	AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
	AIKIDO_ENDPOINT="http://localhost:5000/"

AIKIDO_ENV_DISABLED = \
	AIKIDO_DISABLE=1

# Common target definitions
.PHONY: show-ports
show-ports:
	@echo "Standard ports:"
	@echo "  PORT=$(PORT) (with firewall)"
	@echo "  PORT_DISABLED=$(PORT_DISABLED) (without firewall)"

# Export ports for health check script
export PORT
export PORT_DISABLED
