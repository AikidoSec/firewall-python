#!/bin/bash
# Run a single e2e test suite locally.
# Usage: ./e2e.sh <app-name>
# Example: ./e2e.sh flask-postgres

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

get_testfiles() {
  local app="$1"
  local slug="${app//-/_}"
  local found=""
  for f in "$SCRIPT_DIR"/end2end/"${slug}"*_test.py; do
    [[ -f "$f" ]] || continue
    local stem best_app candidate candidate_slug
    stem="$(basename "$f" _test.py)"
    best_app=""
    for dir in "$SCRIPT_DIR"/sample-apps/*/; do
      candidate="$(basename "$dir")"
      candidate_slug="${candidate//-/_}"
      if [[ "$stem" == "${candidate_slug}"* ]] && [[ ${#candidate} -gt ${#best_app} ]]; then
        best_app="$candidate"
      fi
    done
    [[ "$best_app" == "$app" ]] && found="$found end2end/$(basename "$f")"
  done
  echo "${found# }"
}

get_available_apps() {
  for dir in "$SCRIPT_DIR"/sample-apps/*/; do
    app="$(basename "$dir")"
    if grep -q "runZenDisabled" "$dir/Makefile" 2>/dev/null; then
      if [[ -n "$(get_testfiles "$app")" ]]; then
        echo "  $app"
      fi
    fi
  done | sort
}

APP="${1:-}"
if [[ -z "$APP" ]]; then
  echo "Usage: ./e2e.sh <app-name>"
  echo ""
  echo "Available apps:"
  get_available_apps
  exit 1
fi

APP_DIR="sample-apps/$APP"
if [[ ! -d "$SCRIPT_DIR/$APP_DIR" ]]; then
  echo "Unknown app: $APP"
  echo ""
  echo "Available apps:"
  get_available_apps
  exit 1
fi

TESTFILE="$(get_testfiles "$APP")"
if [[ -z "$TESTFILE" ]]; then
  echo "No test file found for $APP (expected end2end/$(echo "$APP" | tr '-' '_')*_test.py)"
  exit 1
fi
LOG_DIR="$(mktemp -d)"
MOCK_PID=""
APP_PID=""
APP_DISABLED_PID=""

kill_tree() {
  local pid="$1"
  # Kill all descendants first, then the process itself
  for child in $(pgrep -P "$pid" 2>/dev/null); do kill_tree "$child"; done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  local exit_code=$?
  echo ""
  echo "Cleaning up..."
  [[ -n "$MOCK_PID" ]] && kill_tree "$MOCK_PID"
  [[ -n "$APP_PID" ]] && kill_tree "$APP_PID"
  [[ -n "$APP_DISABLED_PID" ]] && kill_tree "$APP_DISABLED_PID"
  if [[ $exit_code -ne 0 ]]; then
    echo ""
    echo "=== mock-server.log ==="
    cat "$LOG_DIR/mock-server.log" 2>/dev/null || true
    echo ""
    echo "=== app.log ==="
    cat "$LOG_DIR/app.log" 2>/dev/null || true
    echo ""
    echo "=== app-disabled.log ==="
    cat "$LOG_DIR/app-disabled.log" 2>/dev/null || true
  fi
  rm -rf "$LOG_DIR"
}
trap cleanup EXIT

wait_for_port() {
  local port="$1"
  local label="$2"
  local logfile="$3"
  local pid="${4:-}"
  local timeout="${5:-60}"
  local end=$((SECONDS + timeout))
  echo "Waiting for $label on port $port..."
  while [[ $SECONDS -lt $end ]]; do
    if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
      echo "  $label process exited unexpectedly"
      echo "--- logs ---"
      cat "$logfile" 2>/dev/null || true
      exit 1
    fi
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/" 2>/dev/null | grep -qE "^[2345]"; then
      echo "  $label is up"
      return 0
    fi
    sleep 2
  done
  echo "  $label failed to start on port $port within ${timeout}s"
  echo "--- logs ---"
  cat "$logfile" 2>/dev/null || true
  exit 1
}

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local timeout="${4:-60}"
  local end=$((SECONDS + timeout))
  echo "Waiting for $label on $host:$port..."
  while [[ $SECONDS -lt $end ]]; do
    if (echo > /dev/tcp/"$host"/"$port") 2>/dev/null; then
      echo "  $label is up"
      return 0
    fi
    sleep 2
  done
  echo "  $label failed to start within ${timeout}s"
  exit 1
}

# Extract ports from the app's Makefile
APP_PORT=$(grep -m1 "^PORT\s*=" "$APP_DIR/Makefile" | awk '{print $3}')
APP_PORT_DISABLED=$(grep -m1 "^PORT_DISABLED\s*=" "$APP_DIR/Makefile" | awk '{print $3}')
APP_PORT="${APP_PORT:-8080}"
APP_PORT_DISABLED="${APP_PORT_DISABLED:-8081}"

# 1. Kill any lingering processes from previous runs
AIKIDO_SOCK=$(AIKIDO_TOKEN="AIK_secret_token" poetry run python3 -c "
import os; os.environ['AIKIDO_TOKEN']='AIK_secret_token'
from aikido_zen.helpers.hash_aikido_token import hash_aikido_token
from aikido_zen.helpers.get_temp_dir import get_temp_dir
print(f'{get_temp_dir()}/aikido_python_{hash_aikido_token()}.sock')
" 2>/dev/null)
if [[ -n "$AIKIDO_SOCK" ]]; then
  rm -f "$AIKIDO_SOCK"
fi
for port in 5000 "$APP_PORT" "$APP_PORT_DISABLED"; do
  lsof -ti :"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
done

# 2. Databases
echo "Starting databases..."
docker compose -f "$SCRIPT_DIR/sample-apps/databases/docker-compose.yml" up -d
wait_for_tcp localhost 5432 "postgres"

# 3. Mock server
echo "Starting mock Aikido server..."
poetry run python3 "$SCRIPT_DIR/end2end/server/mock_aikido_core.py" 5000 > "$LOG_DIR/mock-server.log" 2>&1 &
MOCK_PID=$!
wait_for_port 5000 "mock-server" "$LOG_DIR/mock-server.log" "$MOCK_PID"

# 4. Install sample app deps
echo "Installing $APP dependencies..."
cd "$SCRIPT_DIR/$APP_DIR"
poetry install -q

# 5. Start app with firewall enabled
echo "Starting $APP (firewall on)..."
make run > "$LOG_DIR/app.log" 2>&1 &
APP_PID=$!
cd "$SCRIPT_DIR"

wait_for_port "$APP_PORT" "$APP (fw-on)" "$LOG_DIR/app.log" "$APP_PID"

# 5. Start app with firewall disabled
echo "Starting $APP (firewall off)..."
cd "$SCRIPT_DIR/$APP_DIR"
make runZenDisabled > "$LOG_DIR/app-disabled.log" 2>&1 &
APP_DISABLED_PID=$!
cd "$SCRIPT_DIR"
wait_for_port "$APP_PORT_DISABLED" "$APP (fw-off)" "$LOG_DIR/app-disabled.log" "$APP_DISABLED_PID"

# 6. Run tests
echo ""
echo "Running tests: $TESTFILE"
echo "---"
# shellcheck disable=SC2086
poetry run pytest $TESTFILE -v
