# Flask Sample app
It runs **single-threaded**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8080](http://localhost:8080)
- To Create a reference test dog use `http://localhost:8080/create/doggo`
- To test a sql injection enter the following dog name : `Malicious dog", 1); -- `
