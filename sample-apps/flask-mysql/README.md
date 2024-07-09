# Flask Sample app
Run (with docker-compose installed) :
```bash
docker-compose up --build
```

- You'll be able to access the Flask Server at : [localhost:8080](http://localhost:8080)
- To test a sql injection enter the following link : `http://localhost:8080/create/'); DROP TABLE dogs; #` (not working yet)