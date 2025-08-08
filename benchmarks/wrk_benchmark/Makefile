
.PHONY: benchmark_starlette-postgres-uvicorn
benchmark_starlette-postgres-uvicorn:
	@echo "Running wrk benchmarks for Starlette w/ Postgres, Uvicorn"
	python starlette_postgres_uvicorn.py

.PHONY: benchmark_flask-mysql-uwsgi
benchmark_flask-mysql-uwsgi:
	@echo "Running wrk benchmarks for Flask w/ MySQL, UWSGI"
	python flask_mysql_uwsgi.py

.PHONY: benchmark_flask-mysql
benchmark_flask-mysql:
	@echo "Running wrk benchmarks for Flask w/ MySQL (built-in wsgi server)"
	python flask_mysql.py
