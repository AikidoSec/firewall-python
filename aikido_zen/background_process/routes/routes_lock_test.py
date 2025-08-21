import os
import random
import sys
import threading
import time

from aikido_zen.background_process.routes import Routes
from aikido_zen.helpers.logging import logger


def add_routes(routes, num_routes, error_count):
    """Function to add routes to the Routes object."""
    try:
        for _ in range(num_routes):
            route_metadata = {
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "route": f"/api/test/{random.randint(1, 10000)}",
            }
            routes.increment_route(route_metadata)
    except Exception:
        error_count["errors_add"] += 1


def export_routes(routes, error_count):
    """Function to export routes with hits."""
    while True:
        try:
            routes.get_routes_with_hits()
        except Exception:
            error_count["errors_export"] += 1


def runtime_error_without_data_lock():
    """Test function to check for runtime errors without data locking."""
    routes = Routes(max_size=5000)

    # Create threads for adding routes and exporting routes
    num_add_threads = 30
    num_routes_per_thread = 3000
    num_export_threads = 20
    error_count = {
        "errors_add": 0,
        "errors_export": 0,
    }

    add_threads = []
    for i in range(num_add_threads):
        print(f"Adding thread {i} started")
        thread = threading.Thread(
            target=add_routes,
            args=(routes, num_routes_per_thread, error_count),
            daemon=True,
        )
        add_threads.append(thread)
        thread.start()

    # Start the export thread
    export_threads = []
    for i in range(num_export_threads):
        print(f"Export thread {i} started")
        thread = threading.Thread(
            target=export_routes, args=(routes, error_count), daemon=True
        )
        export_threads.append(thread)
        thread.start()

    # Wait for all add threads to finish
    time.sleep(1)

    for thread in add_threads:
        print("Closing add thread: " + thread.name)
        thread.join(timeout=20 / 1000)

    # Stop the export thread after adding routes
    for thread in export_threads:
        print("Closing export thread: " + thread.name)
        thread.join(timeout=20 / 1000)

    print(error_count)
    assert error_count["errors_add"] == 0
    assert error_count["errors_export"] == 0


if __name__ == "__main__":
    runtime_error_without_data_lock()
