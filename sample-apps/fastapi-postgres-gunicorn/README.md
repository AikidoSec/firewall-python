# FastAPI w/ Postgres and Gunicorn Sample app
It runs **multi-threaded** and **async** with Gunicorn

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the FastAPI Server at : [localhost:8104](http://localhost:8104)
- To Create a reference test dog use `http://localhost:8104/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8104/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `

## Running with Gunicorn
To run with Gunicorn:
```bash
python manage.py gunicornserver
```

This will start the Gunicorn server with Uvicorn workers for optimal async performance.