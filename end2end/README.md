# End-to-end tests

Requires Docker.

```sh
./end2end/e2e.sh <app-name>
# or
make e2e app=<app-name>
```

Available apps:

- `django-mysql`
- `django-mysql-gunicorn`
- `django-postgres-gunicorn`
- `flask-mongo`
- `flask-mysql`
- `flask-mysql-uwsgi`
- `flask-postgres`
- `flask-postgres-xml`
- `quart-postgres-uvicorn`
- `starlette-postgres-uvicorn`
