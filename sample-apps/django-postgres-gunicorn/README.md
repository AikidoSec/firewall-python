# Sample Django/Postgres App with gunicorn
It runs **multi-threaded** and with **multiple cores**

## Getting started
With docker-compose installed run
```bash
docker-compose up --build
```
This will expose a Django web server at [localhost:8100](http://localhost:8100)

## URLS : 
- Homepage : `http://localhost:8100/app`
- Create a dog : `http://localhost:8100/app/create/<dog_name>`
- MySQL attack : `Malicious dog", "Injected wrong boss name"); -- `

To verify your attack was successfully note that the boss_name usualy is 'N/A', if you open the dog page (you can do this from the home page). You should see a "malicious dog" with a boss name that is not permitted.
