# Flask Sample app w/ MongoDB
It runs **multi-threaded**

## Getting started
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8094](http://localhost:8094)
- To Create a reference test dog use `http://localhost:8094/create/`
- To test the nosql injection go to `http://localhost:8094/auth/`
