# Django
## Installation
1. Install `aikido_firewall` package with pip :
```sh
pip install aikido_firewall
```

2. Add the following snippet to the top of your `manage.py` file :
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
