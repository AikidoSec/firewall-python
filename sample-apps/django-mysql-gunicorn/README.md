# Sample Django/Mysql App with Gunicorn installed
it runs 4 processes, called workers, (**multi-process**) which handle requests using 2 threads (**multi-threaded**)

## Getting started
With docker-compose installed run
```bash
docker-compose up --build
```
This will expose a Django web server at [localhost:8080](http://localhost:8080)

## URLS : 
- Homepage : `http://localhost:8080/app`
- Create a dog : `http://localhost:8080/app/create/<dog_name>`
- MySQL attack : `http://localhost:8080/app/create/Malicious dog", "Injected wrong boss name"); --%20`

To verify your attack was successfully note that the boss_name usualy is 'N/A', if you open the dog page (you can do this from the home page). You should see a "malicious dog" with a boss name that is not permitted.
