from aikido_zen.helpers.build_route_from_url import build_route_from_url
import pytest
import hashlib


def generate_hash(algorithm):
    data = "test"
    if algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data.encode()).hexdigest()
    else:
        return None


def test_invalid_urls():
    assert build_route_from_url("") == None
    assert build_route_from_url("http") == None


def test_root_urls():
    assert build_route_from_url("/") == "/"
    assert build_route_from_url("http://localhost/") == "/"


def test_replace_numbers():
    assert build_route_from_url("/posts/3") == "/posts/:number"
    assert build_route_from_url("http://localhost/posts/3") == "/posts/:number"
    assert build_route_from_url("http://localhost/posts/3/") == "/posts/:number"
    assert (
        build_route_from_url("http://localhost/posts/3/comments/10")
        == "/posts/:number/comments/:number"
    )
    assert (
        build_route_from_url("/blog/2023/05/great-article")
        == "/blog/:number/:number/great-article"
    )


def test_replace_dates():
    assert build_route_from_url("/posts/2023-05-01") == "/posts/:date"
    assert build_route_from_url("/posts/2023-05-01/") == "/posts/:date"
    assert (
        build_route_from_url("/posts/2023-05-01/comments/2023-05-01")
        == "/posts/:date/comments/:date"
    )
    assert build_route_from_url("/posts/01-05-2023") == "/posts/:date"


def test_ignore_comma_numbers():
    assert build_route_from_url("/posts/3,000") == "/posts/3,000"


def test_ignore_api_version_numbers():
    assert build_route_from_url("/v1/posts/3") == "/v1/posts/:number"


def test_replace_uuids():
    uuids = [
        "d9428888-122b-11e1-b85c-61cd3cbb3210",
        "000003e8-2363-21ef-b200-325096b39f47",
        "a981a0c2-68b1-35dc-bcfc-296e52ab01ec",
        "109156be-c4fb-41ea-b1b4-efe1671c5836",
        "90123e1c-7512-523e-bb28-76fab9f2f73d",
        "1ef21d2f-1207-6660-8c4f-419efbd44d48",
        "017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
        "0d8f23a0-697f-83ae-802e-48f3756dd581",
    ]
    for uuid in uuids:
        assert build_route_from_url(f"/posts/{uuid}") == "/posts/:uuid"


def test_ignore_invalid_uuids():
    assert (
        build_route_from_url("/posts/00000000-0000-1000-6000-000000000000")
        == "/posts/00000000-0000-1000-6000-000000000000"
    )


def test_ignore_strings():
    assert build_route_from_url("/posts/abc") == "/posts/abc"


def test_replace_email_addresses():
    assert build_route_from_url("/login/john.doe@acme.com") == "/login/:email"
    assert build_route_from_url("/login/john.doe+alias@acme.com") == "/login/:email"


def test_replace_ip_addresses():
    assert build_route_from_url("/block/1.2.3.4") == "/block/:ip"
    assert (
        build_route_from_url("/block/2001:2:ffff:ffff:ffff:ffff:ffff:ffff")
        == "/block/:ip"
    )
    assert build_route_from_url("/block/64:ff9a::255.255.255.255") == "/block/:ip"
    assert build_route_from_url("/block/100::") == "/block/:ip"
    assert build_route_from_url("/block/fec0::") == "/block/:ip"
    assert build_route_from_url("/block/227.202.96.196") == "/block/:ip"


def test_replace_hashes():
    assert build_route_from_url(f"/files/{generate_hash('md5')}") == "/files/:hash"
    assert build_route_from_url(f"/files/{generate_hash('sha1')}") == "/files/:hash"
    assert build_route_from_url(f"/files/{generate_hash('sha256')}") == "/files/:hash"
    assert build_route_from_url(f"/files/{generate_hash('sha512')}") == "/files/:hash"


def test_replace_secrets():
    assert (
        build_route_from_url("/confirm/CnJ4DunhYfv2db6T1FRfciRBHtlNKOYrjoz")
        == "/confirm/:secret"
    )
