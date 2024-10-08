import pytest
from unittest.mock import MagicMock
from .sync_data import process_sync_data
from aikido_zen.background_process.routes import Routes


@pytest.fixture
def setup_connection_manager():
    """Fixture to set up a mock connection manager."""
    connection_manager = MagicMock()
    connection_manager.routes = Routes()
    connection_manager.conf.endpoints = ["endpoint1", "endpoint2"]
    connection_manager.conf.bypassed_ips = ["192.168.1.1"]
    connection_manager.conf.blocked_uids = ["user1", "user2"]
    connection_manager.statistics.requests = {"total": 0}  # Initialize total requests
    return connection_manager


def test_process_sync_data_initialization(setup_connection_manager):
    """Test the initialization of routes and hits update."""
    connection_manager = setup_connection_manager
    data = {
        "current_routes": {
            "route1": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits_delta_since_sync": 5,
                "apispec": {"info": "API spec for resource"},
            },
            "route2": {
                "method": "POST",
                "path": "/api/v1/resource",
                "hits_delta_since_sync": 3,
                "apispec": {"info": "API spec for resource"},
            },
        },
        "reqs": 10,  # Total requests to be added
    }

    result = process_sync_data(connection_manager, data, None)

    # Check that routes were initialized correctly
    assert len(connection_manager.routes) == 2
    assert (
        connection_manager.routes.get({"method": "GET", "route": "/api/v1/resource"})[
            "hits"
        ]
        == 5
    )
    assert (
        connection_manager.routes.get({"method": "POST", "route": "/api/v1/resource"})[
            "hits"
        ]
        == 3
    )

    # Check that the total requests were updated
    assert connection_manager.statistics.requests["total"] == 10

    # Check that the return value is correct
    assert result["routes"] == dict(connection_manager.routes.routes)
    assert result["endpoints"] == connection_manager.conf.endpoints
    assert result["bypassed_ips"] == connection_manager.conf.bypassed_ips
    assert result["blocked_uids"] == connection_manager.conf.blocked_uids


def test_process_sync_data_existing_route(setup_connection_manager):
    """Test updating an existing route's hit count."""
    connection_manager = setup_connection_manager
    data = {
        "current_routes": {
            "route1": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits_delta_since_sync": 5,
                "apispec": {"info": "API spec for resource"},
            }
        },
        "reqs": 5,  # Total requests to be added
    }

    # First call to initialize the route
    process_sync_data(connection_manager, data, None)

    # Second call to update the existing route
    data_update = {
        "current_routes": {
            "route1": {
                "method": "GET",
                "path": "/api/v1/resource",
                "hits_delta_since_sync": 10,
                "apispec": {"info": "Updated API spec for resource"},
            }
        },
        "reqs": 15,  # Additional requests to be added
    }

    result = process_sync_data(connection_manager, data_update, None)

    # Check that the hit count was updated correctly
    assert (
        connection_manager.routes.get({"method": "GET", "route": "/api/v1/resource"})[
            "hits"
        ]
        == 15
    )

    # Check that the total requests were updated
    assert connection_manager.statistics.requests["total"] == 20  # 5 + 15

    # Check that the return value is correct
    assert result["routes"] == dict(connection_manager.routes.routes)


def test_process_sync_data_no_routes(setup_connection_manager):
    """Test behavior when no routes are provided."""
    connection_manager = setup_connection_manager
    data = {"current_routes": {}, "reqs": 0}  # No requests to add

    result = process_sync_data(connection_manager, data, None)

    # Check that no routes were initialized
    assert len(connection_manager.routes) == 0

    # Check that the total requests remain unchanged
