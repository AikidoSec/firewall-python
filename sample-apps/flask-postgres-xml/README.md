# Flask w/ Postgres and xml Sample app
It runs **multi-threaded**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Flask Server at : [localhost:8092](http://localhost:8092)
- To upload xml use `http://localhost:8092/xml/`

- To test a sql injection enter the following xml snippet: 
```xml
<dogs><dog dog_name="Malicious dog', TRUE); -- " /></dogs>
```
