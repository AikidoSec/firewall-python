import pytest
from .extract_route_params import extract_route_params


def test_with_urlencoded_urls():
    url1 = "http://localhost:8080/app/shell/ls%20-la"
    assert extract_route_params(url1) == ["ls -la", "app/shell/ls%20-la"]

    url2 = "http://localhost:8080/app/shell/ls -la"
    assert extract_route_params(url2) == ["ls -la", "app/shell/ls -la"]


def test_uses_keys():
    url = "http://localhost:8080/app/shell/me@woutfeys.be/017shell/127.0.0.1/"
    assert extract_route_params(url) == [
        "me@woutfeys.be",
        "127.0.0.1",
        "app/shell/me@woutfeys.be/017shell/127.0.0.1/",
    ]


def test_with_empty_route():
    url1 = "http://localhost:8080"
    assert extract_route_params(url1) == []

    url2 = "http://localhost:8080"
    assert extract_route_params(url2) == []
