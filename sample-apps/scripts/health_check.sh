#!/bin/bash

# Health check script for benchmark apps
# Usage: ./health_check.sh <port> [timeout_seconds]

PORT="${1:-8080}"
TIMEOUT="${2:-30}"

echo "Checking health on port $PORT..."

end_time=$((SECONDS + TIMEOUT))

while [ $SECONDS -lt $end_time ]; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" | grep -q "200"; then
        echo "✅ App is healthy on port $PORT"
        exit 0
    fi
    echo "⏳ Waiting for app on port $PORT..."
    sleep 2
done

echo "❌ App failed to start on port $PORT within $TIMEOUT seconds"
exit 1
