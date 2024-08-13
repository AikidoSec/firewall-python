# Flask Sample app
It runs **single-threaded**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8086](http://localhost:8086)
- To Create a reference test dog use `http://localhost:8086/create/doggo`
- To test a sql injection enter the following dog name : `Malicious dog", 1); -- `
- To test commands : `http://localhost:8086/shell`, uses subprocess.run
