#!/usr/bin/env bash
set -euo pipefail

: "${ODOO_DATABASE:?ODOO_DATABASE must be set}"

exec /usr/bin/odoo \
    --config=/etc/odoo/odoo.conf \
    --database="${ODOO_DATABASE}" \
    --db-filter="^${ODOO_DATABASE}$" \
    --init=zen_test \
    --without-demo=all \
    --stop-after-init \
    --no-http \
    --load=base,web
