# Odoo

## Installation

1. Install `aikido_zen` package with pip :
```sh
pip install aikido_zen
```

2. Call `protect()` when the process starts, before Odoo handles requests and before `gevent` is imported. A `sitecustomize.py` module on `PYTHONPATH` does this for every process :
```python
import aikido_zen
aikido_zen.protect()
```

3. Setting your environment variables :
Make sure to set your token in order to communicate with Aikido's servers
```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```

Odoo 16 and later. Zen stores the JSON-RPC body and the HTTP form from Odoo's own parse, then checks `psycopg2` calls against that input.

## Blocking mode

By default, the firewall will run in non-blocking mode. When it detects an attack, the attack will be reported to Aikido and continue executing the call.

You can enable blocking mode by setting the environment variable `AIKIDO_BLOCK` to `true`:

```sh
AIKIDO_BLOCK=true
```

## Live chat

The live-chat process imports `gevent`. Zen does not start in a process that has already imported `gevent`, so that worker stays unprotected.
