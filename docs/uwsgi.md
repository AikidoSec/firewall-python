# uWSGI

## Installation/Setup
1. Install `aikido_zen` package with pip:
```sh
pip install aikido_zen
```

2. uWSGI preforks worker processes from its master by default. Use the decorators below to instrument your app before its imports and start Zen's background process after each fork. Add this at the top of your app file, above any other import:
```python
from uwsgidecorators import postfork
import aikido_zen.decorators.uwsgi as aik

@postfork
@aik.postfork
def start_aikido():
    # If you already have a postfork hook, replace pass with your own code.
    pass
```

3. Setting your environment variables:
Make sure to set your token in order to communicate with Aikido's servers
```env
AIKIDO_TOKEN="AIK_RUNTIME_YOUR_TOKEN_HERE"
```

- Enabling extra debugging (optional): ```AIKIDO_DEBUG=1```
- Enabling blocking using an env variable (optional): ```AIKIDO_BLOCK=1```
