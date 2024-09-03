# Quart w/ Mongo Sample app
It runs **multi-threaded** and **async**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Quart Server at : [localhost:8098](http://localhost:8098)
- To Create a reference test dog use `http://localhost:8098/create/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
