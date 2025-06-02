# Flask Sample app with uWSGI & Clickhouse
It runs 4 processes (**multi-process**) which handle requests **multi-threaded**

## Getting Started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Flask Server at : [localhost:8106](http://localhost:8106)
- To Create a reference test dog use `http://localhost:8106/create/doggo`
- To test a sql injection enter the following dog name : `Malicious dog', 1); -- `
