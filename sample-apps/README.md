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
  - Runs on 8094. Without Aikido runs on 8095
- `flask-mysql/` is a Flask app using MySQL.
  - It runs **single-threaded**
  - Runs on 8086. Without Aikido runs on 8087
- `flask-mysql-uwsgi/` is a Flask app using Mysql and running with a uWSGI backend.
  - It runs 4 processes (**multi-process**) which handle requests **multi-threaded**
  - Runs on 8088. Without aikido runs on 8089
- `flask-postres/` is a Flask app using Postgres
  - It runs **multi-threaded**
  - Runs on 8090. Without aikido runs on 8091
- `flask-postres-xml/` is a Flask app using Postgres and XML
  - It runs **multi-threaded**
  - Runs on 8092. Without aikido runs on 8093
- `quart-postgres-uvicorn/` is a Quart app using Postgres and with Uvicorn
  - It runs 4 processes, called workers, (**multi-process**) which handles requests **multi-threaded**
  - This application is **asynchronous**
  - Runs on 8096. Without aikido runs on 8097
- `quart-mongo/` is a Quart app using Mongo (Motor)
  - This application is **asynchronous**
  - Runs on 8098. Without aikido runs on 8099
- `django-postgres-gunicorn/` is a Django app using Postgres and running with a Gunicorn backend.
  - it runs 4 processes, called workers, (**multi-process**) which handle requests using 2 threads (**multi-threaded**)
  - Runs on 8100. Without Aikido runs on 8101
- `starlette-postgres-uvicorn/` is a Starlette app using Postgres and with Uvicorn
  - It runs 4 processes, called workers, (**multi-process**) which handles requests **multi-threaded**
  - This application is **asynchronous**
  - Runs on 8102. Without aikido runs on 8103
- `flask-mssql/` is a Flask app using MSSQL.
  - It runs **single-threaded**
  - Runs on 8104. Without Aikido runs on 8105
- `flask-clickhouse-uwsgi/` is a Flask UWSGI app using Clickhouse
  - It runs **multi-threaded**
  - Runs on 8106. Without Aikido runs on 8107
- `flask-openai/` is a Flask app with openai
  - it runs **multi-threaded**
  - Runs on 8108. Without Aikido runs on 8109
