#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

export COMPOSE_PROJECT_NAME="firewall-python-odoo-smoke-$$"
ODOO_PORT="${ODOO_PORT:-8116}"
ODOO_DISABLED_PORT="${ODOO_DISABLED_PORT:-8117}"
ODOO_START_TIMEOUT="${ODOO_START_TIMEOUT:-300}"
ODOO_WORKER_COUNTS="${ODOO_WORKER_COUNTS:-0 2}"

compose() {
    docker compose "$@"
}

cleanup() {
    compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}

finish() {
    status=$?
    if [ "$status" -ne 0 ]; then
        compose logs --no-color || true
    fi
    cleanup
    exit "$status"
}

assert_equals() {
    expected="$1"
    actual="$2"
    label="$3"
    if [ "$actual" != "$expected" ]; then
        printf 'Expected %s to be %q, got %q\n' "$label" "$expected" "$actual" >&2
        return 1
    fi
}

assert_response() {
    expected="$1"
    shift
    response="$(curl --fail --silent --show-error "$@")"
    assert_equals "$expected" "$response" "response"
}

assert_addon_installed() {
    database="$1"
    state="$(
        compose exec -T postgres \
            psql --username=odoo --dbname="$database" --tuples-only --no-align \
            --command="SELECT state FROM ir_module_module WHERE name = 'zen_test'"
    )"
    assert_equals "installed" "$state" "zen_test state in $database"
}

assert_clean_shutdown() {
    cleanup
    if [ -n "$(compose ps --all --quiet)" ]; then
        printf 'Odoo smoke-test containers are still present after shutdown\n' >&2
        return 1
    fi
    if [ -n "$(docker volume ls --quiet --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}")" ]; then
        printf 'Odoo smoke-test volumes are still present after shutdown\n' >&2
        return 1
    fi
}

trap finish EXIT

for workers in $ODOO_WORKER_COUNTS; do
    printf 'Starting Odoo sample with workers=%s\n' "$workers"
    export ODOO_WORKERS="$workers"
    compose up --detach --wait --wait-timeout "$ODOO_START_TIMEOUT" odoo odoo-disabled

    compose exec -T postgres pg_isready --username=odoo --dbname=postgres >/dev/null
    compose exec -T odoo sh -c \
        "tr '\\000' ' ' </proc/1/cmdline | grep -F '/usr/bin/odoo' | grep -F -- '--workers=${workers}'" \
        >/dev/null
    compose exec -T odoo python3 -c \
        "from importlib.metadata import version; import aikido_zen; assert version('aikido_zen'); assert aikido_zen.__file__.startswith('/usr/local/lib/')"

    assert_addon_installed odoo_zen
    assert_addon_installed odoo_without_zen

    compose logs --no-color odoo | grep -F "Aikido Zen bootstrap post_load completed" >/dev/null
    if compose logs --no-color odoo-init-enabled | grep -F "Aikido Zen bootstrap post_load completed" >/dev/null; then
        printf 'Zen bootstrap ran during database initialization\n' >&2
        exit 1
    fi

    assert_response "ok" "http://localhost:${ODOO_PORT}/zen/status"
    assert_response "ok" "http://localhost:${ODOO_DISABLED_PORT}/zen/status"
    assert_response \
        "printf form-value" \
        --request POST \
        --data-urlencode "command=printf form-value" \
        "http://localhost:${ODOO_PORT}/zen/shell/form"
    assert_response \
        "printf json-value" \
        --request POST \
        --header "Content-Type: application/json" \
        --data '{"command":"printf json-value"}' \
        "http://localhost:${ODOO_PORT}/zen/shell/json"
    assert_response \
        "printf route-value" \
        "http://localhost:${ODOO_PORT}/zen/shell/route/printf%20route-value"

    jsonrpc_response="$(
        curl --fail --silent --show-error \
            --request POST \
            --header "Content-Type: application/json" \
            --data '{"jsonrpc":"2.0","method":"call","params":{"command":"printf jsonrpc-value"},"id":1}' \
            "http://localhost:${ODOO_PORT}/zen/shell/jsonrpc"
    )"
    if [[ "$jsonrpc_response" != *"printf jsonrpc-value"* ]]; then
        printf 'JSON-RPC controller changed its command argument: %s\n' "$jsonrpc_response" >&2
        exit 1
    fi

    assert_clean_shutdown
    printf 'Odoo sample passed with workers=%s\n' "$workers"
done

trap - EXIT
printf 'Odoo sample smoke test passed\n'
