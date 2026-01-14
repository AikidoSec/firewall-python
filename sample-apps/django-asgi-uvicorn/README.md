# Sample Django ASGI App with Gunicorn + Uvicorn
This is a Django ASGI application running with Gunicorn using the UvicornWorker.

## Starting the app

Run:
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

## URLS
- Homepage: `http://localhost:8114/app`
- Create a dog: `http://localhost:8114/app/create/<dog_name>`
- SQL injection attack example: `Malicious dog", "Injected wrong boss name"); -- `
