import pytest
from aikido_zen.helpers.token import Token
from aikido_zen.background_process.api.http_api import ReportingApiHTTP
from aikido_zen.background_process.service_config import ServiceConfig
from aikido_zen.background_process.users import Users
from aikido_zen.background_process.hostnames import Hostnames
from aikido_zen.ratelimiting.rate_limiter import RateLimiter
from aikido_zen.background_process.statistics import Statistics
from . import CloudConnectionManager


@pytest.fixture
def setup_cloud_connection_manager():
    block = None  # Replace with appropriate mock or object if needed
    api = ReportingApiHTTP(None)  # Mock or create an instance of ReportingApiHTTP
    token = Token("AIK_TOKEN_TEST")  # Mock or create an instance of Token
    serverless = "some_value"  # Valid serverless value
    return CloudConnectionManager(block, api, token, serverless)


def test_cloud_connection_manager_initialization(setup_cloud_connection_manager):
    manager = setup_cloud_connection_manager

    # Check that instance variables are initialized correctly
    assert manager.block is None
    assert isinstance(manager.api, ReportingApiHTTP)
    assert isinstance(manager.token, Token)
    assert len(manager.routes) == 0
    assert isinstance(manager.hostnames, Hostnames)
    assert isinstance(manager.conf, ServiceConfig)
    assert isinstance(manager.rate_limiter, RateLimiter)
    assert isinstance(manager.users, Users)
    assert isinstance(manager.statistics, Statistics)
    assert manager.middleware_installed is False
    assert manager.serverless == "some_value"


def test_cloud_connection_manager_empty_serverless():
    block = None  # Replace with appropriate mock or object if needed
    api = ReportingApiHTTP(None)  # Mock or create an instance of ReportingApiHTTP
    token = Token("Hellow")  # Mock or create an instance of Token
    serverless = ""  # Invalid serverless value

    with pytest.raises(ValueError, match="Serverless cannot be an empty string"):
        CloudConnectionManager(block, api, token, serverless)


# Additional tests can be added here for other edge cases or scenarios
