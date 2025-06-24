import pytest
from unittest.mock import MagicMock
from .sync_data import process_sync_data
from aikido_zen.storage.routes import Routes
from aikido_zen.helpers.iplist import IPList
from ..packages import PackagesStore
from ...storage.hostnames import Hostnames
from ...storage.statistics import Statistics


@pytest.fixture
def setup_connection_manager():
    """Fixture to set up a mock connection manager."""
    connection_manager = MagicMock()
    connection_manager.routes = Routes()
    connection_manager.hostnames = Hostnames()
    connection_manager.conf.endpoints = ["endpoint1", "endpoint2"]

    connection_manager.conf.bypassed_ips = IPList()
    connection_manager.conf.bypassed_ips.add("192.168.1.1")
    connection_manager.conf.blocked_uids = ["user1", "user2"]
    connection_manager.conf.last_updated_at = 200
    connection_manager.statistics = Statistics()
    connection_manager.middleware_installed = False
    return connection_manager


def test_process_sync_data_initialization(setup_connection_manager):
    """Test the initialization of routes and hits update."""
    connection_manager = setup_connection_manager
    test_hostnames = Hostnames()
    test_hostnames.add("example2.com", 443, 15)
    test_hostnames.add("bumblebee.com", 8080)

    data = {
        "routes": {
            "GET:/api/v1/resource": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits": 5,
                "hits_delta_since_sync": 2000,
                "apispec": {"info": "API spec for resource"},
            },
            "POST:/api/v1/resource": {
                "method": "POST",
                "path": "/api/v1/resource",
                "hits": 3,
                "apispec": {"info": "API spec for resource"},
            },
        },
        "stats": {
            "startedAt": 1,
            "endedAt": 1,
            "requests": {
                "total": 10,
                "aborted": 0,
                "attacksDetected": {
                    "total": 5,
                    "blocked": 0,
                },
            },
        },
        "middleware_installed": False,
        "hostnames": test_hostnames.as_array(),
        "packages": [
            {
                "name": "test-package",
                "version": "2.2.0",
                "cleared": False,
            }
        ],
    }

    result = process_sync_data(connection_manager, data, None)

    # Check that routes were initialized correctly
    assert len(connection_manager.routes.export()) == 2
    assert connection_manager.routes.get("GET", "/api/v1/resource")["hits"] == 5
    assert connection_manager.routes.get("POST", "/api/v1/resource")["hits"] == 3

    # Check that the total requests were updated
    assert connection_manager.statistics.get_record()["requests"] == {
        "aborted": 0,
        "attacksDetected": {"blocked": 0, "total": 5},
        "total": 10,
    }

    # Check that the return value is correct
    assert result["routes"] == dict(connection_manager.routes.routes)
    assert result["config"] == connection_manager.conf
    assert connection_manager.middleware_installed == False
    assert connection_manager.hostnames.as_array() == [
        {"hits": 15, "hostname": "example2.com", "port": 443},
        {"hits": 1, "hostname": "bumblebee.com", "port": 8080},
    ]
    assert PackagesStore.get_package("test-package") == {
        "name": "test-package",
        "version": "2.2.0",
        "cleared": False,
    }


def test_process_sync_data_with_last_updated_at_below_zero(setup_connection_manager):
    """Test the initialization of routes and hits update."""
    connection_manager = setup_connection_manager
    connection_manager.conf.last_updated_at = -1
    data = {
        "routes": {
            "GET:/api/v1/resource": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits": 5,
                "apispec": {"info": "API spec for resource"},
            },
            "POST:/api/v1/resource": {
                "method": "POST",
                "path": "/api/v1/resource",
                "hits": 3,
                "apispec": {"info": "API spec for another resource"},
            },
        },
        "stats": {
            "startedAt": 1,
            "endedAt": 1,
            "requests": {
                "total": 10,
                "aborted": 0,
                "attacksDetected": {
                    "total": 5,
                    "blocked": 0,
                },
            },
        },
        "middleware_installed": True,
    }

    result = process_sync_data(connection_manager, data, None)

    # Check that routes were initialized correctly
    assert len(connection_manager.routes.export()) == 2
    assert connection_manager.routes.get("GET", "/api/v1/resource") == {
        "hits": 5,
        "method": "GET",
        "path": "/api/v1/resource",
        "apispec": {"info": "API spec for resource"},
    }
    assert connection_manager.routes.get("POST", "/api/v1/resource") == {
        "hits": 3,
        "method": "POST",
        "path": "/api/v1/resource",
        "apispec": {"info": "API spec for another resource"},
    }

    # Check that the total requests were updated
    assert connection_manager.statistics.get_record()["requests"] == {
        "aborted": 0,
        "attacksDetected": {"blocked": 0, "total": 5},
        "total": 10,
    }
    assert connection_manager.middleware_installed == True
    assert len(connection_manager.hostnames.as_array()) == 0
    # Check that the return value is correct
    assert result == {}


def test_process_sync_data_existing_route_and_hostnames(setup_connection_manager):
    """Test updating an existing route's hit count."""
    connection_manager = setup_connection_manager
    connection_manager.hostnames.add("example.com", 443, 200)
    connection_manager.hostnames.add("example.org", 443)
    connection_manager.hostnames.add("a.com", 443)

    hostnames_sync = Hostnames()
    hostnames_sync.add("example.com", 443, 15)
    hostnames_sync.add("c.com", 443)

    data = {
        "routes": {
            "route1": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits": 5,
                "apispec": {"info": "API spec for resource"},
            }
        },
        "stats": {
            "startedAt": 1,
            "endedAt": 1,
            "requests": {
                "total": 5,
                "aborted": 0,
                "attacksDetected": {
                    "total": 5,
                    "blocked": 0,
                },
            },
        },
        "hostnames": hostnames_sync.as_array(),
    }

    # First call to initialize the route
    process_sync_data(connection_manager, data, None)

    # Second call to update the existing route
    data_update = {
        "routes": {
            "route1": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits": 10,
                "apispec": {"info": "Updated API spec for resource"},
            }
        },
        "stats": {
            "startedAt": 1,
            "endedAt": 1,
            "requests": {
                "total": 15,
                "aborted": 0,
                "attacksDetected": {
                    "total": 5,
                    "blocked": 0,
                },
            },
        },
    }

    result = process_sync_data(connection_manager, data_update, None)

    # Check that the hit count was updated correctly
    assert connection_manager.routes.get("GET", "/api/v1/resource")["hits"] == 15

    # Check that the total requests were updated
    assert connection_manager.statistics.get_record()["requests"] == {
        "aborted": 0,
        "attacksDetected": {"blocked": 0, "total": 10},
        "total": 20,
    }
    assert connection_manager.middleware_installed == False
    assert connection_manager.hostnames.as_array() == [
        {"hits": 215, "hostname": "example.com", "port": 443},
        {"hits": 1, "hostname": "example.org", "port": 443},
        {"hits": 1, "hostname": "a.com", "port": 443},
        {"hits": 1, "hostname": "c.com", "port": 443},
    ]

    # Check that the return value is correct
    assert result["routes"] == dict(connection_manager.routes.routes)


def test_process_sync_data_no_routes(setup_connection_manager):
    """Test behavior when no routes are provided."""
    connection_manager = setup_connection_manager
    data = {"routes": {}, "reqs": 0}  # No requests to add

    result = process_sync_data(connection_manager, data, None)

    # Check that no routes were initialized
    assert len(connection_manager.routes.export()) == 0

    # Check that the total requests remain unchanged


def test_process_sync_data_routes_undefined(setup_connection_manager):
    """Test behavior when no routes are provided."""
    connection_manager = setup_connection_manager
    data = {"sdfsdsdfsdfds": {}, "reqs": 0}  # No requests to add

    result = process_sync_data(connection_manager, data, None)

    # Check that no routes were initialized
    assert len(connection_manager.routes.export()) == 0

    # Check that the total requests remain unchanged
