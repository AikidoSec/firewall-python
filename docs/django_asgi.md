# Django ASGI

## Support
Currently Django ASGI is **only supported with gUnicorn** and a uvicorn worker.


## Installation for gUnicorn with a Uvicorn Worker
1. Install `aikido_zen` package with pip :
```sh
pip install aikido_zen
```

2. Use the following template for your `gunicorn_config.py` file :
```python
import aikido_zen.decorators.gunicorn as aik

@aik.post_fork
def post_fork(server, worker):
    # If you already have a config file, replace pass with your own code.
    pass
```
And make sure to include this config when starting gunicorn by adding the `-c gunicorn_config.py` flag.
```sh
gunicorn -c gunicorn_config.py --workers ...
```

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

It's recommended to enable this on your staging environment for a considerable amount of time before enabling it on your production environment (e.g. one week).

## Debug mode

If you need to debug the firewall, you can run your code with the environment variable `AIKIDO_DEBUG` set to `true`:

```sh
AIKIDO_DEBUG=true
```

This will output debug information to the console (e.g. no token was found, unsupported packages, extra information, ...).
