# Odoo w/ Postgres Sample app
It runs the official Odoo server in Docker, **multi-threaded** by default or **multi-process** with `ODOO_WORKERS=2`. Zen starts from the `aikido_zen_bootstrap` addon, as in [docs/odoo.md](../../docs/odoo.md).

## Getting started
Run :
```bash
make up # Builds the wheel and the image, then starts Odoo with and without Zen
make down # Stops everything and removes the databases
```

- Odoo with Zen runs at [localhost:8120](http://localhost:8120), without Zen at [localhost:8121](http://localhost:8121)
- Use another Odoo version with `ODOO_VERSION=19.0 make up` (default `16.0`)
- To test an SQL injection, post the dog name `Dangerous Bobby', TRUE); -- ` as text to `/zen/dog/text`
