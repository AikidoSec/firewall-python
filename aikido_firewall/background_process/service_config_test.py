from .service_config import ServiceConfig


def test_service_config_initialization():
    endpoints = [
        {
            "graphql": False,
            "method": "POST",
            "route": "/v1",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "graphql": True,
            "method": "POST",
            "route": "/v2",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
        {
            "graphql": False,
            "method": "POST",
            "route": "/v3",
            "rate_limiting": {
                "enabled": True,
                "max_requests": 10,
                "window_size_in_ms": 1000,
            },
            "force_protection_off": False,
        },
    ]
    last_updated_at = "2023-10-01"
    service_config = ServiceConfig(endpoints, last_updated_at)

    # Check that non-GraphQL endpoints are correctly filtered
    assert len(service_config.endpoints) == 2
    assert service_config.endpoints[0]["route"] == "/v1"
    assert service_config.endpoints[1]["route"] == "/v3"
    assert service_config.last_updated_at == last_updated_at
