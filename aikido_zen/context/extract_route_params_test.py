import pytest
from .extract_route_params import extract_route_params


def test_with_urlencoded_urls():
    url1 = "http://localhost:8080/app/shell/ls%20-la"
    assert extract_route_params(url1) == ["ls -la"]
