# Odoo

## Installation

1. Install `aikido_zen` package with pip :
```sh
pip install aikido_zen
```

2. Load Zen when Odoo starts, with a server-wide addon named `aikido_zen_bootstrap`.

`aikido_zen_bootstrap/__init__.py`:

```python
from .hooks import post_load
```

`aikido_zen_bootstrap/__manifest__.py`:

```python
{
    "name": "Aikido Zen Bootstrap",
    "version": "1.0.0",
    "author": "Aikido Security",
    "license": "AGPL-3",
    "depends": ["base"],
    "post_load": "post_load",
}
```

`aikido_zen_bootstrap/hooks.py`:

```python
import aikido_zen


def post_load():
    aikido_zen.protect()
```

Add the addon directory to `addons_path` and the addon to the server-wide modules Odoo already loads (`--load`), then restart Odoo:

```sh
# Odoo 16 to 18
odoo --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --load=base,web,aikido_zen_bootstrap

# Odoo 19
odoo --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --load=base,rpc,web,aikido_zen_bootstrap
```

Prefork mode (`--workers`) needs no extra setup.

3. Setting your environment variables :
Make sure to set your token in order to communicate with Aikido's servers
```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```

## Blocking mode

By default, the firewall will run in non-blocking mode. When it detects an attack, the attack will be reported to Aikido and continue executing the call.

You can enable blocking mode by setting the environment variable `AIKIDO_BLOCK` to `true`:

```sh
AIKIDO_BLOCK=true
```

An attack blocked in a JSON-RPC call returns HTTP 200 with a JSON-RPC error, as Odoo does for every failed call.

## Rate limiting and user blocking

To add rate limiting and user blocking, add this check to an addon installed in each database:

`your_addon/models/ir_http.py`:

```python
from odoo import models
from odoo.http import request
from werkzeug.exceptions import abort

from aikido_zen import set_user
from aikido_zen.middleware import should_block_request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)

        if request.env.uid and not request.env.user._is_public():
            set_user({"id": request.env.user.id})

        result = should_block_request()
        if result["block"]:
            status = 429 if result["type"] == "ratelimited" else 403
            abort(request.make_response("Blocked by Zen.", status=status))
```

See [users and rate limiting](user.md) for `set_user` and `set_rate_limit_group`.

## Debug mode

If you need to debug the firewall, you can run your code with the environment variable `AIKIDO_DEBUG` set to `true`:

```sh
AIKIDO_DEBUG=true
```

This will output debug information to the console (e.g. no token was found, unsupported packages, extra information, ...).

## Limitations

- Odoo Online is not supported, because it does not allow installing Python packages.
- Odoo's gevent server (live chat, websocket and long-polling traffic) is not protected.
- Uploaded file names are checked, file contents are not.
- Zen picks the client IP as `AIKIDO_TRUST_PROXY` sets it, not from Odoo's `--proxy-mode` (see [proxy settings](proxy.md)).
- If `odoo.http` lacks a method Zen hooks, Zen logs a warning and does not protect Odoo requests.
