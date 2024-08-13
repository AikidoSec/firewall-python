# Flask w/ Postgres Sample app
It runs **multi-threaded**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8090](http://localhost:8090)
- To Create a reference test dog use `http://localhost:8090/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8090/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
