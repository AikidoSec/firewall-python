# Flask
## Installation
1. Install `aikido_firewall` package with pip :
```sh
pip install aikido_firewall
```

2. Add the following snippet to the top of your `app.py` file :
```python
import aikido_firewall
aikido_firewall.protect()
```
Make sure this is above any other import, including above system imports.

3. Setting your environment variables :
Make sure to set your token in order to communicate with Aikido's servers
```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```

- Enabling extra debugging (optional): ```AIKIDO_DEBUG=1```
- Enabling blocking using an env variable (optional): ```AIKIDO_BLOCKING=1```

## Using gUnicorn
If you're using gunicorn, please check our docs on that first : [Click Here](./gunicorn.md)


## Warning: Installing middleware
When installing middleware make sure to install it like this :
```python
from flask import Flask
app = Flask(__name__)
...
app.wsgi_app = my_middleware(app.wsgi_app)
```
and not like this :
```python
app.wsgi_app = my_middleware
```
Since this removes all other middleware.
