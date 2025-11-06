# Troubleshooting

## Review installation steps

Double-check your setup against the [installation guide](../README.md#installation).
Make sure:
- The package installed correctly.
- The firewall is initialized early in your app (before routes or handlers).
- Your framework-specific integration (middleware, decorator, etc.) matches the example in the README.
- You’re running a supported runtime version for your language.

## Check connection to Aikido

The firewall must be able to reach Aikido’s API endpoints.

Test from the same environment where your app runs and follow the instructions on this page: https://help.aikido.dev/zen-firewall/miscellaneous/outbound-network-connections-for-zen

## Check logs for errors

Common places:
- Docker: `docker logs <your-app-container>`
- systemd: `journalctl -u <your-app-service> --since "1 hour ago"`
- Local dev: your terminal or IDE run console

Tip: search for lines that contain `Aikido` or `aikido_zen`.

## Enable debug logs temporarily
Add this early in your app to surface initialization details:

```python
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("aikido_zen").setLevel(logging.INFO)   # use DEBUG or TRACE if needed
```

If you use Gunicorn or Uvicorn, also run them with higher verbosity so stdout includes the module logs.

## Confirm the package is installed

```
pip show aikido-zen || python -m pip show aikido-zen
python -c "import importlib; print('ok' if importlib.util.find_spec('aikido_zen') else 'missing')"
```

## Confirm it is wired early in the request pipeline
Make sure all requests hit the protection layer before your routes or views.

FastAPI or Starlette (ASGI)
```
from fastapi import FastAPI
import aikido_zen

app = FastAPI()
aikido_zen.protect(app)  # add as early as possible, before routes
# define routes after this
```

Flask (WSGI)

```
from flask import Flask
import aikido_zen

app = Flask(__name__)
aikido_zen.protect(app)  # call before registering blueprints or running the app
```


Django

In settings.py, add the middleware near the top so it runs before others:

```
MIDDLEWARE = [
    "aikido_zen.django.Middleware",   # keep this high in the list
    # ... your other middleware
]
```

Generic ASGI

```
import aikido_zen
from your_asgi_app import app
aikido_zen.protect(app)
```

## Contact support

If you still can’t resolve the issue:

- Use the in-app chat to reach our support team directly.
- Or create an issue on [GitHub](../../issues) with details about your setup, framework, and logs.

Include as much context as possible (framework, logs, and how Aikido was added) so we can help you quickly.
