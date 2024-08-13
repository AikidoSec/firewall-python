# Aikido's sample apps
Overview : 
- `django-mysql/` is a Django app using MySQL.
  - It runs **multi-threaded**
  - Runs on 8080. Without Aikido runs on 8081
- `django-mysql-gunicorn/` is a Django app using MySQL and runnin with a Gunicorn backend.
  - it runs 4 processes, called workers, (**multi-process**) which handle requests using 2 threads (**multi-threaded**)
  - Runs on 8082. Without Aikido runs on 8083
- `flask-mongo/` is a Flask app using MongoDB.
  - It runs **multi-threaded**
  - Runs on 8084. Without Aikido runs on 8085
- `flask-mysql/` is a Flask app using MySQL.
  - It runs **single-threaded**
  - Runs on 8086. Without Aikido runs on 8087
- `flask-mysql-uwsgi/` is a Flask app using Mysql and running with a uWSGI backend.
  - It runs 4 processes (**multi-process**) which handle requests **multi-threaded**
  - Runs on 8088. Without aikido runs on 8089
- `flask-postres/` is a Flask app using Postgres
  - It runs **multi-threaded**
  - Runs on 8090. Without aikido runs on 8091
