# Sample Django/Mysql App with Gunicorn installed
it runs 4 processes, called workers, (**multi-process**) which handle requests using 2 threads (**multi-threaded**)

## Getting started
With docker-compose installed run
```bash
docker-compose up --build
```
This will expose a Django web server at [localhost:8082](http://localhost:8082)

## URLS : 
- Homepage : `http://localhost:8082/app`
- Create a dog : `http://localhost:8082/app/create/`
- MySQL attack : Enter `Malicious dog", "Injected wrong boss name"); -- `

To verify your attack was successfully note that the boss_name usualy is 'N/A', if you open the dog page (you can do this from the home page). You should see a "malicious dog" with a boss name that is not permitted.
