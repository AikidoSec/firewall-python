# Odoo

Zen protects self-hosted Odoo on Odoo's regular HTTP server, in threaded and prefork worker mode. It is tested on Odoo 16 through 19. Zen stores the JSON-RPC body, the HTTP form, the query, cookies, route arguments, and upload file names from Odoo's own parse, then checks database, file, shell and outbound calls against that input.

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
    "license": "AGPL-3",
    "depends": ["base"],
    "post_load": "post_load",
    "installable": True,
    "application": False,
}
```

`aikido_zen_bootstrap/hooks.py`:

```python
import aikido_zen


def post_load():
    aikido_zen.protect()
```

Add the addon directory to `addons_path` and load it as a server-wide module, then restart Odoo:

```sh
odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --load=base,web,aikido_zen_bootstrap
```

In prefork mode, each worker starts Zen again after it is forked.

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

A blocked JSON-RPC call returns HTTP 200 with a JSON-RPC error, because that is how Odoo reports a failed call. The blocked operation does not run.

## Rate limiting and user blocking

Zen does not enable rate limiting or user blocking automatically. To enable them, add a post-authentication policy check to an addon installed in each protected database.

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

        if request.env.uid and not request.env.user.is_public:
            set_user({"id": request.env.user.id})

        result = should_block_request()
        if result["block"] is not True:
            return

        if result["type"] == "blocked":
            message = "You are blocked by Zen."
            status = 403
        elif result["type"] == "ratelimited":
            message = "You are rate limited by Zen."
            if result["trigger"] == "ip" and result["ip"]:
                message += f" (Your IP: {result['ip']})"
            status = 429
        else:
            return

        abort(
            request.make_response(
                message,
                headers=[("Content-Type", "text/plain; charset=utf-8")],
                status=status,
            )
        )
```

Set the user identity that matches your authorization model before calling `should_block_request()`. You can also call `set_rate_limit_group()` there for group-based rate limits. See [users and rate limiting](user.md) for the available APIs.

## Debug mode

If you need to debug the firewall, you can run your code with the environment variable `AIKIDO_DEBUG` set to `true`:

```sh
AIKIDO_DEBUG=true
```

This will output debug information to the console (e.g. no token was found, unsupported packages, extra information, ...).

## Limitations

- Odoo Online is not supported, because it does not allow installing Python packages.
- Odoo's gevent server, used for live chat, websocket and long-polling traffic, is not protected. Zen does not start in a process that has already imported `gevent`.
- XML-RPC calls (`/xmlrpc/2/...`) are not checked yet.
- Uploaded file names are checked. Uploaded file contents are not.
- If `odoo.http` lacks a method Zen hooks, Zen logs a warning and does not protect Odoo requests.
