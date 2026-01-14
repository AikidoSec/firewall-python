# Sample Django ASGI App with Gunicorn + Uvicorn

This is a Django ASGI application running with Gunicorn using the UvicornWorker.

## Getting started

Run:
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

This will expose a Django web server at [localhost:8114](http://localhost:8114)

## Architecture

This sample app demonstrates:
- Django 5.x running in ASGI mode
- Gunicorn as the application server
- Uvicorn workers (via `uvicorn.workers.UvicornWorker`) for ASGI support
- PostgreSQL database integration
- Aikido Zen security integration

## URLS

- Homepage: `http://localhost:8114/app`
- Create a dog: `http://localhost:8114/app/create/<dog_name>`
- SQL injection attack example: `Malicious dog", "Injected wrong boss name"); -- `

To verify your attack was successfully blocked, note that the is_admin field should remain FALSE. If you open the dog page (you can do this from the home page), you should see whether the SQL injection was prevented.
