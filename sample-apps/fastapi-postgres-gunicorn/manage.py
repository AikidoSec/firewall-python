#!/usr/bin/env python3

import os
import sys
from gunicorn.app.base import BaseApplication
from app import create_app

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Config:
    def __init__(self):
        # Default configuration values
        self.gunicorn_workers_count = 4  # (2 x $num_cores) + 1
        self.threads_per_worker = 1
        self.gunicorn_keepalive = 2
        self.gunicorn_max_requests = 1000
        self.gunicorn_max_requests_jitter = 50
        self.requests_read_timeout = 30
        self.gunicorn_graceful_timeout = 30
        self.log_level = "info"
        self.app_dir = os.path.dirname(os.path.abspath(__file__))

def run_gunicorn_server():
    # Optimized Gunicorn with UvicornWorker for high-performance async concurrency
    # Relies on the operating system to provide all of the load balancing
    # Generally we recommend (2 x $num_cores) + 1 as the number of workers

    config = Config()
    WORKERS = config.gunicorn_workers_count
    WORKER_CONNECTIONS = config.threads_per_worker * 100

    class GunicornApplication(BaseApplication):
        def load_config(self):
            self.cfg.set("bind", f"unix:{os.path.join(config.app_dir, 'da.sock')}")
            self.cfg.set("accesslog", "-")
            self.cfg.set("workers", WORKERS)
            self.cfg.set("worker_class", "uvicorn.workers.UvicornWorker")
            self.cfg.set("worker_connections", WORKER_CONNECTIONS)
            self.cfg.set("loglevel", config.log_level)

            # Performance optimizations
            self.cfg.set("keepalive", config.gunicorn_keepalive)
            self.cfg.set("max_requests", config.gunicorn_max_requests)
            self.cfg.set("max_requests_jitter", config.gunicorn_max_requests_jitter)

            # Timeout optimizations
            self.cfg.set("timeout", config.requests_read_timeout)
            self.cfg.set("graceful_timeout", config.gunicorn_graceful_timeout)

        def load(self):
            return create_app()

        def init(self, parser, opts, args):
            return

    if __name__ == "__main__":
        wsgi_server = GunicornApplication()
        wsgi_server.run()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gunicornserver":
        run_gunicorn_server()
    else:
        print("Usage: python manage.py gunicornserver")
        sys.exit(1)