# Flask Sample app with gUnicorn
It runs **multi-threaded**

## Getting started
Run :
```bash
make run # Runs app with zen
make runZenDisabled # Runs app with zen disabled.
```

- You'll be able to access the Flask Server at : [localhost:8110](http://localhost:8086)
- To Create a reference test dog use `http://localhost:8110/create/doggo`
- To test a sql injection enter the following dog name : `Malicious dog", 1); -- `
- To test commands : `http://localhost:8110/shell`, uses subprocess.run
