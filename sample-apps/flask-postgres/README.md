# Flask w/ Postgres Sample app
It runs **multi-threaded**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Flask Server at : [localhost:8090](http://localhost:8090)
- To Create a reference test dog use `http://localhost:8090/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8090/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
