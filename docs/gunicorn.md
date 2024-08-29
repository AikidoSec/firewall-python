# Gunicorn
## Installation/Setup
1. Install `aikido_firewall` package with pip :
```sh
pip install aikido_firewall
```

2. Use the following template for your `gunicorn_config.py` file :
```python
import aikido_firewall.decorators.gunicorn as aik

@aik.post_fork
def post_fork(server, worker):
    pass # You can put your code here
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

- Enabling extra debugging (optional): ```AIKIDO_DEBUG=1```
- Enabling blocking using an env variable (optional): ```AIKIDO_BLOCKING=1```
