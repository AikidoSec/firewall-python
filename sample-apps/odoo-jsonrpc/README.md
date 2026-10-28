# Odoo-shaped JSON-RPC sample

Stand-in for Odoo, not the Odoo product. It is a WSGI app, so Zen's Flask and Django hooks do not see the request. `aikido_zen.protect()` runs at startup. The body matches the Odoo web client: a JSON-RPC call whose `params.kwargs.dog_name` is the user input.

`/web/dataset/call_kw` and `/jsonrpc` paste that value into the SQL string, which is what a custom Odoo module does with `cr.execute`. `/web/dataset/call_kw_safe` binds the value as a parameter, which is what Odoo's ORM does. Both go through a cursor that unwraps an `SQL` object and then calls `psycopg2`, the same handoff as `odoo.sql_db.Cursor`.

Postgres is the database from `sample-apps/databases` (`db` / `user` / `password`).

## Getting started

```bash
make run
make runZenDisabled
```

- With Zen: [localhost:8120](http://localhost:8120)
- Without Zen: [localhost:8121](http://localhost:8121)

Safe name:

```bash
curl -s -X POST http://localhost:8120/web/dataset/call_kw \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"call","params":{"model":"dogs","method":"create","args":[],"kwargs":{"dog_name":"Bobby Tables"}},"id":1}'
```

Injected name:

```bash
curl -s -X POST http://localhost:8120/web/dataset/call_kw \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"call","params":{"model":"dogs","method":"create","args":[],"kwargs":{"dog_name":"Dangerous Bobby'"'"', TRUE); -- "}},"id":1}'
```

Zen already patches `psycopg2`. This stand-in does not import `odoo.http`, so the Odoo source does not see the request and the injected name is still written. The same call to `/web/dataset/call_kw_safe` stores the payload as plain text. An Odoo 16+ process that calls `aikido_zen.protect()` before it serves requests does build that context.
