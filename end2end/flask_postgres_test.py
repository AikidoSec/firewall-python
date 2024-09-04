import pytest
import json
import requests
# e2e tests for flask_postgres sample app
post_url_fw = "http://localhost:8090/create"
post_url_nofw = "http://localhost:8091/create"
get_url_cookie_fw = "http://localhost:8090/create_with_cookie"
get_url_cookie_nofw = "http://localhost:8091/create_with_cookie"

def test_safe_response_with_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_response_without_firewall():
    dog_name = "Bobby Tables"
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_dangerous_response_with_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_fw, data={'dog_name': dog_name})
    assert res.status_code == 500

def test_dangerous_response_without_firewall():
    dog_name = "Dangerous Bobby', TRUE); -- "
    res = requests.post(post_url_nofw, data={'dog_name': dog_name})
    assert res.status_code == 200


def test_safe_cookie_creation_with_firewall():
    cookies = {
        "dog_name": "Bobby Tables",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_fw, cookies=cookies)
    assert res.status_code == 200

def test_safe_cookie_creation_without_firewall():
    cookies = {
        "dog_name": "Bobby Tables",
        "corrupt_data": ";;;;;;;;;;;;;"

    }
    res = requests.get(get_url_cookie_nofw, cookies=cookies)
    assert res.status_code == 200


def test_dangerous_cookie_creation_with_firewall():
    cookies = {
        "dog_name": "Bobby', TRUE) -- ",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_fw, cookies=cookies)
    assert res.status_code == 500

def test_dangerous_cookie_creation_without_firewall():
    cookies = {
        "dog_name": "Bobby', TRUE) -- ",
        "corrupt_data": ";;;;;;;;;;;;;"
    }
    res = requests.get(get_url_cookie_nofw, cookies=cookies)
    assert res.status_code == 200
