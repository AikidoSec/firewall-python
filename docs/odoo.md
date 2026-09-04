# Odoo

Zen supports self-hosted Odoo Community 16 through 19 on Odoo's regular HTTP server in both threaded and prefork worker modes. Odoo's gevent server, websocket traffic, long-polling traffic, Odoo Online, and Odoo.sh are not supported.

## Installation

Choose the instructions that match your Odoo deployment.

### Docker

Extend the Odoo image used by your deployment:

```dockerfile
FROM odoo:19.0

USER root
RUN python3 -m pip install --no-cache-dir --target /opt/aikido-zen aikido_zen
ENV PYTHONPATH=/opt/aikido-zen
USER odoo
```

Use the same Odoo version as your existing image, then rebuild and deploy it.

### Source installation

Install Zen in the virtual environment used to run `odoo-bin`:

```sh
/path/to/venv/bin/python -m pip install aikido_zen
```

### Linux package

Install Zen in a separate directory:

```sh
sudo /usr/bin/python3 -m pip install --target /opt/aikido-zen aikido_zen
```

Add `/opt/aikido-zen` to `PYTHONPATH` in the Odoo service configuration.

Set the Aikido token in the Odoo environment:

```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```

## Load Zen when Odoo starts

Create a server-wide addon named `aikido_zen_bootstrap`.

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

Add the addon directory to `addons_path` and load it as a server-wide module:

```sh
odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
  --load=base,web,aikido_zen_bootstrap
```

Restart Odoo after adding the server-wide module.

## Blocking mode

Zen reports attacks without blocking by default. Enable sink blocking after validating the integration in staging:

```env
AIKIDO_BLOCK=true
```

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

## Limitations

- Only Odoo 16, 17, 18, and 19 are supported.
- Uploaded file contents are not inspected.
- Request policies are not applied to static files or unmatched routes, but Zen still detects attack waves for those requests.
