# Aikido's sample apps
Overview : 
- `django-mysql/` is a Django app using MySQL. 
  - It runs **multi-threaded**
- `django-mysql-gunicorn/` is a Django app using MySQL and runnin with a Gunicorn backend.
  - it runs 4 processes, called workers, (**multi-process**) which handle requests using 2 threads (**multi-threaded**)
- `flask-mongo/` is a Flask app using MongoDB.
  - It runs **multi-threaded**
- `flask-mysql/` is a Flask app using MySQL.
  - It runs **single-threaded**
- `flask-mysql-uwsgi/` is a Flask app using Mysql and running with a uWSGI backend.
  - It runs 4 processes (**multi-process**) which handle requests **multi-threaded**
- `flask-postres/` is a Flask app using Postgres
  - It runs **multi-threaded**
