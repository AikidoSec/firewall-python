# Vulnerable Lambda with python and PyMongo

## Testing : 
Start the Mongo database with `docker-compose up`

Install packages (including aikido_firewall):
```bash
make install
```

Run safe : 
```bash
make run_safe
```

Run unsafe:
```bash
make run_unsafe
```
