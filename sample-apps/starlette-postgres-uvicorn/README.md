# starlette w/ Postgres and Uvicorn Sample app
It runs **multi-threaded** and **async**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the starlette Server at : [localhost:8102](http://localhost:8096)
- To Create a reference test dog use `http://localhost:8102/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8102/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
