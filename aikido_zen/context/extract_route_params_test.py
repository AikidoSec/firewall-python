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


def test_normal_urls():
    assert extract_route_params("http://localhost:8080/a/b/abc2393027def/def") == []


def test_with_empty_route():
    url1 = "http://localhost:8080"
    assert extract_route_params(url1) == []

    url2 = "http://localhost:8080"
    assert extract_route_params(url2) == []


def test_special_characters():
    url1 = "http://localhost:8080/app/shell/!@#$%^&*()"  # Everything past hashtag is not url anymore
    assert extract_route_params(url1) == ["!@", "app/shell/!@"]

    url2 = "http://localhost:8080/app/shell/space test"
    assert extract_route_params(url2) == ["space test", "app/shell/space test"]

    url3 = "http://localhost:8080/app/shell/hello%20world"
    assert extract_route_params(url3) == ["hello world", "app/shell/hello%20world"]


def test_numeric_segments():
    # Alphanum is ignored:
    url1 = "http://localhost:8080/app/shell/12345"
    assert extract_route_params(url1) == []

    url2 = "http://localhost:8080/app/shell/67890/abc"
    assert extract_route_params(url2) == []


def test_mixed_segments():
    url1 = "http://localhost:8080/app/shell/abc123/!@#"
    assert extract_route_params(url1) == ["!@", "app/shell/abc123/!@"]

    url2 = "http://localhost:8080/app/shell/abc/123/!@#"
    assert extract_route_params(url2) == ["!@", "app/shell/abc/123/!@"]


def test_encoded_and_unencoded():
    url1 = "http://localhost:8080/app/shell/%E2%9C%93"
    assert extract_route_params(url1) == ["✓", "app/shell/%E2%9C%93"]

    url2 = "http://localhost:8080/app/shell/%E2%9C%93/normal"
    assert extract_route_params(url2) == ["✓", "app/shell/%E2%9C%93/normal"]


def test_no_params():
    url1 = "http://localhost:8080/app/shell/"
    assert extract_route_params(url1) == []

    url2 = "http://localhost:8080/app/"
    assert extract_route_params(url2) == []


def test_edge_cases():
    url1 = "http://localhost:8080/app/shell/.."
    assert extract_route_params(url1) == ["..", "app/shell/.."]

    url2 = "http://localhost:8080/app/shell/./"
    assert extract_route_params(url2) == ["app/shell/./"]


def test_long_urls():
    url1 = "http://localhost:8080/app./shell/" + "a" * 1000
    assert extract_route_params(url1) == ["app.", "app./shell/" + "a" * 1000]

    url2 = "http://localhost:8080/app./shell/" + "b" * 1000 + "/c" * 1000
    assert extract_route_params(url2) == [
        "app.",
        "app./shell/" + "b" * 1000 + "/c" * 1000,
    ]


def test_query_parameters():
    # Test query parameters are ignored:
    url1 = "http://localhost:8080/app/./shell/?param=value"
    assert extract_route_params(url1) == ["app/./shell/"]

    url2 = "http://localhost:8080/app/./shell/?key1=value1&key2=value2"
    assert extract_route_params(url2) == ["app/./shell/"]


def test_fragment_identifiers():
    # Fragments should be ignored:
    url1 = "http://localhost:8080/app/./shell/#section1"
    assert extract_route_params(url1) == ["app/./shell/"]

    url2 = "http://localhost:8080/app/shell/#/path/to/resource"
    assert extract_route_params(url2) == []
