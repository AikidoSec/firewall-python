# Gunicorn
## Installation/Setup
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

- Enabling extra debugging (optional): ```AIKIDO_DEBUG=1```
- Enabling blocking using an env variable (optional): ```AIKIDO_BLOCKING=1```
