# Quart

1. Install `aikido_zen` package with pip :
```sh
pip install aikido_zen
```

2. Add the following snippet to the top of your `app.py` file :
```python
import aikido_zen
aikido_zen.protect()
```
Make sure this is above any other import, including above builtin package imports.

3. Setting your environment variables :
Make sure to set your token in order to communicate with Aikido's servers
```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```


## Warning: Installing middleware
When installing middleware make sure to install it like this :

```python
from quart import Quart
app = Quart(__name__)
...
app.asgi_app = my_middleware(app.asgi_app)
```

and not like this :

```python
app.asgi_app = my_middleware
```

Since this removes all other middleware.

## Blocking mode

By default, the firewall will run in non-blocking mode. When it detects an attack, the attack will be reported to Aikido and continue executing the call.

You can enable blocking mode by setting the environment variable `AIKIDO_BLOCKING` to `true`:

```sh
AIKIDO_BLOCKING=true
```

It's recommended to enable this on your staging environment for a considerable amount of time before enabling it on your production environment (e.g. one week).

## Rate limiting and user blocking
If you want to add the rate limiting feature to your app, modify your code like this:
```py
from aikido_zen.middleware import AikidoQuartMiddleware

app = Quart(__name__)
app.asgi_app = AikidoQuartMiddleware(app.asgi_app)
# Authorization middleware here (Make sure aikido middleware runs after this)
```

As soon as you identify the user in you authorization middleware, pass the identity info to Aikido. 
```py
from aikido_zen import set_user

# Set a user (presumably in middleware) :
set_user({"id": "123", "name": "John Doe"})
```

## Debug mode

If you need to debug the firewall, you can run your code with the environment variable `AIKIDO_DEBUG` set to `true`:

```sh
AIKIDO_DEBUG=true
```

This will output debug information to the console (e.g. no token was found, unsupported packages, extra information, ...).
