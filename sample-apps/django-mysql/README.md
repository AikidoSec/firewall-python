# Sample Django/Mysql App
It runs **multi-threaded**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```
This will expose a Django web server at [localhost:8080](http://localhost:8080)

## URLS : 
- Homepage : `http://localhost:8080/app`
- Create a dog : `http://localhost:8080/app/create/<dog_name>`
- MySQL attack : `Malicious dog", "Injected wrong boss name"); -- `

To verify your attack was successfully note that the boss_name usualy is 'N/A', if you open the dog page (you can do this from the home page). You should see a "malicious dog" with a boss name that is not permitted.
