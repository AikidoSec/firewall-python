# Quart w/ Postgres and Uvicorn Sample app
It runs **multi-threaded** and **async**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Quart Server at : [localhost:8096](http://localhost:8096)
- To Create a reference test dog use `http://localhost:8096/create/`
- To Create a reference test dog (with executemany) use `http://localhost:8096/create_many/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
