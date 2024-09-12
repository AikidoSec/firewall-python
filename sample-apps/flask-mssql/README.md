# Flask Sample app with MSSQL
It runs **single-threaded**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8104](http://localhost:8104)
- To test a sql injection enter the following dog name : `Malicious dog', 1); -- `
