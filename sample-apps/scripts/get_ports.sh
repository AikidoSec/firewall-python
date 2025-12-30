#!/bin/bash

# Script to extract PORT and PORT_DISABLED from a Makefile
# Usage: ./get_ports.sh <app_directory>

APP_DIR="$1"
if [ -z "$APP_DIR" ]; then
    echo "Usage: $0 <app_directory>"
    exit 1
fi

MAKEFILE="$APP_DIR/Makefile"
if [ ! -f "$MAKEFILE" ]; then
    echo "Makefile not found in $APP_DIR"
    exit 1
fi

# Extract PORT and PORT_DISABLED from Makefile
PORT=$(grep -E '^PORT\s*=' "$MAKEFILE" | head -1 | cut -d'=' -f2 | tr -d ' ')
PORT_DISABLED=$(grep -E '^PORT_DISABLED\s*=' "$MAKEFILE" | head -1 | cut -d'=' -f2 | tr -d ' ')

# If not found in Makefile, use defaults
PORT="${PORT:-8086}"
PORT_DISABLED="${PORT_DISABLED:-8087}"

echo "$PORT $PORT_DISABLED"
