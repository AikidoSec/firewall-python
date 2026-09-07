# Odoo/PostgreSQL sample

> **Warning:** This application contains intentional command- and SQL-injection vulnerabilities. Run it only in an isolated development environment. Never deploy it or expose it to an untrusted network.

This sample runs the official Odoo server with PostgreSQL. The image installs the locally built `aikido_zen` wheel and loads Zen through the `post_load` hook of the server-wide `aikido_zen_bootstrap` addon. It does not use a source bind mount, `PYTHONSTARTUP`, a standalone WSGI application, or middleware around Odoo.

The Compose project creates two isolated Odoo databases and data volumes:

- `odoo` uses the Zen bootstrap and listens on port `8116`.
- `odoo-disabled` loads the same bootstrap with `AIKIDO_DISABLE=true` and listens on port `8117`.

Database initialization installs the `zen_test` addon without loading the Zen bootstrap. The runtime processes then start `/usr/bin/odoo` with `--load=base,web,aikido_zen_bootstrap` before Odoo preloads registries or database connections.

## Requirements

- Docker with Compose
- GNU Make
- Poetry, as required by the repository build

## Run the sample

```bash
make up
curl http://localhost:8116/zen/status
curl http://localhost:8117/zen/status
make down
```

Use prefork mode by setting the worker count before starting the services:

```bash
ODOO_WORKERS=2 make up
```

Override the host ports when necessary:

```bash
ODOO_PORT=8216 ODOO_DISABLED_PORT=8217 make up
```

The default image is the official Odoo 16 image pinned to an immutable digest. A different official image can be supplied for compatibility work:

```bash
ODOO_IMAGE=odoo:17.0 make build
```

## Smoke test

```bash
make smoke
```

The smoke test runs fresh `workers=0` and `workers=2` environments. It verifies that PostgreSQL is healthy, both databases contain the installed test addon, the wheel is installed under `/usr/local`, `/usr/bin/odoo` is the real server process, the bootstrap runs only at runtime, form/JSON/JSON-RPC/route inputs reach controllers unchanged, the disabled service starts, and shutdown removes the project containers and volumes.

Set `ODOO_WORKER_COUNTS` to test a subset while developing:

```bash
ODOO_WORKER_COUNTS=0 make smoke
```

## Test endpoints

| Endpoint | Input | Behavior |
| --- | --- | --- |
| `GET /zen/status` | None | Returns `ok`. |
| `GET /zen/shell/query?command=...` | Query string | Passes `command` to a shell. |
| `POST /zen/shell/form` | Form field `command` | Passes `command` to a shell. |
| `POST /zen/shell/json` | JSON field `command` | Passes `command` to a shell through an HTTP route. |
| `POST /zen/shell/jsonrpc` | JSON-RPC `params.command` | Passes `command` to a shell. |
| `GET /zen/shell/header` | `X-Command` header | Passes the header to a shell. |
| `GET /zen/shell/cookie` | `command` cookie | Passes the cookie to a shell. |
| `GET /zen/shell/route/<command>` | Route parameter | Passes the route value to a shell. |
| `GET /zen/sql?query=...` | Query string | Executes raw SQL through `request.env.cr.execute`. |
| `GET /zen/error` | None | Raises an intentional application exception. |
| `GET /zen/stream` | None | Returns a two-chunk streaming response. |
| `GET /zen/user` | Authenticated session | Returns the stable Odoo user ID. |
| `POST /zen/request-block-side-effect` | None | Records a request-block test side effect. |
| `POST /zen/rate-limit-side-effect` | None | Records a rate-limit test side effect. |
| `GET /zen/side-effects/<name>` | Route parameter | Returns the persisted side-effect count. |

The installed test account is `zen-test-user` with password `zen-test-password`. It exists only for authentication lifecycle checks in this isolated sample.

Phase 1 validates the real runtime and bootstrap only. Odoo-specific Zen request blocking is added and asserted in later phases.
