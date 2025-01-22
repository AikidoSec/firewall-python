# Quart w/ Mongo Sample app
It runs **multi-threaded** and **async**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Quart Server at : [localhost:8098](http://localhost:8098)
- To Create a reference test dog use `http://localhost:8098/create/`

- To test a sql injection enter the following dog name : `Malicious dog', TRUE); -- `
