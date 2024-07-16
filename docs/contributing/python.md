# Poetry

To run scripts, run pylint, etc. enter the virtualenv using :
```bash
poetry shell
```

When adding new packages, add them using :
```bash
poetry add <pacakge_name>
```

# Building
If you want to build this python package you can execute :
```bash
make build
```
When you're done or when you want to clean up use :
```bash
make clean
```

# Linting
We use `black` and `pylint`. To run these tools use :
```bash
make lint
```
