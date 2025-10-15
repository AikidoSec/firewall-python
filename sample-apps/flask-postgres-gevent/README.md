# flask-postgres-gevent
It runs **multi-threaded & async (gevent)**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Flask Server at : [localhost:8110](http://localhost:8110)
- To Create a reference test dog use `http://localhost:8110/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8110/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
