import pytest
import requests
# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8102/create"
post_url_nofw = "http://localhost:8103/create"
sync_route_fw = "http://localhost:8102/sync_route"
sync_route_nofw = "http://localhost:8103/sync_route"

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 201


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 201


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500

def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 201


def test_sync_route_with_firewall():
    res = requests.get(sync_route_fw)
    assert res.status_code == 200

def test_sync_route_without_firewall():
    res = requests.get(sync_route_nofw)
    assert res.status_code == 200
